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
        self.assertIn('showToast("Out of mind", "", "Undo", undoCapture)', APP_JS)
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

    def test_processing_state_is_visible_without_faking_empty_memory(self) -> None:
        self.assertIn('id="attention-processing"', HTML)
        self.assertIn('id="memory-processing"', HTML)
        self.assertIn("Still understanding your recent captures.", APP_JS)
        self.assertIn("Some recent captures couldn't be understood yet.", APP_JS)
        self.assertIn('status: "processing"', APP_JS)
        self.assertIn('status: "processing_failed"', APP_JS)

    def test_capture_feedback_is_transient_and_accessible(self) -> None:
        self.assertNotIn('id="capture-feedback"', HTML)
        self.assertNotIn("inline-feedback", APP_JS)
        self.assertNotIn("inline-feedback", CSS)
        self.assertNotIn("setFeedback", APP_JS)
        self.assertIn('const role = kind === "error" ? "alert" : "status"', APP_JS)
        self.assertIn('showToast("That attachment is over 10 MB. Choose a smaller file.", "error")', APP_JS)
        self.assertIn('showToast("Add a thought or choose an attachment.", "error")', APP_JS)

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
        self.assertIn("attention-card-footer", APP_JS)
        self.assertIn("attention-action-area", APP_JS)
        self.assertIn("attention-card-footer", CSS)
        self.assertIn("attention-complete", CSS)
        self.assertIn("align-self: center", CSS)
        self.assertIn("align-items: center", CSS)
        self.assertRegex(CSS, r"\.quiet-button\.attention-complete\s*\{[\s\S]*?margin-top:\s*0")

    def test_attention_clock_and_ask_thread_behaviors_are_live_bounded_and_calm(self) -> None:
        self.assertIn("scheduleAttentionTicker", APP_JS)
        self.assertIn("state.attentionTimer", APP_JS)
        self.assertIn("document.hidden", APP_JS)
        self.assertIn("new-ask-thread", HTML)
        self.assertIn("askGeneration", APP_JS)
        self.assertIn("slice(-8)", APP_JS)
        self.assertIn("settleAskScroll", APP_JS)
        self.assertIn("const shouldStick = options.forceFollow === true || askIsNearBottom()", APP_JS)
        self.assertIn('renderAskConversation(true, { forceFollow: true, behavior: "smooth" })', APP_JS)
        self.assertIn("scrollAskToTop", APP_JS)
        self.assertIn("scrollAskToLatest", APP_JS)
        self.assertRegex(CSS, r"\.ask-form\s*\{[\s\S]*?position: sticky")
        self.assertIn("--ask-nav-gap: 14px", CSS)
        self.assertIn("var(--ask-nav-gap)", CSS)
        self.assertIn("loading-dots", APP_JS)
        self.assertIn("@keyframes loading-dot", CSS)
        self.assertIn("@media (prefers-reduced-motion: reduce)", CSS)
        self.assertRegex(CSS, r"\.processing-notice\s*\{[\s\S]*?flex-direction:\s*column[\s\S]*?justify-content:\s*center[\s\S]*?text-align:\s*center")
        self.assertNotIn("icon-orbit", HTML)
        self.assertNotIn("icon-orbit", APP_JS)

    def test_memory_is_open_world_and_hides_raw_assertions_from_primary_markup(self) -> None:
        self.assertIn("const normalizeMemory", APP_JS)
        self.assertIn("memory.entities", APP_JS)
        self.assertIn("memory.current_facts", APP_JS)
        self.assertIn("Object.entries(memory)", APP_JS)
        self.assertNotIn("memorySections", APP_JS)
        self.assertIn("What Blackhole knows.", HTML)
        self.assertIn("Why Blackhole knows this", APP_JS)
        self.assertNotIn("source_refs", HTML)
        self.assertIn("column-count: 2", CSS)
        self.assertIn("memory-subsection-label", APP_JS)
        self.assertIn("memory-history-label", APP_JS)
        self.assertIn("attention_history", APP_JS)
        self.assertIn("memory-occurrences", APP_JS)
        self.assertIn("Occurrences · ", APP_JS)
        self.assertIn("memory-history-disclosure", APP_JS)
        self.assertIn("data-clarify-question", APP_JS)
        self.assertIn("navigateToAskWithPrompt", APP_JS)

    def test_capture_and_answer_surfaces_keep_the_final_live_ux_contract(self) -> None:
        self.assertRegex(CSS, r"\.composer\s*\{[\s\S]*?border-radius: 28px")
        self.assertRegex(CSS, r"\.composer textarea\s*\{[\s\S]*?line-height: 24px")
        self.assertIn("chat-assistant-primary", APP_JS)
        self.assertIn("clarify-answer-index", APP_JS)
        self.assertIn("Clarify in Ask", APP_JS)
        self.assertNotIn("answer-grounding", APP_JS)
        self.assertNotIn("Based on what you’ve captured so far.", APP_JS)
        self.assertIn("prefers-reduced-motion: reduce", CSS)

    def test_capture_geometry_has_no_brittle_vertical_offsets(self) -> None:
        self.assertRegex(CSS, r"\.composer textarea\s*\{[\s\S]*?padding: 14px 2px")
        self.assertNotIn("transform: translateY(-1px)", CSS)

    def test_ask_has_natural_examples_and_distinct_failure_copy(self) -> None:
        self.assertIn("What do I need to do today?", APP_JS)
        self.assertIn("What do I know about my car?", APP_JS)
        self.assertIn("const normalizeAnswer", APP_JS)
        self.assertIn("Your latest memory is still safe.", APP_JS)
        self.assertIn("provider_unavailable", APP_JS)
        self.assertIn("Nothing clear came back yet.", APP_JS)
        self.assertIn('mode === "no_data"', APP_JS)
        self.assertIn("No processed memory yet.", APP_JS)
        self.assertNotIn("No supported observations", APP_JS)

    def test_hover_is_pointer_gated_and_touch_targets_are_present(self) -> None:
        self.assertIn("@media (hover: hover) and (pointer: fine)", CSS)
        self.assertGreaterEqual(len(re.findall(r"min-height: 44px", CSS)), 3)
        self.assertIn("touch-action: manipulation", CSS)


if __name__ == "__main__":
    unittest.main()
