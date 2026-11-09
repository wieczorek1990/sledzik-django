import uuid

from django.conf import settings
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
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.vary import vary_on_headers
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


class LogoutView(views.APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return response.Response({"detail": "Logged out"}, status=200)


class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TenantSerializer

    def get_queryset(self):
        return models.Tenant.objects.filter(owners=self.request.user)

    def perform_create(self, serializer):
        with transaction.atomic():
            tenant = serializer.save()
            tenant.owners.add(self.request.user)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ProjectSerializer

    def get_queryset(self):
        qs = models.Project.objects.filter(tenant__owners=self.request.user)
        tenant = self.request.query_params.get("tenant")
        if tenant:
            qs = qs.filter(tenant__id=tenant)
        return qs


class FunnelViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.FunnelSerializer

    def get_queryset(self):
        qs = models.Funnel.objects.filter(project__tenant__owners=self.request.user)
        project = self.request.query_params.get("project")
        if project:
            qs = qs.filter(project__id=project)
        return qs


class ActionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ActionSerializer

    def get_queryset(self):
        return models.Action.objects.filter(
            funnel__project__tenant__owners=self.request.user
        )


class TokenActionsView(views.APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        token_data = request.data.get("token", "")
        if isinstance(token_data, dict):
            token_data = token_data.get("token", "")
        try:
            token = uuid.UUID(str(token_data).strip())
        except (ValueError, AttributeError):
            return response.Response({"failure": "invalid token"}, status=401)
        tenant = models.Tenant.objects.filter(token=token).first()
        if tenant is None:
            return response.Response({"failure": "invalid token"}, status=401)
        actions = models.Action.objects.filter(funnel__project__tenant=tenant)
        return response.Response(serializers.ActionSerializer(actions, many=True).data)


class ActionCounterViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ActionCounterSerializer

    def get_queryset(self):
        return models.ActionCounter.objects.filter(
            action__funnel__project__tenant__owners=self.request.user
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
        if isinstance(token, dict):
            token = token.get("token")

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


class CurrentUserView(views.APIView):
    def get(self, request):
        return response.Response(
            {"id": request.user.pk, "username": request.user.get_username()}
        )


class GlobalVisitsView(views.APIView):
    def get(self, request):
        count = models.ActionCounter.objects.filter(
            action__funnel__project__tenant__owners=request.user
        ).count()
        return response.Response({"visits": count})


class FunnelStatisticsView(views.APIView):
    def get(self, request, pk=None):
        funnel = get_object_or_404(
            models.Funnel.objects.filter(project__tenant__owners=request.user), pk=pk
        )

        funnel_actions = funnel.action_set.annotate(n=Count("actioncounter")).order_by(
            "order", "pk"
        )
        funnel_actions_dictionary = {a.name: a.n for a in funnel_actions}

        granularity = request.query_params.get("granularity", "1min")
        fixed_windows = {
            "30min": 1800,
            "15min": 900,
            "5min": 300,
            "1min": 60,
            "12sec": 12,
        }
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
                {
                    "granularity": "Choose created, 12sec, 1min, 5min, 15min, 30min, hour, day, month, or year."
                },
                status=400,
            )

        grouping = ["period", "action__name"]

        counters = models.ActionCounter.objects.filter(
            action__funnel=funnel,
            action__funnel__project__tenant__owners=request.user,
        ).annotate(period=trunc_fn)
        time_series_qs = (
            counters.values(*grouping).annotate(count=Count("id")).order_by(*grouping)
        )

        def format_created(entry):
            period = entry["period"]
            return period.isoformat() if period is not None else None

        time_series = [
            {
                "created": format_created(entry),
                "action": entry["action__name"],
                "count": entry["count"],
            }
            for entry in time_series_qs
        ]
        viewer_grouping = [key for key in grouping if key != "action__name"]
        unique_viewers = [
            {"created": format_created(entry), "count": entry["count"]}
            for entry in counters.values(*viewer_grouping)
            .annotate(count=Count("user_id", distinct=True))
            .order_by(*viewer_grouping)
        ]

        return response.Response(
            {
                "success": "ok",
                "result": {funnel.name: funnel_actions_dictionary},
                "action_order": [a.name for a in funnel_actions],
                "time_series": time_series,
                "unique_viewers": unique_viewers,
            }
        )


def index(request):
    return render(request, "index.html")


@vary_on_headers("Sec-Fetch-Dest")
def extension(request):
    if request.headers.get("Sec-Fetch-Dest") == "document":
        return render(
            request,
            "extension.html",
            {
                "source": render_to_string("extension.js", request=request),
            },
        )
    return render(
        request, "extension.js", content_type="application/javascript; charset=utf-8"
    )


def sample(request):
    return render(request, "sample.html")


def extension_js(request):
    return render(
        request, "extension.js", content_type="application/javascript; charset=utf-8"
    )


def sample_js(request):
    return render(
        request, "sample.js", content_type="application/javascript; charset=utf-8"
    )


def style_css(request):
    return render(request, "style.css", content_type="text/css")


def favicon(request):
    return FileResponse(
        (settings.BASE_DIR / "counting/static/counting/favicon.ico").open("rb"),
        content_type="image/vnd.microsoft.icon",
    )


@staff_member_required
def links(request):
    return render(request, "links.html")
