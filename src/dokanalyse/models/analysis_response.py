from typing import List
from osgeo import ogr
from .analysis import Analysis
from .fact_sheet import FactSheet
from ..utils.helpers.geometry import add_geojson_crs, create_buffered_geometry


class AnalysisResponse():
    result_list: List[Analysis]

    def __init__(self, input_geometry: dict, input_geometry_area: float, fact_sheet: FactSheet, municipality_number: str, municipality_name: str):
        self.input_geometry = input_geometry
        self.input_geometry_area = input_geometry_area
        self.municipality_number = municipality_number
        self.municipality_name = municipality_name
        self.fact_sheet = fact_sheet
        self.result_list = []
        self.report = None

    def to_dict(self) -> dict:
        result_list = list(
            map(lambda analysis: analysis.to_dict(), self.result_list))

        fact_list = list(
            map(lambda fact_part: fact_part.to_dict(), self.fact_sheet.fact_list))

        return {
            'resultList': result_list,
            'inputGeometry': self.input_geometry,
            'inputGeometryArea': self.input_geometry_area,
            'factSheetRasterResult': self.fact_sheet.raster_result,
            'factSheetCartography': self.fact_sheet.cartography,
            'factList': fact_list,
            'municipalityNumber': self.municipality_number,
            'municipalityName': self.municipality_name,
            'report': self.report
        }

    @classmethod
    def create(cls, geo_json: dict, geometry: ogr.Geometry, epsg: int, orig_epsg: int, buffer: int, fact_sheet: FactSheet, municipality_number: str, municipality_name: str):
        add_geojson_crs(geo_json, orig_epsg)

        if buffer > 0:
            buffered_geom = create_buffered_geometry(geometry, buffer, epsg)
            geometry_area = round(buffered_geom.GetArea(), 2)
        else:
            geometry_area = round(geometry.GetArea(), 2)

        return AnalysisResponse(geo_json, geometry_area, fact_sheet, municipality_number, municipality_name)