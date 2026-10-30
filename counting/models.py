import uuid

from django.conf import settings
from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    token = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="tenants"
    )

    def __str__(self) -> str:
        return f"{self.name}"


class Project(models.Model):
    name = models.CharField(max_length=255)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.tenant.name}: {self.name}"

    class Meta:
        unique_together = ("name", "tenant")


class Funnel(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.project.name}: {self.name}"

    class Meta:
        unique_together = ("name", "project")


class Action(models.Model):
    name = models.CharField(max_length=255)
    funnel = models.ForeignKey(Funnel, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.pk}: {self.funnel.name}: {self.name}"

    class Meta:
        unique_together = ("name", "funnel")


class ActionCounter(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="action_counters",
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.action.name}"
