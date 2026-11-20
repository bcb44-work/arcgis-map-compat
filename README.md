# Parquet URL notebook map

A reduced version of the supplied widget for creating a map and displaying
Parquet layers from HTTP(S) URLs. Python sends layer definitions to the browser.
The ArcGIS Maps SDK for JavaScript reads and renders the files.

## Install

Install the included wheel in the same Python environment as the notebook:

```sh
python -m pip install dist/arcgis_map_compat-0.2.0-py3-none-any.whl
```

On Databricks, upload the wheel to your usual package location and install it
with `%pip install /path/to/arcgis_map_compat-0.2.0-py3-none-any.whl`. Restart
Python if the notebook environment requires it.

Direct Python dependencies are `anywidget`, `ipywidgets`, and `traitlets`.
Their own transitive dependencies are installed normally. The requirement
`ipywidgets>=7.7.2,<9` accepts compatible versions already provided by the runtime.
Use Python 3.10 or newer.

## Use

```python
from arcgis_map_compat import Map

m = Map()
m.center = [46.8, 7.16]  # latitude, longitude, matching the current widget
m.zoom = 12
m.content.add("https://example.com/data.parquet")
m
```

Run another cell to add another layer to the displayed map:

```python
m.content.add("https://example.com/another.parquet?signature=...")
```

The URL is passed through with its query string. URLs with an endpoint path
instead of a `.parquet` filename also work when they serve valid Parquet data.
Use the map's + and − controls to zoom.

## Implementation

The frontend is a reduction of the existing React MapWidgetView. It keeps
anywidget's React model hooks, the ArcGIS CDN loader, `arcgis-map`, `arcgis-zoom`,
the `_view_state` binding, and `_webmap_dict` consumed by `WebMap.fromJSON()`.
The internal WebMap JSON is a small transport dictionary. The Python backend
uses dictionaries directly.

The generated Python models, GIS context adapter, general layer APIs and
additional frontend controls have been removed. The public workflow is
`Map()`, optional initial `center` and `zoom`, and `content.add(url)`.
The local-image/raster-to-media-layer workflow is not supported.

The frame wrapper from the previous compatibility build is retained to isolate
notebook AMD loaders from the ArcGIS CDN. React and its anywidget adapter are
bundled in the frontend. Python installation uses the prebuilt assets.

This temporary distribution keeps the `arcgis_map_compat` namespace to coexist
with the standard package. `RETAINED_FILES.patch` shows edits to retained source
files and new source additions compared with the original uploaded `map/` tree.

## Data access

Use browser-accessible public or signed URLs. The browser must reach the SDK CDN,
basemap services and Parquet endpoint. A cross-origin data server needs CORS and
support for byte-range reads. Driver-only paths such as DBFS paths need to be
exposed through a browser-readable URL first.

The SDK's ParquetLayer supports spatial data in WGS84 or Web Mercator with
Snappy, GZIP, or uncompressed Parquet. Geometry can be inferred from GeoParquet
metadata or recognized latitude/longitude columns.

Databricks rendering still needs a check in the target workspace. Its custom
widget support and installed widget version are separate from Python package
installation. `example.ipynb` provides that check after replacing its URL.

## Validation

Local browser checks pass on ipywidgets 7.7.2 and 7.8.1 with classic Jupyter,
and 8.1.9 with JupyterLab 4. They cover the initial map view, Parquet URL
loading, zooming, and another URL added from a later Python cell. Python
regression checks block imports of arcgis, pandas, Pydantic, GeoPandas and
PyArrow. An occasional SDK startup message, `Host is not attached.`, occurs
in classic Jupyter while these behavior checks still pass.

Actual Databricks workspace rendering remains to be validated.

## Development

The frontend build is reproducible from the included source:

```sh
npm ci
npm run build
python -m pip wheel --no-deps . -w dist
```

Node.js and npm are development tools. The wheel includes the compiled frontend.
The ArcGIS SDK is loaded from the existing 5.1 CDN configuration at runtime.

Run the Python regression checks with:

```sh
python -m unittest discover -s tests -v
```
