import uuid

from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from rest_framework import response, views, viewsets

from counting import models, serializers


class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TenantSerializer

    def get_queryset(self):
        return models.Tenant.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ProjectSerializer

    def get_queryset(self):
        qs = models.Project.objects.filter(tenant__owner=self.request.user)
        tenant = self.request.query_params.get("tenant")
        if tenant:
            qs = qs.filter(tenant__id=tenant)
        return qs


class FunnelViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.FunnelSerializer

    def get_queryset(self):
        qs = models.Funnel.objects.filter(project__tenant__owner=self.request.user)
        project = self.request.query_params.get("project")
        if project:
            qs = qs.filter(project__id=project)
        return qs


class ActionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ActionSerializer

    def get_queryset(self):
        return models.Action.objects.filter(
            funnel__project__tenant__owner=self.request.user
        )


class ActionCounterViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ActionCounterSerializer

    def get_queryset(self):
        return models.ActionCounter.objects.filter(
            action__funnel__project__tenant__owner=self.request.user
        )


class ActionsCounterView(views.APIView):
    authentication_classes = ()
    permission_classes = ()

    def get_object(self):
        pk = self.kwargs.get("pk")
        action = get_object_or_404(
            models.Action.objects.select_related("funnel__project__tenant"), pk=pk
        )
        return action

    def post(self, request, pk=None):
        token = request.data.get("token")

        if not token:
            return response.Response(status=401, data={"failure": "token not present"})

        try:
            submitted = uuid.UUID(str(token))
        except ValueError:
            return response.Response(status=401, data={"failure": "invalid token"})

        action = self.get_object()  # only touch the DB once we have a plausible token

        if submitted != action.funnel.project.tenant.token:
            return response.Response(
                status=401, data={"failure": "invalid authorization"}
            )

        models.ActionCounter.objects.create(action=action)

        return response.Response({"success": "ok"})


class FunnelStatisticsView(views.APIView):
    def get(self, request, pk=None):
        funnel = get_object_or_404(
            models.Funnel.objects.filter(project__tenant__owner=request.user), pk=pk
        )

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


def index_js(request):
    return render(request, "index.js")


def tests(request):
    return render(request, "tests.html")
