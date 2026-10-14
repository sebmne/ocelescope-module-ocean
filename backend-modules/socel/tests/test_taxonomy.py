"""The taxonomy the classes and flow categories come from."""

from api import Api


def paths(nodes: list[dict]) -> list[str]:
    return [path for node in nodes for path in (node["path"], *paths(node["children"]))]


def test_the_taxonomy_is_given_as_trees(api: Api) -> None:
    taxonomy = api.get_class_taxonomies().json()

    assert [node["path"] for node in taxonomy["objectClasses"]] == ["hu", "pr"]
    assert "op.manufacturing.surface.coating" in paths(taxonomy["eventClasses"])
    assert "material.auxiliary.gas" in paths(taxonomy["flowCategories"])
    surface = taxonomy["eventClasses"][0]["children"][0]["children"][5]
    assert (surface["path"], surface["label"]) == ("op.manufacturing.surface", "surface")
