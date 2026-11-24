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
from geoanalytics_widget import Basemap, GIS, MapBuilder
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

    def test_custom_basemap_is_replaced_and_snapshotted(self):
        basemap = Basemap(
            title="Imagery", id="imagery", layer_type="ArcGISTiledMapServiceLayer",
            url="https://example.com/Imagery/MapServer", opacity=0.5,
            options={"futureOption": {"value": "SDK decides"}},
        )
        self.builder.set_basemap(basemap)
        first, messages = self.build()
        original = {
            "title": "Imagery", "baseMapLayers": [{
                "id": "imagery", "layerType": "ArcGISTiledMapServiceLayer",
                "url": "https://example.com/Imagery/MapServer", "opacity": 0.5,
                "title": "Imagery", **deepcopy(basemap.options),
            }],
        }
        first._on_message(first, {"type": "ready"}, [])
        self.assertEqual(messages[0]["definition"]["baseMap"], original)
        basemap.title = "Updated imagery"
        basemap.opacity = 0.75
        basemap.options["futureOption"]["value"] = "Updated option"
        second, _ = self.build()
        self.assertEqual(second._webmap_dict["baseMap"], {
            "title": basemap.title, "baseMapLayers": [{
                **original["baseMapLayers"][0], "opacity": 0.75,
                "title": basemap.title, **basemap.options,
            }],
        })
        self.builder.set_basemap("light")
        third, _ = self.build()
        self.assertEqual(third._webmap_dict["baseMap"]["title"], "Light Gray Canvas")
        self.assertEqual(first._webmap_dict["baseMap"], original)
        self.assertEqual(second._webmap_dict["baseMap"]["baseMapLayers"][0]["opacity"], 0.75)

    def test_basemap_fields_and_options_are_resolved_at_build(self):
        basemap = Basemap(
            id="vector", layer_type="VectorTileLayer",
            style_url="https://example.com/style.json", title="Vector",
            opacity=0, visibility=False,
            options={"title": "Override", "futureOption": {"value": 1}},
        )
        self.builder.set_basemap(basemap)
        first, _ = self.build()
        self.assertEqual(first._webmap_dict["baseMap"]["baseMapLayers"], [{
            "id": "vector", "layerType": "VectorTileLayer",
            "styleUrl": "https://example.com/style.json", "title": "Override",
            "opacity": 0, "visibility": False, "futureOption": {"value": 1},
        }])
        basemap.style_url = "https://example.com/updated.json"
        basemap.options["futureOption"]["value"] = 2
        second, _ = self.build()
        self.assertEqual(second._webmap_dict["baseMap"]["baseMapLayers"][0]["styleUrl"],
                         basemap.style_url)
        self.assertEqual(first._webmap_dict["baseMap"]["baseMapLayers"][0]["futureOption"],
                         {"value": 1})

    def test_basemap_presets_build_and_publish_independent_json(self):
        for name in ("light", "dark", "streets", "osm"):
            with self.subTest(basemap=name):
                self.builder = MapBuilder(basemap=name)
                first, messages = self.build()
                basemap = deepcopy(first._webmap_dict["baseMap"])
                layer = basemap["baseMapLayers"][0]
                self.assertEqual(len(basemap["baseMapLayers"]), 1)
                self.assertFalse(layer.get("isReference", False))
                self.assertEqual(
                    layer["layerType"],
                    "VectorTileLayer" if name == "osm" else "ArcGISTiledMapServiceLayer",
                )
                first._on_message(first, {"type": "ready"}, [])
                self.assertEqual(messages[0]["definition"]["baseMap"], basemap)
                first._webmap_dict["baseMap"]["baseMapLayers"].clear()
                second, _ = self.build()
                self.assertEqual(second._webmap_dict["baseMap"], basemap)
                self.builder.set_basemap("dark" if name != "dark" else "light")
                third, _ = self.build()
                self.assertNotEqual(third._webmap_dict["baseMap"], basemap)
                self.assertEqual(second._webmap_dict["baseMap"], basemap)

    def test_unknown_basemap_preserves_previous_selection(self):
        self.builder.set_basemap("light")
        with self.assertRaisesRegex(ValueError, "light, dark, streets, osm"):
            self.builder.set_basemap("unknown")
        widget, _ = self.build()
        self.assertEqual(widget._webmap_dict["baseMap"]["title"], "Light Gray Canvas")
        with self.assertRaises(ValueError):
            MapBuilder(basemap="unknown")

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

    def test_build_resolves_current_gis_without_changing_layer_json_or_existing_widgets(self):
        gis = GIS("https://portal.example.com/arcgis", "original-token")
        override = GIS("https://other.example.com", "override-token")
        options = {"opacity": 0.5}
        self.builder = MapBuilder(gis)
        self.builder.add_feature_service(
            "https://services.example.com/Test/FeatureServer/0", options=options)
        self.builder.add_feature_service(
            "https://other.example.com/Test/FeatureServer/1", gis=override)
        self.builder.add_parquet_item("a" * 32)
        first, _ = self.build()
        original = deepcopy(first._credentials)
        gis.token = "updated-token"
        gis.portal_url = "https://new.example.com/arcgis/"
        override.token = None
        options["opacity"] = 0.75
        second, _ = self.build()
        self.assertEqual(second._credentials, [
            {"server": "https://services.example.com/Test/FeatureServer", "token": "updated-token"},
            {"server": "https://new.example.com/arcgis/sharing/rest", "token": "updated-token"},
        ])
        self.assertEqual(second._portal_url, gis.portal_url)
        self.assertEqual(second._webmap_dict["operationalLayers"][0]["opacity"], 0.5)
        self.assertEqual(first._credentials, original)
        self.assertEqual(first._portal_url, "https://portal.example.com/arcgis")
        self.assertEqual(first._webmap_dict["operationalLayers"][0]["opacity"], 0.5)
        self.assertEqual(
            first._webmap_dict["operationalLayers"][0]["id"],
            second._webmap_dict["operationalLayers"][0]["id"],
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
        widget, _ = self.build()
        self.assertEqual(widget._credentials, [])

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
