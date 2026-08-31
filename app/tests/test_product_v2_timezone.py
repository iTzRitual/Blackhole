from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.product_v2 import (
    ProductRuntime,
    _discover_posix_timezone_name,
    _zoneinfo_name_from_path,
    local_timezone_name,
    normalize_fact,
    normalize_timestamp,
    resolve_timezone,
)


class RelativeDayOccurrenceProvider:
    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_memory, time_context, contract
        facts: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event["event_id"])
            text = str(event.get("payload", {}).get("text", "")).casefold()
            if "yesterday" in text:
                expression = "yesterday"
                amount = 2
                # Reproduce the live provider shape that supplied the wrong
                # absolute date alongside the raw relative expression.
                model_normalized = "2026-08-29"
            elif "today" in text:
                expression = "today"
                amount = 1
                model_normalized = "2026-08-31"
            else:
                continue
            facts.append(
                {
                    "event_id": event_id,
                    "entity": "X",
                    "concept": "consumption",
                    "knowledge_status": "known",
                    "value": {"amount": amount, "unit": "unit"},
                    "claim_type": "occurrence",
                    "temporal": {
                        "expression": expression,
                        "normalized": model_normalized,
                    },
                }
            )
        return {"facts": facts}


class ProductV2TimezoneTests(unittest.TestCase):
    def local_name_for(self, local_now: datetime, *, environment_tz: str = "") -> str:
        with (
            patch.dict(os.environ, {"TZ": environment_tz}),
            patch("app.product_v2._discover_posix_timezone_name", return_value=None),
            patch("app.product_v2.datetime") as datetime_class,
        ):
            datetime_class.now.return_value.astimezone.return_value = local_now
            return local_timezone_name()

    def test_fixed_offset_datetime_timezone_uses_aware_datetime_offset(self) -> None:
        local_now = datetime(2026, 8, 31, 12, 0, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual(self.local_name_for(local_now), "UTC+02:00")

    def test_negative_fixed_offset_fallback_is_formatted_truthfully(self) -> None:
        local_now = datetime(2026, 8, 31, 12, 0, tzinfo=timezone(-timedelta(hours=5, minutes=30)))
        self.assertEqual(self.local_name_for(local_now), "UTC-05:30")

    def test_zoneinfo_key_is_preferred_when_available(self) -> None:
        try:
            local_zone = ZoneInfo("Europe/Warsaw")
        except ZoneInfoNotFoundError:
            self.skipTest("IANA zoneinfo data is unavailable")
        local_now = datetime(2026, 8, 31, 12, 0, tzinfo=local_zone)
        self.assertEqual(self.local_name_for(local_now), "Europe/Warsaw")

    def test_valid_tz_environment_is_used_after_fixed_offset_tzinfo(self) -> None:
        local_now = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(self.local_name_for(local_now, environment_tz="Europe/Berlin"), "Europe/Berlin")

    def test_posix_zoneinfo_path_and_metadata_are_validated(self) -> None:
        try:
            ZoneInfo("Etc/UTC")
        except ZoneInfoNotFoundError:
            self.skipTest("IANA zoneinfo data is unavailable")
        self.assertEqual(
            _zoneinfo_name_from_path("/private/var/db/timezone/zoneinfo/Etc/UTC"),
            "Etc/UTC",
        )
        with tempfile.TemporaryDirectory() as directory:
            timezone_path = Path(directory) / "timezone"
            timezone_path.write_text("Etc/UTC\n", encoding="ascii")
            self.assertEqual(
                _discover_posix_timezone_name(
                    localtime_path=Path(directory) / "missing-localtime",
                    timezone_path=timezone_path,
                ),
                "Etc/UTC",
            )

    def test_explicit_timezone_wins_without_local_discovery(self) -> None:
        with patch("app.product_v2.local_timezone_name", side_effect=AssertionError("must not discover local timezone")):
            name, zone = resolve_timezone("Europe/Berlin")
        self.assertEqual(name, "Europe/Berlin")
        self.assertEqual(datetime(2026, 1, 1, tzinfo=zone).utcoffset(), timedelta(hours=1))

    def test_default_capture_and_timezone_resolution_succeed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                start_worker=False,
                clock=lambda: datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc),
            ) as runtime:
                saved = runtime.capture("test")
                self.assertTrue(saved["saved"])
                event = runtime.store.raw_event(saved["event_id"])
                self.assertIsNotNone(event)
                timezone_name, zone = resolve_timezone(None)
                self.assertEqual(event["timezone"], timezone_name)
                self.assertIsNotNone(datetime.now(tz=zone).utcoffset())

    def test_relative_time_stays_anchored_to_capture_time(self) -> None:
        captured = datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(
            normalize_timestamp({"relative_minutes": 10}, captured_at=captured, zone=timezone.utc),
            "2026-08-31T10:10:00+00:00",
        )
        delayed_processing = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
        self.assertNotEqual(delayed_processing.isoformat(), "2026-08-31T10:10:00+00:00")

    def test_relative_day_shapes_use_capture_local_calendar_date(self) -> None:
        captured = datetime.fromisoformat("2026-08-31T10:00:00+02:00")
        zone = ZoneInfo("Europe/Warsaw")
        cases = (
            ("yesterday", "2026-08-30"),
            ("today", "2026-08-31"),
            ("tomorrow", "2026-09-01"),
            ("wczoraj", "2026-08-30"),
            ("dzisiaj", "2026-08-31"),
            ("jutro", "2026-09-01"),
            ({"expression": "yesterday"}, "2026-08-30"),
            ({"date": "yesterday"}, "2026-08-30"),
            ({"normalized": "yesterday"}, "2026-08-30"),
            (
                {"expression": "yesterday", "normalized": "2026-08-29"},
                "2026-08-30",
            ),
        )
        for value, expected_date in cases:
            with self.subTest(value=value):
                normalized = normalize_timestamp(value, captured_at=captured, zone=zone)
                self.assertIsNotNone(normalized)
                self.assertEqual(normalized[:10], expected_date)

    def test_relative_temporal_field_is_normalized_from_capture(self) -> None:
        event = {
            "event_id": "relative-field",
            "captured_at": "2026-08-31T10:00:00+02:00",
            "timezone": "Europe/Warsaw",
        }
        fact = normalize_fact(
            {
                "event_id": "relative-field",
                "entity": "X",
                "concept": "consumption",
                "knowledge_status": "known",
                "value": {"amount": 2, "unit": "unit"},
                "claim_type": "occurrence",
                "temporal": {"valid_from": "yesterday"},
            },
            batch_ids={"relative-field"},
            available_ids={"relative-field"},
            event=event,
        )
        self.assertIsNotNone(fact)
        self.assertEqual(fact["temporal"]["valid_from"][:10], "2026-08-30")

    def test_relative_days_use_local_dates_across_dst_boundary(self) -> None:
        zone = ZoneInfo("Europe/Warsaw")
        captured = datetime.fromisoformat("2026-03-29T00:30:00+01:00")
        yesterday = normalize_timestamp("yesterday", captured_at=captured, zone=zone)
        tomorrow = normalize_timestamp("tomorrow", captured_at=captured, zone=zone)
        self.assertIsNotNone(yesterday)
        self.assertIsNotNone(tomorrow)
        self.assertEqual(yesterday[:10], "2026-03-28")
        self.assertEqual(tomorrow[:10], "2026-03-30")
        self.assertTrue(yesterday.endswith("+01:00"))
        self.assertTrue(tomorrow.endswith("+02:00"))

    def test_occurrence_ask_uses_repaired_relative_day_dates(self) -> None:
        captured_at = "2026-08-31T10:00:00+02:00"
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=RelativeDayOccurrenceProvider(),
                start_worker=False,
                batch_size=2,
                clock=lambda: datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc),
            ) as runtime:
                runtime.capture(
                    "Yesterday I consumed 2 units of X.",
                    event_id="relative-yesterday",
                    captured_at=captured_at,
                    timezone_name="Europe/Warsaw",
                )
                runtime.capture(
                    "Today I consumed 1 unit of X.",
                    event_id="relative-today",
                    captured_at=captured_at,
                    timezone_name="Europe/Warsaw",
                )
                self.assertEqual(runtime.process_pending()["processed"], 2)
                current = runtime.snapshot()["current_facts"]
                by_event = {item["source_event_id"]: item for item in current}
                self.assertEqual(by_event["relative-yesterday"]["temporal"]["normalized"][:10], "2026-08-30")
                self.assertEqual(by_event["relative-today"]["temporal"]["normalized"][:10], "2026-08-31")

                answer = runtime.ask("How many X did I record in total?")
                self.assertEqual(answer["mode"], "occurrence_totals")
                self.assertFalse(answer["provider_used"])
                self.assertIn("3 unit", answer["answer"])
                self.assertIn("yesterday", answer["answer"])
                self.assertIn("today", answer["answer"])
                self.assertNotIn("Aug 29", answer["answer"])
