from mezzanine.pages.admin import PageAdmin
from RHESSysWeb import models
from django.contrib import admin

admin.site.register(models.GrassEnvironment, PageAdmin)