from rest_framework import viewsets, decorators, response

from counting import models, serializers


class ActionCounterViewSet(viewsets.ModelViewSet):
    queryset = models.Action.objects.all()
    serializer_class = serializers.ActionSerializer

    @decorators.action(detail=True)
    def hit(self, request, pk=None):
        action = self.get_object()

        try:
            action_counter = models.ActionCounter.objects.get(action=action)
        except models.ActionCounter.DoesNotExist:
            action_counter = models.ActionCounter.objects.create(action=action)

        action_counter.hit()

        return response.Response({'success': "ok"})
