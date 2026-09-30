from django.contrib import admin

from counting import models

admin.site.register(models.Tenant)
admin.site.register(models.Project)
admin.site.register(models.Funnel)
admin.site.register(models.Action)
admin.site.register(models.ActionCounter)
