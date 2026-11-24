"""Optional browser checks: uv pip install playwright, then playwright install chromium."""
import os
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from geoanalytics_widget import GIS, MapBuilder

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


FAKE_SDK = """
window.calls = {tokens:[], maps:[], views:[], credentialCleanup:0};
class Layers {
  constructor(items) { this.items = items; }
  toArray() { return [...this.items]; }
}
class WebMap {
  static fromJSON(json) { return new WebMap(json); }
  constructor(json) {
    this.layers = new Layers(json.operationalLayers);
    calls.maps.push(this);
  }
  async load() { if (window.hold) await window.hold; }
  destroy() { this.destroyed = true; }
}
class MapView {
  constructor(options) { Object.assign(this, options); calls.views.push(this); }
  async when() {}
  async whenLayerView(layer) {
    if (layer.title === "Fail") throw new Error("SECRET_URL_MUST_NOT_BE_SHOWN");
  }
  destroy() { this.destroyed = true; }
}
const identity = {
  registerToken(value) { calls.tokens.push(value); },
  destroyCredentials() { calls.credentialCleanup++; }
};
window.config = {};
window.$arcgis = {import:async () => [WebMap, MapView, identity, config]};
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
        self.builder = MapBuilder()

    def mount(self, *, real=False):
        self.map = self.builder.build()
        self.addCleanup(self.map.close)
        self.messages = []
        sender = patch.object(self.map, "send", self.messages.append)
        sender.start()
        self.addCleanup(sender.stop)

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

    def test_initial_handshake_disconnects_and_ignores_later_messages(self):
        self.builder.add_parquet("https://example.com/test.parquet?signature=SIGNED_SECRET")
        self.builder.add_feature_service(
            "https://example.com/rest/services/Test/FeatureServer/0",
            gis=GIS("https://example.com", "TOKEN_SECRET"),
        )
        self.mount()
        self.loaded()
        self.assertNotIn("SIGNED_SECRET", self.page.locator("iframe").get_attribute("srcdoc"))
        self.assertEqual(self.page.evaluate("window.listenerCount()"), 0)
        self.assertEqual(self.page.evaluate("sent"), [{"type": "ready"}])
        self.assertEqual(len(self.messages), 1)
        self.assertEqual(self.frame.evaluate("calls.maps[0].layers.items.length"), 2)
        self.assertEqual(self.frame.evaluate("calls.views.length"), 1)
        self.assertEqual(self.frame.evaluate("calls.tokens[0].token"), "TOKEN_SECRET")
        self.frame.evaluate("calls.views[0].zoom = 8")
        self.publish()
        self.assertEqual(self.frame.evaluate("calls.maps.length"), 1)
        self.assertEqual(self.frame.evaluate("calls.views[0].zoom"), 8)
        self.assertEqual(self.page.evaluate("sent"), [{"type": "ready"}])
        self.page.evaluate("window.dispose()")
        self.assertEqual(self.page.evaluate("window.listenerCount()"), 0)
        self.assertEqual(self.page.locator("iframe").count(), 0)

    def test_failures_are_visible_without_echoing_secrets(self):
        self.builder.add_parquet("https://example.com/test.parquet?signature=SECRET", title="Fail")
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
    def test_real_sdk_basemap_presets(self):
        self.builder = MapBuilder(basemap="light")
        self.mount(real=True)
        self.loaded()
        for name in ("light", "dark", "streets", "osm"):
            with self.subTest(basemap=name):
                self.builder.set_basemap(name)
                widget = self.builder.build()
                self.addCleanup(widget.close)
                result = self.frame.evaluate("""async definition => {
                    const WebMap = await $arcgis.import("@arcgis/core/WebMap.js");
                    const map = WebMap.fromJSON(definition);
                    try {
                        await map.load();
                        await map.basemap.loadAll();
                        return {
                            types: map.basemap.baseLayers.map(layer => layer.type).toArray(),
                            references: map.basemap.referenceLayers.length,
                        };
                    } finally { map.destroy(); }
                }""", widget._webmap_dict)
                self.assertEqual(result, {
                    "types": ["vector-tile" if name == "osm" else "tile"], "references": 0,
                })

    @unittest.skipUnless(os.getenv("ARCGIS_BROWSER_LIVE"), "Set ARCGIS_BROWSER_LIVE=1 for CDN check")
    def test_real_sdk_feature_service_and_parquet(self):
        self.page.route("https://data.test/**", self.serve_data)
        self.page.route("https://portal.test/arcgis/sharing/rest/**", self.serve_data)
        self.requests = []
        self.builder = MapBuilder(GIS("https://portal.test/arcgis", "PORTAL_TEST_TOKEN"))
        self.builder.set_initial_extent((-119, 33, -117, 35), sref=4326)
        self.builder.add_feature_service(
            "https://data.test/rest/services/Points/FeatureServer/0",
            gis=GIS("https://feature-portal.test", "TEST_TOKEN"),
            options={"opacity": 0.5, "layerDefinition": {"definitionExpression": "OBJECTID = 1"}},
        )
        self.builder.add_parquet([
            "https://data.test/points.parquet?signature=TEST_SIGNATURE",
            "https://data.test/second.parquet?signature=SECOND_SIGNATURE",
        ])
        self.builder.add_parquet_item("a" * 32, options={"opacity": 0.7})
        with self.page.expect_request(
            lambda request: "/query?" in request.url and "OBJECTID%20%3D%201" in request.url,
            timeout=120000,
        ):
            self.mount(real=True)
            self.loaded()
        self.assertGreater(self.frame.locator("canvas").count(), 0)
        self.assertTrue(any("token=TEST_TOKEN" in url for url in self.requests))
        self.assertTrue(any("signature=TEST_SIGNATURE" in url for url in self.requests))
        self.assertTrue(any("signature=SECOND_SIGNATURE" in url for url in self.requests))
        self.assertTrue(any("/items/" in url and "token=PORTAL_TEST_TOKEN" in url
                            for url in self.requests))
        self.assertTrue(any(url.startswith("https://portal.test/arcgis/sharing/rest/content/items/")
                            for url in self.requests))

    def serve_data(self, route):
        self.requests.append(route.request.url)
        headers = {"Access-Control-Allow-Origin": route.request.headers.get("origin", "*"),
                   "Access-Control-Allow-Credentials": "true",
                   "Access-Control-Expose-Headers": "Content-Range, Accept-Ranges",
                   "Access-Control-Allow-Headers": "*", "Accept-Ranges": "bytes"}
        if route.request.method == "OPTIONS":
            return route.fulfill(headers=headers)
        if "/portals/self" in route.request.url:
            return route.fulfill(body=json.dumps({
                "id": "test", "name": "ArcGIS Online", "isPortal": False,
                "portalHostname": "portal.test", "helperServices": {},
                "user": {"username": "test", "orgId": "test"},
            }), headers=headers, content_type="application/json")
        if "/items/" in route.request.url and "token=PORTAL_TEST_TOKEN" not in route.request.url:
            return route.fulfill(body=json.dumps({"error": {
                "code": 499, "message": "Token Required", "details": [],
            }}), headers=headers, content_type="application/json")
        if "signedurl=true" in route.request.url:
            return route.fulfill(
                body=json.dumps({"signedUrl": "https://data.test/points.parquet?signature=PORTAL_SIGNATURE"}),
                headers=headers, content_type="application/json")
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
                                 "owner": "test", "access": "private", "size": 1286,
                                 "modified": 1700000000000}),
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
