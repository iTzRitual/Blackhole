from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
HTML = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
APP_JS = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
CSS = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")


class ProductV2UIContractTests(unittest.TestCase):
    def test_javascript_parses_without_a_build_step(self) -> None:
        result = subprocess.run(
            ["node", "--check", str(WEB_ROOT / "app.js")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_capture_composer_uses_a_simple_plus_and_accepts_attachment_only(self) -> None:
        self.assertIn('class="plus-glyph"', HTML)
        self.assertIn('aria-label="Add an attachment"', HTML)
        self.assertNotIn('class="round-button"', HTML)
        self.assertIn("if (!text.trim() && !attachment)", APP_JS)
        self.assertIn("client.capture({ text, attachment })", APP_JS)

    def test_capture_keyboard_and_double_submit_contract(self) -> None:
        self.assertIn('event.key === "Enter"', APP_JS)
        self.assertIn("!event.shiftKey", APP_JS)
        self.assertIn("requestSubmit()", APP_JS)
        self.assertIn("if (state.submitting) return", APP_JS)
        self.assertIn("submit.disabled = true", APP_JS)
        self.assertRegex(CSS, r"\.composer textarea[\s\S]*?font-size: 16px")

    def test_attachment_preview_is_visual_and_never_copies_file_text(self) -> None:
        self.assertIn('data-attachment-mode="camera"', HTML)
        self.assertIn('data-attachment-mode="photo"', HTML)
        self.assertIn('data-attachment-mode="file"', HTML)
        self.assertIn("attachment-thumb", APP_JS)
        self.assertIn("attachment-file-icon", APP_JS)
        self.assertIn("clearAttachment", APP_JS)
        self.assertNotIn("file.text()", APP_JS)

    def test_success_undo_and_reduced_motion_are_explicit(self) -> None:
        self.assertIn('showToast("+1 off your mind", "", "Undo", undoCapture)', APP_JS)
        self.assertIn("retractCapture", APP_JS)
        self.assertIn('/api/v2/retract', APP_JS)
        self.assertIn("prefers-reduced-motion: reduce", CSS)
        self.assertIn("composer-fade", CSS)
        self.assertIn('matchMedia("(prefers-reduced-motion: reduce)")', APP_JS)

    def test_client_uses_the_real_product_v2_host_contract(self) -> None:
        self.assertIn('api("/api/v2/state")', APP_JS)
        self.assertIn('api("/api/v2/capture"', APP_JS)
        self.assertIn('api("/api/v2/ask"', APP_JS)
        self.assertIn("data_base64", APP_JS)
        self.assertIn("state.processing", APP_JS)
        self.assertIn("scheduleProcessingPoll", APP_JS)

    def test_attention_is_human_oriented_and_badge_is_count_gated(self) -> None:
        self.assertIn("updateAttentionBadge", APP_JS)
        self.assertIn("count > 0", APP_JS)
        self.assertIn("What actually needs you?", HTML)
        self.assertIn("Why this is here", APP_JS)
        self.assertIn("Nothing needs your attention.", APP_JS)
        self.assertNotIn("knowledge_status", HTML)
        attention_renderer = APP_JS[APP_JS.index("const renderAttention"):APP_JS.index("const updateAttentionBadge")]
        self.assertNotIn("item.subject", attention_renderer)
        self.assertNotIn("item.predicate", attention_renderer)

    def test_memory_is_open_world_and_hides_raw_assertions_from_primary_markup(self) -> None:
        self.assertIn("const normalizeMemory", APP_JS)
        self.assertIn("memory.entities", APP_JS)
        self.assertIn("memory.current_facts", APP_JS)
        self.assertIn("Object.entries(memory)", APP_JS)
        self.assertNotIn("memorySections", APP_JS)
        self.assertIn("What Blackhole knows.", HTML)
        self.assertIn("Why Blackhole knows this", APP_JS)
        self.assertNotIn("source_refs", HTML)

    def test_ask_has_natural_examples_and_distinct_failure_copy(self) -> None:
        self.assertIn("What do I need to do today?", APP_JS)
        self.assertIn("What do I know about my car?", APP_JS)
        self.assertIn("const normalizeAnswer", APP_JS)
        self.assertIn("Your latest memory is still safe.", APP_JS)
        self.assertIn("provider_unavailable", APP_JS)
        self.assertIn("Nothing clear came back yet.", APP_JS)
        self.assertNotIn("No supported observations", APP_JS)

    def test_hover_is_pointer_gated_and_touch_targets_are_present(self) -> None:
        self.assertIn("@media (hover: hover) and (pointer: fine)", CSS)
        self.assertGreaterEqual(len(re.findall(r"min-height: 44px", CSS)), 3)
        self.assertIn("touch-action: manipulation", CSS)


if __name__ == "__main__":
    unittest.main()
