from rest_framework import serializers

from counting import models


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Action
        fields = "__all__"
