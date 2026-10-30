import uuid

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import (
    BigIntegerField,
    Count,
    DateTimeField,
    DurationField,
    ExpressionWrapper,
    F,
    Value,
)
from django.db.models.functions import (
    Cast,
    ExtractMinute,
    ExtractSecond,
    Floor,
    TruncDay,
    TruncHour,
    TruncMonth,
    TruncYear,
)
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


class AnonymousRegisterView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        with transaction.atomic():
            user = get_user_model().objects.create_user(
                username=f"anonymous_{uuid.uuid4().hex}", password=None
            )
            token = Token.objects.create(user=user)
        return response.Response(
            {"token": token.key, "username": user.username, "id": user.id},
            status=201,
        )


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

        granularity = request.query_params.get("granularity", "1min")
        fixed_windows = {"30min": 1800, "15min": 900, "5min": 300, "1min": 60, "12sec": 12}
        calendar_windows = {
            "hour": TruncHour,
            "day": TruncDay,
            "month": TruncMonth,
            "year": TruncYear,
        }
        if granularity in calendar_windows:
            trunc_fn = calendar_windows[granularity]("created")
        elif granularity in fixed_windows:
            seconds = fixed_windows[granularity]
            elapsed = ExtractMinute("created") * 60 + ExtractSecond("created")
            offset = ExpressionWrapper(
                Cast(
                    Floor(elapsed / Value(float(seconds))) * Value(seconds * 1_000_000),
                    output_field=BigIntegerField(),
                ),
                output_field=DurationField(),
            )
            trunc_fn = ExpressionWrapper(
                TruncHour("created") + offset, output_field=DateTimeField()
            )
        elif granularity == "created":
            trunc_fn = F("created")
        else:
            return response.Response(
                {"granularity": "Choose created, 12sec, 1min, 5min, 15min, 30min, hour, day, month, or year."}, status=400
            )

        grouping = ["period", "action__name"]
        if granularity == "created":
            grouping.append("created_ns")

        time_series_qs = (
            models.ActionCounter.objects.filter(
                action__funnel=funnel,
                action__funnel__project__tenant__owner=request.user,
            )
            .annotate(period=trunc_fn)
            .values(*grouping)
            .annotate(count=Count("id"))
            .order_by(*grouping)
        )

        def format_created(entry):
            period = entry["period"]
            if granularity == "created" and entry["created_ns"] is not None:
                nanoseconds = entry["created_ns"] % 1_000_000_000
                timestamp = period.isoformat(timespec="seconds")
                return f"{timestamp[:19]}.{nanoseconds:09d}{timestamp[19:]}"
            return period.isoformat() if period is not None else None

        time_series = [
            {
                "created": format_created(entry),
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
