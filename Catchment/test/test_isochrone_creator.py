import pytest
from qgis.core import QgsWkbTypes

from Catchment.core.isochrone_creator import IsochroneCreator

from ..qgis_plugin_tools.tools.exceptions import QgsPluginNetworkException


# Test the plugin with
# 1) no school area boundaries => should yield original isochrone
# 2) square school area boundary => should yield single polygon intersection with isochrone.json
# 3) multipolygon school area boundary => should yield single polygon intersection with isochrone.json
# 4) triangular school area boundary => should yield multipolygon intersection with isochrone.json
# 5) square+triangular school area boundary => should yield single polygon intersection with isochrone.json
@pytest.mark.parametrize(
    "boundary_layer, part_count",
    [
        (None, 1),
        ("square_layer", 1),
        ("multipolygon_layer", 1),
        ("triangle_layer", 3),
        ("square_plus_triangle_layer", 1),
    ],
)
def test_isochrone_layer_isochrone_created(
    isochrone_opts, mock_fetch, boundary_layer, part_count, request
):
    if boundary_layer:
        boundary_layer = request.getfixturevalue(boundary_layer)
    mock_fetch(isochrone_opts.url + "/isochrone")
    assert isochrone_opts.layer.featureCount() == 1
    assert isochrone_opts.check_if_opts_set()
    isochrone_opts.polygon_layer = boundary_layer
    isochrone_layer = IsochroneCreator(isochrone_opts).create_isochrone_layer()
    assert isochrone_layer.featureCount() == 1
    assert isochrone_layer.geometryType() == QgsWkbTypes.PolygonGeometry
    for feature in isochrone_layer.getFeatures():
        assert feature.attribute("original_fid") == "1"
        assert feature.attribute("name") == "school"
        assert feature.attribute("extra_info") == "first_feature"
        assert feature.attribute("isochrone_distance") == 30
        if not boundary_layer:
            assert feature.attribute("boundary_fids") == ""
        else:
            assert feature.attribute("boundary_fids") == ",".join(
                [str(feature["fid"]) for feature in boundary_layer.getFeatures()]
            )
        assert len(feature.geometry().asMultiPolygon()) == part_count


def test_isochrone_layer_isochrones_merged(
    isochrone_opts, mock_fetch, point, another_point, two_point_layer
):
    mock_fetch(
        [isochrone_opts.url + "/isochrone", isochrone_opts.url + "/isochrone"],
        ["isochrones.json", "another_isochrone.json"],
        required_params=[
            {"point": f"{point.asPoint().y()},{point.asPoint().x()}"},
            {"point": f"{another_point.asPoint().y()},{another_point.asPoint().x()}"},
        ],
    )
    isochrone_opts.layer = two_point_layer
    isochrone_opts.merge_by_field = two_point_layer.fields()[
        two_point_layer.dataProvider().fieldNameMap()["extra_field_1"]
    ]
    isochrone_layer = IsochroneCreator(isochrone_opts).create_isochrone_layer()
    assert isochrone_layer.featureCount() == 1
    assert isochrone_layer.geometryType() == QgsWkbTypes.PolygonGeometry
    for feature in isochrone_layer.getFeatures():
        assert feature.attribute("original_fid") == "1,2"
        assert feature.attribute("extra_field_1") == 2
        assert feature.attribute("isochrone_distance") == 30
        assert feature.attribute("boundary_fids") == ""
        # the two isochrones will merge to a polygon with two inner rings
        assert len(feature.geometry().asMultiPolygon()) == 1
        assert len(feature.geometry().asMultiPolygon()[0]) == 3


def test_isochrone_layer_empty(isochrone_opts, mock_fetch):
    mock_fetch(isochrone_opts.url + "/isochrone", "error.json", error=True)
    assert isochrone_opts.layer.featureCount() == 1
    assert isochrone_opts.check_if_opts_set()
    isochrone_layer = IsochroneCreator(isochrone_opts).create_isochrone_layer()
    assert isochrone_layer.featureCount() == 0


def test_isochrone_layer_request_failed(isochrone_opts, mock_fetch):
    mock_fetch("another.url")
    assert isochrone_opts.layer.featureCount() == 1
    assert isochrone_opts.check_if_opts_set()
    with pytest.raises(QgsPluginNetworkException):
        isochrone_layer = IsochroneCreator(isochrone_opts).create_isochrone_layer()
