from __future__ import annotations  # Enables postponed evaluation of type hints

from arcgis_map_compat.dataclasses.models.base_model import BaseModel, common_config
from pydantic import Field
from arcgis_map_compat.dataclasses.enums.popups import AssociationTypes, Order


class AssociationType(BaseModel):
    """
    Object defining the type of associations to display in the pop-up.
    Used with Utility Network layers.
    """

    model_config = common_config

    associated_asset_group: int | None = Field(
        None,
        alias="associatedAssetGroup",
        description="The id of the asset group to filter utility network associations.",
    )
    associated_asset_type: int | None = Field(
        None,
        alias="associatedAssetType",
        description="The id of the asset type to filter utility network associations.",
    )
    associated_network_source_id: int | None = Field(
        None,
        alias="associatedNetworkSourceId",
        description="The id of the network source to filter utility network associations.",
    )
    description: str | None = Field(
        None,
        description="A string that describes the element in detail.",
    )
    title: str | None = Field(
        None,
        description="A string value indicating what the element represents.",
    )
    type: AssociationTypes = Field(
        ...,
        description="String value indicating which type of element to use.",
    )


class OrderByField(BaseModel):
    """
    Object defining the display order of features or records based on a field value, and whether they should be sorted in ascending or descending order.
    """

    model_config = common_config

    field: str = Field(
        ...,
        description="Name of a field. The value of this field will drive the sorting.",
    )
    order: Order = Field(
        ...,
        description="Indicates whether features are sorted in ascending or descending order of the field values.",
    )
