from copy import deepcopy
import math
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit
from uuid import uuid4

import anywidget
from traitlets import Dict, Unicode


class Map(anywidget.AnyWidget):
    """Display a map and add Parquet URLs. Center uses [latitude, longitude]."""

    _esm = Path(__file__).parent / "frontend" / "compat-host.js"
    _renderer_esm = Unicode(
        (Path(__file__).parent / "static" / "map_widget.js").read_text(encoding="utf-8")
    ).tag(sync=True)
    _css = Path(__file__).parent / "static" / "map_widget.css"
    _webmap_dict = Dict().tag(sync=True)
    _view_state = Dict().tag(sync=True)
    js_api_path = Unicode(os.getenv("JSAPI_CDN", "")).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content = MapContent(self)
        self._view_state = {"center": [34.0, -117.0], "zoom": 12}
        self._webmap_dict = {
            "version": "2.37",
            "baseMap": deepcopy(_BASEMAP),
            "spatialReference": {"wkid": 102100, "latestWkid": 3857},
            "operationalLayers": [],
        }
        self._update_source()

    @property
    def center(self):
        return list(self._view_state["center"])

    @center.setter
    def center(self, value):
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("Center must be [latitude, longitude].")
        latitude, longitude = value
        if not all(isinstance(number, (int, float)) and math.isfinite(number) for number in value):
            raise ValueError("Center coordinates must be finite numbers.")
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("Center must use latitude and longitude in degrees.")
        self._view_state = {"center": list(value), "zoom": self.zoom}
        self._update_source()

    @property
    def zoom(self):
        return self._view_state["zoom"]

    @zoom.setter
    def zoom(self, value):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 23:
            raise ValueError("Zoom must be an integer from 0 to 23.")
        self._view_state = {"center": self.center, "zoom": value}
        self._update_source()

    def _update_source(self, layers=None):
        # Preserve the existing WebMap JSON transport and seed its initial view.
        state = self._view_state
        scale = state.get("scale", 591657527.591555 / 2 ** state["zoom"])
        extent = state.get("extent")
        if extent is None:
            latitude, longitude = state["center"]
            latitude = max(-85.05112878, min(85.05112878, latitude))
            x = 6378137 * math.radians(longitude)
            y = 6378137 * math.log(math.tan(math.pi / 4 + math.radians(latitude) / 2))
            extent = {
                "xmin": x - 1000, "ymin": y - 1000,
                "xmax": x + 1000, "ymax": y + 1000,
                "spatialReference": {"wkid": 102100, "latestWkid": 3857},
            }
        self._webmap_dict = {
            **self._webmap_dict,
            "operationalLayers": (
                self._webmap_dict["operationalLayers"] if layers is None else layers
            ),
            "initialState": {"viewpoint": {"targetGeometry": extent, "scale": scale}},
        }


class MapContent:
    def __init__(self, map):
        self._source = map

    def add(self, url: str) -> None:
        """Add a browser-readable HTTP(S) Parquet URL, including signed URLs."""
        if not isinstance(url, str):
            raise TypeError("Pass a Parquet URL as a string.")
        url = url.strip()
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Parquet URLs must use HTTP or HTTPS.")
        layer = {
            "id": uuid4().hex[:12],
            "layerType": "ParquetLayer",
            "source": {"type": "files", "urls": [url]},
            "title": unquote(parsed.path.rsplit("/", 1)[-1]) or "Parquet layer",
        }
        layers = [*self._source._webmap_dict["operationalLayers"], layer]
        self._source._update_source(layers)


_BASEMAP = {
    "baseMapLayers": [
        {
            "id": "world-hillshade-layer",
            "url": "https://services.arcgisonline.com/arcgis/rest/services/Elevation/World_Hillshade/MapServer",
            "layerType": "ArcGISTiledMapServiceLayer",
            "title": "World Hillshade",
            "showLegend": False,
            "visibility": True,
            "opacity": 1,
        },
        {
            "id": "topo-vector-base-layer",
            "styleUrl": "https://www.arcgis.com/sharing/rest/content/items/7dc6cea0b1764a1f9af2e679f642f0f5/resources/styles/root.json",
            "layerType": "VectorTileLayer",
            "title": "World Topo",
            "visibility": True,
            "opacity": 1,
        },
    ],
    "title": "Topographic",
}
