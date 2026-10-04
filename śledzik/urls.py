from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken import views as rf_views

from counting import views

router = routers.DefaultRouter()
router.register(r"tenants", views.TenantViewSet)
router.register(r"projects", views.ProjectViewSet)
router.register(r"funnels", views.FunnelViewSet)
router.register(r"actions", views.ActionViewSet)
router.register(r"action-counters", views.ActionCounterViewSet)

urlpatterns = [
    path("", views.index, name="home"),
    path("admin/", admin.site.urls),
    path("auth/", include("rest_framework.urls")),
    path('auth/token/', rf_views.obtain_auth_token),
    path("api/", include(router.urls)),
    path("api/actions/<int:pk>/hit/", views.CounterView.as_view()),
    path("api/actions/<int:pk>/statistics/", views.CounterView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
