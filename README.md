# Minimal notebook map

A small Python/JavaScript widget for feature-service layers, Parquet URLs
(including signed blob-store URLs), and ArcGIS Online Parquet items.
No React, frontend build, or ArcGIS Python dependency.

## Install

Use Python 3.10+ in the notebook's environment:

```sh
uv venv
uv pip install -e .
```

For distribution, build a wheel with `uv build --wheel`, then install it in the
target notebook environment. On Databricks use `%pip install /path/to/wheel.whl`
and restart Python if required.

Dependencies are anywidget and ipywidgets; their transitive dependencies include
traitlets. Supports **ipywidgets 7.7.2 through 8.x**, including **anywidget 0.7.1**.
Installation does not require upgrading a compatible installed widget version.
The notebook frontend must also support custom widgets; installing Python
packages cannot enable missing frontend support.

## Use

```python
import os
from arcgis_map_compat import Map

m = Map()
m.center = [46.8, 7.16]  # latitude, longitude
m.zoom = 12
m.content.add(os.environ["PARQUET_URL"])  # public or signed URL
m
```

For other sources:

```python
m.content.add_feature_service(
    os.environ["FEATURE_SERVICE_URL"],  # .../FeatureServer/0
    token=os.environ.get("ARCGIS_TOKEN"),  # omit for public services
)
m.content.add_parquet_item(
    os.environ["PARQUET_ITEM_ID"],  # 32-character ArcGIS Online item ID
    token=os.environ.get("ARCGIS_TOKEN"),
)
```

All three methods accept an optional `title`. Additions from later Python cells
preserve browser pan/zoom. Setting `center` or `zoom` explicitly moves the map;
their Python values do not track browser navigation.

## Sharing and credentials

**Map definitions, signed URLs, and tokens are not synchronized widget traits.**
Python keeps them in memory and sends the complete WebMap JSON through a custom
message when the renderer requests it. Updates use the same message channel.
The iframe HTML contains only static renderer code.

Saved widget state and exported HTML contain no runtime map definition or
credentials. They cannot independently replay the map: recipients must rerun
the notebook with their own data access. Without a live kernel the renderer
displays a waiting message.

Obtain credentials from environment variables or a notebook secret store.
This does not remove secrets you put in notebook source, print in outputs, or
expose through other logging. The live browser necessarily receives credentials
and downloaded data. SDK/network diagnostics can contain request URLs.

Tokens are scoped to a feature service or ArcGIS Online's sharing endpoint.
Use one credential per service per map. Automatic token renewal, signed-URL
refresh, layer editing/removal, enterprise portal items, and Python GIS objects
are deliberately out of scope. Create a new map with fresh credentials when
access expires.

## Browser requirements

The browser must reach the ArcGIS 5.1 CDN, basemap services, and data endpoints.
The SDK runs in an iframe to avoid notebook AMD-loader conflicts. The host must
permit same-origin iframe access, inline scripts, and SDK modules.

Blob storage needs CORS and byte-range support. Driver-only DBFS paths are not
browser URLs. Parquet must contain supported spatial geometry, use WGS84 or
Web Mercator, and use Snappy, GZIP, or no compression. Layer failures show a
generic message without echoing URLs or tokens.

Actual Databricks workspace rendering must still be checked on the target
runtime; local widget-version compatibility is not a substitute.

## Development checks

```sh
uv pip install playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python -m unittest discover -s tests -v
ARCGIS_BROWSER_LIVE=1 .venv/bin/python -m unittest discover -s tests -v
```

The optional live check uses the real CDN SDK against controlled feature-service,
signed-URL Parquet, and AGOL item responses. `tests/points.parquet` is a tiny
two-point GeoParquet fixture; reading it in Python requires no Parquet library.
The app has no JavaScript build step or Node dependencies.
