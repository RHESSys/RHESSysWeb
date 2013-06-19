from ga_resources import drivers, models
from osgeo import gdal, ogr, osr
from django.conf import settings
from django.contrib.gis.geos import Polygon
import importlib
import os
import sh

import tempfile
from RHESSysWeb.grassdatalookup import GrassDataLookup

class Grass(drivers.Driver):
    def __init__(self, resource):
        super(Grass, self).__init__(data_resource=resource)
        self.env = self.resource.parent.grassenvironment
        self.ensure_grass()
        self._grassdatalookup = GrassDataLookup(self.g, self.grass_lowlevel)

    def ensure_grass(self):
        if 'GISRC' not in os.environ:
            os.environ['LD_LIBRARY_PATH'] = ':'.join([os.environ['LD_LIBRARY_PATH'], "/usr/lib/grass64/lib"])
            os.putenv("LD_LIBRARY_PATH",':'.join([os.environ['LD_LIBRARY_PATH'], "/usr/lib/grass64/lib"]))
            os.environ['DYLD_LIBRARY_PATH'] = os.path.join(settings.GISBASE, 'lib')
            os.putenv("DYLD_LIBRARY_PATH", os.path.join(settings.GISBASE, "lib"))
            os.environ['GIS_LOCK'] = str(os.getpid())
            os.putenv('GIS_LOCK',str(os.getpid()))
            os.environ['GISRC'] = self._initializeGrassrc()
            os.putenv('GISRC', os.environ['GISRC'])

        if 'LOCATION_NAME' not in os.environ:
            os.environ['LOCATION_NAME'] = self.env.location
            os.putenv('LOCATION_NAME', self.env.location)

        if not hasattr(self, '_gsetup'):
            self._gsetup = importlib.import_module('grass.script.setup')
            self.g = importlib.import_module("grass.script")
            self.grass_lowlevel = importlib.import_module('grass.lib.gis')

        self.grass_lowlevel.G_gisinit('')
        self._gsetup.init(settings.GISBASE, self.env.database, self.env.location, self.env.map_set)

    def _initializeGrassrc(self):
        grassRcFile = tempfile.NamedTemporaryFile(prefix='grassrc-', delete=False)
        grassRcContent = "GISDBASE: %s\nLOCATION_NAME: %s\nMAPSET: %s\n" % \
            (self.env.database, self.env.location, self.env.map_set)
        grassRcFile.write(grassRcContent)
        return grassRcFile.name

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

        from RHESSysWeb import flowtableio, rhessystypes

        patch = int(patch)
        hillslope = int(hillslope)
        zone = int(zone)

        fqpatch_id = rhessystypes.FQPatchID(patchID=patch, hillID=hillslope, zoneID=zone)

        if not hasattr(self, 'flow_table'):
            self.flow_table = flowtableio.readFlowtable(os.path.join(settings.MEDIA_ROOT, self.env.flow_table.name))

        total_gamma = flowtableio.getEntryForFlowtableKey(fqpatch_id, self.flow_table).totalGamma

        receivers = [fqpatch_id] + flowtableio.getReceiversForFlowtableEntry(fqpatch_id, self.flow_table)

        coords = self._grassdatalookup.getCoordinatesForFQPatchIDs(
            receivers,
            'patch_5m','hillslope','hillslope')

        xrc = osr.CoordinateTransformation(self.proj, r_srs)
        self.ensure_grass()

        rasters = self.g.list_strings('rast')
        def best_type(k):
            try:
                return int(k)
            except:
                try:
                    return float(k)
                except:
                    return k

        c = []
        for i, (fqpatchid, pairs) in enumerate(coords.items()):
            for a in pairs:
                c.append({
                      "type" : "Feature",
                      "geometry" : { "type" : "Point", "coordinates" : xrc.TransformPoint(a.easting, a.northing)[0:2] },
                      "properties" : dict(zip(
                          rasters,
                          [best_type(k) for k in self.g.read_command('r.what', input=rasters, east_north='{e},{n}'.format(e=a.easting, n=a.northing)).strip().split('|')]
                      ))
                })
                c[-1]['properties']['fqpatchid'] = [fqpatchid.patchID, fqpatchid.zoneID, fqpatchid.hillID]
                if hasattr(receivers[i], 'gamma'):
                    c[-1]['properties']['gamma'] = receivers[i].gamma
                else:
                    c[-1]['properties']['total_gamma'] = total_gamma


        print len(c), len(coords), len(receivers), coords.keys()
        
        return {
            "type" : "FeatureCollection",
            "features" : c
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
        s_srs =  self.proj

        e4326 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        crx = osr.CoordinateTransformation(s_srs, e4326)

        x0, y0, x1, y1 = r['w'], r['s'], r['e'], r['n']
        self.resource.spatial_metadata.native_srs = s_srs

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
            self.g.run_command('r.out.gdal', nodata='0', input=raster, output=cached_basename + ".native.tif")
            with open(cached_basename+'.native.prj', 'w') as prj:
                prj.write(s_srs.ExportToWkt())

            sh.gdalwarp("-s_srs", cached_basename + '.native.prj', "-t_srs", "EPSG:3857", cached_basename + '.native.tif', cached_tiff)

        return self.cache_path, (
            self.resource.slug,
            e3857.ExportToProj4(),
            {
                "type" : "gdal",
                "file" : cached_tiff,
            }
        )

driver = Grass
