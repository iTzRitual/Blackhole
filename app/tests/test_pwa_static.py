from __future__ import annotations

import json
import unittest
from pathlib import Path


WEB_ROOT = Path(__file__).resolve().parents[1] / "web"


class PWAStaticTests(unittest.TestCase):
    def test_manifest_references_existing_shell_assets(self) -> None:
        manifest = json.loads((WEB_ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["start_url"], "/")
        for icon in manifest["icons"]:
            self.assertTrue((WEB_ROOT / icon["src"].lstrip("/")).is_file())
        for name in ("index.html", "styles.css", "app.js", "sw.js"):
            self.assertTrue((WEB_ROOT / name).is_file())

    def test_client_uses_host_api_without_provider_language(self) -> None:
        app_js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
        html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('api("/api/v2/capture"', app_js)
        self.assertIn('api("/api/v2/state"', app_js)
        self.assertIn('api("/api/v2/ask"', app_js)
        self.assertIn("data_base64", app_js)
        self.assertNotIn('api("/api/capture"', app_js)
        self.assertNotIn('api("/api/query"', app_js)
        self.assertIn('method: "POST"', app_js)
        self.assertNotIn("/api/query?q=", app_js)
        self.assertNotIn("Codex", html)
        self.assertNotIn("semantic extraction", app_js.casefold())

    def test_service_worker_excludes_dynamic_api_responses(self) -> None:
        service_worker = (WEB_ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn('url.pathname.startsWith("/api/")', service_worker)
        self.assertIn("request.mode === \"navigate\"", service_worker)


if __name__ == "__main__":
    unittest.main()
