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
from main.views import RoleDetailView, RoomViewSet, RoleDetailView
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import routers


class RoomRouter(routers.SimpleRouter):
    routes = [
        routers.Route(
            url=r"^{prefix}$",
            mapping={"get": "list",
                     "post": "create"},
            name="{basename}-list",
            detail=False,
            initkwargs={"suffix": "list"},
        ),
        routers.Route(
            url=r"^{prefix}/{lookup}/$",
            mapping={"get": "retrieve",
                     "put": "update",
                     "post": "create",
                     "delete": "destroy",
                     "patch": "partial_update"},
            name="{basename}-detail",
            detail=True,
            initkwargs={"suffix": "Detail"},
        ),
    ]

router = RoomRouter()
router.register(r"rooms", RoomViewSet, basename="rooms")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),  # http://127.0.0.1:8000/api/v1/rooms/
    path("api/v1/rooms/<str:link>/<int:player_id>/", RoleDetailView.as_view()),
    path("api/v1/auth/", include("djoser.urls")),
    re_path(r"^auth/", include("djoser.urls.authtoken")),
]
