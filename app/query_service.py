"""Bounded deterministic views and question routing over a Host snapshot.

This module is deliberately database-free.  A transport supplies a snapshot
from HostRuntime; this service selects a small, deterministic projection and
never calls a provider or invents unsupported answers.
"""

from __future__ import annotations

import copy
from typing import Any

from app.response_projector import ResponseProjector


DEFAULT_QUERY_BUNDLE: dict[str, Any] = {
    "queries": {
        "q-subscriptions-current": {"question": "Which subscriptions are currently active, and what does each currently cost?"},
        "q-subscriptions-history": {"question": "What subscription price changes are supported by the history?"},
        "q-attention-14d": {"question": "Which open deadlines or approval-required items need attention in the next 14 calendar days at this checkpoint?"},
        "q-service-costs": {"question": "Which bills and deterministic totals are directly observed, and which periods are missing?"},
        "q-merchant-observations": {"question": "Which purchases and consumption observations are directly observed?"},
        "q-tasks-state": {"question": "Which tasks are active or completed, and what reassignment or cancellation history is supported?"},
        "q-unresolved": {"question": "Which facts remain unknown, ambiguous, unreadable, or contradictory?"},
        "q-duplicates-changes": {"question": "Which captures are duplicates, which are meaningful changes, and what are the explicit counts?"},
        "q-approval-boundary": {"question": "Which proposed actions require approval, and were any consequential actions executed?"},
        "q-recent-changes": {"question": "Which corrections, contradictions, replacements, and material changes are recorded?"},
    }
}


_KIND_PREDICATES: dict[str, set[str]] = {
    "subscription": {
        "current_price",
        "historical_price",
        "billing_period",
        "currency",
        "cancellation_intent",
        "cancellation_requested",
        "last_charge",
        "termination_date",
        "price_effective",
        "next_renewal",
    },
    "task": {"owner", "deadline", "blocker"},
    "service": {"observed_periods", "observed_total", "missing_periods", "unobserved_periods", "current_amount"},
    "merchant": {"purchase_count", "purchased_total", "confirmed_consumption_quantity", "explicit_zero_is_supported", "unobserved_consumption"},
    "action": {"approval_required", "approval_scope", "approved", "executed"},
    "insurance": {"effective_date", "expiry_date", "policy_id", "premium", "beneficiary", "claim_number"},
    "contract": {"signed_date", "effective_date", "expiry_date", "contract_id"},
    "observation": {"quoted_amount"},
}


def _subjects_with_predicates(snapshot: dict[str, Any]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for collection_name in ("current_facts", "history"):
        collection = snapshot.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            subject = item.get("subject")
            predicate = item.get("predicate")
            if isinstance(subject, str) and isinstance(predicate, str):
                result.setdefault(subject, set()).add(predicate)
    return result


def _inferred_kind(predicates: set[str]) -> str | None:
    """Infer only a presentation kind for an undeclared runtime entity."""

    # Specific fields win over the shared ``status`` predicate.  This is a
    # view concern only; it never changes persisted state or extraction.
    ranked = (
        "subscription",
        "task",
        "service",
        "merchant",
        "action",
        "insurance",
        "contract",
        "observation",
    )
    for kind in ranked:
        if predicates & _KIND_PREDICATES[kind]:
            return kind
    return None


def _projector_contract(contract: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(contract)
    ontology = result.setdefault("public_ontology", {})
    subjects = ontology.setdefault("subjects", [])
    declared = {
        item.get("id")
        for item in subjects
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for subject, predicates in _subjects_with_predicates(snapshot).items():
        if subject in declared or subject.startswith("capture:"):
            continue
        kind = _inferred_kind(predicates)
        if kind is not None:
            subjects.append({"id": subject, "kind": kind})
            declared.add(subject)
    return result


def projections(
    snapshot: dict[str, Any],
    *,
    contract: dict[str, Any],
    query_bundle: dict[str, Any] = DEFAULT_QUERY_BUNDLE,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Build all bounded query projections from one Host-owned snapshot."""

    projector = ResponseProjector(_projector_contract(contract, snapshot), query_bundle)
    query_ids = list(query_bundle.get("queries", {}))
    return projector.project(snapshot, query_ids=query_ids)


def _recent_captures(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "event_id": event.get("event_id"),
            "sequence": event.get("sequence"),
            "observed_at": event.get("observed_at"),
            "source_type": event.get("source_type"),
        }
        for event in reversed(snapshot.get("event_index", [])[-12:])
        if isinstance(event, dict)
    ]


def build_state_view(
    snapshot: dict[str, Any],
    *,
    contract: dict[str, Any],
    query_bundle: dict[str, Any] = DEFAULT_QUERY_BUNDLE,
) -> dict[str, Any]:
    """Return the small Memory/Attention view consumed by the PWA."""

    projected = projections(snapshot, contract=contract, query_bundle=query_bundle)
    return {
        "projection_version": snapshot.get("projection_version"),
        "counts": {
            "captures": len(snapshot.get("event_index", [])),
            "current_facts": len(snapshot.get("current_facts", [])),
            "relationships": len(snapshot.get("relationships", [])),
        },
        "attention": projected["q-attention-14d"]["assertions"],
        "memory": {
            "subscriptions": projected["q-subscriptions-current"]["assertions"],
            "subscription_history": projected["q-subscriptions-history"]["assertions"],
            "tasks": projected["q-tasks-state"]["assertions"],
            "services": projected["q-service-costs"]["assertions"],
            "merchants": projected["q-merchant-observations"]["assertions"],
            "unknown": projected["q-unresolved"]["assertions"],
            "recent_changes": projected["q-recent-changes"]["assertions"],
            "duplicates": projected["q-duplicates-changes"]["assertions"],
        },
        "approval": projected["q-approval-boundary"]["assertions"],
        "recent_captures": _recent_captures(snapshot),
    }


def answer_question_from_snapshot(
    question: str,
    snapshot: dict[str, Any],
    *,
    contract: dict[str, Any],
    query_bundle: dict[str, Any] = DEFAULT_QUERY_BUNDLE,
) -> dict[str, Any]:
    """Route a question to a supported deterministic view."""

    normalized = question.strip().casefold()
    if not normalized:
        raise ValueError("question must not be empty")
    projected = projections(snapshot, contract=contract, query_bundle=query_bundle)
    section_map = {
        "attention": ("Needs attention", "q-attention-14d"),
        "subscriptions": ("Subscriptions", "q-subscriptions-current"),
        "history": ("Subscription history", "q-subscriptions-history"),
        "tasks": ("Tasks", "q-tasks-state"),
        "unknown": ("Incomplete information", "q-unresolved"),
        "changes": ("Recent changes", "q-recent-changes"),
        "duplicates": ("Duplicates and changes", "q-duplicates-changes"),
        "approval": ("Approval boundary", "q-approval-boundary"),
        "services": ("Recurring service costs", "q-service-costs"),
        "merchants": ("Purchases and consumption", "q-merchant-observations"),
    }
    if "attention" in normalized or "need" in normalized:
        selected = [section_map["attention"]]
        mode = "attention"
    elif "subscription" in normalized and ("change" in normalized or "history" in normalized):
        selected = [section_map["history"]]
        mode = "subscription_history"
    elif "subscription" in normalized:
        selected = [section_map["subscriptions"]]
        mode = "subscriptions"
    elif "incomplete" in normalized or "unknown" in normalized or "missing" in normalized:
        selected = [section_map["unknown"]]
        mode = "unknown"
    elif "recurring" in normalized or "cost" in normalized or "paying" in normalized:
        selected = [section_map["subscriptions"], section_map["services"], section_map["merchants"]]
        mode = "recurring_costs"
    elif "change" in normalized or "correction" in normalized:
        selected = [section_map["changes"]]
        mode = "changes"
    elif "duplicate" in normalized:
        selected = [section_map["duplicates"]]
        mode = "duplicates"
    elif "task" in normalized:
        selected = [section_map["tasks"]]
        mode = "tasks"
    elif "approval" in normalized or "action" in normalized or "execute" in normalized:
        selected = [section_map["approval"]]
        mode = "approval"
    else:
        return {
            "question": question.strip(),
            "mode": "unsupported",
            "message": "This question is outside Blackhole's supported local views.",
            "sections": [],
        }
    return {
        "question": question.strip(),
        "mode": mode,
        "sections": [
            {"title": title, "assertions": projected[query_id]["assertions"]}
            for title, query_id in selected
        ],
    }


__all__ = [
    "DEFAULT_QUERY_BUNDLE",
    "answer_question_from_snapshot",
    "build_state_view",
    "projections",
]
