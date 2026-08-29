"""Generate the public Gate A development benchmark and its visible oracle.

This is benchmark design infrastructure, not product code.  The generator keeps
the canonical synthetic world in this file and emits only normalized public
captures plus development expected outputs.  Holdout material is intentionally
not generated here.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / "benchmark" / "dev" / "cases"
EXPECTED_DIR = ROOT / "benchmark" / "dev" / "expected"

CONTRACT_VERSION = "1.0-gate-a-dev"
SCENARIO_ID = "blackhole-dev-001-state-churn"
BASE_DATE = date(2026, 1, 5)
TIMEZONE = "Europe/Berlin"
CHECKPOINTS = (50, 100, 150, 200)
EVENT_COUNT = 200

MISSING = object()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def U(
    state_key: str,
    value: Any = MISSING,
    *,
    status: str = "known",
    reason: str | None = None,
    confirmation: str | None = None,
    extra_refs: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Create an internal state transition template."""

    result: dict[str, Any] = {
        "state_key": state_key,
        "knowledge_status": status,
        "extra_refs": list(extra_refs),
    }
    if value is not MISSING:
        result["value"] = value
    if reason is not None:
        result["unknown_reason"] = reason
    if confirmation is not None:
        result["confirmation_ref"] = confirmation
    return result


def R(
    relation_type: str,
    target_local: int | None = None,
    *,
    changed_fields: tuple[str, ...] = (),
    duplicate_group: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "relation_type": relation_type,
        "target_local": target_local,
    }
    if changed_fields:
        result["changed_fields"] = list(changed_fields)
    if duplicate_group is not None:
        result["duplicate_group"] = duplicate_group
    if note is not None:
        result["note"] = note
    return result


def E(
    text: str,
    *,
    source_type: str = "text",
    updates: tuple[dict[str, Any], ...] = (),
    relations: tuple[dict[str, Any], ...] = (),
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Accept both ``(R(...),)`` and the visually easy-to-write ``R(...)``
    # form so a missing tuple comma cannot turn a relation into its dict keys.
    relation_list = [relations] if isinstance(relations, dict) else list(relations)
    return {
        "text": text,
        "source_type": source_type,
        "updates": list(updates),
        "relations": relation_list,
        "data": data,
    }


def subscription_events() -> list[dict[str, Any]]:
    price = lambda amount: U(
        "subscription:streamly/current_price",
        {"amount": amount, "currency": "EUR", "billing_period": "month"},
    )
    return [
        E("Streamly is active at 12.00 EUR per month.", source_type="subscription", updates=(U("subscription:streamly/status", "active"), price("12.00"), U("subscription:streamly/currency", "EUR"), U("subscription:streamly/billing_period", "month"))),
        E("The Streamly charge appeared on my card.", source_type="receipt", updates=(U("subscription:streamly/last_charge", {"amount": "12.00", "currency": "EUR"}),)),
        E("Streamly sent a notice: the monthly price will be 14.00 EUR.", source_type="subscription", updates=(price("14.00"),), relations=(R("price_change", 1, changed_fields=("amount",))),),
        E("I intend to cancel Streamly, but I have not submitted the cancellation.", source_type="text", updates=(U("subscription:streamly/cancellation_intent", True), U("subscription:streamly/cancellation_requested", False), U("task:cancel-streamly/lifecycle", "inferred"))),
        E("I changed my mind; keep Streamly for now.", source_type="text", updates=(U("subscription:streamly/cancellation_intent", False), U("task:cancel-streamly/lifecycle", "cancelled"))),
        E("The next Streamly charge was 14.00 EUR.", source_type="receipt", updates=(U("subscription:streamly/last_charge", {"amount": "14.00", "currency": "EUR"}),)),
        E("Streamly now costs 16.00 EUR each month.", source_type="subscription", updates=(price("16.00"),), relations=(R("price_change", 6, changed_fields=("amount",))),),
        E("Please cancel Streamly at the end of February; this is a request.", source_type="text", updates=(U("subscription:streamly/cancellation_intent", True), U("subscription:streamly/cancellation_requested", True), U("subscription:streamly/termination_date", "2026-02-28"))),
        E("Streamly cancellation was confirmed for 2026-02-28.", source_type="document", updates=(U("subscription:streamly/status", "cancelled"), U("subscription:streamly/termination_date", "2026-02-28"))),
        E("I reactivated Streamly after all.", source_type="text", updates=(U("subscription:streamly/status", "active"), U("subscription:streamly/cancellation_intent", False), U("subscription:streamly/cancellation_requested", False))),
        E("The reactivated Streamly charge was 16.00 EUR.", source_type="receipt", updates=(U("subscription:streamly/last_charge", {"amount": "16.00", "currency": "EUR"}),)),
        E("The Streamly monthly price is 18.00 EUR from March.", source_type="subscription", updates=(price("18.00"), U("subscription:streamly/price_effective", "2026-03-01")), relations=(R("price_change", 11, changed_fields=("amount",))),),
        E("I might cancel Streamly again, but that is only an intention.", source_type="text", updates=(U("subscription:streamly/cancellation_intent", True), U("subscription:streamly/cancellation_requested", False))),
        E("No, keep Streamly active; cancel that intention.", source_type="text", updates=(U("subscription:streamly/cancellation_intent", False), U("task:cancel-streamly/lifecycle", "cancelled"))),
        E("Streamly billed 18.00 EUR.", source_type="receipt", updates=(U("subscription:streamly/last_charge", {"amount": "18.00", "currency": "EUR"}),)),
        E("Streamly remains active and I did not ask it to be cancelled.", source_type="text", updates=(U("subscription:streamly/status", "active"), U("subscription:streamly/cancellation_requested", False))),
        E("Another Streamly charge was 18.00 EUR.", source_type="receipt", updates=(U("subscription:streamly/last_charge", {"amount": "18.00", "currency": "EUR"}),)),
        E("I am considering cancelling Streamly on renewal.", source_type="text", updates=(U("subscription:streamly/cancellation_intent", True), U("subscription:streamly/cancellation_requested", False))),
        E("I decided not to cancel Streamly.", source_type="text", updates=(U("subscription:streamly/cancellation_intent", False),)),
        E("Streamly is active; the next renewal is 2026-03-20 at 18.00 EUR.", source_type="subscription", updates=(U("subscription:streamly/status", "active"), price("18.00"), U("subscription:streamly/next_renewal", "2026-03-20"))),
    ]


def bill_events() -> list[dict[str, Any]]:
    entries = [
        ("2026-01", "29.90"), ("2026-02", "29.90"), ("2026-03", "29.90"),
        ("2026-04", None), ("2026-05", "31.90"), ("2026-06", "31.90"),
        ("2026-07", "31.90"), ("2026-08", None), ("2026-09", "33.90"),
        ("2026-10", "33.90"), ("2026-11", "33.90"), ("2026-12", "35.90"),
        ("2027-01", "35.90"), ("2027-02", None), ("2027-03", "35.90"),
        ("2027-04", "35.90"), ("2027-05", "37.90"), ("2027-06", "37.90"),
        ("2027-07", None), ("2027-08", "37.90"),
    ]
    result = []
    for period, amount in entries:
        if amount is None:
            result.append(E(f"No Orange Mobile bill was captured for {period}; coverage is missing, not zero.", source_type="text", data={"kind": "bill_missing", "period": period}))
        else:
            result.append(E(f"Orange Mobile bill for {period}: {amount} EUR.", source_type="receipt", updates=(U("finance:orange/current_amount", {"amount": amount, "currency": "EUR"}),), data={"kind": "bill", "period": period, "amount": amount, "currency": "EUR"}))
    return result


def purchase_events() -> list[dict[str, Any]]:
    return [
        E("MarketOne receipt: 3 protein bars for 9.00 EUR.", source_type="receipt", data={"kind": "purchase", "quantity": 3, "amount": "9.00", "currency": "EUR"}),
        E("I ate one protein bar.", source_type="text", data={"kind": "consumption", "quantity": 1}),
        E("I ate two more protein bars.", source_type="text", data={"kind": "consumption", "quantity": 2}),
        E("There is no consumption note for January 12.", source_type="text", data={"kind": "consumption_missing", "period": "2026-01-12"}),
        E("MarketOne receipt: 6 protein bars for 18.00 EUR.", source_type="receipt", data={"kind": "purchase", "quantity": 6, "amount": "18.00", "currency": "EUR"}),
        E("I ate one bar from the second pack.", source_type="text", data={"kind": "consumption", "quantity": 1}),
        E("MarketOne receipt: 2 bars for 6.00 EUR.", source_type="receipt", data={"kind": "purchase", "quantity": 2, "amount": "6.00", "currency": "EUR"}),
        E("I ate two bars.", source_type="text", data={"kind": "consumption", "quantity": 2}),
        E("I did not record whether I ate a bar on February 10.", source_type="text", data={"kind": "consumption_missing", "period": "2026-02-10"}),
        E("I ate three bars from the pantry.", source_type="text", data={"kind": "consumption", "quantity": 3}),
        E("MarketOne receipt: 10 bars for 30.00 EUR.", source_type="receipt", data={"kind": "purchase", "quantity": 10, "amount": "30.00", "currency": "EUR"}),
        E("No consumption observation was captured for February 20.", source_type="text", data={"kind": "consumption_missing", "period": "2026-02-20"}),
        E("I ate four bars.", source_type="text", data={"kind": "consumption", "quantity": 4}),
        E("MarketOne receipt: 4 bars for 12.00 EUR.", source_type="receipt", data={"kind": "purchase", "quantity": 4, "amount": "12.00", "currency": "EUR"}),
        E("I explicitly ate zero bars today.", source_type="text", data={"kind": "consumption", "quantity": 0}),
        E("MarketOne receipt: 5 bars for 15.00 EUR.", source_type="receipt", data={"kind": "purchase", "quantity": 5, "amount": "15.00", "currency": "EUR"}),
        E("I ate one bar.", source_type="text", data={"kind": "consumption", "quantity": 1}),
        E("MarketOne receipt: 3 bars for 9.00 EUR.", source_type="receipt", data={"kind": "purchase", "quantity": 3, "amount": "9.00", "currency": "EUR"}),
        E("I ate two bars.", source_type="text", data={"kind": "consumption", "quantity": 2}),
        E("The later period has no reliable consumption observation.", source_type="text", data={"kind": "consumption_missing", "period": "2026-03-15"}),
    ]


def task_events() -> list[dict[str, Any]]:
    return [
        E("Pick up the parcel for Alex by 2026-01-12.", source_type="task-note", updates=(U("task:parcel-pickup-1/lifecycle", "open"), U("task:parcel-pickup-1/owner", "Alex"), U("task:parcel-pickup-1/deadline", "2026-01-12"))),
        E("Sam will handle parcel pickup instead of Alex.", source_type="task-note", updates=(U("task:parcel-pickup-1/owner", "Sam"),), relations=(R("task_reassignment", 1, changed_fields=("owner",))),),
        E("The store says parcel pickup is still pending.", source_type="text", updates=(U("task:parcel-pickup-1/lifecycle", "open"),)),
        E("The store cancelled parcel pickup; no collection is needed.", source_type="text", updates=(U("task:parcel-pickup-1/lifecycle", "cancelled"),), relations=(R("task_cancellation", 3, changed_fields=("lifecycle",))),),
        E("Open task: Alex should pick up the replacement parcel by 2026-02-25.", source_type="task-note", updates=(U("task:parcel-pickup-2/lifecycle", "open"), U("task:parcel-pickup-2/owner", "Alex"), U("task:parcel-pickup-2/deadline", "2026-02-25"))),
        E("Alex picked up the replacement parcel.", source_type="text", updates=(U("task:parcel-pickup-2/lifecycle", "completed"),)),
        E("The replacement parcel was returned, so pickup is open again.", source_type="text", updates=(U("task:parcel-pickup-2/lifecycle", "open"),), relations=(R("task_reopened", 6, changed_fields=("lifecycle",))),),
        E("Sam is now responsible for the replacement parcel.", source_type="task-note", updates=(U("task:parcel-pickup-2/owner", "Sam"),), relations=(R("task_reassignment", 8, changed_fields=("owner",))),),
        E("Alex will take the replacement parcel task back.", source_type="task-note", updates=(U("task:parcel-pickup-2/owner", "Alex"),), relations=(R("task_reassignment", 9, changed_fields=("owner",))),),
        E("The replacement parcel deadline moved to 2026-03-05.", source_type="task-note", updates=(U("task:parcel-pickup-2/deadline", "2026-03-05"),)),
        E("Return the library books; Sam owns this task by 2026-02-18.", source_type="task-note", updates=(U("task:library-return-1/lifecycle", "open"), U("task:library-return-1/owner", "Sam"), U("task:library-return-1/deadline", "2026-02-18"))),
        E("Sam returned the library books.", source_type="text", updates=(U("task:library-return-1/lifecycle", "completed"),)),
        E("Alex completed the replacement parcel pickup.", source_type="text", updates=(U("task:parcel-pickup-2/lifecycle", "completed"),)),
        E("The parcel was not accepted, so reopen the pickup task.", source_type="text", updates=(U("task:parcel-pickup-2/lifecycle", "open"),), relations=(R("task_reopened", 14, changed_fields=("lifecycle",))),),
        E("Sam will complete the reopened pickup task.", source_type="task-note", updates=(U("task:parcel-pickup-2/owner", "Sam"),), relations=(R("task_reassignment", 15, changed_fields=("owner",))),),
        E("Sam completed the replacement parcel pickup.", source_type="text", updates=(U("task:parcel-pickup-2/lifecycle", "completed"),)),
        E("Open task: Alex must submit the school form by 2026-03-18.", source_type="task-note", updates=(U("task:school-form-1/lifecycle", "open"), U("task:school-form-1/owner", "Alex"), U("task:school-form-1/deadline", "2026-03-18"))),
        E("The school form cannot be submitted until the missing signature is found.", source_type="text", updates=(U("task:school-form-1/blocker", "missing signature", status="inferred"),)),
        E("The school form deadline is still 2026-03-18.", source_type="task-note", updates=(U("task:school-form-1/deadline", "2026-03-18"),)),
        E("The school form remains open with Alex responsible; no completion was recorded.", source_type="task-note", updates=(U("task:school-form-1/lifecycle", "open"), U("task:school-form-1/owner", "Alex"))),
    ]


def insurance_events() -> list[dict[str, Any]]:
    return [
        E("RoadSure policy RS-OLD is active from 2026-01-01 through 2026-06-30.", source_type="document", updates=(U("insurance:current/policy_id", "RS-OLD"), U("insurance:current/status", "active"), U("insurance:current/effective_date", "2026-01-01"), U("insurance:current/expiry_date", "2026-06-30"))),
        E("I think the old RoadSure policy might run until July; this is not confirmed.", source_type="text", updates=(U("insurance:old_possible_expiry", status="unknown", reason="ambiguous_note", extra_refs=("$previous",)),)),
        E("The RoadSure document confirms RS-OLD expires on 2026-06-30.", source_type="document", updates=(U("insurance:old_possible_expiry", "2026-06-30"), U("insurance:current/expiry_date", "2026-06-30"))),
        E("RoadSure offered replacement policy RS-NEW, but this is only a quote.", source_type="document", updates=(U("insurance:replacement_candidate", "RS-NEW", status="inferred"),)),
        E("The signed RoadSure policy RS-NEW is active from 2026-07-01 through 2027-06-30.", source_type="document", updates=(U("insurance:current/policy_id", "RS-NEW"), U("insurance:current/status", "active"), U("insurance:current/effective_date", "2026-07-01"), U("insurance:current/expiry_date", "2027-06-30"), U("insurance:old_policy_status", "superseded")), relations=(R("policy_replacement", 5, changed_fields=("policy_id", "effective_date"))),),
        E("The new RoadSure premium is 42.00 EUR per month.", source_type="document", updates=(U("insurance:current/premium", {"amount": "42.00", "currency": "EUR", "billing_period": "month"}),)),
        E("A RoadSure card shows RS-NEW, not the old policy.", source_type="text", updates=(U("insurance:current/policy_id", "RS-NEW"),)),
        E("The old RoadSure cancellation date was not printed clearly.", source_type="document", updates=(U("insurance:old_cancellation_date", status="unknown", reason="unreadable", extra_refs=("$previous",)),)),
        E("RoadSure confirmed RS-OLD was superseded when RS-NEW started.", source_type="text", updates=(U("insurance:old_policy_status", "superseded"),)),
        E("RS-NEW is the current RoadSure policy.", source_type="document", updates=(U("insurance:current/policy_id", "RS-NEW"),)),
        E("The RS-NEW card again shows expiry 2027-06-30.", source_type="document", updates=(U("insurance:current/expiry_date", "2027-06-30"),)),
        E("The claim number is unreadable in the RoadSure scan.", source_type="document", updates=(U("insurance:current/claim_number", status="unknown", reason="unreadable"),)),
        E("The replacement policy remains active.", source_type="text", updates=(U("insurance:current/status", "active"),)),
        E("RoadSure support reconfirmed that RS-NEW ends on 2027-06-30.", source_type="text", updates=(U("insurance:current/expiry_date", "2027-06-30"),)),
        E("No beneficiary is stated in the insurance records.", source_type="document", updates=(U("insurance:current/beneficiary", status="unknown", reason="not_stated"),)),
        E("The current RoadSure policy is RS-NEW.", source_type="text", updates=(U("insurance:current/policy_id", "RS-NEW"),)),
        E("RS-OLD is historical and RS-NEW is current.", source_type="text", updates=(U("insurance:old_policy_status", "superseded"), U("insurance:current/status", "active"))),
        E("RoadSure sent a renewal reminder for the current policy.", source_type="document", updates=(U("insurance:renewal_reminder", {"policy_id": "RS-NEW"}, status="inferred"),)),
        E("The current RoadSure expiry remains 2027-06-30.", source_type="document", updates=(U("insurance:current/expiry_date", "2027-06-30"),)),
        E("I have no confirmed claim number for RS-NEW.", source_type="text", updates=(U("insurance:current/claim_number", status="unknown", reason="not_available"),)),
    ]


def receipt_events() -> list[dict[str, Any]]:
    return [
        E("Corner Mart receipt R-1001: 11.20 EUR on 2026-01-06.", source_type="receipt"),
        E("Corner Mart receipt R-1001 uploaded again unchanged.", source_type="receipt", relations=(R("exact_duplicate", 1, duplicate_group="corner-r-1001"),)),
        E("Corner Mart receipt R-1001 correction: total is 11.40 EUR.", source_type="receipt", relations=(R("meaningful_change", 1, changed_fields=("amount",), duplicate_group="corner-r-1001"),)),
        E("Corner Mart receipt R-1002: 11.20 EUR on 2026-01-08.", source_type="receipt"),
        E("Corner Mart receipt R-1002 uploaded with the same contents.", source_type="receipt", relations=(R("normalized_duplicate", 4, duplicate_group="corner-r-1002"),)),
        E("Corner Mart receipt R-1002 has a changed date and total: 12.20 EUR on 2026-01-09.", source_type="receipt", relations=(R("meaningful_change", 4, changed_fields=("amount", "date"), duplicate_group="corner-r-1002"),)),
        E("A normalized copy of receipt R-1002 was captured.", source_type="receipt", relations=(R("normalized_duplicate", 6, duplicate_group="corner-r-1002"),)),
        E("Corner Mart receipt R-1003: 8.00 EUR on 2026-01-12.", source_type="receipt"),
        E("Corner Mart receipt R-1004: 8.50 EUR on 2026-01-13.", source_type="receipt"),
        E("Receipt R-1003 was uploaded a second time unchanged.", source_type="receipt", relations=(R("exact_duplicate", 8, duplicate_group="corner-r-1003"),)),
        E("Receipt R-1004 has a tax line correction; total remains 8.50 EUR.", source_type="receipt", relations=(R("meaningful_change", 9, changed_fields=("tax_line",), duplicate_group="corner-r-1004"),)),
        E("Corner Mart receipt R-1005: 21.00 EUR on 2026-01-20.", source_type="receipt"),
        E("Receipt R-1005 looks similar to R-1004 but is a separate purchase.", source_type="receipt", relations=(R("similar_not_duplicate", 12, note="different receipt identifier and purchase"),)),
        E("Receipt R-1005 was captured unchanged again.", source_type="receipt", relations=(R("exact_duplicate", 13, duplicate_group="corner-r-1005"),)),
        E("Corner Mart receipt R-1006: 21.00 EUR on 2026-01-22.", source_type="receipt"),
        E("Receipt R-1006 changed its total to 22.00 EUR after a tip was added.", source_type="receipt", relations=(R("meaningful_change", 15, changed_fields=("amount",), duplicate_group="corner-r-1006"),)),
        E("Receipt R-1006 with the tip is uploaded again.", source_type="receipt", relations=(R("normalized_duplicate", 16, duplicate_group="corner-r-1006"),)),
        E("Corner Mart receipt R-1007: 4.75 EUR on 2026-02-01.", source_type="receipt"),
        E("Receipt R-1007 is a distinct receipt despite the same merchant.", source_type="receipt", relations=(R("similar_not_duplicate", 18, note="different date and identifier"),)),
        E("Receipt R-1007 was uploaded unchanged for backup.", source_type="receipt", relations=(R("exact_duplicate", 19, duplicate_group="corner-r-1007"),)),
    ]


def entity_events() -> list[dict[str, Any]]:
    return [
        E("Jordan asked me to bring the blue folder.", source_type="text", updates=(U("entity-link:mention-001", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Lee from school sent the form.", source_type="document", updates=(U("entity-link:mention-002", "entity-jordan-lee"),)),
        E("Please remind Jordan about the appointment.", source_type="text", updates=(U("entity-link:mention-003", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Kim is the person from the climbing club.", source_type="text", updates=(U("entity-link:mention-004", "entity-jordan-kim"),)),
        E("The Jordan in this note is not identified.", source_type="text", updates=(U("entity-link:mention-005", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Lee confirmed the school deadline.", source_type="text", updates=(U("entity-link:mention-006", "entity-jordan-lee"),)),
        E("I wrote only Jordan, with no surname or context.", source_type="text", updates=(U("entity-link:mention-007", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Kim will bring climbing shoes.", source_type="text", updates=(U("entity-link:mention-008", "entity-jordan-kim"),)),
        E("A message from Jordan needs a reply, but the recipient is unclear.", source_type="text", updates=(U("entity-link:mention-009", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Lee is the sender of the school message.", source_type="document", updates=(U("entity-link:mention-010", "entity-jordan-lee"),)),
        E("Jordan mentioned a meeting without identifying which Jordan.", source_type="text", updates=(U("entity-link:mention-011", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Kim confirmed the climbing meeting.", source_type="text", updates=(U("entity-link:mention-012", "entity-jordan-kim"),)),
        E("The sender called Jordan is still unresolved.", source_type="text", updates=(U("entity-link:mention-013", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Lee sent another school document.", source_type="document", updates=(U("entity-link:mention-014", "entity-jordan-lee"),)),
        E("No evidence links this Jordan note to either known person.", source_type="text", updates=(U("entity-link:mention-015", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Kim is the climbing-club contact.", source_type="text", updates=(U("entity-link:mention-016", "entity-jordan-kim"),)),
        E("A short message says only: ask Jordan.", source_type="text", updates=(U("entity-link:mention-017", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Lee acknowledged the form.", source_type="text", updates=(U("entity-link:mention-018", "entity-jordan-lee"),)),
        E("The final Jordan reminder has no disambiguating context.", source_type="text", updates=(U("entity-link:mention-019", status="unknown", reason="ambiguous_person"),)),
        E("Jordan Kim is confirmed as the climbing contact.", source_type="text", updates=(U("entity-link:mention-020", "entity-jordan-kim"),)),
    ]


def contradiction_events() -> list[dict[str, Any]]:
    return [
        E("HomeFix appointment is on 2026-02-10; quoted amount is 180.00 EUR.", source_type="text", updates=(U("homefix:appointment_date", "2026-02-10"), U("homefix:quoted_amount", {"amount": "180.00", "currency": "EUR"}))),
        E("Another HomeFix note says the appointment is on 2026-02-12.", source_type="text", updates=(U("homefix:appointment_date", status="unknown", reason="conflicting", extra_refs=("$previous",)),), relations=(R("contradiction", 1, changed_fields=("appointment_date",))),),
        E("A reminder repeats February 12 for HomeFix, but it is not authoritative.", source_type="text", updates=(U("homefix:appointment_date", status="unknown", reason="conflicting", extra_refs=("$previous",)),), relations=(R("contradiction", 2, changed_fields=("appointment_date",))),),
        E("I confirm the HomeFix appointment is 2026-02-12; treat that as a correction.", source_type="text", updates=(U("homefix:appointment_date", "2026-02-12", confirmation="$self", extra_refs=("$previous",)),), relations=(R("correction", 3, changed_fields=("appointment_date",))),),
        E("HomeFix still quotes 180.00 EUR.", source_type="document", updates=(U("homefix:quoted_amount", {"amount": "180.00", "currency": "EUR"}),)),
        E("A HomeFix invoice draft says 240.00 EUR instead.", source_type="document", updates=(U("homefix:quoted_amount", status="unknown", reason="conflicting", extra_refs=("$previous",)),), relations=(R("contradiction", 5, changed_fields=("quoted_amount",))),),
        E("I confirmed the HomeFix amount is 220.00 EUR after checking the email.", source_type="text", updates=(U("homefix:quoted_amount", {"amount": "220.00", "currency": "EUR"}, confirmation="$self", extra_refs=("$previous",)),), relations=(R("correction", 6, changed_fields=("quoted_amount",))),),
        E("HomeFix appointment remains scheduled for 2026-02-12.", source_type="text", updates=(U("homefix:appointment_date", "2026-02-12"),)),
        E("A later HomeFix note lists 250.00 EUR.", source_type="document", updates=(U("homefix:quoted_amount", status="unknown", reason="conflicting", extra_refs=("$previous",)),), relations=(R("contradiction", 8, changed_fields=("quoted_amount",))),),
        E("I have not resolved whether HomeFix is 220.00 or 250.00 EUR.", source_type="text", updates=(U("homefix:quoted_amount", status="unknown", reason="conflicting", extra_refs=("$previous",)),)),
        E("The date correction for HomeFix is still 2026-02-12.", source_type="text", updates=(U("homefix:appointment_date", "2026-02-12"),)),
        E("HomeFix sent another invoice copy without clarifying the amount.", source_type="document", updates=(U("homefix:quoted_amount", status="unknown", reason="conflicting", extra_refs=("$previous",)),)),
        E("The HomeFix amount remains unresolved.", source_type="text", updates=(U("homefix:quoted_amount", status="unknown", reason="conflicting", extra_refs=("$previous",)),)),
        E("HomeFix appointment reminder: 2026-02-12.", source_type="text", updates=(U("homefix:appointment_date", "2026-02-12"),)),
        E("No further authoritative HomeFix amount was supplied.", source_type="text", updates=(U("homefix:quoted_amount", status="unknown", reason="conflicting", extra_refs=("$previous",)),)),
        E("HomeFix date is unchanged at 2026-02-12.", source_type="text", updates=(U("homefix:appointment_date", "2026-02-12"),)),
        E("The conflicting HomeFix invoice amount is still awaiting confirmation.", source_type="document", updates=(U("homefix:quoted_amount", status="unknown", reason="conflicting", extra_refs=("$previous",)),)),
        E("I did not approve a new HomeFix amount.", source_type="text", updates=(U("homefix:quoted_amount", status="unknown", reason="conflicting", extra_refs=("$previous",)),)),
        E("HomeFix appointment stays on February 12.", source_type="text", updates=(U("homefix:appointment_date", "2026-02-12"),)),
        E("At cutoff the HomeFix amount remains an unresolved conflict.", source_type="text", updates=(U("homefix:quoted_amount", status="unknown", reason="conflicting", extra_refs=("$previous",)),)),
    ]


def contract_events() -> list[dict[str, Any]]:
    return [
        E("GymFlex contract GYM-OLD was signed 2026-01-02 and is effective 2026-02-01.", source_type="document", updates=(U("contract:gymflex/current/contract_id", "GYM-OLD"), U("contract:gymflex/current/status", "active"), U("contract:gymflex/current/signed_date", "2026-01-02"), U("contract:gymflex/current/effective_date", "2026-02-01"))),
        E("GYM-OLD renews on 2027-01-31.", source_type="document", updates=(U("contract:gymflex/current/renewal_date", "2027-01-31"), U("contract:gymflex/current/expiry_date", "2027-01-31"))),
        E("The old GymFlex contract has a 29.00 EUR monthly fee.", source_type="document", updates=(U("contract:gymflex/current/fee", {"amount": "29.00", "currency": "EUR", "billing_period": "month"}),)),
        E("GymFlex sent replacement terms, not yet signed.", source_type="document", updates=(U("contract:gymflex/replacement_candidate", "GYM-NEW", status="inferred"),)),
        E("I signed replacement GymFlex contract GYM-NEW on 2026-02-15.", source_type="document", updates=(U("contract:gymflex/current/contract_id", "GYM-NEW"), U("contract:gymflex/current/status", "active"), U("contract:gymflex/current/signed_date", "2026-02-15"), U("contract:gymflex/current/effective_date", "2026-03-01"), U("contract:gymflex/old_status", "superseded")), relations=(R("contract_replacement", 5, changed_fields=("contract_id", "effective_date"))),),
        E("GYM-NEW renews on 2027-02-28.", source_type="document", updates=(U("contract:gymflex/current/renewal_date", "2027-02-28"), U("contract:gymflex/current/expiry_date", "2027-02-28"))),
        E("GYM-NEW costs 31.00 EUR monthly.", source_type="document", updates=(U("contract:gymflex/current/fee", {"amount": "31.00", "currency": "EUR", "billing_period": "month"}),)),
        E("The old GymFlex terms are historical.", source_type="text", updates=(U("contract:gymflex/old_status", "superseded"),)),
        E("GYM-NEW became effective on 2026-03-01.", source_type="document", updates=(U("contract:gymflex/current/effective_date", "2026-03-01"),)),
        E("The signed date for GYM-NEW is 2026-02-15.", source_type="document", updates=(U("contract:gymflex/current/signed_date", "2026-02-15"),)),
        E("GymFlex confirms GYM-NEW is the current contract.", source_type="text", updates=(U("contract:gymflex/current/contract_id", "GYM-NEW"),)),
        E("The current GymFlex renewal date remains 2027-02-28.", source_type="document", updates=(U("contract:gymflex/current/renewal_date", "2027-02-28"),)),
        E("No earlier effective date for GYM-NEW is supported.", source_type="text", updates=(U("contract:gymflex/current/effective_date", "2026-03-01"),)),
        E("GYM-OLD was superseded, not deleted.", source_type="document", updates=(U("contract:gymflex/old_status", "superseded"),)),
        E("GYM-NEW fee remains 31.00 EUR per month.", source_type="document", updates=(U("contract:gymflex/current/fee", {"amount": "31.00", "currency": "EUR", "billing_period": "month"}),)),
        E("The current GymFlex contract expires 2027-02-28.", source_type="document", updates=(U("contract:gymflex/current/expiry_date", "2027-02-28"),)),
        E("The contract replacement did not change the signed date.", source_type="text", updates=(U("contract:gymflex/current/signed_date", "2026-02-15"),)),
        E("GymFlex still identifies GYM-NEW as current.", source_type="text", updates=(U("contract:gymflex/current/contract_id", "GYM-NEW"),)),
        E("The renewal reminder refers to 2027-02-28.", source_type="document", updates=(U("contract:gymflex/current/renewal_date", "2027-02-28"),)),
        E("At cutoff GYM-NEW is active through 2027-02-28.", source_type="document", updates=(U("contract:gymflex/current/status", "active"), U("contract:gymflex/current/expiry_date", "2027-02-28"))),
    ]


def approval_events() -> list[dict[str, Any]]:
    return [
        E("I should ask the bank to change the standing order; no request was sent.", source_type="text", updates=(U("action:bank-standing-order/lifecycle", "proposed"), U("action:bank-standing-order/approval_required", True), U("action:bank-standing-order/approved", False), U("action:bank-standing-order/executed", False))),
        E("The walk was pleasant and sunny.", source_type="text"),
        E("Prepare a 50.00 EUR transfer to Sam, but do not send it.", source_type="text", updates=(U("action:transfer-sam/lifecycle", "proposed"), U("action:transfer-sam/amount", {"amount": "50.00", "currency": "EUR"}), U("action:transfer-sam/approval_required", True), U("action:transfer-sam/approved", False), U("action:transfer-sam/executed", False))),
        E("No bank payment was made.", source_type="text", updates=(U("action:bank-standing-order/executed", False), U("action:transfer-sam/executed", False))),
        E("Do not send or change anything without my approval.", source_type="text", updates=(U("action:bank-standing-order/approval_required", True), U("action:bank-standing-order/approved", False), U("action:transfer-sam/approval_required", True), U("action:transfer-sam/approved", False))),
        E("The weather observation is irrelevant to my obligations.", source_type="text"),
        E("Withdraw the proposed transfer to Sam.", source_type="text", updates=(U("action:transfer-sam/lifecycle", "withdrawn"), U("action:transfer-sam/executed", False))),
        E("The bank standing-order change is still only a proposal.", source_type="text", updates=(U("action:bank-standing-order/lifecycle", "proposed"), U("action:bank-standing-order/executed", False))),
        E("I saw rain on the walk.", source_type="text"),
        E("I approve preparing a draft, not sending or changing an account.", source_type="text", updates=(U("action:bank-standing-order/approval_scope", "draft_only", status="known"), U("action:bank-standing-order/approved", False), U("action:bank-standing-order/executed", False))),
        E("The bank change has not been executed.", source_type="text", updates=(U("action:bank-standing-order/executed", False),)),
        E("No transfer to Sam was executed.", source_type="text", updates=(U("action:transfer-sam/executed", False),)),
        E("I am still deciding whether to request the bank change.", source_type="text", updates=(U("action:bank-standing-order/lifecycle", "proposed"), U("action:bank-standing-order/approved", False))),
        E("Do not treat the draft as a completed financial action.", source_type="text", updates=(U("action:bank-standing-order/executed", False),)),
        E("The transfer remains withdrawn.", source_type="text", updates=(U("action:transfer-sam/lifecycle", "withdrawn"), U("action:transfer-sam/executed", False))),
        E("A coffee observation has no task or obligation attached.", source_type="text"),
        E("The bank proposal needs my explicit approval before any external change.", source_type="text", updates=(U("action:bank-standing-order/approval_required", True), U("action:bank-standing-order/approved", False), U("action:bank-standing-order/executed", False))),
        E("I have not approved the transfer.", source_type="text", updates=(U("action:transfer-sam/approved", False), U("action:transfer-sam/executed", False))),
        E("The weather note should not appear in attention items.", source_type="text"),
        E("At cutoff the bank change is proposed, unapproved, and unexecuted.", source_type="text", updates=(U("action:bank-standing-order/lifecycle", "proposed"), U("action:bank-standing-order/approval_required", True), U("action:bank-standing-order/approved", False), U("action:bank-standing-order/executed", False))),
    ]


STORYLINES = {
    "streamly": subscription_events,
    "orange": bill_events,
    "marketone": purchase_events,
    "tasks": task_events,
    "insurance": insurance_events,
    "receipts": receipt_events,
    "entities": entity_events,
    "homefix": contradiction_events,
    "gymflex": contract_events,
    "approval": approval_events,
}


def build_internal_events() -> list[dict[str, Any]]:
    sequences = {name: factory() for name, factory in STORYLINES.items()}
    if any(len(events) != 20 for events in sequences.values()):
        raise AssertionError("every Gate A storyline must contain exactly 20 events")
    result: list[dict[str, Any]] = []
    for local_index in range(1, 21):
        for storyline, events in sequences.items():
            item = copy.deepcopy(events[local_index - 1])
            item["storyline"] = storyline
            item["local_index"] = local_index
            item["sequence"] = len(result) + 1
            item["event_id"] = f"evt-{item['sequence']:03d}"
            result.append(item)
    return result


def _resolve_ref(ref: str, event: dict[str, Any], previous: dict[str, Any] | None) -> str | None:
    if ref == "$self":
        return event["event_id"]
    if ref == "$previous":
        return previous["source_refs"][0] if previous and previous.get("source_refs") else None
    return ref


def make_assertion(
    state_key: str,
    value: Any = MISSING,
    *,
    status: str = "known",
    source_refs: list[str] | None = None,
    unknown_reason: str | None = None,
    confirmation_ref: str | None = None,
) -> dict[str, Any]:
    assertion: dict[str, Any] = {
        "state_key": state_key,
        "knowledge_status": status,
        "source_refs": sorted(set(source_refs or [])),
    }
    if value is not MISSING:
        assertion["value"] = value
    if unknown_reason is not None:
        assertion["unknown_reason"] = unknown_reason
    if confirmation_ref is not None:
        assertion["confirmation_ref"] = confirmation_ref
    return assertion


def apply_event(world: dict[str, Any], event: dict[str, Any]) -> None:
    previous_by_key = world["facts"]
    for transition in event["updates"]:
        key = transition["state_key"]
        previous = previous_by_key.get(key)
        refs = [event["event_id"]]
        for ref in transition.get("extra_refs", []):
            resolved = _resolve_ref(ref, event, previous)
            if resolved:
                refs.append(resolved)
        confirmation = transition.get("confirmation_ref")
        if confirmation:
            confirmation = _resolve_ref(confirmation, event, previous)
        assertion = make_assertion(
            key,
            transition.get("value", MISSING),
            status=transition.get("knowledge_status", "known"),
            source_refs=refs,
            unknown_reason=transition.get("unknown_reason"),
            confirmation_ref=confirmation,
        )
        world["histories"].setdefault(key, []).append(copy.deepcopy(assertion))
        previous_by_key[key] = assertion

    for relation_template in event["relations"]:
        target_local = relation_template.get("target_local")
        target = None
        if target_local is not None:
            target = world["storyline_events"].get((event["storyline"], target_local))
        relation_id = f"rel-{event['event_id']}"
        relation: dict[str, Any] = {
            "relation_id": relation_id,
            "relation_type": relation_template["relation_type"],
            "source_event_id": event["event_id"],
            "target_event_id": target["event_id"] if target else None,
        }
        for field in ("changed_fields", "duplicate_group", "note"):
            if field in relation_template:
                relation[field] = relation_template[field]
        world["relations"].append(relation)
        world["storyline_events"][(event["storyline"], event["local_index"])] = event

    # Register events even when they have no relation so later references work.
    world["storyline_events"][(event["storyline"], event["local_index"])] = event

    data = event.get("data")
    if not data:
        return
    kind = data["kind"]
    if kind in {"bill", "bill_missing", "purchase", "consumption", "consumption_missing"}:
        record = copy.deepcopy(data)
        record["event_id"] = event["event_id"]
        world["financial"].setdefault(kind, []).append(record)


def public_event(event: dict[str, Any]) -> dict[str, Any]:
    observed = BASE_DATE + timedelta(days=(event["sequence"] - 1) // 3)
    captured = datetime(observed.year, observed.month, observed.day, 8 + (event["sequence"] % 8), 0, tzinfo=timezone(timedelta(hours=1)))
    payload = {"text": event["text"]}
    payload_hash = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return {
        "event_id": event["event_id"],
        "sequence": event["sequence"],
        "captured_at": captured.isoformat(),
        "observed_at": observed.isoformat(),
        "source_type": event["source_type"],
        "payload": payload,
        "payload_sha256": payload_hash,
        "metadata": {"synthetic": True, "source_channel": "capture"},
    }


def initial_context() -> dict[str, Any]:
    return {
        "entities": [
            {"entity_id": "entity-jordan-lee", "display_name": "Jordan Lee", "kind": "person"},
            {"entity_id": "entity-jordan-kim", "display_name": "Jordan Kim", "kind": "person"},
            {"entity_id": "entity-alex", "display_name": "Alex", "kind": "person"},
            {"entity_id": "entity-sam", "display_name": "Sam", "kind": "person"},
        ],
        "accepted_state": [],
    }


def assertion_from_fact(fact: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(fact)


def history_unique(world: dict[str, Any], key: str, prefix: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for fact in world["histories"].get(key, []):
        marker = canonical_json({k: fact[k] for k in fact if k not in {"source_refs", "confirmation_ref"}})
        if marker in seen or fact.get("knowledge_status") != "known":
            continue
        seen.add(marker)
        result.append(make_assertion(f"{prefix}/{len(result) + 1}", fact.get("value", MISSING), source_refs=fact.get("source_refs", []), status="known"))
    return result


def relation_assertions(world: dict[str, Any], relation_types: set[str]) -> list[dict[str, Any]]:
    result = []
    for relation in world["relations"]:
        if relation["relation_type"] not in relation_types:
            continue
        value = {k: v for k, v in relation.items() if k != "relation_id"}
        refs = [relation["source_event_id"]]
        if relation.get("target_event_id"):
            refs.append(relation["target_event_id"])
        result.append(make_assertion(f"relation:{relation['relation_id']}", value, source_refs=refs))
    return result


def facts_with_prefix(world: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    return [assertion_from_fact(world["facts"][key]) for key in sorted(world["facts"]) if key.startswith(prefix)]


def as_of_date(events: list[dict[str, Any]]) -> str:
    return public_event(events[-1])["observed_at"]


def query_assertions(world: dict[str, Any], events: list[dict[str, Any]], query_id: str) -> list[dict[str, Any]]:
    if query_id == "q-subscriptions-current":
        return facts_with_prefix(world, "subscription:streamly/")
    if query_id == "q-subscriptions-history":
        return history_unique(world, "subscription:streamly/current_price", "history:subscription:streamly/price")
    if query_id == "q-attention-14d":
        result: list[dict[str, Any]] = []
        current_date = date.fromisoformat(as_of_date(events))
        limit = current_date + timedelta(days=14)
        for key, fact in sorted(world["facts"].items()):
            if not key.endswith("/lifecycle") or fact.get("value") != "open":
                continue
            base = key[:-len("/lifecycle")]
            deadline = world["facts"].get(f"{base}/deadline")
            if not deadline or deadline.get("knowledge_status") != "known":
                continue
            due = date.fromisoformat(deadline["value"])
            if current_date <= due <= limit:
                result.append(make_assertion(f"attention:{base}", {"reason": "open task deadline", "deadline": due.isoformat()}, source_refs=sorted(set(fact.get("source_refs", []) + deadline.get("source_refs", [])))))
        for action in ("action:bank-standing-order", "action:transfer-sam"):
            required = world["facts"].get(f"{action}/approval_required")
            executed = world["facts"].get(f"{action}/executed")
            approved = world["facts"].get(f"{action}/approved")
            if required and required.get("value") is True and executed and executed.get("value") is False and approved and approved.get("value") is False:
                result.append(make_assertion(f"attention:{action}", {"reason": "approval required", "executed": False}, source_refs=sorted(set(required["source_refs"] + executed["source_refs"] + approved["source_refs"]))))
        return result
    if query_id == "q-insurance-expiry":
        return facts_with_prefix(world, "insurance:current/")
    if query_id == "q-orange-costs":
        bills = world["financial"].get("bill", [])
        missing = world["financial"].get("bill_missing", [])
        total = sum((Decimal(item["amount"]) for item in bills), Decimal("0"))
        refs = [item["event_id"] for item in bills]
        result = [
            make_assertion("finance:orange/observed_bill_count", len(bills), source_refs=refs),
            make_assertion("finance:orange/observed_total", {"amount": decimal_string(total), "currency": "EUR"}, source_refs=refs),
            make_assertion("finance:orange/observed_periods", sorted(item["period"] for item in bills), source_refs=refs),
            make_assertion("finance:orange/missing_periods", sorted(item["period"] for item in missing), source_refs=[item["event_id"] for item in missing]),
        ]
        if missing:
            result.append(make_assertion("finance:orange/unobserved_periods", MISSING, status="unknown", source_refs=[item["event_id"] for item in missing], unknown_reason="no_capture_for_period"))
        current = world["facts"].get("finance:orange/current_amount")
        if current:
            result.append(assertion_from_fact(current))
        return result
    if query_id == "q-marketone-observations":
        purchases = world["financial"].get("purchase", [])
        consumption = world["financial"].get("consumption", [])
        missing = world["financial"].get("consumption_missing", [])
        total = sum((Decimal(item["amount"]) for item in purchases), Decimal("0"))
        consumed = sum((int(item["quantity"]) for item in consumption), 0)
        return [
            make_assertion("finance:marketone/purchase_count", len(purchases), source_refs=[x["event_id"] for x in purchases]),
            make_assertion("finance:marketone/purchased_total", {"amount": decimal_string(total), "currency": "EUR"}, source_refs=[x["event_id"] for x in purchases]),
            make_assertion("finance:marketone/confirmed_consumption_quantity", consumed, source_refs=[x["event_id"] for x in consumption]),
            make_assertion("finance:marketone/consumption_observation_count", len(consumption), source_refs=[x["event_id"] for x in consumption]),
            make_assertion("finance:marketone/explicit_zero_is_supported", any(int(x["quantity"]) == 0 for x in consumption), source_refs=[x["event_id"] for x in consumption if int(x["quantity"]) == 0]),
            make_assertion("finance:marketone/unobserved_consumption", MISSING, status="unknown", source_refs=[x["event_id"] for x in missing], unknown_reason="no_consumption_observation"),
        ]
    if query_id == "q-tasks-state":
        result = []
        prefixes = sorted({key.rsplit("/", 1)[0] for key in world["facts"] if key.startswith("task:")})
        for prefix in prefixes:
            result.extend(facts_with_prefix(world, prefix + "/"))
        result.extend(relation_assertions(world, {"task_reassignment", "task_cancellation", "task_reopened"}))
        return result
    if query_id == "q-unresolved":
        return [assertion_from_fact(fact) for fact in world["facts"].values() if fact.get("knowledge_status") == "unknown"]
    if query_id == "q-duplicates-changes":
        return relation_assertions(world, {"exact_duplicate", "normalized_duplicate", "meaningful_change", "similar_not_duplicate"}) + [
            make_assertion("duplicate_event_count", sum(1 for r in world["relations"] if r["relation_type"] in {"exact_duplicate", "normalized_duplicate"}), source_refs=[r["source_event_id"] for r in world["relations"] if r["relation_type"] in {"exact_duplicate", "normalized_duplicate"}]),
            make_assertion("duplicate_group_count", len({r.get("duplicate_group") for r in world["relations"] if r["relation_type"] in {"exact_duplicate", "normalized_duplicate"}}), source_refs=[r["source_event_id"] for r in world["relations"] if r["relation_type"] in {"exact_duplicate", "normalized_duplicate"}]),
            make_assertion("meaningful_change_event_count", sum(1 for r in world["relations"] if r["relation_type"] == "meaningful_change"), source_refs=[r["source_event_id"] for r in world["relations"] if r["relation_type"] == "meaningful_change"]),
        ]
    if query_id == "q-contract-dates":
        return facts_with_prefix(world, "contract:gymflex/current/") + facts_with_prefix(world, "contract:gymflex/old_status")
    if query_id == "q-approval-boundary":
        return facts_with_prefix(world, "action:")
    if query_id == "q-recent-changes":
        return relation_assertions(world, {"correction", "contradiction", "price_change", "policy_replacement", "contract_replacement"})
    raise KeyError(query_id)


QUERY_SPECS = [
    ("q-subscriptions-current", "Which subscriptions are currently active, and what does each currently cost?"),
    ("q-subscriptions-history", "What subscription price changes are supported by the history?"),
    ("q-attention-14d", "Which open deadlines or approval-required items need attention in the next 14 days?"),
    ("q-insurance-expiry", "What is known about the current RoadSure policy and its expiry?"),
    ("q-orange-costs", "What Orange Mobile bills and deterministic totals are directly observed, and which periods are missing?"),
    ("q-marketone-observations", "What MarketOne purchases and consumption are directly observed? Do not infer one from the other."),
    ("q-tasks-state", "Which tasks are active or completed, and what reassignment or cancellation history is supported?"),
    ("q-unresolved", "Which facts remain unknown, ambiguous, unreadable, or contradictory?"),
    ("q-duplicates-changes", "Which captures are duplicates, which are meaningful changes, and what are the explicit counts?"),
    ("q-contract-dates", "What are the current GymFlex contract's signed, effective, renewal, and expiry dates?"),
    ("q-approval-boundary", "Which proposed actions require approval, and were any consequential actions executed?"),
    ("q-recent-changes", "Which corrections, contradictions, replacements, and material changes are recorded?"),
]


def category_for_key(state_key: str) -> str:
    if state_key.startswith("subscription:") or state_key.startswith("history:subscription"):
        return "current_state"
    if state_key.startswith("finance:"):
        return "financial"
    if state_key.startswith("task:") or state_key.startswith("attention:task:"):
        return "task_deadline"
    if state_key.startswith("insurance:") or state_key.startswith("contract:"):
        return "temporal_history"
    if state_key.startswith("entity-link:"):
        return "entity_resolution"
    if state_key.startswith("relation:"):
        return "relation_reconciliation"
    if state_key.startswith("duplicate_") or state_key.startswith("meaningful_change_"):
        return "duplicate_change"
    if state_key.startswith("action:") or state_key.startswith("attention:action:"):
        return "safety"
    if state_key.startswith("homefix:"):
        return "contradiction"
    return "state_maintenance"


def build_outputs() -> tuple[dict[str, Any], dict[str, Any]]:
    internal = build_internal_events()
    public = [public_event(event) for event in internal]
    world = {"facts": {}, "histories": {}, "relations": [], "financial": {}, "storyline_events": {}}
    checkpoints: dict[str, Any] = {}
    expected_queries: dict[str, Any] = {}
    defect_catalog: dict[str, dict[str, Any]] = {}
    for event in internal:
        apply_event(world, event)
        if event["sequence"] in CHECKPOINTS:
            checkpoint_world = copy.deepcopy(world)
            query_map: dict[str, Any] = {}
            for query_id, _question in QUERY_SPECS:
                assertions = query_assertions(checkpoint_world, internal[: event["sequence"]], query_id)
                query_map[query_id] = {"assertions": assertions}
                for assertion in assertions:
                    key = assertion["state_key"]
                    defect_catalog.setdefault(key, {"defect_id": f"defect:{key}", "state_key": key, "category": category_for_key(key)})
            checkpoints[str(event["sequence"])] = {
                "checkpoint": event["sequence"],
                "as_of": public_event(event)["observed_at"],
                "state": {
                    "facts": checkpoint_world["facts"],
                    "histories": checkpoint_world["histories"],
                    "relations": checkpoint_world["relations"],
                    "financial": checkpoint_world["financial"],
                },
            }
            expected_queries[str(event["sequence"])] = query_map

    scenario = {
        "contract_version": CONTRACT_VERSION,
        "scenario_id": SCENARIO_ID,
        "person_id": "person-dev-001",
        "timezone": TIMEZONE,
        "timeline_start": public[0]["observed_at"],
        "cutoff_at": public[-1]["captured_at"],
        "initial_context": initial_context(),
        "checkpoints": list(CHECKPOINTS),
        "raw_events": public,
    }
    expected = {
        "contract_version": CONTRACT_VERSION,
        "scenario_id": SCENARIO_ID,
        "event_count": EVENT_COUNT,
        "raw_event_hashes": {event["event_id"]: event["payload_sha256"] for event in public},
        "checkpoints": expected_queries,
        "state_snapshots": checkpoints,
        "defect_catalog": sorted(defect_catalog.values(), key=lambda item: item["state_key"]),
    }
    return scenario, expected


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="generate in memory and verify stable output without writing")
    args = parser.parse_args()
    scenario, expected = build_outputs()
    if args.check:
        scenario_again, expected_again = build_outputs()
        if canonical_json(scenario) != canonical_json(scenario_again) or canonical_json(expected) != canonical_json(expected_again):
            raise SystemExit("generator is not deterministic")
        print(f"checked {len(scenario['raw_events'])} events and {len(scenario['checkpoints'])} checkpoints")
        return 0
    write_json(CASES_DIR / "scenario-001.json", scenario)
    write_json(EXPECTED_DIR / "scenario-001.json", expected)
    print(f"wrote {CASES_DIR / 'scenario-001.json'}")
    print(f"wrote {EXPECTED_DIR / 'scenario-001.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
