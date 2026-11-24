My goal is to create the simplest possible jupyter compatible notebook that can do two things
1. Plot layers of feature services and parquet feature layers (including parquet that's not in stored in agol and is stored in a blob store - users will just pass a signed url)
2. Support a wide variety of jupyter notebooks - this means we can't be tied to specific versions of anywidget or jupyter
    a. specifically this needs to support older versions of the databricks runtime that use ipywidget 7.x

The goal should be to assemble json for the arcgis map spec and then use the arcgis js api to render it. 

I want to be able to distribute the notebooks so we can't bundle the arcgis token or signed url into the actual html that's rendered. My plan was to use anywidget to pass it to the js after the initial load. No other interactivity is needed from python to js right now (this has way more than we need).

## Notebook usage

The public `set_*` and `add_*` methods mutate and return the same builder, so they
can be chained. `build()` returns the map widget to display:

```python
from geoanalytics_widget import MapBuilder

map_widget = (
    MapBuilder()
    .set_basemap("light")
    .set_initial_extent([-125, 24, -66, 50], sref=4326)
    .build()
)
map_widget
```

Chain `add_feature_service(url)`, `add_parquet(url)`, or `add_parquet_item(item_id)`
before `build()` to include layers. Separate, non-chained calls still work.

Use `.set_width("100%").set_height(480)` before `build()` to size the widget.
Both setters accept CSS lengths or integer pixels. The default is `100%` wide
and `630px` tall. For height relative to the browser viewport, use a value
like `"60vh"`.

## Style a layer

Click a feature to inspect its attributes. If a layer supports popups and
doesn't already have one, the widget generates it from the layer's fields.
Use `options={"popupInfo": ...}` to customize it or
`options={"disablePopup": True}` to turn it off.

Pass `options=` when adding a layer. For example, draw every point in a Parquet
item as a blue circle (use your existing `gis` and `item_id`):

```python
style = {
    "layerDefinition": {
        "drawingInfo": {
            "renderer": {
                "type": "simple",
                "symbol": {
                    "type": "esriSMS",
                    "style": "esriSMSCircle",
                    "color": [0, 120, 255, 255],
                    "size": 8,
                },
            },
        },
    },
}

MapBuilder(gis=gis).add_parquet_item(item_id, options=style).build()
```

Change `color` (red, green, blue, alpha; each 0–255) or `size` (in points).
For lines or polygons, use a matching line or fill symbol instead of a marker.
For more examples, see the [ArcGIS renderer spec](https://developers.arcgis.com/web-map-specification/objects/renderer/).