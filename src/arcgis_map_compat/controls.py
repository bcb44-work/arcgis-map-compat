from __future__ import annotations


class Legend:
    """
    The Legend describes the symbols used to represent layers
    in a map. All symbols and text used in this widget are configured
    in the Renderer of the layer. The legend will only display layers and
    sub-layers that are visible in the map.

    The legend automatically updates when
    - the visibility of a layer or sub-layer changes
    - a layer is added or removed from the map
    - a layer's renderer, opacity, or title is changed
    - the legendEnabled property is changed (set to true or false on the layer)

    .. note::
        This class should now be created by a user but rather called through the `legend` property on
        a Map instance.
    """

    def __init__(self, map) -> None:
        self._source = map

    def __str__(self) -> str:
        return "Legend"

    def __repr__(self) -> str:
        return "Legend()"

    def __setattr__(self, name, value):
        # Allow private attributes and existing properties
        if name.startswith("_") or hasattr(self.__class__, name):
            super().__setattr__(name, value)
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    @property
    def enabled(self) -> bool:
        """
        Get and set whether the legend is shown on the map/scene or not. Set to True for the
        legend to be visible.

        The Legend widget describes the symbols used to represent layers in a map.
        All symbols and text used in this widget are configured in the renderer of the layer.
        The legend will only display layers and sub-layers that are visible in the map.

        The legend automatically updates when
        - the visibility of a layer or sub-layer changes
        - a layer is added or removed from the map
        - a layer's renderer, opacity, or title is changed

        .. note::

            Known Limitations:
            - Currently, the legend widget does not support the following layer types: ElevationLayer, GraphicsLayer, IntegratedMeshLayer, KMLLayer, MapNotesLayer, OpenStreetMapLayer, VectorTileLayer, and WebTileLayer.
            - 3D symbols with more than one symbol layer are not supported.
            - DictionaryRenderer is not supported.

        """
        return self._source._show_legend

    @enabled.setter
    def enabled(self, value: bool):
        if isinstance(value, bool):
            if value != self._source._show_legend:
                # only set if it changed
                self._source._show_legend = value


class LayerList:
    """
    A class that can be used to enable the layer list widget on a rendered Map. This class is most useful when used
    inside a Jupyter Lab environment.

    .. note::
        This class should now be created by a user but rather called through the `layer_list` property on
        a Map instance.
    """

    def __init__(self, map) -> None:
        self._source = map

    def __str__(self) -> str:
        "Layer List"

    def __repr__(self) -> str:
        return "LayerList()"

    def __setattr__(self, name, value):
        # Allow private attributes and existing properties
        if name.startswith("_") or hasattr(self.__class__, name):
            super().__setattr__(name, value)
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    @property
    def enabled(self) -> bool:
        """
        The Layer List widget allows end users to quickly see the layers that are present on your map.
        It displays a list of layers, which are defined inside the Map. Set to True for the
        layer list to be visible. This property is best used inside Jupyter Lab with a rendered Map.

        .. note::
            Any changes made on the layer list widget will only be reflected in the rendered map instance, these
            will not affect the map definition. To change layer visibility in the definition, use the `layer_visibility`
            method.
        """
        return self._source._show_layer_list

    @enabled.setter
    def enabled(self, value):
        if isinstance(value, bool):
            if value != self._source._show_layer_list:
                # only set if it changed
                self._source._show_layer_list = value

