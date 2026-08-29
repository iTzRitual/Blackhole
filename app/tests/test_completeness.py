from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from app.completeness import (
    detect_coverage_gaps,
    deterministic_completions,
    prepare_verifier_observations,
    scan_raw_evidence,
    verification_prompt,
)
from app.state_store import StateStore, canonical_json


CONTRACT = {
    "public_ontology": {
        "subjects": [
            {"id": "agreement", "kind": "contract", "aliases": ["Agreement"]},
            {"id": "policy", "kind": "insurance", "aliases": ["Policy"]},
            {"id": "task", "kind": "task", "aliases": ["Task"]},
            {"id": "action", "kind": "action", "aliases": ["Action"]},
        ],
        "predicates": [
            {"id": "status", "aliases": ["status"]},
            {"id": "signed_date", "aliases": ["signed date"]},
            {"id": "effective_date", "aliases": ["effective date"]},
            {"id": "expiry_date", "aliases": ["expiry date"]},
            {"id": "contract_id", "aliases": ["contract id"]},
            {"id": "policy_id", "aliases": ["policy id"]},
            {"id": "premium", "aliases": ["premium"]},
            {"id": "amount", "aliases": ["amount"]},
            {"id": "executed", "aliases": ["executed"]},
            {"id": "blocker", "aliases": ["blocker"]},
        ],
        "dynamic_subjects": [],
    },
    "predicate_value_shapes": {},
    "unknown_reason": {"allowed_categories": ["missing", "not_stated"]},
    "value_normalization": {},
}


def event(event_id: str, sequence: int, text: str) -> dict:
    payload = {"text": text}
    return {
        "event_id": event_id,
        "sequence": sequence,
        "captured_at": f"2026-01-{sequence:02d}T09:00:00+01:00",
        "observed_at": f"2026-01-{sequence:02d}",
        "source_type": "text",
        "payload": payload,
        "payload_sha256": hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        "metadata": {"synthetic": True},
    }


class CompletenessTests(unittest.TestCase):
    def test_scanner_emits_structural_anchors_and_context(self) -> None:
        evidence = scan_raw_evidence(
            event(
                "capture-a",
                1,
                "Agreement AG-123 was signed 2026-01-02 and effective 2026-02-01 for 27.00 EUR per month; approve the draft.",
            )
        )
        anchors = evidence["anchors"]
        self.assertEqual({item["type"] for item in anchors}, {"date", "amount", "currency", "identifier", "temporal_cue", "lifecycle_cue", "action_cue"})
        self.assertEqual({item["raw_value"] for item in anchors if item["type"] == "date"}, {"2026-01-02", "2026-02-01"})
        self.assertEqual({item["raw_value"] for item in anchors if item["type"] == "identifier"}, {"AG-123"})
        self.assertTrue(any("signed" in item.get("context", "").casefold() for item in anchors if item["type"] == "date"))

    def test_gap_detector_and_completion_cover_only_unambiguous_fields(self) -> None:
        events = [
            event("capture-a", 1, "Agreement AG-123 was signed 2026-01-02."),
            event("capture-b", 2, "Policy PL_928 premium is 42.00 EUR per month."),
            event("capture-c", 3, "Prepare a 50.00 EUR action, but do not send it."),
            event("capture-d", 4, "Reopen the task because the document was not accepted."),
        ]
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(events)
                store.add_observations(
                    [
                        {"event_id": "capture-a", "subject": "agreement", "predicate": "status", "knowledge_status": "known", "value": "signed"},
                        {"event_id": "capture-b", "subject": "policy", "predicate": "premium", "knowledge_status": "known", "value": {"amount": "42", "currency": "eur"}},
                        {"event_id": "capture-c", "subject": "action", "predicate": "amount", "knowledge_status": "known", "value": {"amount": "50", "currency": "eur"}},
                        {"event_id": "capture-c", "subject": "action", "predicate": "executed", "knowledge_status": "known", "value": False},
                        {"event_id": "capture-d", "subject": "task", "predicate": "blocker", "knowledge_status": "known", "value": "document was not accepted"},
                    ],
                    "fixture-extractor",
                )
                store.rebuild_projection()
                snapshot = store.snapshot()
                records = {}
                for item in events:
                    evidence = scan_raw_evidence(item)
                    gap = detect_coverage_gaps(item, evidence, snapshot, CONTRACT)
                    records[item["event_id"]] = (evidence, gap)
                self.assertIn("explicit signed_date not represented", records["capture-a"][1]["reasons"])
                self.assertIn("explicit contract_id not represented", records["capture-a"][1]["reasons"])
                self.assertIn("explicit monthly cue not represented in amount object", records["capture-b"][1]["reasons"])
                self.assertIn("lifecycle cue supports status proposed", records["capture-c"][1]["reasons"])
                self.assertIn("lifecycle cue supports status open", records["capture-d"][1]["reasons"])
                completions = deterministic_completions(events[0], records["capture-a"][1], snapshot)
                self.assertEqual({item["predicate"] for item in completions}, {"contract_id", "signed_date"})
                self.assertEqual({item["value"] for item in completions}, {"ag-123", "2026-01-02"})

    def test_irrelevant_number_and_date_do_not_create_a_gap(self) -> None:
        item = event("capture-a", 1, "I counted 3 items on 2026-01-02; this is only a note.")
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events([item])
                store.rebuild_projection()
                evidence = scan_raw_evidence(item)
                gap = detect_coverage_gaps(item, evidence, store.snapshot(), CONTRACT)
                self.assertEqual(gap["reasons"], [])
                self.assertEqual(deterministic_completions(item, gap, store.snapshot()), [])

    def test_existing_subject_value_suppresses_repeated_anchor(self) -> None:
        first = event("capture-a", 1, "Agreement AG-123 was signed 2026-01-02.")
        second = event("capture-b", 2, "The signed date for AG-123 is 2026-01-02.")
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events([first, second])
                store.add_observations(
                    [
                        {"event_id": "capture-a", "subject": "agreement", "predicate": "signed_date", "knowledge_status": "known", "value": "2026-01-02"},
                        {"event_id": "capture-a", "subject": "agreement", "predicate": "contract_id", "knowledge_status": "known", "value": "AG-123"},
                        {"event_id": "capture-b", "subject": "agreement", "predicate": "status", "knowledge_status": "known", "value": "signed"},
                    ],
                    "fixture-extractor",
                )
                store.rebuild_projection()
                evidence = scan_raw_evidence(second)
                gap = detect_coverage_gaps(second, evidence, store.snapshot(), CONTRACT)
                self.assertEqual(gap["reasons"], [])

    def test_verifier_output_is_scoped_to_event_and_anchors(self) -> None:
        item = event("capture-a", 1, "Agreement AG-123 was signed 2026-01-02.")
        evidence = scan_raw_evidence(item)
        parsed = {
            "add_observations": [
                {"subject": "agreement", "predicate": "signed_date", "knowledge_status": "known", "value": "2026-01-02"},
                {"event_id": "capture-other", "subject": "agreement", "predicate": "status", "knowledge_status": "known", "value": "signed"},
                {"state_key": "hidden", "subject": "agreement", "predicate": "contract_id", "knowledge_status": "known", "value": "AG-123"},
            ],
            "replace_observations": [],
            "no_change": False,
        }
        prepared = prepare_verifier_observations(parsed, event_id="capture-a", evidence=evidence, contract=CONTRACT)
        self.assertEqual(len(prepared["items"]), 1)
        self.assertEqual(prepared["items"][0]["source_refs"], ["capture-a"])
        self.assertEqual(len(prepared["rejected"]), 2)

    def test_verification_prompt_contains_only_scoped_inputs(self) -> None:
        item = event("capture-a", 1, "Agreement AG-123 was signed 2026-01-02.")
        evidence = scan_raw_evidence(item)
        gap = {"event_id": "capture-a", "subjects": ["agreement"], "existing_observations": [], "reasons": ["test"]}
        prompt = verification_prompt(item, gap, evidence, {"current_facts": []}, CONTRACT)
        self.assertIn("Agreement AG-123 was signed 2026-01-02.", prompt)
        self.assertIn("STRUCTURAL EVIDENCE ANCHORS", prompt)
        self.assertNotIn("scenario-001", prompt)
        self.assertNotIn("q-contract-dates", prompt)


if __name__ == "__main__":
    unittest.main()
