from django.db import models
import uuid


class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    token = models.CharField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=255)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name

    class Meta:
        unique_together = ["name", "tenant"]


class Funnel(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name

    class Meta:
        unique_together = ["name", "project"]


class Action(models.Model):
    name = models.CharField(max_length=255)
    funnel = models.ForeignKey(Funnel, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name

    class Meta:
        unique_together = ["name", "funnel"]


class ActionCounter(models.Model):
    action = models.OneToOneField(Action, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.action.name

    def hit(self):
        self.count += 1
        self.save()
