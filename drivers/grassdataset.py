from ga_resources import drivers, models
from osgeo import gdal, ogr, osr
from django.conf import settings
from django.contrib.gis.geos import Polygon
import importlib
import mapnik
import sys
import os
import sh

# if 'LD_LIBRARY_PATH' not in os.environ or '/usr/lib/grass64/lib' not in os.environ['LD_LIBRARY_PATH']:
os.environ['LD_LIBRARY_PATH'] = ':'.join([os.environ['LD_LIBRARY_PATH'], "/usr/lib/grass64/lib"])

import grass.script.setup as gsetup

class Grass(drivers.Driver):
    def __init__(self, resource):
        super(Grass, self).__init__(data_resource=resource)
        self.ensure_grass()

    def ensure_grass(self):
        os.environ['LD_LIBRARY_PATH'] = ':'.join([os.environ['LD_LIBRARY_PATH'], "/usr/lib/grass64/lib"])
        os.putenv("LD_LIBRARY_PATH",':'.join([os.environ['LD_LIBRARY_PATH'], "/usr/lib/grass64/lib"]))
        os.environ['DYLD_LIBRARY_PATH'] = os.path.join(settings.GISBASE, 'lib')
        os.putenv("DYLD_LIBRARY_PATH", os.path.join(settings.GISBASE, "lib"))
        os.environ['GIS_LOCK'] = str(os.getpid())
        os.putenv('GIS_LOCK',str(os.getpid()))

        self.env = self.resource.parent.grassenvironment

        self._gsetup = gsetup
        self._gsetup.init(settings.GISBASE, self.env.database, self.env.location, self.env.map_set)
        self.g = importlib.import_module("grass.script")

    def get_data_fields(self, **kwargs):
        return self.g.raster.list_pairs('rast')

    @property
    def proj(self):

        if not hasattr(self, '_proj'):
            self._proj = osr.SpatialReference()
            self._proj.ImportFromProj4( self.g.raster.read_command('g.proj', flags='j') )

        return self._proj

    @property
    def region(self):

        if not hasattr(self, '_region'):
            self._region = self.g.region()

        return self._region

    def get_data_for_point(self, wherex, wherey, srs, fuzziness=0, **kwargs):

        r_srs = osr.SpatialReference()

        if isinstance(srs, basestring):
            if srs.lower().startswith('epsg'):
                srs = int(srs[5:])
                r_srs.ImportFromEPSG(srs)
            else:
                r_srs.ImportFromProj4(srs)
        else:
            r_srs.ImportFromEPSG(srs)

        crx = osr.CoordinateTransformation(r_srs, self.proj)

        easting, northing, _ = crx.TransformPoint(wherex, wherey)
        #dataset_name = kwargs['RASTER'] if 'RASTER' in kwargs else self.env.default_raster
        #values = self.g.read_command("r.what", **{
        #    "input" : dataset_name,
        #    "null" : "None", "east_north" :
        #    "{easting},{northing}".format(easting=easting, northing=northing)
        #}).strip().split('|')

        ### everything below here is specific to rhessys and the hackathon ###

        _, _, _, patch = self.g.read_command("r.what", **{
            "input" : 'patch_5m',
            "null" : "None", "east_north" :
            "{easting},{northing}".format(easting=easting, northing=northing)
        }).strip().split('|')

        _, _, _, hillslope = self.g.read_command("r.what", **{
            "input" : 'hillslope',
            "null" : "None", "east_north" :
            "{easting},{northing}".format(easting=easting, northing=northing)
        }).strip().split('|')

        _, _, _, zone = self.g.read_command("r.what", **{
            "input" : 'hillslope',
            "null" : "None", "east_north" :
            "{easting},{northing}".format(easting=easting, northing=northing)
        }).strip().split('|')

        from RHESSysWeb import grassdatalookup, readflowtable, types

        patch = int(patch)
        hillslope = int(hillslope)
        zone = int(zone)

        fqpatch_id = types.FQPatchID(patchID=patch, hillID=hillslope, zoneID=zone)

        if not hasattr(self, 'flow_table'):
            self.flow_table = readflowtable.readFlowtable(os.path.join(settings.MEDIA_ROOT, self.env.flow_table.name))

        receivers = [fqpatch_id] + readflowtable.getReceiversForFlowtableEntry(fqpatch_id, self.flow_table)


        coords = grassdatalookup.getCoordinatesForFQPatchIDs(
            receivers,
            grassdatalookup.GRASSConfig(gisbase=settings.GISBASE, dbase=self.env.database, location=self.env.location, mapset=self.env.map_set),
            'patch_5m','hillslope','hillslope')

        print len(coords)

        xrc = osr.CoordinateTransformation(self.proj, r_srs)
        rasters = self.g.raster.list_strings('rast')
        def best_type(k):
            try:
                return int(k)
            except:
                try:
                    return float(k)
                except:
                    return k

        coords = [{
                      "type" : "Feature",
                      "geometry" : { "type" : "Point", "coordinates" : xrc.TransformPoint(a.easting, a.northing)[0:2] },
                      "properties" : dict(zip(
                          rasters,
                          [best_type(k) for k in self.g.read_command('r.what', input=rasters, east_north='{e},{n}'.format(e=a.easting, n=a.northing)).strip().split('|')]
                      ))
                  } for a in coords]

        return {
            "type" : "FeatureCollection",
            "features" : coords
        }

        ### everything above here is specific to rhessys and the hackathon ###

        #return {
        #    "easting" : easting,
        #    "northing" : northing,
        #    dataset_name : values[-1]
        #}

    def get_metadata(self, **kwargs):
        return []

    def compute_fields(self, **kwargs):

        r = self.region
        proj =  self.proj

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

        r = self.region
        s_srs =  self.proj

        e3857 = osr.SpatialReference()
        e3857.ImportFromEPSG(3857)
        crx = osr.CoordinateTransformation(s_srs, e3857)

        x0, y0, x1, y1 = r['w'], r['s'], r['e'], r['n']
        self.resource.spatial_metadata.native_srs = s_srs.ExportToProj4()

        xx0, yy0, _ = crx.TransformPoint(x0, y0)
        xx1, yy1, _ = crx.TransformPoint(x1, y1)

        raster = kwargs['RASTER'] if 'RASTER' in kwargs else self.env.default_raster
        cached_basename = os.path.join(self.cache_path, raster)
        cached_tiff = cached_basename + '.tif'
        if not os.path.exists(cached_tiff):
            self.g.run_command('r.out.tiff', flags='t', input=raster, output=cached_basename + ".native.tif")
            with open(cached_basename+'.native.prj', 'w') as prj:
                prj.write(s_srs.ExportToWkt())

            sh.gdalwarp("-s_srs", cached_basename + '.native.prj', "-t_srs", "EPSG:3857", cached_basename + '.native.tif', cached_tiff)

        return self.cache_path, (
            self.resource.slug,
            e3857.ExportToProj4(),
            {
                "type" : "raster",
                "file" : cached_tiff,
                "lox" : str(xx0),
                "loy" : str(yy0),
                "hix" : str(xx1),
                "hiy" : str(yy1)
            }
        )

driver = Grass