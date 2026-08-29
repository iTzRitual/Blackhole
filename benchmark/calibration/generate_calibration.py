#!/usr/bin/env python3
"""Generate the non-scored Blackhole benchmark-size calibration data.

This utility creates synthetic raw histories and calibration-only oracle data.
It is deliberately not an application runner, baseline, or evaluator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any


TARGETS = (50, 100, 200, 400)
SEED = "life-inbox-size-calibration-v1"
BASE_DATE = date(2026, 1, 5)

STORYLINES = (
    {"id": "s01", "entity": "Aster", "field": "mode", "values": ("quiet", "active", "paused", "active")},
    {"id": "s02", "entity": "Beryl", "field": "window", "values": ("morning", "afternoon", "evening", "afternoon")},
    {"id": "s03", "entity": "Cinder", "field": "access", "values": ("enabled", "revoked", "limited", "enabled")},
    {"id": "s04", "entity": "Dune", "field": "route", "values": ("north", "west", "east", "west")},
    {"id": "s05", "entity": "Ember", "field": "tier", "values": ("basic", "plus", "basic", "pro")},
    {"id": "s06", "entity": "Flint", "field": "status", "values": ("scheduled", "rescheduled", "cancelled", "scheduled")},
    {"id": "s07", "entity": "Grove", "field": "assignment", "values": ("Mira", "Noah", "unassigned", "Mira"), "inferred": True},
    {"id": "s08", "entity": "Halo", "field": "registration", "values": ("pending", "confirmed", "waitlisted", "confirmed")},
    {"id": "s09", "entity": "Iris", "field": "contact", "values": ("North", "South", "North", "shared")},
    {"id": "s10", "entity": "Jade", "field": "appointment", "values": ("open", "moved", "cancelled", "open")},
)

# The schedule creates uneven observation gaps while keeping all ten
# storylines active. It is intentionally independent from the final benchmark.
SCHEDULE = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
    0, 2, 4, 6, 8, 1, 3, 5, 7, 9,
    0, 3, 6, 9, 1, 4, 7, 2, 5, 8,
    0, 4, 8, 2, 6, 1, 5, 9, 3, 7,
)

QUERIES = [
    {
        "query_id": "current-state",
        "prompt": "What is the current value and knowledge status for each storyline?",
        "kind": "current",
    },
    {
        "query_id": "prior-values",
        "prompt": "For each storyline, report the immediately preceding observed value before the current value, or unknown when none exists.",
        "kind": "previous",
    },
    {
        "query_id": "missing-secondary-fields",
        "prompt": "For each calibration storyline, report that the intentionally unobserved secondary field is unknown with reason missing. Do not invent a field name or treat absence as zero or false.",
        "kind": "missing",
    },
    {
        "query_id": "event-relations",
        "prompt": "How many correction, contradiction, ambiguous-link, and duplicate events are present?",
        "kind": "relations",
    },
]


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def approx_tokens(text: str) -> int:
    """A deliberately conservative planning estimate, not a tokenizer."""

    return max(1, math.ceil(len(text) / 4))


def new_states() -> dict[str, dict[str, Any]]:
    return {
        story["id"]: {
            "version": 0,
            "current": None,
            "previous": None,
            "previous_status": "unknown",
            "current_status": "unknown",
            "conflict_active": False,
            "last_event_id": None,
            "successful_event_ids": [],
            "observed_dates": [],
        }
        for story in STORYLINES
    }


def next_value(story: dict[str, Any], state: dict[str, Any]) -> str:
    value_index = state["version"] % len(story["values"])
    return story["values"][value_index]


def update_state(
    story: dict[str, Any],
    state: dict[str, Any],
    value: str,
    event_id: str,
    observed_at: str,
) -> None:
    state["previous"] = state["current"]
    state["previous_status"] = state["current_status"]
    state["version"] += 1
    state["current"] = value
    state["current_status"] = "inferred" if story.get("inferred") else "known"
    state["conflict_active"] = False
    state["last_event_id"] = event_id
    state["successful_event_ids"].append(event_id)
    state["observed_dates"].append(observed_at)


def make_history(event_count: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    states = new_states()
    events: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    corrections: list[str] = []
    contradictions: list[str] = []
    ambiguous_links: list[str] = []
    duplicate_pairs: list[dict[str, str]] = []

    for sequence in range(1, event_count + 1):
        story = STORYLINES[SCHEDULE[(sequence - 1) % len(SCHEDULE)]]
        state = states[story["id"]]
        event_id = f"cal-{sequence:04d}"
        observed_at = (BASE_DATE + timedelta(days=(sequence - 1) // 3)).isoformat()
        event_kind = "state_update"

        if sequence >= 40 and sequence % 53 == 0 and state["successful_event_ids"]:
            source_id = state["successful_event_ids"][-1]
            source = next(event for event in events if event["event_id"] == source_id)
            text = source["payload"]["text"]
            event_kind = "duplicate"
            duplicate_pairs.append({"event_id": event_id, "duplicate_of": source_id})
            relations.append({"type": "exact_duplicate", "event_id": event_id, "related_event_id": source_id})
        elif sequence >= 30 and sequence % 47 == 0:
            text = (
                f"A note mentions {story['entity']}, but it may refer to {story['entity']} North "
                f"or {story['entity']} South. The entity link is unresolved and no state change is accepted."
            )
            event_kind = "ambiguous_link"
            ambiguous_links.append(event_id)
            relations.append({"type": "ambiguous_link", "event_id": event_id, "storyline_id": story["id"]})
        elif sequence >= 30 and (sequence % 37 == 0 or sequence == 400):
            conflicting_value = f"conflict-{state['version'] + 1:02d}"
            text = (
                f"Conflicting note for {story['entity']}: the current {story['field']} is {conflicting_value}. "
                "This disagrees with the earlier record and remains unresolved."
            )
            event_kind = "contradiction"
            state["conflict_active"] = True
            contradictions.append(event_id)
            relations.append({"type": "contradiction", "event_id": event_id, "storyline_id": story["id"]})
        else:
            value = next_value(story, state)
            previous_event_id = state["last_event_id"]
            if sequence >= 35 and sequence % 41 == 0:
                text = (
                    f"Correction for {story['entity']}: the earlier {story['field']} value was wrong. "
                    f"The current {story['field']} is {value}; keep the earlier record but use this correction."
                )
                event_kind = "correction"
                corrections.append(event_id)
            elif story.get("inferred"):
                text = (
                    f"Tentative note for {story['entity']}: the current {story['field']} is probably {value}. "
                    "Treat this as an unconfirmed observation until stronger evidence appears."
                )
                event_kind = "inferred_update"
            else:
                text = (
                    f"Update for {story['entity']}: the current {story['field']} is {value}. "
                    "This supersedes the earlier value for current-state queries; retain the history."
                )
            update_state(story, state, value, event_id, observed_at)
            if previous_event_id:
                relations.append({"type": "supersedes", "event_id": event_id, "related_event_id": previous_event_id})
            if event_kind == "correction":
                relations.append({"type": "correction", "event_id": event_id, "storyline_id": story["id"]})

        payload = {"text": text}
        events.append(
            {
                "event_id": event_id,
                "sequence": sequence,
                "captured_at": f"{observed_at}T09:00:00Z",
                "observed_at": observed_at,
                "source_type": "text",
                "payload": payload,
                "payload_sha256": hashlib.sha256(compact_json(payload).encode("utf-8")).hexdigest(),
                "metadata": {"synthetic": True, "calibration_only": True},
            }
        )

    final_state: dict[str, Any] = {}
    for story in STORYLINES:
        state = states[story["id"]]
        if state["conflict_active"]:
            current = {
                "knowledge_status": "unknown",
                "unknown_reason": "conflicting",
            }
        else:
            current = {
                "value": state["current"],
                "knowledge_status": state["current_status"],
                "source_ref": state["last_event_id"],
            }
        final_state[story["id"]] = {
            "entity": story["entity"],
            "field": story["field"],
            "current": current,
            "previous": {
                "value": state["previous"],
                "knowledge_status": state["previous_status"] if state["previous"] is not None else "unknown",
                "unknown_reason": "missing" if state["previous"] is None else None,
            },
            "secondary_field": {
                "field": "secondary_field",
                "knowledge_status": "unknown",
                "unknown_reason": "missing",
            },
            "last_event_id": state["last_event_id"],
            "observed_event_count": len(state["successful_event_ids"]),
            "observation_dates": state["observed_dates"],
        }

    missing_periods = {}
    for story in STORYLINES:
        dates = [date.fromisoformat(value) for value in states[story["id"]]["observed_dates"]]
        gaps = [(later - earlier).days for earlier, later in zip(dates, dates[1:])]
        missing_periods[story["id"]] = {
            "max_gap_days_between_observations": max(gaps) if gaps else None,
            "secondary_field": "secondary_field",
        }

    diagnostics = {
        "correction_event_ids": corrections,
        "contradiction_event_ids": contradictions,
        "ambiguous_link_event_ids": ambiguous_links,
        "duplicate_pairs": duplicate_pairs,
        "relation_count": len(relations),
        "missing_periods": missing_periods,
    }
    query_answers = []
    for query in QUERIES:
        if query["kind"] == "current":
            assertions = []
            for story_id, story in final_state.items():
                assertion = {"state_key": f"{story_id}/{story['field']}/current", **story["current"]}
                assertions.append(assertion)
            query_answers.append({"query_id": query["query_id"], "assertions": assertions})
        elif query["kind"] == "previous":
            assertions = []
            for story_id, story in final_state.items():
                previous = {"state_key": f"{story_id}/{story['field']}/previous", **story["previous"]}
                assertions.append(previous)
            query_answers.append({"query_id": query["query_id"], "assertions": assertions})
        elif query["kind"] == "missing":
            assertions = []
            for story_id, story in final_state.items():
                assertions.append(
                    {
                        "state_key": f"{story_id}/{story['secondary_field']['field']}",
                        **story["secondary_field"],
                    }
                )
            query_answers.append({"query_id": query["query_id"], "assertions": assertions})
        else:
            query_answers.append(
                {
                    "query_id": query["query_id"],
                    "relation_summary": {
                        "correction_count": len(corrections),
                        "contradiction_count": len(contradictions),
                        "ambiguous_link_count": len(ambiguous_links),
                        "duplicate_count": len(duplicate_pairs),
                    },
                }
            )

    oracle = {
        "contract_version": "0.1-calibration-not-scored",
        "dataset": "life-inbox-size-calibration",
        "event_count": event_count,
        "final_state": final_state,
        "diagnostics": diagnostics,
        "query_bundle": QUERIES,
        "query_answers": query_answers,
        "scoring_note": "Calibration oracle only. These assertions are not part of the final benchmark and must not be used to tune a baseline prompt.",
    }
    return events, oracle


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(compact_json(value) + "\n" for value in values), encoding="utf-8")


def build_report(histories: dict[int, list[dict[str, Any]]]) -> dict[str, Any]:
    # These are planning constants, not claims about any provider's tokenizer.
    system_overhead_tokens = 160
    query_bundle_tokens = approx_tokens("\n".join(query["prompt"] for query in QUERIES))
    rows = []
    for event_count, events in histories.items():
        serialized = "\n".join(compact_json(event) for event in events)
        history_tokens = approx_tokens(serialized)
        final_input_tokens = history_tokens + system_overhead_tokens + query_bundle_tokens
        checkpoints = [target for target in TARGETS if target <= event_count]
        checkpoint_input_tokens = sum(
            approx_tokens("\n".join(compact_json(event) for event in events[:checkpoint]))
            + system_overhead_tokens
            + query_bundle_tokens
            for checkpoint in checkpoints
        )
        rows.append(
            {
                "event_count": event_count,
                "history_characters": len(serialized),
                "approx_history_tokens": history_tokens,
                "approx_final_query_input_tokens": final_input_tokens,
                "checkpoint_prefixes": checkpoints,
                "approx_checkpoint_sweep_input_tokens": checkpoint_input_tokens,
                "fit_by_context_limit_with_75_percent_usable_budget": {
                    str(limit): final_input_tokens <= int(limit * 0.75)
                    for limit in (16_000, 32_000, 64_000, 128_000, 200_000)
                },
            }
        )
    return {
        "dataset": "life-inbox-size-calibration",
        "scored": False,
        "token_estimate_method": "ceil(serialized characters / 4), plus fixed planning overhead; use a provider tokenizer when exposed and retain runtime usage separately",
        "system_overhead_tokens": system_overhead_tokens,
        "query_bundle_tokens": query_bundle_tokens,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    histories_dir = output_dir / "histories"
    oracle_dir = output_dir / "oracle"
    reports_dir = output_dir / "reports"

    histories: dict[int, list[dict[str, Any]]] = {}
    oracle_hashes: dict[str, str] = {}
    for event_count in TARGETS:
        events, oracle = make_history(event_count)
        histories[event_count] = events
        history_path = histories_dir / f"history-{event_count:03d}.jsonl"
        oracle_path = oracle_dir / f"oracle-{event_count:03d}.json"
        write_jsonl(history_path, events)
        write_json(oracle_path, oracle)
        oracle_hashes[str(event_count)] = hashlib.sha256(oracle_path.read_bytes()).hexdigest()

    manifest = {
        "dataset": "life-inbox-size-calibration",
        "version": "0.1",
        "scored": False,
        "seed_label": SEED,
        "event_counts": list(TARGETS),
        "storyline_ids": [story["id"] for story in STORYLINES],
        "storyline_count": len(STORYLINES),
        "schedule_length": len(SCHEDULE),
        "history_files": [f"histories/history-{count:03d}.jsonl" for count in TARGETS],
        "oracle_files": [f"oracle/oracle-{count:03d}.json" for count in TARGETS],
        "oracle_sha256": oracle_hashes,
        "ground_truth_boundary": "Calibration-only oracle data is separate from benchmark/dev and benchmark/holdout. It must not be used to tune baseline prompts.",
    }
    write_json(output_dir / "manifest.json", manifest)
    write_json(reports_dir / "token-estimates.json", build_report(histories))


if __name__ == "__main__":
    main()
