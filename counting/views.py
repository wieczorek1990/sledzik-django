from rest_framework import viewsets, decorators, response, permissions

from counting import models, serializers


class ActionCounterViewSet(viewsets.ModelViewSet):
    queryset = models.Action.objects.all()
    serializer_class = serializers.ActionSerializer
    permission_classes = (permissions.AllowAny,)

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

        return response.Response({'success': "ok"})
