"""The taxonomy the classes and flow categories come from."""

from api import Api

from ocelescope_module_socel.domain.models.class_taxonomy import ClassTaxonomies


def test_the_taxonomy_is_given_as_trees(api: Api) -> None:
    response = api.get_class_taxonomies()
    assert response.status_code == 200
    payload = response.json()
    taxonomy = ClassTaxonomies.model_validate(payload)

    assert [node.label for node in taxonomy.object_classes] == ["hu", "pr"]
    assert "op.manufacturing.surface.coating" in taxonomy.event_classes[0].paths()
    assert "material.auxiliary.gas" in taxonomy.flow_categories[1].paths()
    surface = payload["eventClasses"][0]["children"][0]["children"][5]
    assert surface == {
        "label": "surface",
        "children": [{"label": "cleaning", "children": []}, {"label": "coating", "children": []}],
    }
