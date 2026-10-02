from rest_framework import decorators, response, viewsets

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


class ActionViewSet(viewsets.ModelViewSet):
    queryset = models.Action.objects.all()
    serializer_class = serializers.ActionSerializer

    @decorators.action(detail=True, methods=["POST"])
    def hit(self, request, pk=None):
        action = self.get_object()

        try:
            action_counter = models.ActionCounter.objects.get(action=action)
        except models.ActionCounter.DoesNotExist:
            action_counter = models.ActionCounter.objects.create(action=action)

        token = request.data.get("token")
        if not token:
            return response.Response(status=401, data={"success": "token not present"})
        if token != action_counter.action.funnel.project.tenant.token:
            return response.Response(status=401, data={"success": "invalid token"})

        action_counter.hit()

        return response.Response({"success": "ok"})


class ActionCounterViewSet(viewsets.ModelViewSet):
    queryset = models.ActionCounter.objects.all()
    serializer_class = serializers.ActionCounterSerializer
