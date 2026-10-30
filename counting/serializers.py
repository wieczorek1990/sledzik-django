from django.contrib.auth import get_user_model
from rest_framework import serializers

from counting import models

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True, default="")

    class Meta:
        model = User
        fields = ("id", "username", "password", "email")

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
        )


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tenant
        fields = (
            "id",
            "name",
        )


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = ("id", "name", "tenant")

    def validate_tenant(self, value):
        # value is the Tenant object passed in the request
        if value.owner != self.context["request"].user:
            raise serializers.ValidationError("You do not own this tenant.")
        return value


class FunnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Funnel
        fields = ("id", "name", "project")

    def validate_project(self, value):
        # value is the Project object
        if value.tenant.owner != self.context["request"].user:
            raise serializers.ValidationError("You do not own this project.")
        return value


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Action
        fields = ("id", "name", "funnel")

    def validate_funnel(self, value):
        # value is the Funnel object
        if value.project.tenant.owner != self.context["request"].user:
            raise serializers.ValidationError("You do not own this funnel.")
        return value


class ActionCounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ActionCounter
        fields = ("id", "action", "created")

    def validate_action(self, value):
        # value is the Action object
        if value.funnel.project.tenant.owner != self.context["request"].user:
            raise serializers.ValidationError("You do not own this action.")
        return value
