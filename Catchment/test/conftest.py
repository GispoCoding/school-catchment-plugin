# type: ignore
# flake8: noqa ANN201
"""
This class contains fixtures and common helper function to keep the test files shorter
"""
import json
import os
from typing import Callable, Dict, List, Optional, Union

import pytest
from PyQt5.QtCore import QVariant

# from PyQt5.QtNetwork import QNetworkReply
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsLineString,
    QgsPointXY,
    QgsPolygon,
    QgsVectorLayer,
)

from Catchment.core.isochrone_creator import IsochroneOpts
from Catchment.definitions.constants import Profile, Unit
from Catchment.plugin import Plugin

from ..qgis_plugin_tools.tools.exceptions import QgsPluginNetworkException
from ..qgis_plugin_tools.tools.i18n import tr

MOCK_URL = "http://mock.url"


@pytest.fixture(scope="function")
def mock_fetch(mocker, request) -> None:
    """Makes fetch return JSON(s) (and optional error(s)) for specified URL(s).
    Use by calling mock_fetch(desired_url(s), json_file_name(s), error_desired, required_params(s)) in a test.
    """

    def _mock_fetch(
        desired_url: Union[str, List[str]],
        json_to_return: Union[str, List[str]] = "isochrones.json",
        error: Union[bool, List[bool]] = False,
        required_params: Union[
            Optional[Dict[str, str]], List[Optional[Dict[str, str]]]
        ] = None,
    ) -> Callable:
        if isinstance(desired_url, str):
            desired_url = [desired_url]
        if isinstance(json_to_return, str):
            json_to_return = len(desired_url) * [json_to_return]
        if isinstance(error, bool):
            error = len(desired_url) * [error]
        if isinstance(required_params, dict) or not required_params:
            required_params = len(desired_url) * [required_params]

        def mocked_fetch(
            url: str,
            params: Optional[Dict[str, str]] = None,
        ) -> str:
            indices = [
                idx
                for idx, matching_url in enumerate(desired_url)
                if url == matching_url
            ]
            # return first matching url+parameter combination
            for index in indices:
                # only check parameters if we require specific params
                if not required_params[index] or all(
                    [
                        params.get(key, None) == required_params[index][key]
                        for key in required_params[index].keys()
                    ]
                ):
                    with open(
                        os.path.join(
                            request.fspath.dirname, "fixtures", json_to_return[index]
                        )
                    ) as f:
                        # mock error if desired
                        if error[index]:
                            raise QgsPluginNetworkException(f.read(), error=302)
                        return f.read()
            raise QgsPluginNetworkException(tr("Request failed"))

        mocker.patch("Catchment.core.isochrone_creator.fetch", new=mocked_fetch)

    yield _mock_fetch


@pytest.fixture(scope="function")
def point() -> None:
    yield QgsGeometry.fromPointXY(QgsPointXY(1.0, 1.0))


@pytest.fixture(scope="function")
def another_point() -> None:
    yield QgsGeometry.fromPointXY(QgsPointXY(0.9, 0.9))


@pytest.fixture(scope="function")
def square() -> None:
    yield QgsGeometry.fromPolygonXY(
        [
            [
                QgsPointXY(0.0, 0.0),
                QgsPointXY(2.0, 0.0),
                QgsPointXY(2.0, 2.0),
                QgsPointXY(0.0, 2.0),
            ]
        ]
    )


@pytest.fixture(scope="function")
def multipolygon() -> None:
    yield QgsGeometry.fromMultiPolygonXY(
        [
            [
                [
                    QgsPointXY(0.0, 0.0),
                    QgsPointXY(2.0, 0.0),
                    QgsPointXY(2.0, 2.0),
                    QgsPointXY(0.0, 2.0),
                ]
            ],
            [
                [
                    QgsPointXY(4.0, 4.0),
                    QgsPointXY(6.0, 4.0),
                    QgsPointXY(6.0, 6.0),
                    QgsPointXY(4.0, 6.0),
                ]
            ],
        ]
    )


@pytest.fixture(scope="function")
def triangle() -> None:
    yield QgsGeometry.fromPolygonXY(
        [[QgsPointXY(-1.0, -1.0), QgsPointXY(3.0, -1.0), QgsPointXY(1.0, 2.0)]]
    )


@pytest.fixture(scope="function")
def fields() -> None:
    fields = QgsFields()
    fields.append(QgsField("fid", QVariant.Int))
    fields.append(QgsField("name", QVariant.String))
    fields.append(QgsField("extra_info", QVariant.String))
    fields.append(QgsField("extra_field_1", QVariant.Int))
    fields.append(QgsField("extra_field_2", QVariant.Int))
    yield fields


@pytest.fixture(scope="function")
def point_feature(fields, point) -> None:
    feature = QgsFeature(fields)
    feature.setGeometry(point)
    feature.setAttribute("fid", 1)
    feature.setAttribute("name", "school")
    feature.setAttribute("extra_info", "first_feature")
    feature.setAttribute("extra_field_1", 2)
    feature.setAttribute("extra_field_2", 3)
    yield feature


@pytest.fixture(scope="function")
def another_point_feature(fields, another_point) -> None:
    feature = QgsFeature(fields)
    feature.setGeometry(another_point)
    feature.setAttribute("fid", 2)
    feature.setAttribute("name", "school")
    feature.setAttribute("extra_info", "second_feature")
    feature.setAttribute("extra_field_1", 2)
    feature.setAttribute("extra_field_2", 4)
    yield feature


@pytest.fixture(scope="function")
def square_feature(fields, square) -> None:
    feature = QgsFeature(fields)
    feature.setGeometry(square)
    feature.setAttribute("fid", 1)
    feature.setAttribute("name", "square_school_area_boundary")
    yield feature


@pytest.fixture(scope="function")
def multipolygon_feature(fields, multipolygon) -> None:
    feature = QgsFeature(fields)
    feature.setGeometry(multipolygon)
    feature.setAttribute("fid", 1)
    feature.setAttribute("name", "multipolygon_school_area_boundary")
    yield feature


@pytest.fixture(scope="function")
def triangle_feature(fields, triangle) -> None:
    feature = QgsFeature(fields)
    feature.setGeometry(triangle)
    feature.setAttribute("fid", 1)
    feature.setAttribute("name", "triangular_school_area_boundary")
    yield feature


@pytest.fixture(scope="function")
def point_layer(fields, point_feature) -> None:
    layer = QgsVectorLayer("Point?crs=epsg:4326&index=yes", "test_points", "memory")
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()
    provider.addFeature(point_feature)
    layer.updateExtents()
    yield layer


@pytest.fixture(scope="function")
def two_point_layer(fields, point_feature, another_point_feature) -> None:
    layer = QgsVectorLayer("Point?crs=epsg:4326&index=yes", "test_points", "memory")
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()
    provider.addFeature(point_feature)
    provider.addFeature(another_point_feature)
    layer.updateExtents()
    yield layer


@pytest.fixture(scope="function")
def square_layer(fields, square_feature) -> None:
    layer = QgsVectorLayer(
        "Polygon?crs=epsg:4326&index=yes", "test_boundaries", "memory"
    )
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()
    provider.addFeature(square_feature)
    layer.updateExtents()
    yield layer


@pytest.fixture(scope="function")
def multipolygon_layer(fields, multipolygon_feature) -> None:
    layer = QgsVectorLayer(
        "Polygon?crs=epsg:4326&index=yes", "test_boundaries", "memory"
    )
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()
    provider.addFeature(multipolygon_feature)
    layer.updateExtents()
    yield layer


@pytest.fixture(scope="function")
def triangle_layer(fields, triangle_feature) -> None:
    layer = QgsVectorLayer(
        "Polygon?crs=epsg:4326&index=yes", "test_boundaries", "memory"
    )
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()
    provider.addFeature(triangle_feature)
    layer.updateExtents()
    yield layer


@pytest.fixture(scope="function")
def square_plus_triangle_layer(fields, square_feature, triangle_feature) -> None:
    layer = QgsVectorLayer(
        "Polygon?crs=epsg:4326&index=yes", "test_boundaries", "memory"
    )
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()
    provider.addFeature(square_feature)
    provider.addFeature(triangle_feature)
    layer.updateExtents()
    yield layer


@pytest.fixture(scope="function")
def isochrone_opts(point_layer, request) -> None:
    opts = IsochroneOpts(
        url=MOCK_URL,
        layer=point_layer,
        distance=30,
        unit=Unit.MINUTES,
        profile=Profile.WALKING,
    )
    yield opts


@pytest.fixture(scope="function")
def new_plugin(qgis_iface, isochrone_opts) -> None:
    plugin = Plugin(qgis_iface)
    plugin.initGui()
    # mock options, since mock QgisInterface does not support QgsMapLayerComboBox
    plugin.dlg.read_isochrone_options = lambda: isochrone_opts
    yield plugin
