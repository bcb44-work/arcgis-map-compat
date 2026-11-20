import importlib.abc
import json
import sys
import unittest
from copy import deepcopy
from unittest.mock import patch


class BlockUnusedDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"arcgis", "pandas", "pydantic", "geopandas", "pyarrow"}:
            raise AssertionError(f"Visualization requested {fullname}")
        return None


sys.meta_path.insert(0, BlockUnusedDependencies())
from arcgis_map_compat import Map
from ipywidgets import Widget
from ipywidgets.embed import embed_minimal_html


class VisualizationTests(unittest.TestCase):
    def setUp(self):
        self.map = Map()
        self.addCleanup(self.map.close)
        self.messages = []
        self.send = patch.object(self.map, "send", self.messages.append)
        self.send.start()
        self.addCleanup(self.send.stop)

    def test_initial_center_zoom_and_explicit_updates(self):
        self.map.center = [46.8, 7.16]
        self.map.zoom = 12
        self.assertEqual(self.map.center, [46.8, 7.16])
        state = self.messages[-1]["definition"]["initialState"]["viewpoint"]
        self.assertEqual(state["targetGeometry"]["spatialReference"]["wkid"], 3857)
        self.assertGreater(state["scale"], 0)
        center = self.map.center
        center[0] = 0
        self.assertEqual(self.map.center, [46.8, 7.16])

    def test_signed_urls_and_multiple_layers(self):
        url = "https://example.com/download?signature=a%2Bb&file=layer"
        self.map.content.add(url)
        original = deepcopy(self.messages[-1])
        self.map.content.add(url)
        layers = self.messages[-1]["definition"]["operationalLayers"]
        self.assertEqual(len(layers), 2)
        self.assertNotEqual(layers[0]["id"], layers[1]["id"])
        self.assertEqual(layers[0]["layerType"], "ParquetLayer")
        self.assertEqual(layers[0]["source"], {"type": "files", "urls": [url]})
        self.assertEqual(len(original["definition"]["operationalLayers"]), 1)

    def test_feature_service_and_portal_credentials(self):
        url = "https://example.com/arcgis/rest/services/Test/FeatureServer/0"
        self.map.content.add_feature_service(url, token="feature-secret")
        self.map.content.add_parquet_item("a" * 32, token="portal-secret")
        message = self.messages[-1]
        self.assertEqual(message["definition"]["operationalLayers"][0]["url"], url)
        self.assertEqual(
            message["definition"]["operationalLayers"][1]["source"],
            {"type": "portal-item", "itemId": "a" * 32},
        )
        self.assertEqual(message["credentials"], [
            {"server": url.rsplit("/", 1)[0], "token": "feature-secret"},
            {"server": "https://www.arcgis.com/sharing/rest", "token": "portal-secret"},
        ])

    def test_each_ready_request_replays_current_snapshot(self):
        self.map.content.add("https://example.com/first.parquet")
        first = deepcopy(self.messages[-1])
        self.map._on_message(self.map, {"type": "ready"}, [])
        self.assertEqual(self.messages[-1], first)
        self.map.content.add("https://example.com/second.parquet")
        self.map._on_message(self.map, {"type": "ready"}, [])
        self.assertEqual(len(self.messages[-1]["definition"]["operationalLayers"]), 2)
        count = len(self.messages)
        self.map._on_message(self.map, {"type": "unknown"}, [])
        self.assertEqual(len(self.messages), count)

    def test_secrets_absent_from_serialized_state_and_html(self):
        from io import StringIO
        url = "https://example.com/data.parquet?signature=SIGNED_SECRET"
        self.map.content.add(url)
        self.map.content.add_feature_service(
            "https://example.com/rest/services/Test/FeatureServer/0", token="TOKEN_SECRET"
        )
        html = StringIO()
        embed_minimal_html(html, views=[self.map])
        serialized = json.dumps(Widget.get_manager_state()) + html.getvalue()
        for secret in (url, "SIGNED_SECRET", "TOKEN_SECRET"):
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, repr(self.map))
        self.assertNotIn("_webmap_dict", self.map.get_state())
        self.assertIn("SIGNED_SECRET", json.dumps(self.messages[-1]))

    def test_bad_inputs_leave_map_unchanged(self):
        original = deepcopy(self.map._webmap_dict)
        for value in ("file:///tmp/data.parquet", "dbfs:/data.parquet", "not a URL"):
            with self.assertRaises(ValueError):
                self.map.content.add(value)
        with self.assertRaises(TypeError):
            self.map.content.add({"url": "https://example.com/data.parquet"})
        for value in ([91, 0], [0, 181], [float("nan"), 0], [True, 0], [0]):
            with self.assertRaises(ValueError):
                self.map.center = value
        for value in ("12", True, -1, 24):
            with self.assertRaises(ValueError):
                self.map.zoom = value
        with self.assertRaises(ValueError):
            self.map.content.add_feature_service("https://example.com/FeatureServer")
        with self.assertRaises(ValueError):
            self.map.content.add_parquet_item("bad")
        with self.assertRaises(ValueError):
            self.map.content.add_parquet_item("a" * 32, token=42)
        self.assertEqual(self.map._webmap_dict, original)
        self.assertEqual(self.map._credentials, [])
        self.assertEqual(self.messages, [])


if __name__ == "__main__":
    unittest.main()
