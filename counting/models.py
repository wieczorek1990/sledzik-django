from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class Funnel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class Action(models.Model):
    name = models.CharField(max_length=255, unique=True)
    funnel = models.ForeignKey(Funnel, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name


class ActionCounter(models.Model):
    action = models.OneToOneField(Action, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.action.name

    def hit(self):
        self.count += 1
        self.save()
