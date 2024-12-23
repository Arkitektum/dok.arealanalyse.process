import json
from sys import maxsize
from typing import List, Dict
from uuid import UUID
from pydash import get
from osgeo import ogr
from .analysis import Analysis
from .result_status import ResultStatus
from .config.dataset_config import DatasetConfig
from ..services.geolett import get_geolett_data
from ..services.raster_result import get_raster_result, get_cartography_url
from ..utils.helpers.geometry import create_buffered_geometry, geometry_from_json, transform_geometry
from ..http_clients.ogc_api import query_ogc_api


class OgcApiAnalysis(Analysis):
    def __init__(self, dataset_id: UUID, config: DatasetConfig, geometry: ogr.Geometry, epsg: int, orig_epsg: int, buffer: int):
        super().__init__(dataset_id, config, geometry, epsg, orig_epsg, buffer)

    async def _run_queries(self) -> None:
        first_layer = self.config.layers[0]
        geolett_data = await get_geolett_data(first_layer.geolett_id)

        for layer in self.config.layers:
            status_code, api_response = await query_ogc_api(
                self.config.ogc_api, layer.ogc_api, self.config.geom_field, self.run_on_input_geometry, self.epsg)

            if status_code == 408:
                self.result_status = ResultStatus.TIMEOUT
                break
            elif status_code != 200:
                self.result_status = ResultStatus.ERROR
                break

            self._add_run_algorithm(f'intersect layer {layer.ogc_api}')

            if api_response is not None:
                response = self.__parse_response(api_response)

                if len(response['properties']) > 0:
                    geolett_data = await get_geolett_data(layer.geolett_id)

                    self.data = response['properties']
                    self.geometries = response['geometries']
                    self.raster_result = get_raster_result(
                        self.config.wms, layer.wms)
                    self.cartography = await get_cartography_url(
                        self.config.wms, layer.wms)
                    self.result_status = layer.result_status
                    break

        self.geolett = geolett_data

    async def _set_distance_to_object(self) -> None:
        buffered_geom = create_buffered_geometry(self.geometry, 20000, self.epsg)
        layer = self.config.layers[0]

        _, response = await query_ogc_api(self.config.ogc_api, layer.ogc_api, self.config.geom_field, buffered_geom, self.epsg)

        if response is None:
            self.distance_to_object = maxsize
            return

        distances = []

        for feature in response['features']:
            feature_geom = self.__get_geometry_from_response(feature)

            if feature_geom is not None:
                distance = round(self.run_on_input_geometry.Distance(feature_geom))
                distances.append(distance)

        distances.sort()
        self._add_run_algorithm('get distance')

        if len(distances) == 0:
            self.distance_to_object = maxsize
        else:
            self.distance_to_object = distances[0]

    def __parse_response(self, ogc_api_response: Dict) -> Dict[str, List]:
        data = {
            'properties': [],
            'geometries': []
        }

        for feature in ogc_api_response['features']:
            data['properties'].append(self.__map_properties(
                feature, self.config.properties))
            data['geometries'].append(
                self.__get_geometry_from_response(feature))

        return data

    def __map_properties(self, feature: Dict, mappings: List[str]) -> Dict:
        props = {}

        for mapping in mappings:
            key = mapping.split('.')[-1]
            value = get(feature['properties'], mapping, None)
            props[key] = value

        return props

    def __get_geometry_from_response(self, feature: Dict) -> ogr.Geometry:
        json_str = json.dumps(feature['geometry'])
        geometry = geometry_from_json(json_str)
        
        return transform_geometry(geometry, 4326, 25833)
        
