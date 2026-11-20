"""Optional browser checks: uv pip install playwright, then playwright install chromium."""
import os
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from arcgis_map_compat import Map

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


FAKE_SDK = """
window.calls = {tokens:[], maps:[], views:[], credentialCleanup:0};
class Layers {
  constructor(items) { this.items = items; }
  toArray() { return [...this.items]; }
  remove(layer) { this.items = this.items.filter(item => item !== layer); }
}
class WebMap {
  static fromJSON(json) { return new WebMap(json); }
  constructor(json) {
    this.layers = new Layers(json.operationalLayers);
    this.initialViewProperties = {viewpoint:json.initialState.viewpoint};
    calls.maps.push(this);
  }
  async load() { if (window.hold) await window.hold; }
  findLayerById(id) { return this.layers.items.find(layer => layer.id === id); }
  add(layer) { this.layers.items.push(layer); }
  destroy() { this.destroyed = true; }
}
class MapView {
  constructor(options) { Object.assign(this, options); this.gotos=[]; calls.views.push(this); }
  async when() {}
  async goTo(value) { this.gotos.push(value); }
  async whenLayerView(layer) {
    if (layer.title === "Fail") throw new Error("SECRET_URL_MUST_NOT_BE_SHOWN");
  }
  destroy() { this.destroyed = true; }
}
const identity = {
  registerToken(value) { calls.tokens.push(value); },
  destroyCredentials() { calls.credentialCleanup++; }
};
window.$arcgis = {import:async () => [WebMap, MapView, identity]};
"""

HOST = """async source => {
  // Simulate a notebook's AMD loader in the parent, not in the isolated iframe.
  window.define = () => { throw Error("Notebook AMD loader used"); };
  window.define.amd = {};
  const listeners = new Set();
  window.sent = [];
  window.receive = message => listeners.forEach(fn => fn(message));
  const model = {
    on: (name, fn) => listeners.add(fn),
    off: (name, fn) => listeners.delete(fn),
    send: message => window.sent.push(message)
  };
  window.listenerCount = () => listeners.size;
  const url = URL.createObjectURL(new Blob([source], {type:"text/javascript"}));
  const {default: widget} = await import(url);
  window.dispose = widget.render({model, el:document.body});
  URL.revokeObjectURL(url);
}"""


@unittest.skipIf(sync_playwright is None, "Install playwright for browser checks")
class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)
        self.map = Map()
        self.addCleanup(self.map.close)
        self.messages = []
        sender = patch.object(self.map, "send", self.messages.append)
        sender.start()
        self.addCleanup(sender.stop)

    def mount(self, *, real=False):
        if not real:
            self.page.route("https://js.arcgis.com/5.1/core.js",
                            lambda route: route.fulfill(body=FAKE_SDK, content_type="text/javascript"))
            self.page.route("**/main.css", lambda route: route.fulfill(body=""))
        source = self.map.get_state()["_esm"]
        self.page.evaluate(HOST, source)
        self.page.wait_for_function("sent.some(message => message.type === 'ready')")
        self.frame = self.page.frames[1]
        self.map._on_message(self.map, {"type": "ready"}, [])
        self.publish()

    def publish(self):
        self.page.evaluate("message => window.receive(message)", self.messages[-1])

    def loaded(self):
        self.frame.wait_for_function(
            "!/Loading|Waiting/.test(document.querySelector('[role=status]').textContent)",
                                     timeout=120000)
        self.assertEqual(self.frame.locator("[role=status]").inner_text(), "")

    def test_handshake_incremental_layers_and_local_navigation(self):
        self.map.content.add("https://example.com/test.parquet?signature=SIGNED_SECRET")
        self.mount()
        self.loaded()
        self.assertNotIn("SIGNED_SECRET", self.page.locator("iframe").get_attribute("srcdoc"))
        self.frame.evaluate("calls.views[0].gotos.push('browser navigation')")
        self.map.content.add_feature_service(
            "https://example.com/rest/services/Test/FeatureServer/0", token="TOKEN_SECRET"
        )
        self.publish()
        self.frame.wait_for_function("calls.maps[0].layers.items.length === 2")
        self.loaded()
        self.assertEqual(self.frame.evaluate("calls.views.length"), 1)
        self.assertEqual(self.frame.evaluate("calls.views[0].gotos.length"), 2)
        self.assertEqual(self.frame.evaluate("calls.tokens[0].token"), "TOKEN_SECRET")
        self.map.zoom = 8
        self.publish()
        self.frame.wait_for_function("calls.views[0].gotos.length === 3")
        self.page.evaluate("window.dispose()")
        self.assertEqual(self.page.evaluate("window.listenerCount()"), 0)
        self.assertEqual(self.page.locator("iframe").count(), 0)

    def test_failures_are_visible_without_echoing_secrets(self):
        self.map.content.add("https://example.com/test.parquet?signature=SECRET", title="Fail")
        self.mount()
        self.frame.wait_for_function(
            "document.querySelector('[role=status]').textContent.startsWith('A layer could not')")
        self.assertNotIn("SECRET", self.frame.locator("body").inner_text())

    def test_disposal_during_sdk_loading(self):
        self.mount()
        self.page.evaluate("window.dispose()")
        self.assertEqual(self.page.evaluate("window.listenerCount()"), 0)
        self.assertEqual(self.page.locator("iframe").count(), 0)

    @unittest.skipUnless(os.getenv("ARCGIS_BROWSER_LIVE"), "Set ARCGIS_BROWSER_LIVE=1 for CDN check")
    def test_real_sdk_feature_service_and_parquet(self):
        self.page.route("https://data.test/**", self.serve_data)
        self.page.route("https://www.arcgis.com/sharing/rest/**", self.serve_data)
        self.requests = []
        self.map.center = [34, -118]
        self.map.zoom = 8
        self.map.content.add_feature_service(
            "https://data.test/rest/services/Points/FeatureServer/0", token="TEST_TOKEN"
        )
        self.map.content.add("https://data.test/points.parquet?signature=TEST_SIGNATURE")
        self.mount(real=True)
        self.loaded()
        self.assertGreater(self.frame.locator("canvas").count(), 0)
        self.assertTrue(any("token=TEST_TOKEN" in url for url in self.requests))
        self.assertTrue(any("signature=TEST_SIGNATURE" in url for url in self.requests))
        self.map.content.add_parquet_item("a" * 32, token="PORTAL_TEST_TOKEN")
        self.publish()
        self.loaded()
        self.assertTrue(any("/items/" in url and "token=PORTAL_TEST_TOKEN" in url
                            for url in self.requests))

    def serve_data(self, route):
        self.requests.append(route.request.url)
        headers = {"Access-Control-Allow-Origin": "*",
                   "Access-Control-Expose-Headers": "Content-Range, Accept-Ranges",
                   "Access-Control-Allow-Headers": "*", "Accept-Ranges": "bytes"}
        if route.request.method == "OPTIONS":
            return route.fulfill(headers=headers)
        if "/portals/self" in route.request.url:
            return route.fulfill(body=json.dumps({
                "id": "test", "name": "ArcGIS Online", "isPortal": False,
                "portalHostname": "www.arcgis.com", "helperServices": {},
                "user": {"username": "test", "orgId": "test"},
            }), headers=headers, content_type="application/json")
        if "/items/" in route.request.url and "token=PORTAL_TEST_TOKEN" not in route.request.url:
            return route.fulfill(body=json.dumps({"error": {
                "code": 499, "message": "Token Required", "details": [],
            }}), headers=headers, content_type="application/json")
        path = urlsplit(route.request.url).path
        if path.endswith((".parquet", "/data")):
            body = Path(__file__).with_name("points.parquet").read_bytes()
            byte_range = route.request.headers.get("range")
            if byte_range:
                start, end = byte_range.removeprefix("bytes=").split("-")
                start, end = int(start), min(int(end) if end else len(body) - 1, len(body) - 1)
                headers["Content-Range"] = f"bytes {start}-{end}/{len(body)}"
                return route.fulfill(status=206, body=body[start:end + 1], headers=headers,
                                     content_type="application/octet-stream")
            return route.fulfill(body=body, headers=headers,
                                 content_type="application/octet-stream")
        if "/items/" in route.request.url:
            return route.fulfill(
                body=json.dumps({"id": "a" * 32, "type": "Apache Parquet", "title": "Points",
                                 "owner": "test", "access": "public", "size": 1286}),
                headers=headers, content_type="application/json")
        fields = [{"name": "OBJECTID", "type": "esriFieldTypeOID", "alias": "OBJECTID"}]
        extent = {"xmin": -118.1, "ymin": 34, "xmax": -118, "ymax": 34.1,
                  "spatialReference": {"wkid": 4326}}
        if "/query" in route.request.url:
            data = {"objectIdFieldName": "OBJECTID", "geometryType": "esriGeometryPoint",
                    "spatialReference": {"wkid": 4326}, "fields": fields,
                    "features": [{"attributes": {"OBJECTID": 1},
                                  "geometry": {"x": -118, "y": 34}}],
                    "count": 1, "objectIds": [1], "extent": extent}
        else:
            data = {"currentVersion": 11.3, "id": 0, "name": "Points",
                    "type": "Feature Layer", "geometryType": "esriGeometryPoint",
                    "objectIdField": "OBJECTID", "fields": fields,
                    "extent": extent, "capabilities": "Query",
                    "supportedQueryFormats": "JSON", "maxRecordCount": 1000,
                    "drawingInfo": {"renderer": {"type": "simple",
                        "symbol": {"type": "esriSMS", "style": "esriSMSCircle",
                                   "color": [255, 0, 0, 255], "size": 8}}}}
        route.fulfill(body=json.dumps(data), headers=headers, content_type="application/json")


if __name__ == "__main__":
    unittest.main()
