"""
URL configuration for spy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin

# class RoomRouter(routers.SimpleRouter):
#     routes = [
#         routers.Route(
#             url=r"^{prefix}$",
#             mapping={"get": "list", "post": "create"},
#             name="{basename}-list",
#             detail=False,
#             initkwargs={"suffix": "list"},
#         ),
#         routers.Route(
#             url=r"^{prefix}/{lookup}/$",
#             mapping={
#                 "get": "retrieve",
#                 "put": "update",
#                 "post": "create",
#                 "delete": "destroy",
#                 "patch": "partial_update",
#             },
#             name="{basename}-detail",
#             detail=True,
#             initkwargs={"suffix": "Detail"},
#         ),
#     ]
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from main.views import RoleDetailView, RoomViewSet, RoomConnectionView
from rest_framework import permissions, routers
from rest_framework.routers import DefaultRouter

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version="v1",
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r"rooms", RoomViewSet, basename="rooms")

urlpatterns = [
    path(
        "swagger.<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),  # http://127.0.0.1:8000/api/v1/rooms/(1-2-3-4-5)
    path("api/v1/rooms/<str:link>/<int:player_id>/", RoleDetailView.as_view()),
    path('api/v1/rooms/<slug:link>/connect/', RoomConnectionView.as_view(), name='room-connect'),
    path("api/v1/auth/", include("djoser.urls")),
    re_path(r"^auth/", include("djoser.urls.authtoken")),
]
