"""Generic public contract used by the personal Blackhole runtime.

The benchmark response contract remains a separate, frozen artifact.  The
runtime contract intentionally leaves entity identity open while documenting
the small vocabulary that helps the local semantic provider emit useful
atomic observations.
"""

from __future__ import annotations

import copy
from typing import Any


RUNTIME_CONTRACT: dict[str, Any] = {
    "response_contract": "blackhole-runtime-v1",
    "unknown_reason": {
        "allowed_categories": [
            "ambiguous_person",
            "conflicting",
            "missing",
            "no_capture_for_period",
            "no_consumption_observation",
            "not_available",
            "not_stated",
            "unreadable",
        ]
    },
    "public_ontology": {
        "subjects": [],
        "predicates": [
            {"id": "status"},
            {"id": "current_price"},
            {"id": "historical_price"},
            {"id": "billing_period"},
            {"id": "currency"},
            {"id": "price_effective"},
            {"id": "next_renewal"},
            {"id": "deadline"},
            {"id": "owner"},
            {"id": "blocker"},
            {"id": "observed_total"},
            {"id": "observed_periods"},
            {"id": "missing_periods"},
            {"id": "purchased_total"},
            {"id": "purchase_count"},
            {"id": "approval_required"},
            {"id": "executed"},
            {"id": "entity_link"},
        ],
    },
    "predicate_value_shapes": {
        "current_price": {"type": "money", "fields": ["amount", "currency", "billing_period"]},
        "historical_price": {"type": "money", "fields": ["amount", "currency", "billing_period"]},
        "observed_total": {"type": "money", "fields": ["amount", "currency"]},
        "purchased_total": {"type": "money", "fields": ["amount", "currency"]},
    },
    "value_normalization": {
        "object_field_aliases": {
            "amount": ["value", "price", "total"],
            "currency": ["currency_code"],
            "billing_period": ["period", "cadence"],
        },
        "enum_field_aliases": {},
    },
}


def runtime_contract() -> dict[str, Any]:
    """Return an independent copy suitable for a HostRuntime instance."""

    return copy.deepcopy(RUNTIME_CONTRACT)


__all__ = ["RUNTIME_CONTRACT", "runtime_contract"]
