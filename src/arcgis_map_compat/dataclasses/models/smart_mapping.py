from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from arcgis_map_compat.dataclasses.enums.renderers import Focus, UnivariateTheme
from arcgis_map_compat.dataclasses.models.base_model import BaseModel, common_config
from arcgis_map_compat.dataclasses.enums.renderers import UnivariateSymbolStyle
from arcgis_map_compat.dataclasses.models.renderers import AttributeColorInfo, LegendOptions
from arcgis_map_compat.dataclasses.models.symbols import Outline
from pydantic import Field, field_validator, model_validator


class SmartMappingParams(BaseModel):
    model_config = common_config


class RelationshipField(SmartMappingParams):
    field: str = Field(
        ..., description="Name of the numeric field used in the relationship renderer."
    )
    normalization_field: str | None = Field(
        default=None,
        alias="normalizationField",
        description="Field used to normalize the main relationship field values before classification.",
    )
    max_value: float | int | None = Field(
        default=None,
        alias="maxValue",
        description="Custom upper bound used with min_value to constrain statistics and class breaks.",
    )
    min_value: float | int | None = Field(
        default=None,
        alias="minValue",
        description="Custom lower bound used with max_value to constrain statistics and class breaks.",
    )
    label: str | None = Field(
        default=None,
        description="Display label used for this field in relationship legend and UI text.",
    )


class Statistics(SmartMappingParams):
    average: float | int | None = Field(
        default=None, description="Average value from the field statistics query."
    )
    count: int | None = Field(
        default=None, description="Number of features included in the statistics query."
    )
    max: float | int | None = Field(
        default=None, description="Maximum value observed in the queried data."
    )
    min: float | int | None = Field(
        default=None, description="Minimum value observed in the queried data."
    )
    median: float | int | None = Field(
        default=None, description="Median value from the queried distribution."
    )
    stddev: float | int | None = Field(
        default=None, description="Standard deviation of the queried values."
    )
    sum: float | int | None = Field(
        default=None, description="Sum of all queried values."
    )
    variance: float | int | None = Field(
        default=None, description="Variance of the queried values."
    )
    null_count: int | None = Field(
        default=None,
        alias="nullCount",
        description="Count of features where the target value is null.",
    )


class Scheme(SmartMappingParams):
    name: str | None = Field(
        default=None, description="Display name of the predefined smart-mapping scheme."
    )
    tags: list[str] | None = Field(
        default=None,
        description="Tags describing scheme purpose (for example, theme or color family).",
    )
    id: str | None = Field(
        default=None,
        description="Unique identifier for the scheme in the JavaScript API.",
    )
    colors: list[Any] | None = Field(
        default=None,
        description="Ordered RGBA color entries used as the smart-mapping ramp for the renderer.",
    )
    outline: Outline | None = Field(
        default=None,
        description="Outline symbol configuration returned by some polygon-oriented scheme generators.",
    )
    opacity: float | int | None = Field(
        default=None,
        description="Opacity value included by the scheme for supported renderer/symbol outputs.",
    )
    size: float | int | None = Field(
        default=None,
        description="Default symbol size supplied by size-aware smart-mapping schemes.",
    )
    color_for_others_category: list[Any] | None = Field(
        default=None,
        alias="colorForOthersCategory",
        description='RGBA color assigned to the aggregated "others" category in supported categorical schemes.',
    )


class ColorOptions(SmartMappingParams):
    color_scheme: dict[str, Any] | None = Field(
        default=None,
        alias="colorScheme",
        description="Color scheme dictionary for the color portion of the visualization; schema depends on layer type and renderer context.",
    )
    is_continuous: bool | None = Field(
        default=None,
        alias="isContinuous",
        description="If true, treats the color scheme as a continuous ramp instead of discrete classes.",
    )


class SizeOptions(SmartMappingParams):
    size_scheme: dict[str, Any] | None = Field(
        default=None,
        alias="sizeScheme",
        description="Size scheme dictionary for the size portion of the visualization; structure varies by layer geometry/type.",
    )
    size_optimization_enabled: bool | None = Field(
        default=None,
        alias="sizeOptimizationEnabled",
        description="Enables view-scale optimization for symbol sizes when supported by the layer type.",
    )


class SymbolOptions(SmartMappingParams):
    symbol_style: UnivariateSymbolStyle | str | None = Field(
        default=None,
        alias="symbolStyle",
        description='Named symbol style for "above-and-below" themes. Common values: "caret", "circle-caret", "arrow", "circle-arrow", "plus-minus", "circle-plus-minus", "square", "circle", "triangle", "happy-sad", "thumb".',
    )
    symbols: dict[str, Any] | None = Field(
        default=None,
        description='Custom symbols keyed by semantic role (for example, "above" and "below"); expected symbol dictionaries depend on layer geometry/type.',
    )


class CategoryAttribute(SmartMappingParams):
    field: str | None = Field(
        default=None,
        description="Numeric field used for a dot-density category or pie slice; ignored when value_expression is set.",
    )
    label: str | None = Field(
        default=None, description="Display label shown in the legend for this category."
    )
    value_expression: str | None = Field(
        default=None,
        alias="valueExpression",
        description="Arcade expression (Visualization profile) that returns a numeric value for this category.",
    )
    value_expression_title: str | None = Field(
        default=None,
        alias="valueExpressionTitle",
        description="Legend label used to describe the value_expression.",
    )


class PredominanceField(SmartMappingParams):
    name: str = Field(
        ...,
        description="Name of a numeric field competing in the predominance calculation.",
    )
    label: str | None = Field(
        default=None, description="Optional legend label for the predominance field."
    )


class RelationshipClassificationMethod(str, Enum):
    QUANTILE = "quantile"
    EQUAL_INTERVAL = "equal-interval"
    NATURAL_BREAKS = "natural-breaks"


class PieChartShape(str, Enum):
    PIE = "pie"
    DONUT = "donut"


class PredominanceSortBy(str, Enum):
    COUNT = "count"
    VALUE = "value"


class ClassBreaksType(str, Enum):
    SIZE = "classBreaksSize"
    COLOR = "classBreaksColor"


class ClassBreaksNormalizationType(str, Enum):
    LOG = "log"
    PERCENT_OF_TOTAL = "percent-of-total"
    FIELD = "field"


class ClassBreaksClassificationMethod(str, Enum):
    EQUAL_INTERVAL = "equal-interval"
    NATURAL_BREAKS = "natural-breaks"
    QUANTILE = "quantile"
    STANDARD_DEVIATION = "standard-deviation"


class UniqueValuesSortBy(str, Enum):
    COUNT = "count"
    VALUE = "value"
    NONE = "none"


class RelationshipRendererParams(SmartMappingParams):
    """
    Parameters for generating a relationship renderer from two numeric fields in a bivariate choropleth visualization.

    .. note::
        When calling the smart mapping method `create_renderer` the output for this renderer type is a :class:`arcgis.map.renderers.PredominanceRenderer` object.
    """

    type: Literal["relationship"] = Field(
        default="relationship",
        description="Renderer type identifier used by the JavaScript API.",
    )
    symbol_type: Literal["2d"] = Field(
        default="2d",
        alias="symbolType",
        description="Symbol type identifier used by the JavaScript API.",
    )
    field1: RelationshipField = Field(
        ...,
        description="A numeric field definition used on the vertical axis of the relationship legend.",
    )
    field2: RelationshipField = Field(
        ...,
        description="A numeric field definition used on the horizontal axis of the relationship legend.",
    )
    classification_method: RelationshipClassificationMethod | str | None = Field(
        default="quantile",
        alias="classificationMethod",
        description='The method for classifying each field\'s data values ("quantile", "equal-interval", "natural-breaks").',
    )
    focus: Focus | str | None = Field(
        default=None,
        description='Legend orientation hint. Accepted values are None, "HH", "HL", "LH", and "LL".',
    )
    num_classes: int | None = Field(
        default=3,
        alias="numClasses",
        description="Number of classes used to break each field. Supported values are 2, 3, or 4.",
    )
    outline_optimization_enabled: bool = Field(
        default=False,
        alias="outlineOptimizationEnabled",
        description="For polygon layers, indicates whether polygon outline width should vary by view scale.",
    )
    size_optimization_enabled: bool = Field(
        default=False,
        alias="sizeOptimizationEnabled",
        description="For point and polyline layers, indicates whether symbol sizes should vary by view scale.",
    )
    legend_options: LegendOptions | None = Field(
        default=None,
        alias="legendOptions",
        description="Options for modifying legend properties describing the relationship visualization.",
    )
    relationship_scheme: Scheme | None = Field(
        default=None,
        alias="relationshipScheme",
        description="A predefined relationship scheme used instead of generating one from the map background.",
    )
    default_symbol_enabled: bool = Field(
        default=True,
        alias="defaultSymbolEnabled",
        description="Enables a default symbol for features with null or out-of-range values.",
    )
    for_binning: bool | None = Field(
        default=None,
        alias="forBinning",
        description="Indicates whether the renderer is for binning and uses aggregate featureReduction fields.",
    )


class UnivariateColorSizeRendererParams(SmartMappingParams):
    """
    Parameters for generating a univariate color-and-size renderer for quantitative data visualization.

    .. note::
        When calling the smart mapping method `create_renderer` the output for this renderer type is a :class:`arcgis.map.renderers.ClassBreaksRenderer` object.
    """

    type: Literal["univariateColorSize"] = Field(
        default="univariateColorSize",
        description="Renderer type identifier used by the JavaScript API.",
    )
    symbol_type: Literal["2d"] = Field(
        default="2d",
        alias="symbolType",
        description="Symbol type identifier used by the JavaScript API.",
    )
    field: str | None = Field(
        default=None,
        description="Field used for statistics and data-driven visualization; ignored when value_expression is set.",
    )
    normalization_field: str | None = Field(
        default=None,
        alias="normalizationField",
        description="Field used to normalize the primary field values.",
    )
    value_expression: str | None = Field(
        default=None,
        alias="valueExpression",
        description="Arcade expression (Visualization profile) returning a numeric value; overrides field.",
    )
    value_expression_title: str | None = Field(
        default=None,
        alias="valueExpressionTitle",
        description="Legend title for the value_expression.",
    )
    theme: UnivariateTheme | str | None = Field(
        default="high-to-low",
        description='Theme controlling color/size stops. Values: "high-to-low", "above", "below", "above-and-below".',
    )
    sql_expression: str | None = Field(
        default=None,
        alias="sqlExpression",
        description="SQL expression that evaluates to a number.",
    )
    sql_where: str | None = Field(
        default=None,
        alias="sqlWhere",
        description="SQL where clause used to filter features for statistics queries.",
    )
    statistics: Statistics | None = Field(
        default=None,
        description="Precomputed field statistics to avoid an additional server query.",
    )
    min_value: int | None = Field(
        default=None,
        alias="minValue",
        description="Custom lower bound used to generate statistics and visual variable stops.",
    )
    max_value: int | None = Field(
        default=None,
        alias="maxValue",
        description="Custom upper bound used to generate statistics and visual variable stops.",
    )
    default_symbol_enabled: bool | None = Field(
        default=None,
        alias="defaultSymbolEnabled",
        description="Enables a default symbol for features with null or out-of-range values.",
    )
    color_options: ColorOptions | None = Field(
        default=None,
        alias="colorOptions",
        description="Options for configuring the color portion of the visualization.",
    )
    size_options: SizeOptions | None = Field(
        default=None,
        alias="sizeOptions",
        description="Options for configuring the size portion of the visualization.",
    )
    symbol_options: SymbolOptions | None = Field(
        default=None,
        alias="symbolOptions",
        description="Symbol options used primarily with the above-and-below theme.",
    )
    legend_options: LegendOptions | None = Field(
        default=None,
        alias="legendOptions",
        description="Options for configuring legend display.",
    )
    for_binning: bool | None = Field(
        default=None,
        alias="forBinning",
        description="Indicates whether the renderer is for binning and uses aggregate featureReduction fields.",
    )


class HeatmapRendererParams(SmartMappingParams):
    """Parameters for generating a heatmap renderer that visualizes point density as a raster surface."""

    type: Literal["heatmap"] = Field(
        default="heatmap",
        description="Renderer type identifier used by the JavaScript API.",
    )
    field: str | None = Field(
        default=None,
        description="Numeric field used as a multiplier in heatmap density calculations.",
    )
    scheme: Scheme | None = Field(
        default=None,
        alias="heatmapScheme",
        description="Predefined heatmap scheme used instead of generating one from map background.",
    )
    statistics: Statistics | None = Field(
        default=None,
        description="Precomputed field statistics to avoid an additional server query.",
    )
    fade_ratio: float | None = Field(
        default=None,
        alias="fadeRatio",
        description="Amount of fading applied to lower color stops to create a fuzzy boundary at the heatmap edge.",
    )
    fade_to_transparent: bool = Field(
        default=True,
        alias="fadeToTransparent",
        description="If True, lower color stops fade to transparent at the heatmap edge; if False, fade_ratio is ignored.",
    )
    radius: int | None = Field(
        default=None,
        description="Radius in points defining each point feature's area of influence.",
    )
    min_ratio: float | None = Field(
        default=None,
        alias="minRatio",
        description="Minimum ratio used to normalize heatmap intensity values.",
    )
    max_ratio: float | None = Field(
        default=None,
        alias="maxRatio",
        description="Maximum ratio used to normalize heatmap intensity values.",
    )


class DotDensityRendererParams(SmartMappingParams):
    """Parameters for generating a dot-density renderer for polygon layers using complementary numeric attributes."""

    type: Literal["dotDensity"] = Field(
        default="dotDensity",
        description="Renderer type identifier used by the JavaScript API.",
    )
    attributes: list[AttributeColorInfo] = Field(
        ...,
        description="List of complementary numeric field/expression definitions used as dot-density categories.",
    )
    dot_value_optimization_enabled: bool = Field(
        default=True,
        alias="dotValueOptimizationEnabled",
        description="Enables optimization to find the best dot value per polygon.",
    )
    dot_blending_enabled: bool = Field(
        default=True,
        alias="dotBlendingEnabled",
        description="Enables blending of overlapping dots.",
    )
    outline_optimization_enabled: bool = Field(
        default=False,
        alias="outlineOptimizationEnabled",
        description="Enables optimization of polygon outline color for dot density.",
    )
    scheme: Scheme | None = Field(
        default=None,
        alias="dotDensityScheme",
        description="Predefined dot density scheme used instead of generating one from map background.",
    )
    for_binning: bool | None = Field(
        default=None,
        alias="forBinning",
        description="Indicates whether the renderer is for binning and uses aggregate featureReduction fields.",
    )

    @field_validator("attributes", mode="before")
    @classmethod
    def _ensure_attributes_list(cls, value):
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
        raise ValueError(
            f"attributes must be a list of dictionaries. {type(value)} was passed."
        )


class PieChartRendererParams(SmartMappingParams):
    """Parameters for generating per-feature pie or donut chart renderers from numeric attributes."""

    type: Literal["pieChart"] = Field(
        default="pieChart",
        description="Renderer type identifier used by the JavaScript API.",
    )
    attributes: list[CategoryAttribute] = Field(
        ...,
        description="List of complementary numeric field/expression definitions used to create pie or donut slices.",
    )
    shape: PieChartShape | str | None = Field(
        default="pie",
        description='Shape used for chart symbols ("pie" or "donut").',
    )
    include_size_variable: bool | None = Field(
        default=None,
        alias="includeSizeVariable",
        description="If True, includes data-driven chart sizing based on attribute totals.",
    )
    outline_optimization_enabled: bool = Field(
        default=False,
        alias="outlineOptimizationEnabled",
        description="For polygon layers, indicates whether outline width varies by view scale.",
    )
    size_optimization_enabled: bool = Field(
        default=False,
        alias="sizeOptimizationEnabled",
        description="Indicates whether symbol size varies by view scale.",
    )
    scheme: Scheme | None = Field(
        default=None,
        alias="pieChartScheme",
        description="Predefined pie chart scheme used instead of generating one from map background.",
    )
    for_binning: bool | None = Field(
        default=None,
        alias="forBinning",
        description="Indicates whether the renderer is for binning and uses aggregate featureReduction fields.",
    )

    @field_validator("attributes", mode="before")
    @classmethod
    def _ensure_attributes_list(cls, value):
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
        raise ValueError(
            f"attributes must be a list of dictionaries. {type(value)} was passed."
        )


class PredominanceRendererParams(SmartMappingParams):
    """Parameters for generating a predominance renderer based on which competing numeric field wins per feature."""

    type: Literal["predominance"] = Field(
        default="predominance",
        description="Renderer type identifier used by the JavaScript API.",
    )
    symbol_type: Literal["2d"] = Field(
        default="2d",
        alias="symbolType",
        description="Symbol type identifier used by the JavaScript API.",
    )
    fields: list[PredominanceField] = Field(
        ...,
        description="Competing numeric field definitions used as the basis of predominance visualization; provide at least two fields.",
    )
    include_opacity_variable: bool | None = Field(
        default=None,
        alias="includeOpacityVariable",
        description="If True, includes data-driven opacity based on how strongly the winning field predominates.",
    )
    include_size_variable: bool | None = Field(
        default=None,
        alias="includeSizeVariable",
        description="If True, includes data-driven size based on the sum of competing values.",
    )
    outline_optimization_enabled: bool = Field(
        default=False,
        alias="outlineOptimizationEnabled",
        description="For polygon layers, indicates whether outline width varies by view scale.",
    )
    size_optimization_enabled: bool = Field(
        default=False,
        alias="sizeOptimizationEnabled",
        description="Indicates whether symbol size varies by view scale.",
    )
    statistics: Statistics | None = Field(
        default=None,
        description="Precomputed field statistics to avoid an additional server query.",
    )
    sort_by: PredominanceSortBy | str | None = Field(
        default=None,
        alias="sortBy",
        description='Legend sort mode. "count" sorts by descending feature counts per category; "value" preserves field order.',
    )
    scheme: Scheme | None = Field(
        default=None,
        alias="predominanceScheme",
        description="Predefined predominance scheme used instead of generating one from map background.",
    )
    default_symbol_enabled: bool | None = Field(
        default=True,
        alias="defaultSymbolEnabled",
        description="Enables a default symbol for features with no value.",
    )
    for_binning: bool | None = Field(
        default=None,
        alias="forBinning",
        description="Indicates whether the renderer is for binning and uses aggregate featureReduction fields.",
    )


class ClassBreaksRendererParams(SmartMappingParams):
    """Parameters for generating class-break renderers that symbolize numeric ranges by color or size."""

    symbol_type: Literal["2d"] = Field(
        default="2d",
        alias="symbolType",
        description="Symbol type identifier used by the JavaScript API.",
    )
    break_type: ClassBreaksType | str = Field(
        ..., description='Type of class breaks to generate ("size" or "color").'
    )
    field: str | None = Field(
        default=None,
        description="Field used for statistics and class breaks; ignored when value_expression is set.",
    )
    normalization_field: str | None = Field(
        default=None,
        alias="normalizationField",
        description="Field used to normalize the primary field values.",
    )
    normalization_type: ClassBreaksNormalizationType | str | None = Field(
        default=None,
        alias="normalizationType",
        description='Normalization method applied before classing: "log", "percent-of-total", or "field".',
    )
    normalization_total: int | None = Field(
        default=None,
        alias="normalizationTotal",
        description='Total used when normalization_type is "percent-of-total".',
    )
    classification_method: ClassBreaksClassificationMethod | str | None = Field(
        default=None,
        alias="classificationMethod",
        description='Method used to compute class breaks: "equal-interval", "natural-breaks", "quantile", or "standard-deviation".',
    )
    standard_deviation_interval: float | None = Field(
        default=None,
        alias="standardDeviationInterval",
        description='Standard deviation interval used when classification_method is "standard-deviation". Supported values: 1, 0.5, 0.33, 0.25.',
    )
    num_classes: int | None = Field(
        default=None,
        alias="numClasses",
        description="Number of classes; ignored for standard-deviation classification.",
    )
    value_expression: str | None = Field(
        default=None,
        alias="valueExpression",
        description="Arcade expression that returns a numeric value and overrides the field parameter.",
    )
    value_expression_title: str | None = Field(
        default=None,
        alias="valueExpressionTitle",
        description="Legend title for the value_expression.",
    )
    sql_expression: str | None = Field(
        default=None,
        alias="sqlExpression",
        description="SQL expression that evaluates to a number.",
    )
    sql_where: str | None = Field(
        default=None,
        alias="sqlWhere",
        description="SQL where clause used to filter features for statistics queries.",
    )
    outline_optimization_enabled: bool = Field(
        default=False,
        alias="outlineOptimizationEnabled",
        description="For polygon layers, indicates whether outline width varies by view scale.",
    )
    min_value: int | None = Field(
        default=None,
        alias="minValue",
        description="Custom lower bound used to generate statistics and visual variable stops.",
    )
    max_value: int | None = Field(
        default=None,
        alias="maxValue",
        description="Custom upper bound used to generate statistics and visual variable stops.",
    )
    default_symbol_enabled: bool = Field(
        default=True,
        alias="defaultSymbolEnabled",
        description="Enables a default symbol for features with null or out-of-range values.",
    )
    for_binning: bool | None = Field(
        default=None,
        alias="forBinning",
        description="Indicates whether the renderer is for binning and uses aggregate featureReduction fields.",
    )

    @field_validator("standard_deviation_interval")
    @classmethod
    def _validate_standard_deviation_interval(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value not in [1, 0.5, 0.33, 0.25]:
            return 1
        return value

    @model_validator(mode="after")
    def _set_standard_deviation_interval_default(self):
        if (
            self.classification_method == "standard-deviation"
            and self.standard_deviation_interval is None
        ):
            self.standard_deviation_interval = 1
        return self


class UniqueValuesRendererParams(SmartMappingParams):
    """Parameters for generating unique-values renderers from one or more categorical fields or an expression."""

    type: Literal["uniqueValues"] = Field(
        default="uniqueValues",
        description="Renderer type identifier used by the JavaScript API.",
    )
    symbol_type: Literal["2d"] = Field(
        default="2d",
        alias="symbolType",
        description="Symbol type identifier used by the JavaScript API.",
    )
    field: str | None = Field(
        default=None,
        description="Primary field used to derive unique categories; ignored when value_expression is set.",
    )
    field2: str | None = Field(
        default=None,
        description="Second field used to build combined unique categories; ignored when value_expression is set.",
    )
    field3: str | None = Field(
        default=None,
        description="Third field used to build combined unique categories; ignored when value_expression is set.",
    )
    num_types: int | None = Field(
        default=None,
        alias="numTypes",
        description="Number of unique categories to display; use -1 to include all types (JavaScript API default is typically 10 when unspecified).",
    )
    sort_by: UniqueValuesSortBy | str | None = Field(
        default=None,
        alias="sortBy",
        description='Legend sort mode: "count" (highest to lowest), "value" (field order), or "none" (statistics/query order).',
    )
    value_expression: str | None = Field(
        default=None,
        alias="valueExpression",
        description="Arcade expression (Visualization profile) returning a value used for unique categories; overrides field/field2/field3.",
    )
    value_expression_title: str | None = Field(
        default=None,
        alias="valueExpressionTitle",
        description="Legend title for the value_expression.",
    )
    outline_optimization_enabled: bool = Field(
        default=False,
        alias="outlineOptimizationEnabled",
        description="For polygon layers, indicates whether outline width varies by view scale.",
    )
    size_optimization_enabled: bool = Field(
        default=False,
        alias="sizeOptimizationEnabled",
        description="Indicates whether symbol size varies by view scale.",
    )
    legend_options: LegendOptions | None = Field(
        default=None,
        alias="legendOptions",
        description="Options for configuring legend display.",
    )
    default_symbol_enabled: bool = Field(
        default=True,
        alias="defaultSymbolEnabled",
        description="Enables a default symbol for features with no value.",
    )
    statistics: Statistics | None = Field(
        default=None,
        description="Precomputed unique value statistics to avoid an additional server query.",
    )
    for_binning: bool | None = Field(
        default=None,
        alias="forBinning",
        description="Indicates whether the renderer is for binning and uses aggregate featureReduction fields.",
    )
