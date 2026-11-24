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