from django.shortcuts import get_object_or_404, render
from rest_framework import response, views, viewsets
import uuid
from django.db.models import Count

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


class ActionCounterViewSet(viewsets.ModelViewSet):
    queryset = models.ActionCounter.objects.all()
    serializer_class = serializers.ActionCounterSerializer


class CounterView(views.APIView):
    authentication_classes = ()
    permission_classes = ()

    def get_object(self):
        pk = self.kwargs.get("pk")
        action = get_object_or_404(
            models.Action.objects.select_related("funnel__project__tenant"),
            pk=pk)
        return action

    def post(self, request, pk=None):
        token = request.data.get("token")

        if not token:
            return response.Response(status=401, data={"failure": "token not present"})

        action = self.get_object()

        try:
            submitted = uuid.UUID(str(token))
        except ValueError:
            return response.Response(status=401, data={"failure": "invalid token"})
        if submitted != action.funnel.project.tenant.token:
            return response.Response(status=401, data={"failure": "invalid authorization"})

        models.ActionCounter.objects.create(action=action)

        return response.Response({"success": "ok"})


class FunnelStatisticsView(views.APIView):
    def get(self, request, pk=None):
        funnel = get_object_or_404(models.Funnel, pk=pk)

        funnel_actions = funnel.action_set.annotate(n=Count("actioncounter"))
        funnel_actions_dictionary = {a.name: a.n for a in funnel_actions}

        return response.Response(
            {
                "success": "ok",
                "result": {funnel.name: funnel_actions_dictionary},
            }
        )


def index(request):
    return render(request, "index.html")
