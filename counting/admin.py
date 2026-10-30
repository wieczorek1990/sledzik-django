from django.contrib import admin

from counting import models


class TenantAdmin(admin.ModelAdmin):
    readonly_fields = ("token",)
    filter_horizontal = ("owners",)


class ActionCounterAdmin(admin.ModelAdmin):
    list_filter = ("created",)
    readonly_fields = ("created",)


class ActionInline(admin.TabularInline):
    model = models.Action
    fields = ("name", "order")
    extra = 0


class FunnelAdmin(admin.ModelAdmin):
    inlines = (ActionInline,)


class ActionAdmin(admin.ModelAdmin):
    list_display = ("name", "funnel", "order")
    list_editable = ("order",)
    list_filter = ("funnel",)


admin.site.register(models.Tenant, TenantAdmin)
admin.site.register(models.Project)
admin.site.register(models.Funnel, FunnelAdmin)
admin.site.register(models.Action, ActionAdmin)
admin.site.register(models.ActionCounter, ActionCounterAdmin)
