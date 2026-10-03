from rest_framework import decorators, permissions, response, views, viewsets
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from counting import models, serializers


class TenantViewSet(viewsets.ModelViewSet):
    queryset = models.Tenant.objects.all()
    serializer_class = serializers.TenantSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer


class FunnelViewSet(viewsets.ModelViewSet):
    queryset = models.Funnel.objects.all()
    serializer_class = serializers.FunnelSerializer


@method_decorator(csrf_exempt, name="dispatch")
class ActionViewSet(viewsets.ModelViewSet):
    queryset = models.Action.objects.all()
    serializer_class = serializers.ActionSerializer

    @decorators.action(detail=True, methods=["GET"])
    @decorators.authentication_classes([])
    @decorators.permission_classes([])
    def hit(self, request, pk=None):
        token = request.data.get("token")
        if not token:
            return response.Response(status=401, data={"failure": "token not present"})

        action = self.get_object()
        if token != action.funnel.project.tenant.token:
            return response.Response(status=401, data={"failure": "invalid token"})
        models.ActionCounter.objects.create(action=action)

        return response.Response({"success": "ok"})


class ActionCounterViewSet(viewsets.ModelViewSet):
    queryset = models.ActionCounter.objects.all()
    serializer_class = serializers.ActionCounterSerializer
