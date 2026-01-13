from datetime import timedelta
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
import secrets

from .models import LocationsGroup, Room, RoomConnection, Locations
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
    RoomConnectionSerializer,
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

class RoomConnectionView():
    queryset = RoomConnection.objects.all()
    serializer_class = RoomConnectionSerializer

class RoomConnectionView(APIView):
    def get(self, request, link):
        # Получаем комнату по slug (link)
        # GET запрос направлять по уникальной ссылке
        room = Room.objects.filter(link=link).first()

        if not room:
            return Response({"detail": "Комната не найдена."}, status=status.HTTP_404_NOT_FOUND)

        # Получаем device_hash из query параметра или заголовка
        device_hash = request.query_params.get("device_hash") or request.headers.get("X-Device-Hash")

        # Запрос должен быть такой
        # GET /api/rooms/spy-room-123/connect/?device_hash=abc123

        if not device_hash:
            return Response({"detail": "Передай device_hash в query (?device_hash=...) или в заголовке X-Device-Hash."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Генерация случайного номера игрока от 1 до num_of_players
        random_player_number = secrets.randbelow(room.num_of_players) + 1

        # Проверяем, является ли игрок шпионом
        if room.spy_id == random_player_number:
            return Response({"detail": "Ты шпион!"}, status=status.HTTP_200_OK)
        else:
            # Присваиваем локацию для игрока (используем текущую локацию комнаты)
            location_to_show = Locations.objects.filter(id=room.current_location.id)

        # Создаем RoomConnection
        room_connection = RoomConnection.objects.create(
            room=room,
            my_room_id=random_player_number,
            device_hash=device_hash,
        )

        # Добавляем локацию в ManyToManyField
        room_connection.location_to_show.set(location_to_show)

        # Сериализуем и возвращаем данные
        data = RoomConnectionSerializer(room_connection).data
        return Response(data, status=status.HTTP_201_CREATED)
    
# НЕ забудь бизнес логику создания и изменения комнаты сделать, гений))

# Внутри комнаты сделать кнопку узнать локацию
# При нажатии отправляется GET запрос v1/api/get_role условно
# Там как раз и выдаётся ID в комнате, хэш браузера, и соответственно роль
# И записывается всё это в БД, и передаётся в ответе по запросу
