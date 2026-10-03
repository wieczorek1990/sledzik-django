from django.contrib import admin

from counting import models


class TenantAdmin(admin.ModelAdmin):
    readonly_fields = ("token",)


class ActionCounterAdmin(admin.ModelAdmin):
    list_filter = ("created",)


admin.site.register(models.Tenant, TenantAdmin)
admin.site.register(models.Project)
admin.site.register(models.Funnel)
admin.site.register(models.Action)
admin.site.register(models.ActionCounter, ActionCounterAdmin)
