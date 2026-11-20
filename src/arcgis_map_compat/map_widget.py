from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import math
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

import anywidget

Extent = list[float] | tuple[float, float, float, float]
JSON = dict[str, Any]


@dataclass
class GIS:
    portal_url: str
    token: str | None = field(repr=False)


class MapBuilder:
    def __init__(self, gis: GIS | None = None) -> None:
        self._gis = gis
        self._initial_state: tuple[Extent, int] | None = None
        self._layers: list[JSON] = []
        self._credentials: list[JSON] = []

    def set_initial_state(self, extent: Extent, sref: int) -> None:
        self._initial_state = (extent, sref)

    def build(self) -> Map:
        definition: JSON = {
            "version": "2.37",
            "baseMap": {
                "title": "Topographic",
                "baseMapLayers": [{
                    "id": "topographic",
                    "layerType": "ArcGISTiledMapServiceLayer",
                    "url": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
                }],
            },
            "operationalLayers": self._layers,
        }
        if self._initial_state is not None:
            extent, sref = self._initial_state
            if not isinstance(extent, (list, tuple)) or len(extent) != 4:
                raise ValueError("Extent must be [xmin, ymin, xmax, ymax].")
            if not all(
                isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)
                for n in extent
            ):
                raise ValueError("Extent coordinates must be finite numbers.")
            xmin, ymin, xmax, ymax = extent
            if xmin > xmax or ymin > ymax:
                raise ValueError("Extent minimums must not exceed maximums.")
            if not isinstance(sref, int) or isinstance(sref, bool) or sref <= 0:
                raise ValueError("sref must be a positive WKID.")
            definition["initialState"] = {"viewpoint": {"targetGeometry": {
                "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax,
                "spatialReference": {"wkid": sref},
            }}}
        return Map(
            definition, self._credentials,
            self._gis.portal_url if self._gis is not None else None,
        )

    def add_parquet(
        self, url: str | list[str], *, title: str = "Parquet layer", options: JSON | None = None,
    ) -> None:
        """Add a public or signed HTTP(S) Parquet URL, without reading it in Python."""
        urls = [url] if isinstance(url, str) else url
        if not isinstance(urls, list):
            raise TypeError("Pass a URL or a list of URLs.")
        if not urls:
            raise ValueError("Pass at least one Parquet URL.")
        urls = [_http_url(value) for value in urls]
        self._add_layer(
            "ParquetLayer", title, {"source": {"type": "files", "urls": urls}}, options=options,
        )

    def add_feature_service(
        self, url: str, *, gis: GIS | None = None, title: str = "Feature layer",
        options: JSON | None = None,
    ) -> None:
        """Add a FeatureServer/<layer ID> endpoint, optionally using an ArcGIS token."""
        url = _http_url(url)
        parsed = urlsplit(url)
        if not re.search(r"/FeatureServer/\d+/?$", parsed.path, re.IGNORECASE):
            raise ValueError("Use a FeatureServer URL ending in a numeric layer ID.")
        server = parsed._replace(
            path=parsed.path.rstrip("/").rsplit("/", 1)[0], query="", fragment=""
        ).geturl()
        gis = gis if gis is not None else self._gis
        self._add_layer(
            "ArcGISFeatureLayer", title, {"url": url},
            token=gis.token if gis is not None else None, server=server, options=options,
        )

    def add_parquet_item(
        self, item_id: str, *, title: str = "Parquet layer", options: JSON | None = None,
    ) -> None:
        """Add an ArcGIS Online Parquet item, optionally using an ArcGIS token."""
        if not isinstance(item_id, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", item_id):
            raise ValueError("Pass a 32-character ArcGIS Online item ID.")
        self._add_layer(
            "ParquetLayer", title, {"source": {"type": "portal-item", "itemId": item_id}},
            token=self._gis.token if self._gis is not None else None,
            server=self._gis.portal_url.rstrip("/") + "/sharing/rest" if self._gis is not None else None,
            options=options,
        )

    def _add_layer(
        self, layer_type: str, title: str, source: JSON, *,
        token: str | None = None, server: str | None = None,
        options: JSON | None = None,
    ) -> None:
        if not isinstance(title, str):
            raise TypeError("Layer title must be a string.")
        if token is not None and (not isinstance(token, str) or not token):
            raise ValueError("Token must be a nonempty string or None.")
        if token is not None:
            self._credentials.append({"server": server, "token": token})
        self._layers.append({
            "id": uuid4().hex, "layerType": layer_type, "title": title, **source, **(options or {}),
        })


class Map(anywidget.AnyWidget):
    _esm = Path(__file__).parent / "map.js"

    def __init__(self, definition: JSON, credentials: list[JSON], portal_url: str | None) -> None:
        super().__init__()
        self._webmap_dict = deepcopy(definition)
        self._credentials = deepcopy(credentials)
        self._portal_url = portal_url
        self._published = False
        self.on_msg(self._on_message)

    def _on_message(
        self, widget: anywidget.AnyWidget, content: JSON, buffers: list[memoryview],
    ) -> None:
        if content.get("type") == "ready" and not self._published:
            self._published = True
            self.on_msg(self._on_message, remove=True)
            self.send({
                "type": "map",
                "definition": deepcopy(self._webmap_dict),
                "credentials": deepcopy(self._credentials),
                "portal_url": self._portal_url,
            })

    def close(self) -> None:
        if hasattr(self, "_credentials"):
            self._credentials.clear()
            self._webmap_dict["operationalLayers"].clear()
        super().close()


def _http_url(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("Pass an HTTP(S) URL as a string.")
    value = value.strip()
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URLs must use HTTP or HTTPS.")
    return value
