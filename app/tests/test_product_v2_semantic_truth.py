from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from typing import Any, Callable

from app.product_v2 import ProductRuntime, normalize_temporal, normalize_timestamp


BASE_NOW = datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)
MISSING = object()


def fact(
    event_id: str,
    entity: str,
    concept: str,
    value: Any = MISSING,
    *,
    status: str = "known",
    operation: str = "set",
    supersedes: str | None = None,
    temporal: dict[str, Any] | None = None,
    attribution: Any = MISSING,
    certainty: Any = MISSING,
    confidence: Any = MISSING,
    claim_type: Any = MISSING,
    negated: Any = MISSING,
    polarity: Any = MISSING,
    semantic_relation: Any = MISSING,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "event_id": event_id,
        "entity": entity,
        "concept": concept,
        "knowledge_status": status,
        "operation": operation,
    }
    if value is not MISSING:
        item["value"] = value
    if supersedes is not None:
        item["supersedes_event_id"] = supersedes
    if temporal is not None:
        item["temporal"] = copy.deepcopy(temporal)
    for key, candidate in (
        ("attribution", attribution),
        ("certainty", certainty),
        ("confidence", confidence),
        ("claim_type", claim_type),
        ("negated", negated),
        ("polarity", polarity),
        ("semantic_relation", semantic_relation),
    ):
        if candidate is not MISSING:
            item[key] = copy.deepcopy(candidate)
    return item


def attention(
    event_id: str,
    title: str,
    *,
    kind: str = "task",
    status: str = "open",
    knowledge_status: str = "known",
    due_at: Any = MISSING,
    starts_at: Any = MISSING,
    lifecycle_key: str | None = None,
    lifecycle_action: str | None = None,
    related_event_id: str | None = None,
    actionable: Any = MISSING,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "event_id": event_id,
        "kind": kind,
        "title": title,
        "status": status,
        "knowledge_status": knowledge_status,
    }
    for key, candidate in (("due_at", due_at), ("starts_at", starts_at), ("actionable", actionable)):
        if candidate is not MISSING:
            item[key] = copy.deepcopy(candidate)
    merged_details = copy.deepcopy(details or {})
    if lifecycle_key is not None:
        merged_details["lifecycle_key"] = lifecycle_key
    if lifecycle_action is not None:
        merged_details["lifecycle_action"] = lifecycle_action
    if related_event_id is not None:
        merged_details["related_event_id"] = related_event_id
    item["details"] = merged_details
    return item


def capture(event_id: str, text: str | None = None, **kwargs: Any) -> dict[str, Any]:
    return {"event_id": event_id, "text": text or event_id, **kwargs}


def semantic_case(
    name: str,
    captures: list[dict[str, Any]],
    facts_by_event: dict[str, list[dict[str, Any]]],
    current: dict[tuple[str, str], dict[str, Any]],
    *,
    relations_by_event: dict[str, list[dict[str, Any]]] | None = None,
    attention_by_event: dict[str, list[dict[str, Any]]] | None = None,
    retract_before: list[str] | None = None,
    retract_after: list[str] | None = None,
    snapshot_now: datetime | None = None,
    attention_expected: dict[str, Any] | None = None,
    history_expected: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "captures": captures,
        "facts_by_event": facts_by_event,
        "relations_by_event": relations_by_event or {},
        "attention_by_event": attention_by_event or {},
        "current": current,
        "retract_before": retract_before or [],
        "retract_after": retract_after or [],
        "snapshot_now": snapshot_now,
        "attention_expected": attention_expected or {},
        "history_expected": history_expected or {},
    }


def current_expectation(
    value: Any = MISSING,
    *,
    status: str = "known",
    state: str | None = None,
    contains: list[str] | None = None,
    refs: list[str] | None = None,
    metadata_contains: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"status": status}
    if value is not MISSING:
        result["value"] = value
    if state is not None:
        result["state"] = state
    if contains:
        result["contains"] = contains
    if refs is not None:
        result["refs"] = refs
    if metadata_contains:
        result["metadata_contains"] = metadata_contains
    return result


def _same_entity_concept(item: dict[str, Any], key: tuple[str, str]) -> bool:
    return item.get("entity_key") == key[0] and item.get("concept") == key[1]


class SemanticTruthProvider:
    """Deterministic provider seam whose outputs model semantic understanding."""

    def __init__(
        self,
        facts_by_event: dict[str, list[dict[str, Any]]],
        relations_by_event: dict[str, list[dict[str, Any]]],
        attention_by_event: dict[str, list[dict[str, Any]]],
        answer_fn: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self.facts_by_event = facts_by_event
        self.relations_by_event = relations_by_event
        self.attention_by_event = attention_by_event
        self.answer_fn = answer_fn
        self.answer_contexts: list[dict[str, Any]] = []
        self.extract_calls: list[list[str]] = []

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_memory, time_context, contract
        event_ids = [str(event["event_id"]) for event in events]
        self.extract_calls.append(event_ids)
        return {
            "facts": [
                copy.deepcopy(item)
                for event_id in event_ids
                for item in self.facts_by_event.get(event_id, [])
            ],
            "relationships": [
                copy.deepcopy(item)
                for event_id in event_ids
                for item in self.relations_by_event.get(event_id, [])
            ],
            "attention": [
                copy.deepcopy(item)
                for event_id in event_ids
                for item in self.attention_by_event.get(event_id, [])
            ],
        }

    def answer(
        self,
        *,
        question: str,
        context: dict[str, Any],
        time_context: dict[str, Any],
    ) -> dict[str, Any]:
        del time_context
        self.answer_contexts.append(copy.deepcopy(context))
        if self.answer_fn is not None:
            return self.answer_fn(question, context)
        evidence_ids = [
            item["evidence_id"]
            for collection in ("facts", "history", "relationships", "attention")
            for item in context.get(collection, [])
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        ]
        return {"answer": "The structured evidence is available.", "evidence_ids": evidence_ids}


def answer_from_collections(
    answer: str,
    *collections: str,
) -> Callable[[str, dict[str, Any]], dict[str, Any]]:
    def make(_question: str, context: dict[str, Any]) -> dict[str, Any]:
        ids = [
            item["evidence_id"]
            for collection in collections
            for item in context.get(collection, [])
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        ]
        return {"answer": answer, "evidence_ids": ids}

    return make


def _relation(
    event_id: str,
    relation_type: str,
    target_event_id: str,
    *,
    source_entity_key: str = "",
    target_entity_key: str = "",
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "relation_type": relation_type,
        "target_event_id": target_event_id,
        "source_entity_key": source_entity_key or None,
        "target_entity_key": target_entity_key or None,
    }


SEMANTIC_CASES: list[dict[str, Any]] = [
    semantic_case(
        "simple-current-fact",
        [capture("s01")],
        {"s01": [fact("s01", "basement keys", "location", "desk drawer")]},
        {("basement_keys", "location"): current_expectation("desk drawer", refs=["s01"])},
    ),
    semantic_case(
        "explicit-unknown",
        [capture("s02")],
        {"s02": [fact("s02", "boiler warranty", "expiry", status="unknown")]},
        {("boiler_warranty", "expiry"): current_expectation(status="unknown")},
    ),
    semantic_case(
        "explicit-correction-with-pointer",
        [capture("s03-old"), capture("s03-new")],
        {
            "s03-old": [fact("s03-old", "basement keys", "location", "mum's place")],
            "s03-new": [fact("s03-new", "basement keys", "location", "desk drawer", operation="correction", supersedes="s03-old")],
        },
        {("basement_keys", "location"): current_expectation("desk drawer", refs=["s03-new"])},
        history_expected={"s03-old": {"superseded": True}, "s03-new": {"current": True}},
    ),
    semantic_case(
        "implicit-correction-without-pointer",
        [capture("s04-old"), capture("s04-new")],
        {
            "s04-old": [fact("s04-old", "meeting", "location", "Tuesday room")],
            "s04-new": [fact("s04-new", "meeting", "location", "Friday room", operation="correction")],
        },
        {("meeting", "location"): current_expectation("Friday room", refs=["s04-new"])},
    ),
    semantic_case(
        "cross-language-correction",
        [capture("s05-pl"), capture("s05-en")],
        {
            "s05-pl": [fact("s05-pl", "basement keys", "location", "mum's place")],
            "s05-en": [fact("s05-en", "basement keys", "location", "my desk", operation="correction", supersedes="s05-pl")],
        },
        {("basement_keys", "location"): current_expectation("my desk", refs=["s05-en"])},
    ),
    semantic_case(
        "polish-correction-to-english",
        [capture("s06-old"), capture("s06-new")],
        {
            "s06-old": [fact("s06-old", "Marta", "key_holder", "Adam")],
            "s06-new": [fact("s06-new", "Marta", "key_holder", "Marta", operation="correction")],
        },
        {("marta", "key_holder"): current_expectation("Marta")},
    ),
    semantic_case(
        "semantic-relation-correction",
        [capture("s07-old"), capture("s07-new")],
        {
            "s07-old": [fact("s07-old", "wifi", "password", "BlueRiver7")],
            "s07-new": [fact("s07-new", "wifi", "password", "GreenRiver9", semantic_relation="correction")],
        },
        {("wifi", "password"): current_expectation("GreenRiver9")},
    ),
    semantic_case(
        "plain-competing-observations-stay-conflicting",
        [capture("s08-a"), capture("s08-b")],
        {
            "s08-a": [fact("s08-a", "car", "diagnosis", "left bearing")],
            "s08-b": [fact("s08-b", "car", "diagnosis", "front tyre")],
        },
        {("car", "diagnosis"): current_expectation(status="unknown", state="conflict", contains=["left bearing", "front tyre"], refs=["s08-a", "s08-b"])},
    ),
    semantic_case(
        "future-effective-change-before-date",
        [capture("s09-old"), capture("s09-new")],
        {
            "s09-old": [fact("s09-old", "PocketWave", "recurring_cost", {"amount": "9", "currency": "EUR"})],
            "s09-new": [fact("s09-new", "PocketWave", "recurring_cost", {"amount": "11", "currency": "EUR"}, temporal={"valid_from": "2026-09-01T00:00:00+00:00"})],
        },
        {("pocketwave", "recurring_cost"): current_expectation({"amount": "9", "currency": "EUR"}, refs=["s09-old"])},
    ),
    semantic_case(
        "future-effective-change-after-date",
        [capture("s10-old"), capture("s10-new")],
        {
            "s10-old": [fact("s10-old", "PocketWave", "recurring_cost", {"amount": "9", "currency": "EUR"})],
            "s10-new": [fact("s10-new", "PocketWave", "recurring_cost", {"amount": "11", "currency": "EUR"}, temporal={"valid_from": "2026-09-01T00:00:00+00:00"})],
        },
        {("pocketwave", "recurring_cost"): current_expectation({"amount": "11", "currency": "EUR"}, refs=["s10-new"])},
        snapshot_now=datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc),
    ),
    semantic_case(
        "historical-validity-window",
        [capture("s11-old"), capture("s11-new")],
        {
            "s11-old": [fact("s11-old", "PocketWave", "recurring_cost", {"amount": "9", "currency": "EUR"}, temporal={"valid_to": "2026-08-20T00:00:00+00:00"})],
            "s11-new": [fact("s11-new", "PocketWave", "recurring_cost", {"amount": "11", "currency": "EUR"})],
        },
        {("pocketwave", "recurring_cost"): current_expectation({"amount": "11", "currency": "EUR"}, refs=["s11-new"])},
    ),
    semantic_case(
        "duplicate-evidence-explicit",
        [capture("s12-a"), capture("s12-b")],
        {
            "s12-a": [fact("s12-a", "basement keys", "location", "mum's place")],
            "s12-b": [fact("s12-b", "basement keys", "location", "mum's place", operation="duplicate")],
        },
        {("basement_keys", "location"): current_expectation("mum's place", refs=["s12-a", "s12-b"])},
    ),
    semantic_case(
        "duplicate-evidence-implicit",
        [capture("s13-a"), capture("s13-b")],
        {
            "s13-a": [fact("s13-a", "basement keys", "location", "mum's place")],
            "s13-b": [fact("s13-b", "basement keys", "location", "mum's place")],
        },
        {("basement_keys", "location"): current_expectation("mum's place", refs=["s13-a", "s13-b"])},
    ),
    semantic_case(
        "different-concepts-coexist",
        [capture("s14-a"), capture("s14-b")],
        {
            "s14-a": [fact("s14-a", "car", "color", "blue")],
            "s14-b": [fact("s14-b", "car", "condition", "knocking")],
        },
        {
            ("car", "color"): current_expectation("blue"),
            ("car", "condition"): current_expectation("knocking"),
        },
    ),
    semantic_case(
        "different-entities-coexist",
        [capture("s15-a"), capture("s15-b")],
        {
            "s15-a": [fact("s15-a", "Kuba", "favorite_food", "green pasta")],
            "s15-b": [fact("s15-b", "Kuba", "clothing_size", 43)],
        },
        {
            ("kuba", "favorite_food"): current_expectation("green pasta"),
            ("kuba", "clothing_size"): current_expectation(43),
        },
    ),
    semantic_case(
        "uncertain-only",
        [capture("s16")],
        {"s16": [fact("s16", "boiler warranty", "expiry", "December", status="inferred", certainty="maybe")]},
        {("boiler_warranty", "expiry"): current_expectation("December", status="inferred", state="uncertain", contains=["December"])},
    ),
    semantic_case(
        "legacy-known-speculation-downgraded",
        [capture("s17")],
        {"s17": [fact("s17", "spare key", "holder", "Marta", certainty="speculative")]},
        {("spare_key", "holder"): current_expectation("Marta", status="inferred", state="uncertain")},
    ),
    semantic_case(
        "later-observation-resolves-uncertainty",
        [capture("s18-guess"), capture("s18-found")],
        {
            "s18-guess": [fact("s18-guess", "basement keys", "location", "mum's place", status="inferred")],
            "s18-found": [fact("s18-found", "basement keys", "location", "desk drawer", semantic_relation="resolution")],
        },
        {("basement_keys", "location"): current_expectation("desk drawer", refs=["s18-found"])},
        history_expected={"s18-guess": {"resolved": True}},
    ),
    semantic_case(
        "confirmed-value-survives-later-speculation",
        [capture("s19-known"), capture("s19-maybe")],
        {
            "s19-known": [fact("s19-known", "basement keys", "location", "desk drawer")],
            "s19-maybe": [fact("s19-maybe", "basement keys", "location", "car", status="inferred", certainty="maybe")],
        },
        {("basement_keys", "location"): current_expectation("desk drawer", state="current", refs=["s19-known"], metadata_contains={"uncertainty_source_refs": ["s19-maybe"]})},
    ),
    semantic_case(
        "confirmed-value-survives-unknown-followup",
        [capture("s20-known"), capture("s20-unknown")],
        {
            "s20-known": [fact("s20-known", "permit", "status", "valid")],
            "s20-unknown": [fact("s20-unknown", "permit", "status", status="unknown")],
        },
        {("permit", "status"): current_expectation("valid", state="current", refs=["s20-known"])},
    ),
    semantic_case(
        "inferred-values-conflict",
        [capture("s21-a"), capture("s21-b")],
        {
            "s21-a": [fact("s21-a", "car", "possible_cause", "left bearing", status="inferred")],
            "s21-b": [fact("s21-b", "car", "possible_cause", "front tyre", status="inferred")],
        },
        {("car", "possible_cause"): current_expectation(status="unknown", state="conflict", contains=["left bearing", "front tyre"])},
    ),
    semantic_case(
        "known-values-conflict",
        [capture("s22-a"), capture("s22-b")],
        {
            "s22-a": [fact("s22-a", "house", "owner", "Alice")],
            "s22-b": [fact("s22-b", "house", "owner", "Bob")],
        },
        {("house", "owner"): current_expectation(status="unknown", state="conflict", contains=["Alice", "Bob"], refs=["s22-a", "s22-b"])},
    ),
    semantic_case(
        "attributed-string-claim",
        [capture("s23")],
        {"s23": [fact("s23", "car", "possible_cause", "left bearing", status="inferred", attribution="mechanic")]},
        {("car", "possible_cause"): current_expectation("left bearing", status="inferred", metadata_contains={"attribution": "mechanic"})},
    ),
    semantic_case(
        "attributed-structured-claim",
        [capture("s24")],
        {"s24": [fact("s24", "boiler", "condition", "leak", status="inferred", attribution={"name": "Marta", "role": "neighbour"})]},
        {("boiler", "condition"): current_expectation("leak", status="inferred", metadata_contains={"attribution": {"name": "Marta", "role": "neighbour"}})},
    ),
    semantic_case(
        "explicit-negation",
        [capture("s25")],
        {"s25": [fact("s25", "Adam", "eats_peanuts", "peanuts", negated=True)]},
        {("adam", "eats_peanuts"): current_expectation("peanuts", contains=["peanuts"], metadata_contains={"negated": True})},
    ),
    semantic_case(
        "polarity-negation",
        [capture("s26")],
        {"s26": [fact("s26", "permit", "due_this_week", True, polarity="negative")]},
        {("permit", "due_this_week"): current_expectation(True, metadata_contains={"negated": True})},
    ),
    semantic_case(
        "positive-and-negative-conflict",
        [capture("s27-positive"), capture("s27-negative")],
        {
            "s27-positive": [fact("s27-positive", "boiler", "leak", True)],
            "s27-negative": [fact("s27-negative", "boiler", "leak", True, negated=True)],
        },
        {("boiler", "leak"): current_expectation(status="unknown", state="conflict", contains=["true"], metadata_contains={"conflicting_fact_ids": [1, 2]})},
    ),
    semantic_case(
        "negated-correction",
        [capture("s28-old"), capture("s28-new")],
        {
            "s28-old": [fact("s28-old", "Netflix", "cancelled", True)],
            "s28-new": [fact("s28-new", "Netflix", "cancelled", True, negated=True, operation="correction", supersedes="s28-old")],
        },
        {("netflix", "cancelled"): current_expectation(True, refs=["s28-new"], metadata_contains={"negated": True})},
    ),
    semantic_case(
        "contradictory-report-is-not-erasure",
        [capture("s29-a"), capture("s29-b")],
        {
            "s29-a": [fact("s29-a", "car", "diagnosis", "left bearing")],
            "s29-b": [fact("s29-b", "car", "diagnosis", "bearing okay; tyre", operation="contradiction")],
        },
        {("car", "diagnosis"): current_expectation(status="unknown", state="conflict", refs=["s29-a", "s29-b"])},
    ),
    semantic_case(
        "unknown-does-not-become-zero",
        [capture("s30")],
        {"s30": [fact("s30", "invoice", "amount", status="unknown")]},
        {("invoice", "amount"): current_expectation(status="unknown")},
    ),
    semantic_case(
        "relation-correction-target",
        [capture("s31-old"), capture("s31-new")],
        {
            "s31-old": [fact("s31-old", "basement keys", "location", "mum's place")],
            "s31-new": [fact("s31-new", "basement keys", "location", "desk drawer")],
        },
        {("basement_keys", "location"): current_expectation("desk drawer", refs=["s31-new"])},
        relations_by_event={"s31-new": [_relation("s31-new", "correction", "s31-old")]},
    ),
    semantic_case(
        "relation-duplicate-does-not-supersede",
        [capture("s32-old"), capture("s32-new")],
        {
            "s32-old": [fact("s32-old", "basement keys", "location", "mum's place")],
            "s32-new": [fact("s32-new", "basement keys", "location", "mum's place")],
        },
        {("basement_keys", "location"): current_expectation("mum's place", refs=["s32-new", "s32-old"])},
        relations_by_event={"s32-new": [_relation("s32-new", "duplicate", "s32-old")]},
    ),
    semantic_case(
        "relation-supersession-target",
        [capture("s33-old"), capture("s33-new")],
        {
            "s33-old": [fact("s33-old", "wifi", "password", "BlueRiver7")],
            "s33-new": [fact("s33-new", "wifi", "password", "GreenRiver9")],
        },
        {("wifi", "password"): current_expectation("GreenRiver9", refs=["s33-new"])},
        relations_by_event={"s33-new": [_relation("s33-new", "supersession", "s33-old")]},
    ),
    semantic_case(
        "relation-contradiction-retains-both",
        [capture("s34-old"), capture("s34-new")],
        {
            "s34-old": [fact("s34-old", "car", "possible_cause", "left bearing")],
            "s34-new": [fact("s34-new", "car", "possible_cause", "tyre")],
        },
        {("car", "possible_cause"): current_expectation(status="unknown", state="conflict", refs=["s34-new", "s34-old"])},
        relations_by_event={"s34-new": [_relation("s34-new", "contradiction", "s34-old")]},
    ),
    semantic_case(
        "retract-before-processing",
        [capture("s35")],
        {"s35": [fact("s35", "basement keys", "location", "car")]},
        {},
        retract_before=["s35"],
        history_expected={"s35": {"retracted": True, "active": False}},
    ),
    semantic_case(
        "retract-after-processing",
        [capture("s36")],
        {"s36": [fact("s36", "basement keys", "location", "car")]},
        {},
        retract_after=["s36"],
        history_expected={"s36": {"retracted": True, "active": False}},
    ),
    semantic_case(
        "retract-correction-restores-prior-evidence",
        [capture("s37-old"), capture("s37-new")],
        {
            "s37-old": [fact("s37-old", "basement keys", "location", "mum's place")],
            "s37-new": [fact("s37-new", "basement keys", "location", "desk drawer", operation="correction", supersedes="s37-old")],
        },
        {("basement_keys", "location"): current_expectation("mum's place", refs=["s37-old"])},
        retract_after=["s37-new"],
        history_expected={"s37-new": {"retracted": True, "active": False}, "s37-old": {"current": True}},
    ),
    semantic_case(
        "retract-relation-superseder-restores-prior-evidence",
        [capture("s38-old"), capture("s38-new")],
        {
            "s38-old": [fact("s38-old", "wifi", "password", "BlueRiver7")],
            "s38-new": [fact("s38-new", "wifi", "password", "GreenRiver9")],
        },
        {("wifi", "password"): current_expectation("BlueRiver7", refs=["s38-old"])},
        relations_by_event={"s38-new": [_relation("s38-new", "correction", "s38-old")]},
        retract_after=["s38-new"],
    ),
    semantic_case(
        "exact-temporal-value",
        [capture("s39")],
        {"s39": [fact("s39", "dentist", "appointment", "appointment", temporal={"normalized": "2026-09-03T16:00:00+02:00", "precision": "minute"})]},
        {("dentist", "appointment"): current_expectation("appointment")},
    ),
    semantic_case(
        "structured-weekday-time",
        [capture("s40", timezone_name="UTC")],
        {"s40": [fact("s40", "meeting with Marek", "appointment", "meeting with Marek", temporal={"weekday_index": 3, "local_time": "16:00"})]},
        {("meeting_with_marek", "appointment"): current_expectation("meeting with Marek")},
        attention_expected={"count": 1, "starts_at": "2026-09-03T16:00:00+00:00"},
    ),
    semantic_case(
        "structured-weekday-time-cross-language",
        [capture("s41", timezone_name="UTC")],
        {"s41": [fact("s41", "meeting with Marek", "appointment", "Donnerstag 16:00", temporal={"weekday_index": 3, "local_time": {"hour": 16, "minute": 0}, "expression": "mixed-language weekday"})]},
        {("meeting_with_marek", "appointment"): current_expectation("Donnerstag 16:00")},
        attention_expected={"count": 1, "starts_at": "2026-09-03T16:00:00+00:00"},
    ),
    semantic_case(
        "relative-fact-time",
        [capture("s42", captured_at="2026-08-30T10:00:00+02:00", timezone_name="Europe/Berlin")],
        {"s42": [fact("s42", "children", "pickup", "pickup", temporal={"relative_minutes": 10})]},
        {("children", "pickup"): current_expectation("pickup")},
    ),
    semantic_case(
        "relative-attention-time",
        [capture("s43", captured_at="2026-08-30T10:00:00+02:00", timezone_name="Europe/Berlin")],
        {},
        {},
        attention_by_event={"s43": [attention("s43", "Pick up children", due_at={"relative_minutes": 10})]},
        attention_expected={"count": 1, "due_at": "2026-08-30T10:10:00+02:00"},
    ),
    semantic_case(
        "exact-attention-date-time",
        [capture("s44", timezone_name="UTC")],
        {},
        {},
        attention_by_event={"s44": [attention("s44", "Renew permit", due_at="2026-09-04T17:00:00+00:00")]},
        attention_expected={"count": 1, "due_at": "2026-09-04T17:00:00+00:00"},
    ),
    semantic_case(
        "coarse-next-week",
        [capture("s45")],
        {},
        {},
        attention_by_event={"s45": [attention("s45", "Review plan", due_at="next week")]},
        attention_expected={"count": 1, "due_at": None, "detail_time_status": "coarse_or_ambiguous"},
    ),
    semantic_case(
        "coarse-month-fact",
        [capture("s46")],
        {"s46": [fact("s46", "boiler warranty", "expiry", "December", temporal={"expression": "sometime in December"})]},
        {("boiler_warranty", "expiry"): current_expectation("December")},
    ),
    semantic_case(
        "ambiguous-around-four",
        [capture("s47")],
        {"s47": [fact("s47", "delivery", "time", "around 4", temporal={"expression": "around 4"})]},
        {("delivery", "time"): current_expectation("around 4")},
    ),
    semantic_case(
        "historical-event-no-attention",
        [capture("s48")],
        {"s48": [fact("s48", "brother", "travel_event", "flew there last Thursday")]},
        {("brother", "travel_event"): current_expectation("flew there last Thursday")},
        attention_expected={"count": 0},
    ),
    semantic_case(
        "document-fact-no-attention",
        [capture("s49")],
        {"s49": [fact("s49", "rental contract", "notice_period", "30 days") ]},
        {("rental_contract", "notice_period"): current_expectation("30 days")},
        attention_expected={"count": 0},
    ),
    semantic_case(
        "possible-plan-no-urgent-attention",
        [capture("s50")],
        {"s50": [fact("s50", "Japan", "travel_plan", "next year", status="inferred", certainty="possible")]},
        {("japan", "travel_plan"): current_expectation("next year", status="inferred", state="uncertain")},
        attention_expected={"count": 0},
    ),
    semantic_case(
        "actionable-deadline",
        [capture("s51")],
        {},
        {},
        attention_by_event={"s51": [attention("s51", "Renew parking permit", due_at="2026-09-04T17:00:00+00:00", lifecycle_key="parking-permit")]},
        attention_expected={"count": 1, "status": "open"},
    ),
    semantic_case(
        "attention-reschedule",
        [capture("s52-old"), capture("s52-new")],
        {},
        {},
        attention_by_event={
            "s52-old": [attention("s52-old", "Dentist visit", starts_at="2026-09-01T14:00:00+02:00", lifecycle_key="dentist")],
            "s52-new": [attention("s52-new", "Dentist visit", starts_at="2026-09-03T16:30:00+02:00", lifecycle_key="dentist", lifecycle_action="reschedule", related_event_id="s52-old")],
        },
        attention_expected={"count": 1, "starts_at": "2026-09-03T16:30:00+02:00", "status": "open"},
    ),
    semantic_case(
        "attention-complete",
        [capture("s53-open"), capture("s53-done")],
        {},
        {},
        attention_by_event={
            "s53-open": [attention("s53-open", "Submit report", lifecycle_key="report")],
            "s53-done": [attention("s53-done", "Submit report", status="completed", lifecycle_key="report", lifecycle_action="complete", related_event_id="s53-open")],
        },
        attention_expected={"count": 1, "status": "completed", "state": "completed"},
    ),
    semantic_case(
        "attention-cancel",
        [capture("s54-open"), capture("s54-cancel")],
        {},
        {},
        attention_by_event={
            "s54-open": [attention("s54-open", "Pick up children", lifecycle_key="children-pickup")],
            "s54-cancel": [attention("s54-cancel", "Pick up children", lifecycle_key="children-pickup", lifecycle_action="cancel", related_event_id="s54-open")],
        },
        attention_expected={"count": 1, "status": "cancelled", "state": "cancelled"},
    ),
    semantic_case(
        "attention-date-correction",
        [capture("s55-old", timezone_name="UTC"), capture("s55-new", timezone_name="UTC")],
        {},
        {},
        attention_by_event={
            "s55-old": [attention("s55-old", "Renew permit", due_at="2026-09-02T17:00:00+00:00", lifecycle_key="permit")],
            "s55-new": [attention("s55-new", "Renew permit", due_at="2026-09-04T17:00:00+00:00", lifecycle_key="permit", lifecycle_action="correction", related_event_id="s55-old")],
        },
        attention_expected={"count": 1, "due_at": "2026-09-04T17:00:00+00:00", "status": "open"},
    ),
    semantic_case(
        "uncertain-future-does-not-create-attention",
        [capture("s56")],
        {"s56": [fact("s56", "spare key", "location", "Marta", status="inferred", certainty="maybe")]},
        {("spare_key", "location"): current_expectation("Marta", status="inferred", state="uncertain")},
        attention_by_event={"s56": [attention("s56", "Maybe check spare key next week", due_at="next week", knowledge_status="inferred", actionable=False)]},
        attention_expected={"count": 0},
    ),
    semantic_case(
        "fact-task-auto-attention",
        [capture("s57")],
        {"s57": [fact("s57", "parking permit", "task", "Renew parking permit", temporal={"valid_to": "2026-09-04T17:00:00+00:00"})]},
        {("parking_permit", "task"): current_expectation("Renew parking permit")},
        attention_expected={"count": 1, "title": "Renew parking permit"},
    ),
    semantic_case(
        "appointment-fact-reschedule",
        [capture("s58-old"), capture("s58-new")],
        {
            "s58-old": [fact("s58-old", "dentist", "appointment", "Tuesday 14:00", temporal={"normalized": "2026-09-01T14:00:00+02:00"}, semantic_relation="set")],
            "s58-new": [fact("s58-new", "dentist", "appointment", "Thursday 16:30", temporal={"normalized": "2026-09-03T16:30:00+02:00"}, semantic_relation="reschedule")],
        },
        {("dentist", "appointment"): current_expectation("Thursday 16:30", refs=["s58-new"])},
        attention_expected={"count": 1, "starts_at": "2026-09-03T16:30:00+02:00"},
    ),
    semantic_case(
        "attention-linked-by-related-event",
        [capture("s59-old"), capture("s59-new")],
        {},
        {},
        attention_by_event={
            "s59-old": [attention("s59-old", "Call insurer", lifecycle_key="insurance")],
            "s59-new": [attention("s59-new", "Call insurer tomorrow", related_event_id="s59-old", due_at="2026-08-31T09:00:00+00:00")],
        },
        attention_expected={"count": 1, "title": "Call insurer tomorrow"},
    ),
    semantic_case(
        "uncertainty-resolution-is-targeted",
        [capture("s60-a"), capture("s60-b"), capture("s60-c")],
        {
            "s60-a": [fact("s60-a", "boiler", "condition", "valve", status="inferred")],
            "s60-b": [fact("s60-b", "boiler", "temperature", "70 C")],
            "s60-c": [fact("s60-c", "boiler", "condition", "pump")],
        },
        {
            ("boiler", "condition"): current_expectation("pump", refs=["s60-c"]),
            ("boiler", "temperature"): current_expectation("70 C", refs=["s60-b"]),
        },
    ),
    semantic_case(
        "newer-fact-does-not-supersede-unrelated-history",
        [capture("s61-a"), capture("s61-b")],
        {
            "s61-a": [fact("s61-a", "Kuba", "favorite_food", "green pasta")],
            "s61-b": [fact("s61-b", "Kuba", "clothing_size", 43)],
        },
        {
            ("kuba", "favorite_food"): current_expectation("green pasta", refs=["s61-a"]),
            ("kuba", "clothing_size"): current_expectation(43, refs=["s61-b"]),
        },
    ),
    semantic_case(
        "future-effective-value-coexists-with-current",
        [capture("s62-current"), capture("s62-planned")],
        {
            "s62-current": [fact("s62-current", "parking permit", "fee", 9)],
            "s62-planned": [fact("s62-planned", "parking permit", "fee", 11, temporal={"effective_at": "2026-10-01T00:00:00+00:00"})],
        },
        {("parking_permit", "fee"): current_expectation(9, refs=["s62-current"])},
    ),
    semantic_case(
        "same-value-negation-is-not-duplicate",
        [capture("s63-a"), capture("s63-b")],
        {
            "s63-a": [fact("s63-a", "permit", "active", True)],
            "s63-b": [fact("s63-b", "permit", "active", True, negated=True)],
        },
        {("permit", "active"): current_expectation(status="unknown", state="conflict", refs=["s63-a", "s63-b"])},
    ),
    semantic_case(
        "source-attribution-survives-correction",
        [capture("s64-old"), capture("s64-new")],
        {
            "s64-old": [fact("s64-old", "car", "possible_cause", "bearing", status="inferred", attribution="mechanic one")],
            "s64-new": [fact("s64-new", "car", "possible_cause", "tyre", status="inferred", attribution="mechanic two", operation="contradiction")],
        },
        {("car", "possible_cause"): current_expectation(status="unknown", state="conflict", metadata_contains={"conflicting_fact_ids": [1, 2]})},
    ),
]


class ProductV2SemanticTruthTests(unittest.TestCase):
    def _run_case(self, case: dict[str, Any]) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as directory:
            provider = SemanticTruthProvider(
                case["facts_by_event"],
                case["relations_by_event"],
                case["attention_by_event"],
            )
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                batch_size=50,
                clock=lambda: BASE_NOW,
            ) as runtime:
                for item in case["captures"]:
                    runtime.capture(
                        item.get("text"),
                        event_id=item["event_id"],
                        captured_at=item.get("captured_at"),
                        timezone_name=item.get("timezone_name"),
                    )
                    if item["event_id"] in case["retract_before"]:
                        runtime.retract(item["event_id"], reason="semantic truth test undo")
                result = runtime.process_pending()
                self.assertEqual(result["failed"], 0, case["name"])
                for event_id in case["retract_after"]:
                    runtime.retract(event_id, reason="semantic truth test undo")
                snapshot_now = case.get("snapshot_now") or BASE_NOW
                return runtime.store.snapshot(now=snapshot_now)

    def _assert_case(self, case: dict[str, Any], state: dict[str, Any]) -> None:
        current = {
            (item["entity_key"], item["concept"]): item
            for item in state["current_facts"]
        }
        self.assertEqual(set(current), set(case["current"]), case["name"])
        for key, expectation in case["current"].items():
            item = current[key]
            self.assertEqual(item["knowledge_status"], expectation["status"], case["name"])
            if "value" in expectation:
                self.assertEqual(item.get("value"), expectation["value"], case["name"])
            if "state" in expectation:
                self.assertEqual(item.get("metadata", {}).get("semantic_state"), expectation["state"], case["name"])
            for fragment in expectation.get("contains", []):
                self.assertIn(fragment.casefold(), json.dumps(item, ensure_ascii=False).casefold(), case["name"])
            if "refs" in expectation:
                self.assertEqual(item.get("source_refs"), expectation["refs"], case["name"])
            for metadata_key, metadata_value in expectation.get("metadata_contains", {}).items():
                self.assertEqual(item.get("metadata", {}).get(metadata_key), metadata_value, case["name"])

        history = {item["source_event_id"]: item for item in state["fact_history"]}
        deleted = set(case["retract_before"] + case["retract_after"])
        for event_id, expectation in case["history_expected"].items():
            if event_id in deleted:
                self.assertNotIn(event_id, history, case["name"])
                continue
            self.assertIn(event_id, history, case["name"])
            for key, expected in expectation.items():
                self.assertEqual(history[event_id].get(key), expected, case["name"])
        for event_id in deleted:
            self.assertNotIn(event_id, history, case["name"])
            self.assertNotIn(event_id, state["retracted_event_ids"], case["name"])

        attention_state = state["attention"]
        attention_expectation = case["attention_expected"]
        if "count" in attention_expectation:
            self.assertEqual(len(attention_state), attention_expectation["count"], case["name"])
        if attention_state:
            item = attention_state[0]
            for key in ("status", "state", "starts_at", "due_at"):
                if key in attention_expectation:
                    self.assertEqual(item.get(key), attention_expectation[key], case["name"])
            if "title" in attention_expectation:
                self.assertIn(attention_expectation["title"], item["title"], case["name"])
            if "detail_time_status" in attention_expectation:
                self.assertEqual(item["details"].get("time_status"), attention_expectation["detail_time_status"], case["name"])

    def test_suite_has_at_least_50_sequence_cases(self) -> None:
        self.assertGreaterEqual(len(SEMANTIC_CASES), 50)
        self.assertGreaterEqual(
            sum(len(case["captures"]) > 1 for case in SEMANTIC_CASES),
            25,
        )

    def test_semantic_sequence_matrix(self) -> None:
        for case in SEMANTIC_CASES:
            with self.subTest(case=case["name"]):
                self._assert_case(case, self._run_case(case))

    def test_capture_reference_time_is_used_for_relative_normalization(self) -> None:
        captured = datetime(2026, 8, 30, 10, 0, tzinfo=timezone.utc)
        zone = timezone.utc
        self.assertEqual(
            normalize_timestamp({"relative_minutes": 10}, captured_at=captured, zone=zone),
            "2026-08-30T10:10:00+00:00",
        )
        delayed_processing_now = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(
            normalize_timestamp({"relative_minutes": 10}, captured_at=captured, zone=zone),
            "2026-08-30T10:10:00+00:00",
        )
        self.assertNotEqual(delayed_processing_now.isoformat(), "2026-08-30T10:10:00+00:00")

    def test_structured_temporal_semantics_are_equivalent_across_surface_languages(self) -> None:
        captured = datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)
        expected = "2026-09-03T16:00:00+00:00"
        for surface in ("Thursday at 16:00", "w czwartek o 16:00", "Donnerstag 16:00", "el jueves a las 16:00", "jeudi à 16h00"):
            with self.subTest(surface=surface):
                temporal = normalize_temporal(
                    {
                        "expression": surface,
                        "weekday_index": 3,
                        "local_time": "16:00",
                        "normalized": None,
                        "precision": None,
                    },
                    captured_at=captured,
                    zone=timezone.utc,
                )
                self.assertEqual(temporal["normalized"], expected)
                self.assertEqual(temporal["precision"], "minute")

    def test_nullable_temporal_fields_do_not_mask_deterministic_coarse_normalization(self) -> None:
        captured = datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)
        temporal = normalize_temporal(
            {
                "expression": "sometime in December",
                "precision": None,
                "interval_start": None,
                "interval_end": None,
            },
            captured_at=captured,
            zone=timezone.utc,
        )
        self.assertEqual(temporal["precision"], "month")
        self.assertIn("interval_start", temporal)
        self.assertIn("interval_end", temporal)

    def test_coarse_time_does_not_invent_a_point(self) -> None:
        captured = datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)
        temporal = normalize_temporal(
            {"expression": "sometime in December"},
            captured_at=captured,
            zone=timezone.utc,
        )
        self.assertEqual(temporal["precision"], "month")
        self.assertIn("interval_start", temporal)
        self.assertIn("interval_end", temporal)
        self.assertNotIn("normalized", temporal)
        self.assertIsNone(normalize_timestamp("sometime in December", captured_at=captured, zone=timezone.utc))

    def test_rebuild_preserves_incremental_semantic_state(self) -> None:
        captures = [capture("rebuild-old"), capture("rebuild-new")]
        facts = {
            "rebuild-old": [fact("rebuild-old", "basement keys", "location", "mum's place")],
            "rebuild-new": [fact("rebuild-new", "basement keys", "location", "desk drawer", operation="correction", supersedes="rebuild-old")],
        }
        attention_map = {
            "rebuild-old": [attention("rebuild-old", "Dentist visit", starts_at="2026-09-01T14:00:00+02:00", lifecycle_key="dentist")],
            "rebuild-new": [attention("rebuild-new", "Dentist visit", starts_at="2026-09-03T16:30:00+02:00", lifecycle_key="dentist", lifecycle_action="reschedule", related_event_id="rebuild-old")],
        }
        with tempfile.TemporaryDirectory() as directory:
            provider = SemanticTruthProvider(facts, {}, attention_map)
            with ProductRuntime(directory, provider=provider, start_worker=False, batch_size=1, clock=lambda: BASE_NOW) as runtime:
                for item in captures:
                    runtime.capture(item["text"], event_id=item["event_id"])
                self.assertEqual(runtime.process_pending()["processed"], 2)
                before = runtime.store.snapshot(now=BASE_NOW)
                runtime.store.rebuild()
                after = runtime.store.snapshot(now=BASE_NOW)

        def semantic_subset(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "facts": state["current_facts"],
                "history": [
                    {
                        key: item.get(key)
                        for key in ("source_event_id", "knowledge_status", "value", "temporal", "active", "current", "superseded", "resolved", "retracted")
                    }
                    for item in state["fact_history"]
                ],
                "attention": [
                    {
                        key: item.get(key)
                        for key in ("kind", "title", "status", "starts_at", "due_at", "details", "state")
                    }
                    for item in state["attention"]
                ],
            }

        self.assertEqual(semantic_subset(before), semantic_subset(after))

    def test_ask_renders_current_history_uncertainty_conflict_and_negation_with_precise_refs(self) -> None:
        facts = {
            "ask-old": [fact("ask-old", "basement keys", "location", "mum's place")],
            "ask-new": [fact("ask-new", "basement keys", "location", "desk drawer", operation="correction", supersedes="ask-old")],
            "ask-warranty": [fact("ask-warranty", "boiler warranty", "expiry", "December", status="inferred", certainty="maybe")],
            "ask-a": [fact("ask-a", "car", "possible_cause", "left bearing", attribution="mechanic one")],
            "ask-b": [fact("ask-b", "car", "possible_cause", "tyre", attribution="mechanic two", operation="contradiction")],
            "ask-negated": [fact("ask-negated", "Netflix", "cancelled", True, negated=True)],
        }

        def answer_fn(question: str, context: dict[str, Any]) -> dict[str, Any]:
            lowered = question.casefold()
            if "warranty" in lowered:
                answer = "It is possibly due to expire in December; that was not confirmed."
                ids = [
                    item["evidence_id"]
                    for item in context.get("facts", [])
                    if isinstance(item, dict)
                    and item.get("concept") == "expiry"
                    and isinstance(item.get("evidence_id"), str)
                ]
                return {"answer": answer, "evidence_ids": ids}
            elif "causing" in lowered or "cause" in lowered:
                answer = "Needs clarification: there are conflicting notes about the left bearing and tyre."
                ids = [
                    item["evidence_id"]
                    for item in context.get("facts", [])
                    if isinstance(item, dict)
                    and item.get("concept") == "possible_cause"
                    and isinstance(item.get("evidence_id"), str)
                ]
                return {"answer": answer, "evidence_ids": ids}
            elif "previous" in lowered or "earlier" in lowered:
                answer = "Previously the keys were at mum's place."
                ids = [
                    item["evidence_id"]
                    for item in context.get("history", [])
                    if isinstance(item, dict)
                    and item.get("value") == "mum's place"
                    and isinstance(item.get("evidence_id"), str)
                ]
                return {"answer": answer, "evidence_ids": ids}
            elif "netflix" in lowered:
                answer = "The current fact is not cancelled."
                collections = ("facts",)
            else:
                current = next(
                    (
                        item
                        for item in context.get("facts", [])
                        if isinstance(item, dict) and item.get("knowledge_status") != "unknown"
                    ),
                    None,
                )
                value = current.get("value") if current else None
                answer = f"The current value is {value}."
                collections = ("facts",)
            return answer_from_collections(answer, *collections)(question, context)

        with tempfile.TemporaryDirectory() as directory:
            provider = SemanticTruthProvider(facts, {}, {}, answer_fn=answer_fn)
            with ProductRuntime(directory, provider=provider, start_worker=False, batch_size=50, clock=lambda: BASE_NOW) as runtime:
                for event_id in facts:
                    runtime.capture(event_id, event_id=event_id)
                self.assertEqual(runtime.process_pending()["processed"], len(facts))
                current = runtime.ask("Where are the keys now?")
                self.assertEqual(current["source_refs"], ["ask-new"])
                self.assertIn("desk drawer", current["answer"])

                history = runtime.ask("Where were the keys earlier?")
                self.assertIn("ask-old", history["source_refs"])
                self.assertNotIn("ask-new", history["source_refs"])
                self.assertIn("mum's place", history["answer"])

                uncertainty = runtime.ask("When does the warranty expire?")
                self.assertIn("possibly", uncertainty["answer"])
                self.assertIn("not confirmed", uncertainty["answer"])
                self.assertEqual(uncertainty["source_refs"], ["ask-warranty"])

                conflict = runtime.ask("What's causing the car noise?")
                self.assertIn("needs clarification", conflict["answer"].casefold())
                self.assertEqual(conflict["source_refs"], ["ask-a", "ask-b"])

                negated = runtime.ask("Is Netflix cancelled?")
                self.assertEqual(negated["source_refs"], ["ask-negated"])
                self.assertIn("not cancelled", negated["answer"])

                for context in provider.answer_contexts:
                    self.assertNotIn("payload", json.dumps(context, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
