from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.product_v2 import (
    ProductRuntime,
    _discover_posix_timezone_name,
    _zoneinfo_name_from_path,
    local_timezone_name,
    normalize_timestamp,
    resolve_timezone,
)


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
