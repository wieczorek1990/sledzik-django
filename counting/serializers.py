from typing import ClassVar

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
    owners = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False, allow_empty=False
    )

    class Meta:
        model = models.Tenant
        fields = (
            "id",
            "name",
            "owners",
        )


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = ("id", "name", "tenant")

    def validate_tenant(self, value):
        # value is the Tenant object passed in the request
        if not value.owners.filter(pk=self.context["request"].user.pk).exists():
            raise serializers.ValidationError("You do not own this tenant.")
        return value


class FunnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Funnel
        fields = ("id", "name", "project")

    def validate_project(self, value):
        # value is the Project object
        if not value.tenant.owners.filter(pk=self.context["request"].user.pk).exists():
            raise serializers.ValidationError("You do not own this project.")
        return value


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Action
        fields = ("id", "name", "funnel", "order")
        extra_kwargs: ClassVar[dict[str, dict[str, int]]] = {"order": {"min_value": 0}}

    def validate_funnel(self, value):
        # value is the Funnel object
        if not value.project.tenant.owners.filter(
            pk=self.context["request"].user.pk
        ).exists():
            raise serializers.ValidationError("You do not own this funnel.")
        return value


class ActionCounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ActionCounter
        fields = ("id", "action", "created")

    def validate_action(self, value):
        # value is the Action object
        if not value.funnel.project.tenant.owners.filter(
            pk=self.context["request"].user.pk
        ).exists():
            raise serializers.ValidationError("You do not own this action.")
        return value
