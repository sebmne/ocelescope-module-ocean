"""Attribute references on the wire, shared by the routes that carry rules."""

from typing import Annotated, Literal

from pydantic import Field

from ocelescope_module_ocean.api.schema import ApiModel
from ocelescope_module_ocean.domain.models.attributes import (
    AttributeRef,
    EventAttributeRef,
    ObjectAttributeRef,
)


class EventAttributeRefModel(ApiModel):
    target: Literal["event"]
    name: str

    def to_domain(self) -> EventAttributeRef:
        return EventAttributeRef(name=self.name)


class ObjectAttributeRefModel(ApiModel):
    target: Literal["object"]
    object_type: str
    name: str
    qualifier: str | None = None

    def to_domain(self) -> ObjectAttributeRef:
        return ObjectAttributeRef(
            object_type=self.object_type, name=self.name, qualifier=self.qualifier
        )


AttributeRefModel = Annotated[
    EventAttributeRefModel | ObjectAttributeRefModel, Field(discriminator="target")
]


def attribute_ref_from_domain(attribute: AttributeRef) -> AttributeRefModel:
    match attribute:
        case EventAttributeRef():
            return EventAttributeRefModel(target="event", name=attribute.name)
        case ObjectAttributeRef():
            return ObjectAttributeRefModel(
                target="object",
                object_type=attribute.object_type,
                name=attribute.name,
                qualifier=attribute.qualifier,
            )
