from rest_framework import serializers

from counting import models


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tenant
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = "__all__"


class FunnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Funnel
        fields = "__all__"


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Action
        fields = "__all__"


class ActionCounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ActionCounter
        fields = "__all__"
