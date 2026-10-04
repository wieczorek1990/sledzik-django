from rest_framework import serializers

from counting import models


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tenant
        fields = ("name",)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = ("name", "tenant")
        read_only_fields = ("tenant",)

        def validate_tenant(self, value):
            if value.owner != self.context["request"].user:
                raise serializers.ValidationError("You do not own this tenant.")
            return value


class FunnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Funnel
        fields = ("name", "project")
        read_only_fields = ("project",)


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Action
        fields = ("name", "funnel")
        read_only_fields = ("funnel",)


class ActionCounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ActionCounter
        fields = ("action", "created")
