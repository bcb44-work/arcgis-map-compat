from __future__ import annotations

from pydantic import Field, ConfigDict
from arcgis_map_compat.dataclasses.models.base_model import BaseModel
from arcgis_map_compat.dataclasses.enums.layers import BlendMode, ListMode


class LayerOptions(BaseModel):
    """
    A model representing the options for a layer in a map.
    This model is used to configure various properties of a layer,
    such as its title, visibility, opacity, and other display
    settings that can be defined when adding or updating a layer on the map.

    For more information on the available options and their usage, refer to the `ArcGIS Maps SDK for Javascript layers <https://developers.arcgis.com/javascript/latest/references/core/layers/Layer/>`_ documentation.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        use_enum_values=True,
    )

    blend_mode: BlendMode | None = Field(
        None,
        alias="blendMode",
        description="Blend modes are used to create various effects by blending colors of top and background layers.",
    )
    disable_popup: bool | None = Field(
        None,
        alias="disablePopup",
        description="Whether to disable popups for the layer.",
    )
    list_mode: ListMode | None = Field(
        None,
        alias="listMode",
        description="To show or hide the sublayer in the layer list. If the layer has sublayers, selecting `hide-children` will hide them in the layer list.",
    )
    max_scale: float | None = Field(
        None,
        alias="maxScale",
        description="The maximum scale at which the layer is visible.",
    )
    min_scale: float | None = Field(
        None,
        alias="minScale",
        description="The minimum scale at which the layer is visible.",
    )
    opacity: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="The opacity of the layer, ranging from 0.0 (fully transparent) to 1.0 (fully opaque).",
    )
    refresh_interval: float | None = Field(
        None,
        alias="refreshInterval",
        description="Refresh interval of the layer in minutes. Non-zero value indicates automatic layer refresh at the specified interval. Value of 0 indicates auto refresh is not enabled.",
    )
    show_labels: bool | None = Field(
        None,
        alias="showLabels",
        description="Whether to show labels for the layer. Labels will display if this is set to True.",
    )
    show_legend: bool | None = Field(
        None,
        alias="showLegend",
        description="Whether to show the layer in the Map or Scene legend.",
    )
    time_animation: bool | None = Field(
        None,
        alias="timeAnimation",
        description="Whether to enable time animation for the layer if the layer supports it.",
    )
    title: str | None = Field(
        None,
        description="The title of the layer as it appears in the layer list and legend.",
    )
    visibility: bool | None = Field(
        None, description="Whether the layer is visible in the Map or Scene."
    )
