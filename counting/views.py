
from rest_framework import response, views, viewsets
from django.shortcuts import get_object_or_404

from counting import models, serializers
from django.shortcuts import render

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

    @staticmethod
    def get(_, pk=None):
        funnel = get_object_or_404(models.Funnel, pk=pk)

        funnel_actions_dictionary = {
            action.name: action.actioncounter_set.count()
            for action in funnel.action_set.all()  # noqa
        }

        return response.Response({
            "success": "ok",
            "result": {funnel.name: funnel_actions_dictionary},
        })


def index(request):
    from rest_framework.authtoken.models import Token

    context = {"api_token": Token.objects.first().key}

    return render(request, "index.html", context=context)
