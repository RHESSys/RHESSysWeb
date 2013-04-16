from ga_resources import drivers, models
from osgeo import gdal, ogr, osr
from django.conf import settings
from django.contrib.gis.geos import Polygon
import importlib
import mapnik
import os

class Grass(drivers.Driver):
    def __init__(self, resource):
        super(Grass, self).__init__(data_resource=resource)
        self.env = resource.parent

        self.g = importlib.import_module('grass.script')
        self._gsetup = importlib.import_module('grass.script.setup')
        self._gsetup.init(settings.GISBASE, self.env.database, self.env.location, self.env.map_set)

    def get_data_fields(self, **kwargs):
        return self.g.raster.list_pairs('rast')

    def get_data_for_point(self, wherex, wherey, srs, fuzziness=0, **kwargs):
        return {}

    def get_metadata(self, **kwargs):
        return []

    def compute_fields(self, **kwargs):
        r = self.g.region()
        proj =  self.g.raster.read_command('g.proj', flags='j')

        s_srs = osr.SpatialReference()
        e4326 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        s_srs.ImportFromProj4(proj)
        crx = osr.CoordinateTransformation(s_srs, e4326)

        x0, y0, x1, y1 = r['w'], r['s'], r['e'], r['n']
        self.resource.spatial_metadata.native_srs = proj

        xx0, yy0, _ = crx.TransformPoint(r['w'], r['s'])
        xx1, yy1, _ = crx.TransformPoint(r['e'], r['n'])
        self.resource.spatial_metadata.native_bounding_box = Polygon.from_bbox((x0, y0, x1, y1))
        self.resource.spatial_metadata.bounding_box = Polygon.from_bbox((xx0, yy0, xx1, yy1))
        self.resource.spatial_metadata.three_d = False
        self.resource.spatial_metadata.save()

    def ready_data_resource(self, **kwargs):
        r = self.g.region()
        proj =  self.g.raster.read_command('g.proj', flags='j')

        s_srs = osr.SpatialReference()
        e3857 = osr.SpatialReference()
        e3857.ImportFromEPSG(3857)
        s_srs.ImportFromProj4(proj)
        crx = osr.CoordinateTransformation(s_srs, e3857)

        x0, y0, x1, y1 = r['w'], r['s'], r['e'], r['n']
        self.resource.spatial_metadata.native_srs = proj

        xx0, yy0, _ = crx.TransformPoint(x0, y0)
        xx1, yy1, _ = crx.TransformPoint(x1, y1)

        cached_basename = os.path.join(self.cache_path, kwargs['raster'])
        cached_tiff = cached_basename + '.tif'
        if not os.path.exists(cached_tiff):
            self.g.run_command('r.out.tiff', flags='t', input=kwargs['raster'], output=cached_tiff)

        return self.cache_path, (
            self.resource.slug,
            self.resource.spatial_metadata.native_srs,
            {
                "type" : "raster",
                "file" : cached_tiff,
                "lox" : xx0,
                "loy" : yy0,
                "hix" : xx1,
                "hiy" : yy1
            }
        )
