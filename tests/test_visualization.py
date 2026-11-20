import importlib.abc
import sys
import unittest
from copy import deepcopy


class BlockUnusedDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'arcgis', 'pandas', 'pydantic', 'geopandas', 'pyarrow'}:
            raise AssertionError(f'Visualization requested {fullname}')
        return None


sys.meta_path.insert(0, BlockUnusedDependencies())

from arcgis_map_compat import Map


class VisualizationTests(unittest.TestCase):
    def setUp(self):
        self.map = Map()
        self.addCleanup(self.map.close)

    def test_initial_center_zoom_and_widget_protocol(self):
        self.map.center = [46.8, 7.16]
        self.map.zoom = 12
        self.assertEqual(self.map._view_state, {'center': [46.8, 7.16], 'zoom': 12})
        self.assertEqual(self.map._webmap_dict['version'], '2.37')
        viewpoint = self.map._webmap_dict['initialState']['viewpoint']
        self.assertEqual(viewpoint['targetGeometry']['spatialReference']['wkid'], 102100)
        self.assertGreater(viewpoint['scale'], 0)
        data, metadata = self.map._repr_mimebundle_()
        self.assertEqual(data['application/vnd.jupyter.widget-view+json']['model_id'], self.map.model_id)

    def test_signed_urls_and_multiple_layers(self):
        url = 'https://example.com/data.parquet?signature=a%2Bb'
        self.map.content.add(url)
        original = deepcopy(self.map._webmap_dict)
        self.map.content.add(url)
        layers = self.map._webmap_dict['operationalLayers']
        self.assertEqual(len(layers), 2)
        self.assertNotEqual(layers[0]['id'], layers[1]['id'])
        self.assertEqual(layers[0]['layerType'], 'ParquetLayer')
        self.assertEqual(layers[0]['source'], {'type': 'files', 'urls': [url]})
        self.assertEqual(len(original['operationalLayers']), 1)
        self.map.content.add('https://example.com/download?file=layer')
        self.assertEqual(len(self.map._webmap_dict['operationalLayers']), 3)

    def test_later_layer_preserves_browser_view(self):
        extent = {'xmin': 1, 'ymin': 2, 'xmax': 3, 'ymax': 4, 'spatialReference': {'wkid': 3857}}
        self.map._view_state = {'center': [10, 20], 'zoom': 8, 'scale': 20000, 'extent': extent}
        self.map.content.add('https://example.com/next.parquet')
        viewpoint = self.map._webmap_dict['initialState']['viewpoint']
        self.assertEqual(viewpoint, {'targetGeometry': extent, 'scale': 20000})

    def test_bad_inputs_leave_map_unchanged(self):
        original = deepcopy(self.map._webmap_dict)
        for value in ('file:///tmp/data.parquet', 'dbfs:/data.parquet', 'not a URL'):
            with self.assertRaises(ValueError):
                self.map.content.add(value)
        with self.assertRaises(TypeError):
            self.map.content.add({'url': 'https://example.com/data.parquet'})
        with self.assertRaises(ValueError):
            self.map.center = [91, 0]
        with self.assertRaises(ValueError):
            self.map.zoom = '12'
        self.assertEqual(self.map._webmap_dict, original)


if __name__ == '__main__':
    unittest.main()
