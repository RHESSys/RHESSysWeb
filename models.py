from django.db import models
from mezzanine.pages.models import Page, RichText
from ga_resources.models import DataResource

class GrassEnvironment(Page, RichText):
    database = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    map_set = models.CharField(max_length=255)