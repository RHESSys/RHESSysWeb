#from django.db import models
from django.contrib.gis.db import models
from mezzanine.pages.models import Page, RichText

class GrassEnvironment(Page, RichText):
    database = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    map_set = models.CharField(max_length=255)
    default_raster = models.CharField(max_length=255, null=True, blank=True)
    flow_table = models.FileField(upload_to='rhessysweb', null=True, blank=True) # RHESSys specific.  move later.

class FlowTable(Page):
    flow_table = models.FileField(upload_to='rhessysweb', null=True, blank=True) # RHESSys specific.  move later.

class WorldVars(models.Model):
    key = models.CharField(max_length=255, db_index=True)
    value = models.TextField()
    
class Stratum(models.Model):
    vars = models.ManyToMany(WorldVars)
    
class Patch(models.Model):
    vars = models.ManyToMany(WorldVars)
    point = models.PointField()
    zone = models.ForeignKey(Zone)
    hillslope = models.ForeignKey(Hillslope)
    basin = models.ForeignKey(Basin)
    world = models.ForeignKey(World)
    
class Zone(models.Model):
    vars = models.ManyToMany(WorldVars)
    point = models.PointField()
    hillslope = models.ForeignKey(Hillslope)

class Hillslope(models.Model):
    vars = models.ManyToMany(WorldVars)
    point = models.PointField()
    basin = models.ForeignKey(Basin)
    
class Basin(models.Model):
    vars = models.ManyToMany(WorldVars)
    point = models.PointField()
    world = models.ForeignKey(World)
    
class World(models.Model):