from django.db import models
from mezzanine.pages.models import Page, RichText

class GrassEnvironment(Page, RichText):
    database = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    map_set = models.CharField(max_length=255)
    default_raster = models.CharField(max_length=255, null=True, blank=True)
    flow_table = models.FileField(upload_to='rhessysweb', null=True, blank=True) # RHESSys specific.  move later.