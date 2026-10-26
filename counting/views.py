import uuid

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from django.shortcuts import get_object_or_404, render
from rest_framework import permissions, response, views, viewsets
from rest_framework.authtoken.models import Token

from counting import models, serializers


class RegisterView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = serializers.RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return response.Response(
                {"token": token.key, "username": user.username, "id": user.id},
                status=201,
            )
        return response.Response(serializer.errors, status=400)


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
    def get_object(self):
        pk = self.kwargs.get("pk")
        action = get_object_or_404(
            models.Action.objects.select_related("funnel__project__tenant"), pk=pk
        )
        return action

    def post(self, request, pk=None):
        token = request.data.get("token")

        if not token or (isinstance(token, str) and not token.strip()):
            return response.Response(status=401, data={"failure": "token not present"})

        try:
            token_string = str(token).strip()
            submitted = uuid.UUID(token_string)
        except (ValueError, AttributeError):
            return response.Response(status=401, data={"failure": "invalid token"})

        action = self.get_object()  # only touch the DB once we have a plausible token

        if submitted != action.funnel.project.tenant.token:
            return response.Response(
                status=401, data={"failure": "invalid authorization"}
            )

        models.ActionCounter.objects.create(action=action, user=request.user)

        return response.Response({"success": "ok"})


class FunnelStatisticsView(views.APIView):
    def get(self, request, pk=None):
        funnel = get_object_or_404(
            models.Funnel.objects.filter(project__tenant__owner=request.user), pk=pk
        )

        funnel_actions = funnel.action_set.annotate(n=Count("actioncounter"))
        funnel_actions_dictionary = {a.name: a.n for a in funnel_actions}

        granularity = request.query_params.get("granularity", "day")
        if granularity == "hour":
            trunc_fn = TruncHour("created")
        elif granularity == "month":
            trunc_fn = TruncMonth("created")
        else:
            trunc_fn = TruncDate("created")

        time_series_qs = (
            models.ActionCounter.objects.filter(
                action__funnel=funnel,
                action__funnel__project__tenant__owner=request.user,
            )
            .annotate(period=trunc_fn)
            .values("period", "action__name")
            .annotate(count=Count("id"))
            .order_by("period", "action__name")
        )

        time_series = [
            {
                "date": (
                    (
                        entry["period"].isoformat()
                        if hasattr(entry["period"], "isoformat")
                        else str(entry["period"])
                    )
                    if entry["period"]
                    else None
                ),
                "action": entry["action__name"],
                "count": entry["count"],
            }
            for entry in time_series_qs
        ]

        return response.Response(
            {
                "success": "ok",
                "result": {funnel.name: funnel_actions_dictionary},
                "time_series": time_series,
            }
        )


@staff_member_required
def index(request):
    return render(request, "index.html")


def extension(request):
    return render(request, "extension.js", content_type="application/javascript")


def sample(request):
    return render(request, "sample.html")
