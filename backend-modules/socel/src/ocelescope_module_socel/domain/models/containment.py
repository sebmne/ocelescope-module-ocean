from ocelescope_module_socel.domain.models.base import Model


class TypeContainment(Model):
    """Objects of `object_type` lie inside the object of `parent_type` that the
    object-to-object relation `qualifier` leads them to, for each of `flows`.
    The relation is read in the direction it is stored, from the object to the
    one around it."""

    object_type: str
    parent_type: str
    qualifier: str
    flows: tuple[str, ...]
