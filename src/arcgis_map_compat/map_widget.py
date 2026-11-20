from copy import deepcopy
import math
from pathlib import Path
import re
from urllib.parse import urlsplit
from uuid import uuid4

import anywidget


class Map(anywidget.AnyWidget):
    """A notebook map. Definitions and credentials travel only in custom messages."""

    _esm = Path(__file__).parent / "map.js"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content = MapContent(self)
        self._view_state = {"center": [34.0, -117.0], "zoom": 12}
        self._credentials = []
        self._webmap_dict = {
            "version": "2.37",
            "baseMap": {
                "title": "Topographic",
                "baseMapLayers": [{
                    "id": "topographic",
                    "layerType": "ArcGISTiledMapServiceLayer",
                    "url": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
                }],
            },
            "operationalLayers": [],
        }
        self.on_msg(self._on_message)
        self._update_source()

    @property
    def center(self):
        """Initial center as [latitude, longitude]. Browser navigation stays local."""
        return list(self._view_state["center"])

    @center.setter
    def center(self, value):
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("Center must be [latitude, longitude].")
        if not all(
            isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)
            for n in value
        ):
            raise ValueError("Center coordinates must be finite numbers.")
        if not -90 <= value[0] <= 90 or not -180 <= value[1] <= 180:
            raise ValueError("Center must use latitude and longitude in degrees.")
        self._view_state["center"] = list(value)
        self._update_source()

    @property
    def zoom(self):
        return self._view_state["zoom"]

    @zoom.setter
    def zoom(self, value):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 23:
            raise ValueError("Zoom must be an integer from 0 to 23.")
        self._view_state["zoom"] = value
        self._update_source()

    def _on_message(self, widget, content, buffers):
        if content.get("type") == "ready":
            self._publish()

    def _publish(self):
        self.send({
            "type": "map",
            "definition": deepcopy(self._webmap_dict),
            "credentials": deepcopy(self._credentials),
        })

    def _update_source(self):
        latitude, longitude = self.center
        latitude = max(-85.05112878, min(85.05112878, latitude))
        x = 6378137 * math.radians(longitude)
        y = 6378137 * math.log(math.tan(math.pi / 4 + math.radians(latitude) / 2))
        self._webmap_dict["initialState"] = {"viewpoint": {
            "targetGeometry": {
                "xmin": x - 1000, "ymin": y - 1000,
                "xmax": x + 1000, "ymax": y + 1000,
                "spatialReference": {"wkid": 3857},
            },
            "scale": 591657527.591555 / 2 ** self.zoom,
        }}
        self._publish()

    def close(self):
        if hasattr(self, "_credentials"):
            self._credentials.clear()
            self._webmap_dict["operationalLayers"].clear()
        super().close()


class MapContent:
    def __init__(self, map):
        self._map = map

    def add(self, url: str, *, title="Parquet layer") -> None:
        """Add a public or signed HTTP(S) Parquet URL, without reading it in Python."""
        url = _http_url(url)
        self._add("ParquetLayer", title, {"source": {"type": "files", "urls": [url]}})

    def add_feature_service(self, url: str, *, token=None, title="Feature layer") -> None:
        """Add a FeatureServer/<layer ID> endpoint, optionally using an ArcGIS token."""
        url = _http_url(url)
        parsed = urlsplit(url)
        if not re.search(r"/FeatureServer/\d+/?$", parsed.path, re.IGNORECASE):
            raise ValueError("Use a FeatureServer URL ending in a numeric layer ID.")
        server = parsed._replace(
            path=parsed.path.rstrip("/").rsplit("/", 1)[0], query="", fragment=""
        ).geturl()
        self._add("ArcGISFeatureLayer", title, {"url": url}, token=token, server=server)

    def add_parquet_item(self, item_id: str, *, token=None, title="Parquet layer") -> None:
        """Add an ArcGIS Online Parquet item, optionally using an ArcGIS token."""
        if not isinstance(item_id, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", item_id):
            raise ValueError("Pass a 32-character ArcGIS Online item ID.")
        self._add(
            "ParquetLayer", title, {"source": {"type": "portal-item", "itemId": item_id}},
            token=token, server="https://www.arcgis.com/sharing/rest",
        )

    def _add(self, layer_type, title, source, *, token=None, server=None):
        if not isinstance(title, str):
            raise TypeError("Layer title must be a string.")
        if token is not None and (not isinstance(token, str) or not token):
            raise ValueError("Token must be a nonempty string or None.")
        if token is not None:
            self._map._credentials.append({"server": server, "token": token})
        self._map._webmap_dict["operationalLayers"].append({
            "id": uuid4().hex, "layerType": layer_type, "title": title, **source,
        })
        self._map._publish()


def _http_url(value):
    if not isinstance(value, str):
        raise TypeError("Pass an HTTP(S) URL as a string.")
    value = value.strip()
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URLs must use HTTP or HTTPS.")
    return value
