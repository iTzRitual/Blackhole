"""Deterministic query projections from the Blackhole state snapshot.

The semantic model extracts observations and relations. This module selects
the small, query-relevant view that is returned to the public response
contract. Arithmetic, date windows, history traversal, and duplicate
bookkeeping happen here rather than in a model query. The projector consumes
only the public contract, query bundle, and the derived snapshot; it never
reads expected output.
"""

from __future__ import annotations

import copy
import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


class ResponseProjector:
    def __init__(self, contract: dict[str, Any], query_bundle: dict[str, Any]) -> None:
        self.contract = contract
        self.query_bundle = query_bundle
        self.subject_kinds = {
            entry["id"]: entry.get("kind")
            for entry in contract.get("public_ontology", {}).get("subjects", [])
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)
        }

    def _kind(self, subject: str) -> str | None:
        return self.subject_kinds.get(subject)

    def _subjects_of_kind(self, snapshot: dict[str, Any], kind: str) -> list[str]:
        """Return public subjects of a kind that are present or declared."""

        subjects = {
            subject
            for subject, subject_kind in self.subject_kinds.items()
            if subject_kind == kind
        }
        for collection in (snapshot.get("current_facts", []), snapshot.get("history", [])):
            if not isinstance(collection, list):
                continue
            for item in collection:
                if not isinstance(item, dict) or not isinstance(item.get("subject"), str):
                    continue
                subject = item["subject"]
                if self._kind(subject) == kind:
                    subjects.add(subject)
        return sorted(subjects)

    def _aggregate_subject(self, snapshot: dict[str, Any]) -> str:
        subjects = self._subjects_of_kind(snapshot, "aggregate")
        return subjects[0] if subjects else "aggregate"

    @staticmethod
    def _clean_value(value: Any) -> Any:
        """Apply small, public-value normalizations without changing meaning."""

        if isinstance(value, dict):
            result = {key: ResponseProjector._clean_value(item) for key, item in value.items()}
            period = result.get("billing_period")
            if isinstance(period, str) and period.casefold().strip() in {"monthly", "per month", "month"}:
                result["billing_period"] = "month"
            return result
        if isinstance(value, list):
            return [ResponseProjector._clean_value(item) for item in value]
        if isinstance(value, str) and value.casefold().strip() in {"monthly", "per month"}:
            return "month"
        return copy.deepcopy(value)

    @staticmethod
    def _fact(
        subject: str,
        predicate: str,
        status: str,
        source_refs: list[str],
        *,
        value: Any = None,
        unknown_reason: str | None = None,
    ) -> dict[str, Any]:
        item: dict[str, Any] = {
            "subject": subject,
            "predicate": predicate,
            "knowledge_status": status,
            "source_refs": sorted({ref for ref in source_refs if isinstance(ref, str)}),
        }
        if status == "unknown":
            item["unknown_reason"] = unknown_reason or "missing"
        else:
            item["value"] = ResponseProjector._clean_value(value)
        return item

    @classmethod
    def _fact_from_state(cls, item: dict[str, Any], *, predicate: str | None = None) -> dict[str, Any]:
        subject = str(item.get("subject"))
        output_predicate = predicate or str(item.get("predicate"))
        status = str(item.get("knowledge_status", "unknown"))
        refs = item.get("source_refs", [])
        if not isinstance(refs, list):
            refs = []
        if status == "unknown":
            return cls._fact(
                subject,
                output_predicate,
                status,
                refs,
                unknown_reason=str(item.get("unknown_reason") or "missing"),
            )
        return cls._fact(
            subject,
            output_predicate,
            status,
            refs,
            value=item.get("value"),
        )

    def _current_facts(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            self._fact_from_state(item)
            for item in snapshot.get("current_facts", [])
            if isinstance(item, dict)
        ]

    def _history(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        return [item for item in snapshot.get("history", []) if isinstance(item, dict)]

    @staticmethod
    def _sequence(item: dict[str, Any]) -> int:
        value = item.get("sequence")
        return value if isinstance(value, int) else -1

    def _effective_current(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        """Return current facts plus explicitly linked price supersessions."""

        facts = self._current_facts(snapshot)
        by_key = {(item["subject"], item["predicate"]): item for item in facts}
        history = self._history(snapshot)
        history_by_event: dict[str, list[dict[str, Any]]] = {}
        for item in history:
            history_by_event.setdefault(str(item.get("event_id")), []).append(item)
        for relation in snapshot.get("relationships", []):
            if not isinstance(relation, dict):
                continue
            changed_fields = relation.get("changed_fields", [])
            source_event = relation.get("source_event_id")
            if "current_price" not in changed_fields or not isinstance(source_event, str):
                continue
            for observation in history_by_event.get(source_event, []):
                if observation.get("predicate") != "historical_price" or "value" not in observation:
                    continue
                key = (str(observation.get("subject")), "current_price")
                by_key[key] = self._fact(
                    key[0],
                    key[1],
                    str(observation.get("knowledge_status", "known")),
                    list(observation.get("source_refs", [source_event])),
                    value=observation.get("value"),
                    unknown_reason=observation.get("unknown_reason"),
                )
        return list(by_key.values())

    def _decompose_objects(self, facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = list(facts)
        existing = {(item["subject"], item["predicate"]) for item in result}
        for item in facts:
            value = item.get("value")
            if item.get("knowledge_status") not in {"known", "inferred"} or not isinstance(value, dict):
                continue
            if item.get("predicate") not in {
                "current_price",
                "last_charge",
                "current_amount",
                "purchased_total",
                "premium",
                "quoted_amount",
            }:
                continue
            for field in ("currency", "billing_period"):
                if field not in value or (item["subject"], field) in existing:
                    continue
                result.append(
                    self._fact(
                        item["subject"],
                        field,
                        item["knowledge_status"],
                        item.get("source_refs", []),
                        value=value[field],
                    )
                )
                existing.add((item["subject"], field))
        return result

    @staticmethod
    def _dedupe(assertions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for item in assertions:
            semantic = dict(item)
            semantic.pop("source_refs", None)
            key = json.dumps(semantic, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    def _subscription_current(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        allowed = {
            "status",
            "current_price",
            "billing_period",
            "currency",
            "cancellation_intent",
            "cancellation_requested",
            "last_charge",
            "termination_date",
            "price_effective",
            "next_renewal",
        }
        return [
            item
            for item in self._decompose_objects(self._effective_current(snapshot))
            if self._kind(item["subject"]) == "subscription" and item["predicate"] in allowed
        ]

    def _subscription_history(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen_values: set[str] = set()
        for item in sorted(self._history(snapshot), key=self._sequence):
            subject = item.get("subject")
            if not isinstance(subject, str) or self._kind(subject) != "subscription" or item.get("predicate") not in {"current_price", "historical_price"}:
                continue
            if item.get("operation") == "duplicate" or item.get("knowledge_status") not in {"known", "inferred"}:
                continue
            if "value" not in item:
                continue
            value = self._clean_value(item["value"])
            key = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if key in seen_values:
                continue
            seen_values.add(key)
            result.append(
                self._fact(
                    subject,
                    "historical_price",
                    str(item.get("knowledge_status", "known")),
                    list(item.get("source_refs", [str(item.get("event_id"))])),
                    value=value,
                )
            )
        return result

    def _latest_observed_date(self, snapshot: dict[str, Any]) -> date | None:
        dates = [
            str(item.get("observed_at"))[:10]
            for item in snapshot.get("event_index", [])
            if isinstance(item, dict) and isinstance(item.get("observed_at"), str)
        ]
        for value in reversed(dates):
            try:
                return date.fromisoformat(value)
            except ValueError:
                continue
        return None

    @staticmethod
    def _date_value(value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None

    def _attention(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        current = self._current_facts(snapshot)
        by_subject: dict[str, dict[str, dict[str, Any]]] = {}
        for item in current:
            by_subject.setdefault(item["subject"], {})[item["predicate"]] = item
        result: list[dict[str, Any]] = []
        checkpoint_date = self._latest_observed_date(snapshot)
        if checkpoint_date is not None:
            end_date = checkpoint_date + timedelta(days=14)
            for subject, facts in by_subject.items():
                if self._kind(subject) != "task":
                    continue
                status = facts.get("status")
                deadline = facts.get("deadline")
                if not status or status.get("knowledge_status") == "unknown" or not isinstance(status.get("value"), str):
                    continue
                if status["value"].casefold() in {"cancelled", "canceled", "completed", "done", "closed"}:
                    continue
                if not deadline or deadline.get("knowledge_status") == "unknown":
                    continue
                deadline_date = self._date_value(deadline.get("value"))
                if deadline_date is None or not checkpoint_date <= deadline_date <= end_date:
                    continue
                result.append(
                    self._fact(
                        subject,
                        "needs_attention",
                        "known",
                        list(deadline.get("source_refs", [])) + list(status.get("source_refs", [])),
                        value={"reason": "open task deadline", "deadline": deadline.get("value")},
                    )
                )

        global_approval = next(
            (
                facts.get("approval_required")
                for subject, facts in by_subject.items()
                if self._kind(subject) == "aggregate" and facts.get("approval_required") is not None
            ),
            None,
        )
        global_requires_approval = (
            global_approval is not None
            and global_approval.get("knowledge_status") in {"known", "inferred"}
            and global_approval.get("value") is True
        )
        for subject, facts in by_subject.items():
            if self._kind(subject) != "action":
                continue
            required = facts.get("approval_required")
            requires_approval = global_requires_approval or (
                required is not None
                and required.get("knowledge_status") in {"known", "inferred"}
                and required.get("value") is True
            )
            executed = facts.get("executed")
            if not requires_approval or executed is None or executed.get("knowledge_status") == "unknown":
                continue
            if executed.get("value") is True:
                continue
            result.append(
                self._fact(
                    subject,
                    "needs_attention",
                    "known",
                    list(executed.get("source_refs", []))
                    + list(required.get("source_refs", []) if required else [])
                    + list(global_approval.get("source_refs", []) if global_approval else []),
                    value={"reason": "approval required", "executed": False},
                )
            )
        return self._dedupe(result)

    def _insurance(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        allowed = {"effective_date", "expiry_date", "policy_id", "premium", "status", "beneficiary", "claim_number"}
        return [
            item
            for item in self._effective_current(snapshot)
            if self._kind(item["subject"]) == "insurance" and item["predicate"] in allowed
        ]

    @staticmethod
    def _decimal(value: Any) -> Decimal | None:
        raw = value.get("amount") if isinstance(value, dict) else value
        if isinstance(raw, bool) or raw is None:
            return None
        try:
            number = Decimal(str(raw))
        except (InvalidOperation, ValueError):
            return None
        return number if number.is_finite() else None

    @staticmethod
    def _amount_value(number: Decimal, currency: Any) -> dict[str, Any]:
        return {"amount": format(number, "f"), "currency": currency}

    @staticmethod
    def _render_number(number: Decimal) -> int | str:
        return int(number) if number == number.to_integral_value() else format(number, "f")

    def _service_costs(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        history = self._history(snapshot)
        by_subject_event: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for item in history:
            subject = item.get("subject")
            if not isinstance(subject, str) or self._kind(subject) != "service":
                continue
            by_subject_event.setdefault(subject, {}).setdefault(str(item.get("event_id")), []).append(item)

        result: list[dict[str, Any]] = []
        for subject in sorted(by_subject_event):
            by_event = by_subject_event[subject]
            bills: dict[str, dict[str, Any]] = {}
            missing_periods: set[str] = set()
            missing_refs: list[str] = []
            unobserved_refs: list[str] = []
            for event_id, items in by_event.items():
                if any(item.get("operation") == "duplicate" for item in items):
                    continue
                periods: list[str] = []
                amount_item: dict[str, Any] | None = None
                for item in items:
                    refs = item.get("source_refs", [event_id])
                    if not isinstance(refs, list):
                        refs = [event_id]
                    if item.get("predicate") == "observed_periods" and item.get("knowledge_status") in {"known", "inferred"} and isinstance(item.get("value"), list):
                        periods.extend(str(value) for value in item["value"] if isinstance(value, str))
                    if item.get("predicate") == "observed_total" and item.get("knowledge_status") in {"known", "inferred"} and self._decimal(item.get("value")) is not None:
                        amount_item = item
                    if item.get("predicate") == "missing_periods" and item.get("knowledge_status") in {"known", "inferred"} and isinstance(item.get("value"), list):
                        missing_periods.update(str(value) for value in item["value"] if isinstance(value, str))
                        missing_refs.extend(refs)
                    if item.get("predicate") == "unobserved_periods":
                        unobserved_refs.extend(refs)
                if amount_item is None:
                    continue
                refs = amount_item.get("source_refs", [event_id])
                if not isinstance(refs, list):
                    refs = [event_id]
                key = periods[0] if periods else event_id
                candidate = {
                    "event_id": event_id,
                    "sequence": self._sequence(amount_item),
                    "value": amount_item.get("value"),
                    "source_refs": list(refs),
                }
                prior = bills.get(key)
                if prior is None or candidate["sequence"] >= prior["sequence"]:
                    bills[key] = candidate

            if not bills:
                continue
            refs = [ref for item in bills.values() for ref in item["source_refs"]]
            totals = [self._decimal(item["value"]) for item in bills.values()]
            currencies = [
                item["value"].get("currency")
                for item in bills.values()
                if isinstance(item["value"], dict) and item["value"].get("currency") is not None
            ]
            result.append(self._fact(subject, "observed_bill_count", "known", refs, value=len(bills)))
            if all(value is not None for value in totals) and currencies and len({str(value).casefold() for value in currencies}) == 1:
                result.append(
                    self._fact(
                        subject,
                        "observed_total",
                        "known",
                        refs,
                        value=self._amount_value(sum(value for value in totals if value is not None), currencies[0]),
                    )
                )
            observed_periods = sorted(key for key in bills if key.startswith("20") and len(key) == 7)
            if observed_periods:
                result.append(self._fact(subject, "observed_periods", "known", refs, value=observed_periods))
            if missing_periods:
                result.append(self._fact(subject, "missing_periods", "known", missing_refs, value=sorted(missing_periods)))
            if unobserved_refs or missing_periods:
                result.append(
                    self._fact(
                        subject,
                        "unobserved_periods",
                        "unknown",
                        unobserved_refs or missing_refs,
                        unknown_reason="no_capture_for_period",
                    )
                )
            latest = max(bills.values(), key=lambda item: item["sequence"])
            result.append(self._fact(subject, "current_amount", "known", latest["source_refs"], value=latest["value"]))
        return result

    def _merchant_observations(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        history = self._history(snapshot)
        by_subject: dict[str, dict[str, Any]] = {}
        for item in history:
            subject = item.get("subject")
            if not isinstance(subject, str) or self._kind(subject) != "merchant" or item.get("operation") == "duplicate":
                continue
            event_id = str(item.get("event_id"))
            bucket = by_subject.setdefault(
                subject,
                {"purchase_events": {}, "consumption": [], "explicit_zero": [], "unobserved_refs": []},
            )
            if item.get("predicate") in {"purchase_count", "purchased_total"} and item.get("knowledge_status") in {"known", "inferred"}:
                bucket["purchase_events"].setdefault(event_id, {})[item["predicate"]] = item
            elif item.get("predicate") == "confirmed_consumption_quantity" and item.get("knowledge_status") in {"known", "inferred"} and self._decimal(item.get("value")) is not None:
                bucket["consumption"].append(item)
            elif item.get("predicate") == "explicit_zero_is_supported" and item.get("knowledge_status") in {"known", "inferred"}:
                bucket["explicit_zero"].append(item)
            elif item.get("predicate") == "unobserved_consumption":
                refs = item.get("source_refs", [event_id])
                bucket["unobserved_refs"].extend(refs if isinstance(refs, list) else [event_id])

        result: list[dict[str, Any]] = []
        for subject in sorted(by_subject):
            bucket = by_subject[subject]
            purchase_events = bucket["purchase_events"]
            consumption = bucket["consumption"]
            explicit_zero = bucket["explicit_zero"]
            unobserved_refs = bucket["unobserved_refs"]
            refs = [ref for event in purchase_events.values() for item in event.values() for ref in item.get("source_refs", [])]
            if purchase_events:
                result.append(
                    self._fact(
                        subject,
                        "purchase_count",
                        "known",
                        refs,
                        value=self._render_number(sum(self._decimal(item.get("purchase_count", {}).get("value")) or Decimal(0) for item in purchase_events.values())),
                    )
                )
                purchase_amounts = [
                    self._decimal(item["purchased_total"].get("value"))
                    for item in purchase_events.values()
                    if "purchased_total" in item
                ]
                currencies = [
                    item["purchased_total"].get("value", {}).get("currency")
                    for item in purchase_events.values()
                    if "purchased_total" in item and isinstance(item["purchased_total"].get("value"), dict)
                ]
                if purchase_amounts and all(value is not None for value in purchase_amounts) and currencies and len({str(value).casefold() for value in currencies}) == 1:
                    result.append(
                        self._fact(
                            subject,
                            "purchased_total",
                            "known",
                            refs,
                            value=self._amount_value(sum(value for value in purchase_amounts if value is not None), currencies[0]),
                        )
                    )
            consumption_refs = [ref for item in consumption for ref in item.get("source_refs", [])]
            if consumption:
                result.append(
                    self._fact(
                        subject,
                        "confirmed_consumption_quantity",
                        "known",
                        consumption_refs,
                        value=self._render_number(sum(self._decimal(item.get("value")) or Decimal(0) for item in consumption)),
                    )
                )
                result.append(self._fact(subject, "consumption_observation_count", "known", consumption_refs, value=len(consumption)))
                zero_supported = any(item.get("value") is True for item in explicit_zero)
                zero_refs = [ref for item in explicit_zero for ref in item.get("source_refs", [])]
                result.append(self._fact(subject, "explicit_zero_is_supported", "known", zero_refs or consumption_refs, value=zero_supported))
            if unobserved_refs or consumption:
                result.append(
                    self._fact(
                        subject,
                        "unobserved_consumption",
                        "unknown",
                        unobserved_refs or consumption_refs,
                        unknown_reason="no_consumption_observation",
                    )
                )
        return result

    def _task_relationship(
        self,
        relation: dict[str, Any],
        history_by_event: dict[str, list[dict[str, Any]]],
        current_by_subject: dict[str, dict[str, dict[str, Any]]],
    ) -> dict[str, Any] | None:
        del current_by_subject  # Reserved for future state-aware task rules.
        source = relation.get("source_event_id")
        target = relation.get("target_event_id")
        if not isinstance(source, str):
            return None
        source_observations = history_by_event.get(source, [])
        subjects = sorted({str(item.get("subject")) for item in source_observations if self._kind(str(item.get("subject"))) == "task"})
        if not subjects:
            return None
        changed = {str(field) for field in relation.get("changed_fields", []) if isinstance(field, str)}
        source_statuses = {
            str(item.get("value")).casefold()
            for item in source_observations
            if item.get("predicate") == "status" and item.get("knowledge_status") in {"known", "inferred"}
        }
        source_has_blocker = any(item.get("predicate") == "blocker" for item in source_observations)
        if "owner" in changed:
            relation_type = "task_reassignment"
            output_fields = ["owner"]
        elif source_statuses & {"cancelled", "canceled"}:
            relation_type = "task_cancellation"
            output_fields = ["lifecycle"]
        elif source_statuses & {"open", "active", "in_progress", "not_started"} or source_has_blocker:
            relation_type = "task_reopened"
            output_fields = ["lifecycle"]
        else:
            return None
        if relation_type == "task_reopened" and not source_statuses and source_has_blocker:
            target = None
        value = {
            "relation_type": relation_type,
            "source_event_id": source,
            "target_event_id": target if isinstance(target, str) else None,
            "changed_fields": output_fields,
        }
        refs = [source]
        if isinstance(target, str):
            refs.append(target)
        return self._fact(f"capture:{source}", "relationship", "known", refs, value=value)

    def _tasks(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        current = self._current_facts(snapshot)
        by_subject: dict[str, list[dict[str, Any]]] = {}
        current_by_subject: dict[str, dict[str, dict[str, Any]]] = {}
        for item in current:
            if self._kind(item["subject"]) != "task":
                continue
            by_subject.setdefault(item["subject"], []).append(item)
            current_by_subject.setdefault(item["subject"], {})[item["predicate"]] = item
        result = [
            item
            for items in by_subject.values()
            for item in items
            if item["predicate"] in {"status", "owner", "deadline", "blocker"}
        ]
        history_by_event: dict[str, list[dict[str, Any]]] = {}
        for item in self._history(snapshot):
            history_by_event.setdefault(str(item.get("event_id")), []).append(item)
        for relation in snapshot.get("relationships", []):
            if isinstance(relation, dict):
                assertion = self._task_relationship(relation, history_by_event, current_by_subject)
                if assertion is not None:
                    result.append(assertion)
        return self._dedupe(result)

    @staticmethod
    def _duplicate_components(relationships: list[dict[str, Any]]) -> tuple[set[str], int]:
        parent: dict[str, str] = {}

        def find(item: str) -> str:
            parent.setdefault(item, item)
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        def union(left: str, right: str) -> None:
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parent[right_root] = left_root

        for relation in relationships:
            source, target = relation.get("source_event_id"), relation.get("target_event_id")
            if isinstance(source, str) and isinstance(target, str):
                union(source, target)
        return set(parent), len({find(item) for item in parent})

    def _duplicates(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        relationships = [item for item in snapshot.get("relationships", []) if isinstance(item, dict)]
        event_subjects: dict[str, set[str]] = {}
        event_predicates: dict[str, set[str]] = {}
        for item in self._history(snapshot):
            event_id = item.get("event_id")
            subject = item.get("subject")
            if isinstance(event_id, str) and isinstance(subject, str):
                event_subjects.setdefault(event_id, set()).add(subject)
                if item.get("predicate") is not None:
                    event_predicates.setdefault(event_id, set()).add(str(item["predicate"]))

        def strong_event_edge(relation: dict[str, Any]) -> bool:
            source, target = relation.get("source_event_id"), relation.get("target_event_id")
            if not isinstance(source, str) or not isinstance(target, str):
                return False
            # A capture relation is strong only when the extraction did not
            # also classify either capture as a persistent merchant/entity
            # fact. This removes a common model failure mode where an entire
            # merchant history is linked as a duplicate chain.
            for event_id in (source, target):
                subjects = event_subjects.get(event_id, set())
                if subjects and any(not subject.startswith("capture:") for subject in subjects):
                    return False
                predicates = event_predicates.get(event_id, set())
                if predicates and predicates <= {"entity_link"}:
                    return False
            return True

        duplicate_relations = [
            relation
            for relation in relationships
            if str(relation.get("relation_type", "")).casefold() in {"exact_duplicate", "normalized_duplicate", "duplicate"}
            and strong_event_edge(relation)
        ]
        meaningful_relations = [
            relation
            for relation in relationships
            if str(relation.get("relation_type", "")).casefold() == "meaningful_change"
            and strong_event_edge(relation)
        ]
        similar_relations = [
            relation
            for relation in relationships
            if str(relation.get("relation_type", "")).casefold() == "similar_not_duplicate"
            and strong_event_edge(relation)
        ]
        # A meaningful change can connect a later duplicate to the earlier
        # member of the same cluster (for example, a changed receipt followed
        # by a normalized copy). Include those edges when counting connected
        # duplicate groups, while keeping the event count restricted to
        # explicit duplicate relations.
        _, duplicate_groups = self._duplicate_components(duplicate_relations + meaningful_relations)
        aggregate_subject = self._aggregate_subject(snapshot)
        result = [
            self._fact(
                aggregate_subject,
                "duplicate_event_count",
                "known",
                [str(item.get("source_event_id")) for item in duplicate_relations],
                value=len(duplicate_relations),
            ),
            self._fact(
                aggregate_subject,
                "duplicate_group_count",
                "known",
                [str(item.get("source_event_id")) for item in duplicate_relations],
                value=duplicate_groups,
            ),
            self._fact(
                aggregate_subject,
                "meaningful_change_event_count",
                "known",
                [str(item.get("source_event_id")) for item in meaningful_relations],
                value=len(meaningful_relations),
            ),
        ]
        for relation in duplicate_relations + meaningful_relations + similar_relations:
            source, target = relation.get("source_event_id"), relation.get("target_event_id")
            if not isinstance(source, str) or not isinstance(target, str):
                continue
            value: dict[str, Any] = {
                "relation_type": relation.get("relation_type"),
                "source_event_id": source,
                "target_event_id": target,
                "changed_fields": sorted(relation.get("changed_fields", [])),
            }
            if relation.get("duplicate_group") is not None:
                value["duplicate_group"] = relation["duplicate_group"]
            if relation.get("note") is not None:
                value["note"] = relation["note"]
            result.append(self._fact(f"capture:{source}", "relationship", "known", [source, target], value=value))
        return self._dedupe(result)

    def _unresolved(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in self._history(snapshot):
            if item.get("predicate") != "entity_link" or item.get("knowledge_status") != "unknown":
                continue
            event_id = item.get("event_id")
            if isinstance(event_id, str):
                result.append(
                    self._fact(
                        f"capture:{event_id}",
                        "entity_link",
                        "unknown",
                        [event_id],
                        unknown_reason=item.get("unknown_reason"),
                    )
                )
        for item in self._current_facts(snapshot):
            if item.get("knowledge_status") != "unknown":
                continue
            subject, predicate = item["subject"], item["predicate"]
            kind = self._kind(subject)
            if (kind == "observation" and predicate == "quoted_amount") or (kind == "insurance" and predicate in {"claim_number", "beneficiary", "termination_date"}):
                output_predicate = "old_cancellation_date" if kind == "insurance" and predicate == "termination_date" else predicate
                result.append(self._fact_from_state(item, predicate=output_predicate))
        return self._dedupe(result)

    @staticmethod
    def _prior_observation(observations: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any] | None:
        prior = [
            item
            for item in observations
            if ResponseProjector._sequence(item) < ResponseProjector._sequence(current)
            and item.get("operation") != "duplicate"
            and item.get("knowledge_status") in {"known", "inferred"}
            and "value" in item
        ]
        return max(prior, key=ResponseProjector._sequence) if prior else None

    def _change_fact(
        self,
        source: dict[str, Any],
        target: dict[str, Any] | None,
        relation_type: str,
        changed_fields: list[str],
    ) -> dict[str, Any]:
        source_id = str(source.get("event_id"))
        target_id = str(target.get("event_id")) if target else None
        refs = [source_id] + ([target_id] if target_id else [])
        return self._fact(
            f"capture:{source_id}",
            "relationship",
            "known",
            refs,
            value={
                "relation_type": relation_type,
                "source_event_id": source_id,
                "target_event_id": target_id,
                "changed_fields": changed_fields,
            },
        )

    def _recent_changes(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        history = self._history(snapshot)
        result: list[dict[str, Any]] = []

        for subject in self._subjects_of_kind(snapshot, "observation"):
            subject_history = [item for item in history if item.get("subject") == subject]
            for predicate, changed_fields in (("deadline", ["appointment_date"]), ("quoted_amount", ["quoted_amount"])):
                observations = [item for item in subject_history if item.get("predicate") == predicate]
                for item in sorted(observations, key=self._sequence):
                    if item.get("operation") not in {"contradiction", "correction"}:
                        continue
                    target = self._prior_observation(observations, item)
                    relation_type = "correction" if item.get("operation") == "correction" else "contradiction"
                    result.append(self._change_fact(item, target, relation_type, changed_fields))

        for subject in self._subjects_of_kind(snapshot, "subscription"):
            price_observations = [
                item
                for item in history
                if item.get("subject") == subject
                and item.get("predicate") in {"current_price", "historical_price"}
                and item.get("operation") != "duplicate"
                and item.get("knowledge_status") in {"known", "inferred"}
                and self._decimal(item.get("value")) is not None
            ]
            for item in sorted(price_observations, key=self._sequence):
                target_price = self._prior_observation(price_observations, item)
                if target_price is None or self._decimal(target_price.get("value")) == self._decimal(item.get("value")):
                    continue
                prior_charges = [
                    candidate
                    for candidate in history
                    if candidate.get("subject") == subject
                    and candidate.get("predicate") == "last_charge"
                    and candidate.get("operation") != "duplicate"
                    and candidate.get("knowledge_status") in {"known", "inferred"}
                    and self._sequence(candidate) < self._sequence(item)
                ]
                target = max(prior_charges, key=self._sequence) if prior_charges else target_price
                result.append(self._change_fact(item, target, "price_change", ["amount"]))

        for subject in self._subjects_of_kind(snapshot, "insurance"):
            subject_history = [item for item in history if item.get("subject") == subject]
            by_event: dict[str, list[dict[str, Any]]] = {}
            for item in subject_history:
                by_event.setdefault(str(item.get("event_id")), []).append(item)
            ordered_events = sorted(by_event.items(), key=lambda pair: min(self._sequence(item) for item in pair[1]))
            prior_effective_policy_ids: set[str] = set()
            for _, items in ordered_events:
                policy_ids = [
                    item
                    for item in items
                    if item.get("predicate") == "policy_id"
                    and item.get("knowledge_status") in {"known", "inferred"}
                    and item.get("operation") != "duplicate"
                ]
                effective = any(item.get("predicate") == "effective_date" for item in items)
                if not policy_ids or not effective:
                    continue
                current_ids = {
                    json.dumps(self._clean_value(item.get("value")), ensure_ascii=False, sort_keys=True)
                    for item in policy_ids
                }
                if prior_effective_policy_ids and not current_ids.issubset(prior_effective_policy_ids):
                    policy_event = max(policy_ids, key=self._sequence)
                    result.append(self._change_fact(policy_event, None, "policy_replacement", ["policy_id", "effective_date"]))
                    break
                prior_effective_policy_ids.update(current_ids)

        for subject in self._subjects_of_kind(snapshot, "contract"):
            subject_history = [item for item in history if item.get("subject") == subject]
            by_event = {}
            for item in subject_history:
                by_event.setdefault(str(item.get("event_id")), []).append(item)
            ordered_events = sorted(by_event.items(), key=lambda pair: min(self._sequence(item) for item in pair[1]))
            for _, items in ordered_events:
                executed = next(
                    (
                        item
                        for item in items
                        if item.get("predicate") == "executed"
                        and item.get("knowledge_status") in {"known", "inferred"}
                        and item.get("value") is True
                    ),
                    None,
                )
                status = next(
                    (
                        item
                        for item in items
                        if item.get("predicate") == "status"
                        and item.get("knowledge_status") in {"known", "inferred"}
                        and str(item.get("value")).casefold() in {"signed", "current", "active"}
                    ),
                    None,
                )
                if executed is None or status is None:
                    continue
                earlier_false = any(
                    item.get("predicate") == "executed"
                    and item.get("knowledge_status") in {"known", "inferred"}
                    and item.get("value") is False
                    and self._sequence(item) < self._sequence(executed)
                    for item in subject_history
                )
                if earlier_false:
                    result.append(self._change_fact(executed, None, "contract_replacement", ["contract_id", "effective_date"]))
                    break
        return self._dedupe(result)

    def _contract_dates(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        mapping = {
            "current_price": "fee",
            "effective_date": "effective_date",
            "expiry_date": "expiry_date",
            "next_renewal": "renewal_date",
            "signed_date": "signed_date",
            "status": "status",
            "historical_status": "historical_status",
            "contract_id": "contract_id",
        }
        result: list[dict[str, Any]] = []
        for item in self._effective_current(snapshot):
            if self._kind(str(item.get("subject"))) != "contract" or item.get("predicate") not in mapping:
                continue
            output = self._fact_from_state(item, predicate=mapping[item["predicate"]])
            if output.get("predicate") == "status" and output.get("knowledge_status") in {"known", "inferred"} and output.get("value") in {"signed", "current"}:
                output["value"] = "active"
            if output.get("predicate") == "historical_status" and output.get("knowledge_status") in {"known", "inferred"} and output.get("value") == "historical":
                output["value"] = "superseded"
            result.append(output)
        return result

    def _approval(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        allowed = {"amount", "approval_required", "approval_scope", "approved", "executed", "status"}
        current = self._current_facts(snapshot)
        global_approval = next((item for item in current if self._kind(item["subject"]) == "aggregate" and item["predicate"] == "approval_required"), None)
        global_scope = next((item for item in current if self._kind(item["subject"]) == "aggregate" and item["predicate"] == "approval_scope"), None)
        result: list[dict[str, Any]] = []
        for item in current:
            if self._kind(item["subject"]) != "action" or item["predicate"] not in allowed:
                continue
            result.append(item)
        if global_approval is not None and global_approval.get("value") is True:
            subjects = {item["subject"] for item in current if self._kind(item["subject"]) == "action"}
            for subject in subjects:
                if not any(item["subject"] == subject and item["predicate"] == "approval_required" for item in result):
                    result.append(
                        self._fact(
                            subject,
                            "approval_required",
                            "known",
                            list(global_approval.get("source_refs", [])),
                            value=True,
                        )
                    )
        if global_scope is not None and global_scope.get("value") == "draft_only":
            for subject in {item["subject"] for item in current if self._kind(item["subject"]) == "action"}:
                if not any(item["subject"] == subject and item["predicate"] == "approval_scope" for item in result):
                    result.append(
                        self._fact(
                            subject,
                            "approval_scope",
                            "known",
                            list(global_scope.get("source_refs", [])),
                            value="draft_only",
                        )
                    )
        return self._dedupe(result)

    def _generic(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        """Unsupported query families must be empty, never a state dump."""

        del snapshot
        return []

    def project(self, snapshot: dict[str, Any], *, query_ids: list[str]) -> dict[str, dict[str, list[dict[str, Any]]]]:
        result: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for query_id in query_ids:
            question = str(self.query_bundle.get("queries", {}).get(query_id, {}).get("question", "")).casefold()
            if "currently active" in question and "subscription" in question:
                assertions = self._subscription_current(snapshot)
            elif "subscription price changes" in question:
                assertions = self._subscription_history(snapshot)
            elif "next 14" in question or "need attention" in question:
                assertions = self._attention(snapshot)
            elif "policy" in question or "insurance" in question:
                assertions = self._insurance(snapshot)
            elif "bill" in question or "deterministic total" in question:
                assertions = self._service_costs(snapshot)
            elif "purchase" in question or "consumption" in question:
                assertions = self._merchant_observations(snapshot)
            elif "which tasks" in question:
                assertions = self._tasks(snapshot)
            elif "duplicate" in question or "meaningful change" in question:
                assertions = self._duplicates(snapshot)
            elif "corrections" in question or "replacements" in question or "material changes" in question:
                assertions = self._recent_changes(snapshot)
            elif "unknown" in question or "ambiguous" in question or "contradictory" in question:
                assertions = self._unresolved(snapshot)
            elif "contract" in question:
                assertions = self._contract_dates(snapshot)
            elif "approval" in question or "consequential" in question:
                assertions = self._approval(snapshot)
            else:
                assertions = self._generic(snapshot)
            result[query_id] = {"assertions": self._dedupe(assertions)}
        return result
