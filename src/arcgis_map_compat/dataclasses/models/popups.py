from __future__ import annotations  # Enables postponed evaluation of type hints

from arcgis_map_compat._compat import deprecated
from arcgis_map_compat.dataclasses.models.base_model import BaseModel, common_config
from pydantic import Field
from typing import Literal, Any, Annotated
from arcgis_map_compat.dataclasses.enums.popups import (
    AttachmentType,
    StringFieldOption,
    MediaType,
    AttachmentDisplayType,
    ArcadeReturnType,
)
from arcgis_map_compat.dataclasses.enums.layer_definition import (
    DateFormat,
    StatisticType,
    FormatStyle,
    DateTimeStyle,
)
from arcgis_map_compat.dataclasses.models.shared_types import AssociationType, OrderByField
from arcgis_map_compat.dataclasses.models.geometry import PointGeometry


class FieldFormatDateTime(BaseModel):
    """
    An object defining how to format date and time fields.
    """

    model_config = common_config

    date_style: DateTimeStyle | None = Field(
        None,
        alias="dateStyle",
        description="A string used with date fields to specify how the date should be styled.",
    )
    hour_12: FormatStyle | None = Field(
        None,
        alias="hour12",
        description="A string value that indicates whether to show a 12-hour cycle when formatting time",
    )
    month: DateTimeStyle | None = Field(
        None,
        description="A string used with date fields to specify how the month should be styled.",
    )
    time_style: DateTimeStyle | None = Field(
        None,
        alias="timeStyle",
        description="A string used with date fields to specify how the time should be styled.",
    )
    type: Literal["date-time"] = Field(
        "date-time",
        description="Indicates that the field format is for date and time fields.",
    )
    year: Literal["numeric"] = Field(
        "numeric",
        description="A string used with date fields to specify how the year should be styled.",
    )


class FieldFormatNumber(BaseModel):
    """
    An object defining how to format number fields.
    """

    model_config = common_config

    maximum_fraction_digits: int | None = Field(
        2,
        alias="maximumFractionDigits",
        description="A number indicating the maximum number of decimal places to display. The default is `2` with minimum and maximum values as `0` and `20` respectively.",
        ge=0,
        le=20,
    )
    minimum_fraction_digits: int | None = Field(
        0,
        alias="minimumFractionDigits",
        description="A number indicating the minimum number of decimal places to display. The default is `0`. If no value is provided, the formatter will not enforce any minimum number of decimal places. There is no strict upper limit, bit it should not exceed `maximumFractionDigits`.",
        ge=0,
        le=20,
    )
    style: Literal["decimal"] = Field(
        "decimal",
        description="A string value that indicates the formatting style to use, such as `decimal` for general number formatting.",
    )
    type: Literal["number"] = Field(
        "number",
        description="Indicates that the field format is for number fields.",
    )
    use_grouping: FormatStyle | None = Field(
        None,
        alias="useGrouping",
        description="A string value that indicates whether to use grouping separators, such as thousands separators, when formatting numbers.",
    )


class Format(BaseModel):
    """
    The format object can be used with numerical or date fields to provide
    more detail about how values should be formatted for display.
    """

    model_config = common_config

    date_format: DateFormat | None = Field(
        None,
        alias="dateFormat",
        description="A string used with date fields to specify how the date should be formatted.",
    )
    digit_separator: bool | None = Field(
        None,
        alias="digitSeparator",
        description="A Boolean used with numerical fields. If True, allows the number to have a digit (or thousands) separator. Depending on the locale, this separator is a decimal point or a comma. If False, means that no separator will be used.",
    )
    places: int | None = Field(
        None,
        description="An integer used with numerical fields to specify the number of decimal places. Any places beyond this value are rounded.",
    )


class FieldInfo(BaseModel):
    """
    Defines how a field in the dataset participates (or does not participate) in a popup window.
    Configuring fields should be handled using the [fieldConfiguration](fieldConfiguration.md) objects specified via the associated layer's `fieldConfigurations` property, instead of the properties on this object. The properties on this object are retained for backward compatibility but behavior may change as the specification evolves.
    """

    model_config = common_config

    field_format: FieldFormatDateTime | FieldFormatNumber | None = Field(
        None,
        alias="fieldFormat",
        description="An object defining how to format date, time and number fields.",
    )
    field_name: str | None = Field(
        None,
        alias="fieldName",
        description="A string containing the field name as defined by the service.",
    )
    format: Format | None = Field(
        None,
        description="A format object used with numerical or date fields to provide more detail about how the value should be displayed in a web map popup window. **Deprecation notes**: 1) In the context of [popupInfo.fieldInfos](popupInfo.md), this property is deprecated in favor of using the `fieldFormat` property of the [fieldConfiguration](fieldConfiguration.md) objects specified via the associated layer's `fieldConfigurations` property. 2) In the context of `fieldInfos` defined in [popupElement fields](popupElement_fields.md), this property is deprecated in favor of the `fieldFormat` property listed above.",
    )
    is_editable: bool | None = Field(
        True,
        alias="isEditable",
        description="A Boolean determining whether users can edit this field. Not applicable to Arcade expressions.",
    )
    label: str | None = Field(
        None,
        description="A string containing the field alias. This can be overridden by the web map author. Not applicable to Arcade expressions as `title` is used instead.This property is deprecated when used with [popupInfo.fieldInfos](popupInfo.md).  Instead, use the `alias` property from the associated field's [fieldConfiguration](fieldConfiguration.md) object.",
    )
    statistic_type: StatisticType | None = Field(
        None,
        alias="statisticType",
        description="Used in a 1:many or many:many relationship to compute the statistics on the field to show in the popup.",
    )
    string_field_option: StringFieldOption | str | None = Field(
        None,
        alias="stringFieldOption",
        description="A string determining what type of input box editors see when editing the field. Applies only to string fields. Not applicable to Arcade expressions.",
    )
    tooltip: str | None = Field(
        None,
        description="A string providing an editing hint for editors of the field. Not applicable to Arcade expressions.",
    )
    visible: bool = Field(
        True,
        description="A Boolean determining whether the field is visible in the popup window.",
    )


class PopupLayerOptions(BaseModel):
    """
    Additional options available for the popup layer.
    """

    model_config = common_config

    return_topmost_raster: bool | None = Field(
        None,
        alias="returnTopmostRaster",
        description="Indicates whether or not only the topmost raster should be displayed.",
    )
    show_no_data_records: bool | None = Field(
        None,
        alias="showNoDataRecords",
        description="Indicates whether or not the NoData records should be displayed.",
    )


@deprecated(
    deprecated_in="5.1.0",
    removed_in="5.4.0",
    details="Use `PopupLayerOptions` instead.",
)
class LayerOptions(PopupLayerOptions):
    """
    Legacy name for PopupLayerOptions. This class is retained for backward compatibility but will be removed in future versions in favor of :class:`~arcgis.map.popups.PopupLayerOptions` instead.
    """

    model_config = common_config


class Value(BaseModel):
    """
    The value object contains information for popup windows about how images should be retrieved or charts constructed.
    """

    model_config = common_config

    colors: list[list[Annotated[int, Field(ge=0, le=255)]]] | None = Field(
        None,
        description="Used with charts. An optional array of colors where each `color` sequentially corresponds to a field in the `fields` property. When the value for `mediaInfo.type` is `linechart`, the first color in the array will drive the line color. If `colors` is longer than `fields`, unmatched colors are ignored. If `colors` is shorter than `fields` or `colors` isn't specified, a default color ramp is applied.",
    )
    fields: list[str] | None = Field(
        None,
        description="Used with charts. An array of strings, with each string containing the name of a field to display in the chart.",
    )
    link_url: str | None = Field(
        None,
        alias="linkURL",
        description="Used with images. A string containing a URL to be launched in a browser when a user clicks the image.",
    )
    normalize_field: str | None = Field(
        None,
        alias="normalizeField",
        description="Used with charts. An optional string containing the name of a field. The values of all fields in the chart will be normalized (divided) by the value of this field.",
    )
    source_url: str | None = Field(
        None,
        alias="sourceURL",
        description="Used with images. A string containing the URL to the image.",
    )
    tooltip_field: str | None = Field(
        None,
        alias="tooltipField",
        description="String value indicating the tooltip for a chart specified from another field. This field is needed when related records are not used. It is used for showing tooltips from another field in the same layer or related layer/table.",
    )


class MediaInfo(BaseModel):
    """
    Defines an image or a chart to be displayed in a popup window.
    """

    model_config = common_config

    alt_text: str | None = Field(
        None,
        alias="altText",
        description="A string providing the alternate text for the media.",
    )
    caption: str | None = Field(
        None, description="A string caption describing the media."
    )
    refresh_interval: float | int | None = Field(
        0,
        alias="refreshInterval",
        description="Refresh interval of the layer in minutes. Non-zero value indicates automatic layer refresh at the specified interval. Value of 0 indicates auto refresh is not enabled. If the property does not exist, it's equivalent to having a value of 0. Only applicable when `type` is set to `image`.",
    )
    title: str | None = Field(None, description="A string title for the media.")
    type: MediaType | None = Field(
        None, description="A string defining the type of media."
    )
    value: Value | None = Field(
        None,
        description="A value object containing information about how the image should be retrieved or how the chart should be constructed.",
    )


class PopupElementAttachments(BaseModel):
    """
    Configures attachments in popup elements.
    """

    model_config = common_config

    attachment_keywords: list[str] | None = Field(
        None,
        alias="attachmentKeywords",
        description="An array of strings used to identify attachment(s). When attachments are displayed, this property is used to query attachments using an exact match on the keywords provided.",
    )
    attachment_types: list[AttachmentType] | None = Field(
        None,
        alias="attachmentTypes",
        description="An array of strings representing MIME types. When attachments are displayed, this property is used to query attachments based on MIME type. Valid values: `application`, `audio`, `image`, `model`, `text`, and `video`.",
    )
    description: str | None = Field(
        None, description="An optional string value describing the element in detail."
    )
    display_type: AttachmentDisplayType | None = Field(
        None,
        alias="displayType",
        description="This property applies to elements of type `attachments`. A string value indicating how to display the attachment. If `list` is specified, attachments show as links. If `preview` is specified, attachments expand to the width of the pop-up. The default `auto` setting allows applications to choose the most suitable default experience.",
    )
    order_by_fields: list[OrderByField] | None = Field(
        None,
        alias="orderByFields",
        description="Array of `orderByField` objects indicating the display order for the attachments, and whether they should be sorted in ascending `'asc'` or descending `'desc'` order. If `orderByFields` is not provided, the popupElement will display whatever is specified directly in the `popupInfo.attachmentsInfo.orderByFields` property.",
    )
    title: str | None = Field(
        None,
        description="An optional string value indicating what the element represents.",
    )
    type: Literal["attachments"] = "attachments"


class PopupExpressionInfo(BaseModel):
    """
    An Arcade expression that defines the pop-up element content. The return type will always be a `dictionary` that defines the desired pop-up element as outlined [in the Arcade documentation](https://developers.arcgis.com/arcade/guide/profiles/#popup-element).
    """

    model_config = common_config

    expression: str | None = Field(None, description="The Arcade expression.")
    return_type: ArcadeReturnType | None = Field(
        "string",
        alias="returnType",
        description="Optional return type of the Arcade expression. Defaults to string value. Number values are assumed to be `double`. This can be determined by the authoring client by executing the expression using a sample feature, although it can be corrected by the user. Knowing the returnType allows the authoring client to present fields in relevant contexts. For example, numeric fields in numeric contexts such as charts.",
    )
    title: str | None = Field(None, description="Title of the expression.")
    name: str | None = Field(None, description="Name of the expression.")


class PopupElementFields(BaseModel):
    """
    Configures fields in popup elements.
    """

    model_config = common_config

    attributes: dict[str, Any] | None = Field(
        None,
        description="A dictionary of key value pairs representing attributes to be used instead of fields and their values. This property is only used when an element of type `fields` is being returned inside an element of type `expression` and should be returned as part of the arcade expression itself. This property allows passing arcade derived attribute values into `fields` elements. More details can be found [here](https://developers.arcgis.com/arcade/guide/profiles/#popup-element).",
    )
    description: str | None = Field(
        None, description="An optional string value describing the element in detail."
    )
    field_infos: list[FieldInfo] | None = Field(
        None,
        alias="fieldInfos",
        description="It is an array of `fieldInfo` objects representing a field/value pair displayed as a table within the popupElement. If the `fieldInfos` property is not provided, the popupElement will display whatever is specified directly in the `popupInfo.fieldInfos` property.",
    )
    title: str | None = Field(
        None,
        description="An optional string value indicating what the element represents.",
    )
    type: Literal["fields"] = Field(
        "fields", description="Specifies the type of element."
    )


class PopupElementMedia(BaseModel):
    """
    Configures media in popup elements.
    """

    model_config = common_config

    attributes: dict[str, Any] | None = Field(
        None,
        description="A dictionary of key value pairs representing attributes to be used instead of fields and their values.  This property is only used when an element of type  `media` is being returned inside an element of type `expression` and should be returned as part of the arcade expression itself. This property allows passing arcade derived attribute values into `mediaInfos` such as charts. More details can be found [here](https://developers.arcgis.com/arcade/guide/profiles/#popup-element).",
    )
    description: str | None = Field(
        None, description="An optional string value describing the element in detail."
    )
    media_infos: list[MediaInfo] | None = Field(
        None,
        alias="mediaInfos",
        description="An array of `mediaInfo` objects representing an image or chart for display. If no `mediaInfos` property is provided, the popupElement will display whatever is specified in the `popupInfo.mediaInfos` property.",
    )
    title: str | None = Field(
        None,
        description="An optional string value indicating what the element represents.",
    )
    type: Literal["media"] = "media"


class PopupElementRelationship(BaseModel):
    """
    Provides the ability to navigate and view related records from a layer or table associated within the popup.
    """

    model_config = common_config

    description: str | None = Field(
        None, description="A string that describes the element in detail."
    )
    display_count: int | None = Field(
        None,
        alias="displayCount",
        description="An integer that indicates the maximum number of records to display.",
    )
    display_type: Literal["list"] = Field(
        "list",
        alias="displayType",
        description="A string that defines how the related records should be displayed.",
    )
    order_by_fields: list[OrderByField] | None = Field(
        None,
        alias="orderByFields",
        description="Array of `orderByField` objects indicating the display order for the related records, and whether they should be sorted in ascending `'asc'` or descending `'desc'` order. If `orderByFields` is not provided, the popupElement will display whatever is specified directly in the `popupInfo.relatedRecordsInfo.orderByFields` property.",
    )
    relationship_id: int = Field(
        ...,
        alias="relationshipId",
        description="The id of the relationship as defined in the feature layer definition",
    )
    title: str | None = Field(
        None, description="A string value indicating what the element represents."
    )
    type: Literal["relationship"] = Field(
        "relationship",
        description="String value indicating which type of element to use.",
    )


class PopupElementText(BaseModel):
    """
    Configures text in popup elements.
    """

    model_config = common_config

    text: str | None = Field(
        None,
        description="String value indicating the text to be displayed within the popupElement. If no `text` property is provided, the popupElement will display whatever is set in the popupInfo.description property.",
    )
    type: Literal["text"] = "text"


class RelatedRecordsInfo(BaseModel):
    """
    Applicable only when popupInfo contains a relationship content element. This is needed for backward compatibility for some web maps.
    """

    model_config = common_config

    order_by_fields: list[OrderByField] | None = Field(
        None,
        alias="orderByFields",
        description="Array of orderByField objects indicating the field display order for the related records, and whether they should be sorted in ascending (asc) or descending (desc) order.",
    )
    show_related_records: bool | None = Field(
        None,
        alias="showRelatedRecords",
        description="Required boolean value indicating whether to display related records. If True, client should let the user navigate to the related records. Defaults to True if the layer participates in a relationship AND the related layer/table has already been added to the map (either as an operationalLayer or as a table).",
    )


class PopupElementExpression(BaseModel):
    """
    A pop-up element defined by an arcade expression.
    """

    model_config = common_config

    expression_info: PopupExpressionInfo = Field(
        ...,
        alias="expressionInfo",
        description="An Arcade expression that defines the pop-up element content. The return type will always be `dictionary` as outlined [in the Arcade documentation](https://developers.arcgis.com/arcade/guide/profiles/#popup-element).",
    )
    type: Literal["expression"] = Field(
        "expression", description="Specifies the type of element."
    )


class PopupElementUtilityNetworkAssociations(BaseModel):
    """
    Provides the ability to navigate and view associated objects from a layer or table associated within the [pop-up](popupInfo.md).
    """

    model_config = common_config

    association_types: list[AssociationType] | None = Field(
        ...,
        alias="associationTypes",
        description="An array of `associationType` objects that represent the utility network associations.",
    )
    description: str | None = Field(
        None,
        description="A string that describes the element in detail.",
    )
    display_count: int | None = Field(
        None,
        alias="displayCount",
        description="An integer that indicates the maximum number of records to display.",
    )
    title: str | None = Field(
        None,
        description="A string value indicating what the element represents.",
    )
    type: Literal["utilityNetworkAssociations"] = Field(
        "utilityNetworkAssociations",
        description="String value indicating which type of element to use.",
    )


class PopupInfo(BaseModel):
    """
    Defines the look and feel of popup windows when a user clicks or queries a feature.
    """

    model_config = common_config

    description: str | None = Field(
        None,
        description="A string that appears in the body of the popup window as a description. A basic subset of HTML may also be used to enrich the text. The supported HTML for ArcGIS Online can be seen in the [Supported HTML](https://doc.arcgis.com/en/arcgis-online/reference/supported-html.htm) page.",
    )
    expression_infos: list[PopupExpressionInfo] | None = Field(
        None,
        alias="expressionInfos",
        description="List of Arcade expressions added to the pop-up.",
    )
    field_infos: list[FieldInfo] | None = Field(
        None,
        alias="fieldInfos",
        description="Array of FieldInfo information properties. This information is provided by the service layer definition. When the description uses name/value pairs, the order of the array is how the fields display in the editable Map Viewer popup and the resulting popup. It is also possible to specify HTML-formatted content. Support is currently limited to feature service-backed Feature Layers, Catalog Footprint Layers, Oriented Imagery Layers, Subtype Layers, Subtype Tables, and Tables. Support for additional layer types is planned for future releases.",
    )
    layer_options: PopupLayerOptions | None = Field(
        None,
        alias="layerOptions",
        description="Additional options that can be defined for the popup layer.",
    )
    media_infos: list[MediaInfo] | None = Field(
        None,
        alias="mediaInfos",
        description="Array of various mediaInfo to display. Can be of type `image`, `piechart`, `barchart`, `columnchart`, or `linechart`. The order given is the order in which is displays.",
    )
    popup_elements: (
        list[
            PopupElementAttachments
            | PopupElementExpression
            | PopupElementFields
            | PopupElementMedia
            | PopupElementRelationship
            | PopupElementText
            | PopupElementUtilityNetworkAssociations
        ]
        | None
    ) = Field(
        None,
        alias="popupElements",
        description="An array of popupElement objects that represent an ordered list of popup elements.",
    )
    related_records_info: RelatedRecordsInfo | None = Field(
        None,
        alias="relatedRecordsInfo",
        description="Applicable only when the pop-up contains a relationship content element. This is needed for backward compatibility for some web maps.",
    )
    show_attachments: bool | None = Field(
        None,
        alias="showAttachments",
        description="Indicates whether attachments will be loaded for feature layers that have attachments.",
    )
    show_last_edit_info: bool | None = Field(
        None,
        alias="showLastEditInfo",
        description="Indicates whether popup will display information about when and who last edited the feature. Applicable only to layers that have been configured to keep track of such information.",
    )
    title: str | None = Field(
        None,
        description="A string that appears at the top of the popup window as a title.",
    )


class FeatureGlobalId(BaseModel):
    """
    A unique reference to a feature inside a layer based on its globalid.
    """

    model_config = common_config
    type: Literal["globalId"] = Field(
        "globalId",
        description="Type of unique identifier for the feature.",
    )
    value: str = Field(
        ...,
        description="The globalid value of the feature. The globalid is a unique identifier for a feature across all layers in the service.",
    )


class LayerReference(BaseModel):
    model_config = common_config
    layer_id: str = Field(..., alias="layerId", description="The id of the layer.")
    sub_layer_id: int | None = Field(
        None,
        alias="subLayerId",
        description="The id of the sublayer. If the layer is not a sublayer, this value is null.",
    )


class FeatureObjectId(BaseModel):
    """
    A unique reference to a feature inside a layer based on its objectid.
    """

    model_config = common_config
    type: Literal["objectId"] = Field(
        "objectId",
        description="Type of unique identifier for the feature.",
    )
    value: int = Field(
        ...,
        description="The objectid value of the feature. The objectid is a unique identifier for a feature within its layer.",
    )


class FeatureReference(BaseModel):
    """
    References a feature by unique identifier, layer id, and sublayer id, if applicable.
    """

    model_config = common_config
    id: FeatureGlobalId | FeatureObjectId = Field(
        ...,
        description="Unique value type and unique value identifying the feature within the layer.",
    )
    layer_reference: LayerReference = Field(
        ..., description="Identifies the layer to which the feature belongs."
    )


class SlidePopupInfo(BaseModel):
    model_config = common_config
    features: list[FeatureReference] = Field(
        ..., description="A list of feature references associated with the slide."
    )
    location: PointGeometry = Field(..., description="The location of the slide.")
    selected_feature_index: int | None = Field(
        None,
        ge=0,
        description="The index of the selected feature in the slide. If not specified, the first feature in the list is selected.",
        alias="selectedFeatureIndex",
    )
