from datetime import timedelta
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import LocationsGroup, Room, UpdateHistory
from .roomlogic import (
    MyMixin,
    creator_id,
    join_room,
    refresh_room,
    room_create,
    set_id_of_connected_player,
)
from .serializers import (
    LocationsGroupSerializer,
    RoleSerializer,
    RoomListSerializer,
    RoomSerializer,
)


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated | AllowAny]
    filter = [SearchFilter]
    search_fields = ["name"]

    def get_permissions(self):
        if self.action == "list" or self.action == "retrieve":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if self.action == "list" or self.action == "retrieve":
            return Room.objects.all()
        elif self.action in ["update", "destroy"]:
            room = Room.objects.get(pk=self.kwargs["pk"])
            if room.owner != user:
                raise PermissionDenied(
                    "Вы не можете изменять или удалять эту комнату, так как вы не её владелец."
                )
            return Room.objects.filter(owner=user)
        return Room.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        room = self.get_object()
        if room.owner != request.user:
            raise PermissionDenied(
                "Вы не можете обновить эту комнату, так как вы не её владелец."
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        room = self.get_object()
        if room.owner != request.user:
            raise PermissionDenied(
                "Вы не можете удалить эту комнату, так как вы не её владелец."
            )

        return super().destroy(request, *args, **kwargs)


# Внутри комнаты сделать кнопку узнать локацию
# При нажатии отправляется GET запрос v1/api/get_role условно
# Там как раз и выдаётся ID в комнате, хэш браузера, и соответственно роль
# И записывается всё это в БД, и передаётся в ответе по запросу
