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
from geoanalytics_widget import GIS, MapBuilder
from ipywidgets import Widget
from ipywidgets.embed import embed_minimal_html


class VisualizationTests(unittest.TestCase):
    def setUp(self):
        self.builder = MapBuilder()

    def build(self):
        widget = self.builder.build()
        self.addCleanup(widget.close)
        messages = []
        sender = patch.object(widget, "send", messages.append)
        sender.start()
        self.addCleanup(sender.stop)
        return widget, messages

    def test_build_uses_final_extent_and_sref(self):
        self.builder.set_initial_state((0, 0, 1000, 1000), sref=3857)
        extent = [-119, 33, -117, 35]
        self.builder.set_initial_state(extent, sref=4326)
        widget, messages = self.build()
        state = widget._webmap_dict["initialState"]["viewpoint"]
        self.assertEqual(state, {"targetGeometry": {
            "xmin": -119, "ymin": 33, "xmax": -117, "ymax": 35,
            "spatialReference": {"wkid": 4326},
        }})
        extent[0] = -120
        second, _ = self.build()
        self.assertEqual(
            second._webmap_dict["initialState"]["viewpoint"]["targetGeometry"]["xmin"],
            -120,
        )
        self.assertEqual(state["targetGeometry"]["xmin"], -119)
        self.assertEqual(messages, [])

    def test_missing_extent_uses_sdk_defaults(self):
        widget, _ = self.build()
        self.assertNotIn("initialState", widget._webmap_dict)

    def test_signed_urls_and_multiple_layers(self):
        url = "https://example.com/download?signature=a%2Bb&file=layer"
        self.builder.add_parquet(url)
        original = deepcopy(self.builder._layers)
        self.builder.add_parquet(url)
        widget, messages = self.build()
        layers = widget._webmap_dict["operationalLayers"]
        self.assertEqual(len(layers), 2)
        self.assertNotEqual(layers[0]["id"], layers[1]["id"])
        self.assertEqual(layers[0]["layerType"], "ParquetLayer")
        self.assertEqual(layers[0]["source"], {"type": "files", "urls": [url]})
        self.assertEqual(len(original), 1)
        self.assertEqual(messages, [])

    def test_feature_service_and_portal_credentials(self):
        url = "https://example.com/arcgis/rest/services/Test/FeatureServer/0"
        self.builder = MapBuilder(GIS("https://portal.example.com/arcgis/", "portal-secret"))
        self.builder.add_feature_service(url, gis=GIS("https://other.example.com", "feature-secret"))
        self.builder.add_parquet_item("a" * 32)
        widget, messages = self.build()
        widget._on_message(widget, {"type": "ready"}, [])
        message = messages[-1]
        self.assertEqual(message["definition"]["operationalLayers"][0]["url"], url)
        self.assertEqual(
            message["definition"]["operationalLayers"][1]["source"],
            {"type": "portal-item", "itemId": "a" * 32},
        )
        self.assertEqual(message["credentials"], [
            {"server": url.rsplit("/", 1)[0], "token": "feature-secret"},
            {"server": "https://portal.example.com/arcgis/sharing/rest", "token": "portal-secret"},
        ])
        self.assertEqual(message["portal_url"], "https://portal.example.com/arcgis/")

    def test_builder_gis_is_used_by_feature_services(self):
        self.builder = MapBuilder(GIS("https://portal.example.com", "shared-token"))
        self.builder.add_feature_service("https://services.example.com/Test/FeatureServer/0")
        widget, _ = self.build()
        self.assertEqual(widget._credentials, [{
            "server": "https://services.example.com/Test/FeatureServer", "token": "shared-token",
        }])

    def test_layer_options_are_merged_last_without_validation(self):
        options = {
            "id": "user-defined-id", "title": "Override", "opacity": "SDK decides",
            "layerDefinition": {"definitionExpression": "VALUE > 10"},
            "futureOption": {"nested": [1, 2, 3]},
        }
        self.builder.add_parquet("https://example.com/data.parquet", options=options)
        self.builder.add_feature_service(
            "https://example.com/Test/FeatureServer/0", options=options)
        self.builder.add_parquet_item("a" * 32, options=options)
        widget, _ = self.build()
        for layer in widget._webmap_dict["operationalLayers"]:
            for key, value in options.items():
                self.assertEqual(layer[key], value)
        options["layerDefinition"]["definitionExpression"] = "CHANGED"
        self.assertEqual(
            widget._webmap_dict["operationalLayers"][0]["layerDefinition"]["definitionExpression"],
            "VALUE > 10",
        )

    def test_parquet_url_list_creates_one_layer(self):
        urls = [
            "https://example.com/first.parquet?signature=a%2Bb",
            "https://example.com/download?signature=c%2Fd",
        ]
        expected = list(urls)
        self.builder.add_parquet(urls, title="Combined")
        urls.clear()
        widget, _ = self.build()
        layers = widget._webmap_dict["operationalLayers"]
        self.assertEqual(len(layers), 1)
        self.assertEqual(layers[0]["title"], "Combined")
        self.assertEqual(layers[0]["source"], {"type": "files", "urls": expected})

    def test_ready_publishes_once_and_disconnects(self):
        self.builder.add_parquet("https://example.com/first.parquet")
        widget, messages = self.build()
        widget._on_message(widget, {"type": "unknown"}, [])
        self.assertEqual(messages, [])
        widget._on_message(widget, {"type": "ready"}, [])
        first = deepcopy(messages[0])
        widget._on_message(widget, {"type": "ready"}, [])
        self.assertEqual(messages, [first])
        self.assertNotIn(widget._on_message, widget._msg_callbacks.callbacks)

    def test_builds_are_independent_of_later_builder_changes(self):
        self.builder.add_parquet("https://example.com/first.parquet")
        first, messages = self.build()
        original = deepcopy(first._webmap_dict)
        self.builder.set_initial_state((0, 0, 1, 1), sref=4326)
        self.builder.add_feature_service(
            "https://example.com/Test/FeatureServer/0", gis=GIS("https://example.com", "second-secret"))
        second, _ = self.build()
        self.assertEqual(first._webmap_dict, original)
        self.assertEqual(first._credentials, [])
        self.assertEqual(len(second._webmap_dict["operationalLayers"]), 2)
        self.assertNotIn("initialState", first._webmap_dict)
        self.assertIn("initialState", second._webmap_dict)
        self.assertEqual(messages, [])
        self.assertFalse(hasattr(first, "center"))
        self.assertFalse(hasattr(first, "zoom"))
        self.assertFalse(hasattr(first, "extent"))
        self.assertFalse(hasattr(first, "content"))

    def test_secrets_absent_from_serialized_state_and_html(self):
        from io import StringIO
        url = "https://example.com/data.parquet?signature=SIGNED_SECRET"
        self.builder.add_parquet(url)
        self.builder.add_feature_service(
            "https://example.com/rest/services/Test/FeatureServer/0",
            gis=GIS("https://example.com", "TOKEN_SECRET"),
        )
        widget, messages = self.build()
        html = StringIO()
        embed_minimal_html(html, views=[widget])
        serialized = json.dumps(Widget.get_manager_state()) + html.getvalue()
        for secret in (url, "SIGNED_SECRET", "TOKEN_SECRET"):
            self.assertNotIn(secret, serialized)
            self.assertNotIn(secret, repr(widget))
        self.assertNotIn("_webmap_dict", widget.get_state())
        widget._on_message(widget, {"type": "ready"}, [])
        self.assertIn("SIGNED_SECRET", json.dumps(messages[-1]))
        self.assertNotIn("TOKEN_SECRET", repr(GIS("https://example.com", "TOKEN_SECRET")))

    def test_bad_layer_inputs_leave_builder_unchanged(self):
        original = deepcopy(self.builder._layers)
        for value in (
            "file:///tmp/data.parquet", "dbfs:/data.parquet", "not a URL", [],
            ["https://example.com/valid.parquet", "not a URL"],
        ):
            with self.assertRaises(ValueError):
                self.builder.add_parquet(value)
        for value in (
            {"url": "https://example.com/data.parquet"},
            ["https://example.com/valid.parquet", 42],
        ):
            with self.assertRaises(TypeError):
                self.builder.add_parquet(value)
        with self.assertRaises(ValueError):
            self.builder.add_feature_service("https://example.com/FeatureServer")
        with self.assertRaises(ValueError):
            self.builder.add_parquet_item("bad")
        with self.assertRaises(ValueError):
            self.builder.add_feature_service(
                "https://example.com/Test/FeatureServer/0", gis=GIS("https://example.com", 42))
        self.assertEqual(self.builder._layers, original)
        self.assertEqual(self.builder._credentials, [])

    def test_invalid_extent_is_rejected_at_build(self):
        for extent in (
            [0], [0, 0, float("nan"), 1], [True, 0, 1, 1],
            [2, 0, 1, 1], [0, 2, 1, 1],
        ):
            builder = MapBuilder()
            builder.set_initial_state(extent, sref=4326)
            with self.assertRaises(ValueError):
                builder.build()
        for sref in (None, "4326", True, -1, 0):
            builder = MapBuilder()
            builder.set_initial_state((0, 0, 1, 1), sref=sref)
            with self.assertRaises(ValueError):
                builder.build()


if __name__ == "__main__":
    unittest.main()
