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


@dataclass
class Basemap:
    """Single-layer basemap; use url for tile services or style_url for vector styles.

    Options override layer fields without validation.
    Specs: https://developers.arcgis.com/web-map-specification/objects/baseMap/
    https://developers.arcgis.com/web-map-specification/objects/baseMapLayer/
    https://developers.arcgis.com/web-map-specification/objects/vectorTileLayer/
    """
    title: str
    layer_type: str
    url: str | None = None
    style_url: str | None = None
    opacity: float | None = None
    visibility: bool | None = None
    options: JSON | None = None
    id: str = field(default_factory=lambda: uuid4().hex)


# Presets omit separate reference-label layers. Streets and OSM retain built-in labels.
# https://developers.arcgis.com/web-map-specification/objects/baseMapLayer/
# https://developers.arcgis.com/web-map-specification/objects/vectorTileLayer/
_BASEMAPS = {
    name: Basemap(
        title=title, id=name, layer_type=layer_type,
        url=url if layer_type == "ArcGISTiledMapServiceLayer" else None,
        style_url=url if layer_type == "VectorTileLayer" else None,
    )
    for name, title, layer_type, url in [
        ("light", "Light Gray Canvas", "ArcGISTiledMapServiceLayer",
         "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer"),
        ("dark", "Dark Gray Canvas", "ArcGISTiledMapServiceLayer",
         "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer"),
        ("streets", "Esri Streets Basemap", "ArcGISTiledMapServiceLayer",
         "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer"),
        ("osm", "OpenStreetMap Vector Basemap", "VectorTileLayer",
         "https://basemaps.arcgis.com/arcgis/rest/services/OpenStreetMap_v2/VectorTileServer/resources/styles/root.json"),
    ]
}


class MapBuilder:
    """Collect map inputs; public set_* and add_* methods return this builder."""

    def __init__(self, gis: GIS | None = None, *, basemap: str | Basemap | None = None) -> None:
        """Collect Web Map inputs; GIS provides runtime context, not JSON fields.

        Spec: https://developers.arcgis.com/web-map-specification/objects/webmap/
        """
        self._gis = gis
        self._initial_state: tuple[Extent, int] | None = None
        self._basemap: str | Basemap = Basemap(
            title="Topographic",
            id="topographic",
            layer_type="ArcGISTiledMapServiceLayer",
            url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
        )
        self._layers: list[JSON] = []
        self._credentials: list[tuple[str | None, GIS]] = []
        if basemap is not None:
            self.set_basemap(basemap)

    def set_basemap(self, basemap: str | Basemap) -> MapBuilder:
        """Store light, dark, streets, osm, or an unvalidated custom Basemap.

        Presets omit separate reference-label layers, not labels built into styles.
        Spec: https://developers.arcgis.com/web-map-specification/objects/baseMap/
        """
        if isinstance(basemap, str) and basemap not in _BASEMAPS:
            raise ValueError("Choose a basemap from: light, dark, streets, osm.")
        self._basemap = basemap
        return self

    def set_initial_extent(self, extent: Extent, sref: int) -> MapBuilder:
        """Store [xmin, ymin, xmax, ymax] and its WKID for the initial viewpoint.

        JSON assembly is deferred until build().
        Specs: https://developers.arcgis.com/web-map-specification/objects/initialState/
        https://developers.arcgis.com/web-map-specification/objects/extent/
        """
        self._initial_state = (extent, sref)
        return self

    def build(self) -> Map:
        """Assemble Web Map JSON with the configured basemap and operational layers.

        Specs: https://developers.arcgis.com/web-map-specification/objects/webmap/
        https://developers.arcgis.com/web-map-specification/objects/baseMap/
        https://developers.arcgis.com/web-map-specification/objects/tiledMapServiceLayer/
        """
        credentials: list[JSON] = []
        for server, gis in self._credentials:
            if gis.token is not None:
                if not isinstance(gis.token, str) or not gis.token:
                    raise ValueError("Token must be a nonempty string or None.")
                # Portal scopes resolve from the current GIS; service scopes stay per endpoint.
                credentials.append({
                    "server": server if server is not None else gis.portal_url.rstrip("/") + "/sharing/rest",
                    "token": gis.token,
                })
        basemap = _BASEMAPS[self._basemap] if isinstance(self._basemap, str) else self._basemap
        basemap_layer = {
            **{key: value for key, value in {
                "id": basemap.id, "layerType": basemap.layer_type,
                "url": basemap.url, "styleUrl": basemap.style_url, "title": basemap.title,
                "opacity": basemap.opacity, "visibility": basemap.visibility,
            }.items() if value is not None},
            **(basemap.options or {}),
        }
        definition: JSON = {
            "version": "2.37",
            "baseMap": {
                "title": basemap.title, "baseMapLayers": [basemap_layer],
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
            # Without scale, the SDK fits targetGeometry; the WKID describes its coordinates.
            # https://developers.arcgis.com/web-map-specification/objects/viewpoint/
            definition["initialState"] = {"viewpoint": {"targetGeometry": {
                "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax,
                "spatialReference": {"wkid": sref},
            }}}
        return Map(
            definition, credentials,
            self._gis.portal_url if self._gis is not None else None,
        )

    def add_parquet(
        self, url: str | list[str], *, title: str = "Parquet layer", options: JSON | None = None,
    ) -> MapBuilder:
        """Add one ParquetLayer with a files source; JavaScript reads the URLs.

        Specs: https://developers.arcgis.com/web-map-specification/objects/parquetLayer/
        https://developers.arcgis.com/web-map-specification/objects/parquetSourceFiles/
        """
        urls = [url] if isinstance(url, str) else url
        if not isinstance(urls, list):
            raise TypeError("Pass a URL or a list of URLs.")
        if not urls:
            raise ValueError("Pass at least one Parquet URL.")
        urls = [_http_url(value) for value in urls]
        self._add_layer(
            "ParquetLayer", title, {"source": {"type": "files", "urls": urls}}, options=options,
        )
        return self

    def add_feature_service(
        self, url: str, *, gis: GIS | None = None, title: str = "Feature layer",
        options: JSON | None = None,
    ) -> MapBuilder:
        """Add an ArcGISFeatureLayer using its service URL; keep tokens outside JSON.

        Spec: https://developers.arcgis.com/web-map-specification/objects/featureLayer/
        """
        url = _http_url(url)
        if not re.search(r"/FeatureServer/\d+/?$", urlsplit(url).path, re.IGNORECASE):
            raise ValueError("Use a FeatureServer URL ending in a numeric layer ID.")
        parsed = urlsplit(url)
        server = parsed._replace(
            path=parsed.path.rstrip("/").rsplit("/", 1)[0], query="", fragment="",
        ).geturl()
        self._add_layer(
            "ArcGISFeatureLayer", title, {"url": url},
            gis=gis if gis is not None else self._gis, server=server, options=options,
        )
        return self

    def add_parquet_item(
        self, item_id: str, *, title: str = "Parquet layer", options: JSON | None = None,
    ) -> MapBuilder:
        """Add a ParquetLayer with a portal-item source resolved in the builder's portal.

        The source contains itemId, not a per-layer portal URL.
        Specs: https://developers.arcgis.com/web-map-specification/objects/parquetLayer/
        https://developers.arcgis.com/web-map-specification/objects/parquetSourcePortalItem/
        """
        if not isinstance(item_id, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", item_id):
            raise ValueError("Pass a 32-character ArcGIS Online item ID.")
        self._add_layer(
            "ParquetLayer", title, {"source": {"type": "portal-item", "itemId": item_id}},
            gis=self._gis, options=options,
        )
        return self

    def _add_layer(
        self, layer_type: str, title: str, source: JSON, *,
        gis: GIS | None = None, server: str | None = None, options: JSON | None = None,
    ) -> None:
        """Append layer JSON, retaining its GIS separately until build().

        Options overwrite fields without validation or a recursive merge.
        Spec: https://developers.arcgis.com/web-map-specification/objects/operationalLayers/
        """
        if not isinstance(title, str):
            raise TypeError("Layer title must be a string.")
        if gis is not None and gis.token is not None and (
            not isinstance(gis.token, str) or not gis.token
        ):
            raise ValueError("Token must be a nonempty string or None.")
        if gis is not None:
            self._credentials.append((server, gis))
        self._layers.append({
            "id": uuid4().hex, "layerType": layer_type, "title": title, **source, **(options or {}),
        })


class Map(anywidget.AnyWidget):
    _esm = Path(__file__).parent / "map.js"

    def __init__(self, definition: JSON, credentials: list[JSON], portal_url: str | None) -> None:
        """Snapshot Web Map JSON separately from runtime credentials and portal context.

        Spec: https://developers.arcgis.com/web-map-specification/objects/webmap/
        """
        super().__init__()
        self._webmap_dict = deepcopy(definition)
        self._credentials = deepcopy(credentials)
        self._portal_url = portal_url
        self._published = False
        self.on_msg(self._on_message)

    def _on_message(
        self, widget: anywidget.AnyWidget, content: JSON, buffers: list[memoryview],
    ) -> None:
        """Publish the Web Map snapshot once, after JavaScript is ready.

        Only definition is Web Map JSON; the surrounding message is widget transport.
        Spec: https://developers.arcgis.com/web-map-specification/objects/webmap/
        """
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
        """Release local credentials and operationalLayers, without editing the JS map.

        Spec: https://developers.arcgis.com/web-map-specification/objects/operationalLayers/
        """
        if hasattr(self, "_credentials"):
            self._credentials.clear()
            self._webmap_dict["operationalLayers"].clear()
        super().close()


def _http_url(value: str) -> str:
    """Check source URLs before constructing layers, not the layer JSON schema.

    Specs: https://developers.arcgis.com/web-map-specification/objects/featureLayer/
    https://developers.arcgis.com/web-map-specification/objects/parquetSourceFiles/
    """
    if not isinstance(value, str):
        raise TypeError("Pass an HTTP(S) URL as a string.")
    value = value.strip()
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URLs must use HTTP or HTTPS.")
    return value
