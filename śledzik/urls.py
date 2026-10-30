from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers
from rest_framework.authtoken import views as rf_views

from counting import views

router = routers.DefaultRouter()
router.register(r"tenants", views.TenantViewSet, basename="tenant")
router.register(r"projects", views.ProjectViewSet, basename="project")
router.register(r"funnels", views.FunnelViewSet, basename="funnel")
router.register(r"actions", views.ActionViewSet, basename="action")
router.register(
    r"action-counters", views.ActionCounterViewSet, basename="actioncounter"
)

urlpatterns = [
    path("", views.index, name="home"),
    path("extension/", views.extension, name="extension"),
    path("sample/", views.sample, name="sample"),
    path("admin/", admin.site.urls),
    path("auth/", include("rest_framework.urls")),
    path("auth/token/", rf_views.obtain_auth_token),
    re_path(r"^api/auth/?$", rf_views.obtain_auth_token, name="api-auth"),
    re_path(r"^api/register/?$", views.RegisterView.as_view(), name="api-register"),
    re_path(
        r"^api/register/anonymous/?$",
        views.AnonymousRegisterView.as_view(),
        name="api-register-anonymous",
    ),
    path("api/", include(router.urls)),
    path("api/actions/<int:pk>/hit/", views.ActionsCounterView.as_view()),
    path("api/funnels/<int:pk>/statistics/", views.FunnelStatisticsView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
