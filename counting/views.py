
from rest_framework import response, views, viewsets

from counting import models, serializers
import json
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from django.shortcuts import render
from django.http import JsonResponse

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
        return models.Action.objects.get(pk=pk)

    def post(self, request, pk=None):
        token = request.data.get("token")

        if not token:
            return response.Response(status=401, data={"failure": "token not present"})

        action = self.get_object()

        if token != action.funnel.project.tenant.token:
            return response.Response(status=401, data={"failure": "invalid token"})

        models.ActionCounter.objects.create(action=action)

        return response.Response({"success": "ok"})

    def get(self, _, pk=None):
        action = self.get_object()

        funnel = action.funnel
        funnel_dictionary = {}
        funnel_actions_dictionary = {}
        funnel_actions = funnel.action_set.all()
        for action in funnel_actions:
            action_counter_count = action.actioncounter_set.count()
            funnel_actions_dictionary[action.name] = action_counter_count
        funnel_dictionary[funnel.name] = funnel_actions_dictionary

        return response.Response(
            {
                "success": "ok",
                "result": funnel_dictionary,
            }
        )


# counting/views.py
import plotly.graph_objects as go
from django.shortcuts import render

def index(request):
    numbers = [39, 27.4, 20.6, 11, 2]
    stages = ["Website visit", "Downloads", "Potential customers", "Requested price", "Invoice sent"]

    fig = go.Figure(go.Funnel(
        y=stages,
        x=numbers,
        textinfo="value+percent initial",
    ))
    fig.update_layout(title="Sales Funnel")

    chart_json = fig.to_json()
    return render(request, "index.html", {"chart": chart_json})
