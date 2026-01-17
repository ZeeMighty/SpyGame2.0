import random
import secrets
from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Locations, LocationsGroup, Room, RoomConnection
from .serializers import (
    LocationsGroupSerializer,
    RoomConnectionSerializer,
    RoomSerializer,
)

# Функции с логикой, которые можно вынести в отдельный файл


def room_restart(serializer):
    num_of_players = serializer.validated_data["num_of_players"]
    spy_id = random.randint(1, num_of_players)

    locations_group = serializer.validated_data["locations_group"]
    locations = locations_group.locations.all()
    random_location = random.choice(locations)
    return spy_id, random_location


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated | AllowAny]
    filter = [SearchFilter]
    search_fields = ["name"]
    lookup_field = "link"

    def get_permissions(self):
        # ВАЖНО: имя экшена здесь совпадает с именем функции
        if self.action in ["list", "retrieve", "verify_password"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Room.objects.none()
        
        # Для чтения и проверки пароля доступны все комнаты
        if self.action in ["list", "retrieve", "verify_password"]:
            return Room.objects.all()
        
        # Для изменений — только свои (дополнительная страховка)
        if self.request.user.is_authenticated:
            return Room.objects.filter(owner=self.request.user)
        return Room.objects.none()

    def perform_create(self, serializer):
        spy_id, random_location = room_restart(serializer)
        serializer.save(
            owner=self.request.user, spy_id=spy_id, current_location=random_location
        )

    def perform_update(self, serializer):
        room_instance = self.get_object()
        spy_id, random_location = room_restart(serializer)
        RoomConnection.objects.filter(room=room_instance).delete()
        serializer.save(
            owner=self.request.user, spy_id=spy_id, current_location=random_location
        )

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
    
    @action(
        detail=True, 
        methods=['post'], 
        url_path='check-password',
        permission_classes=[AllowAny],
        authentication_classes=[]  # <--- Ключевое исправление! Игнорируем токены, чтобы избежать 401
    )
    def verify_password(self, request, link=None):
        room = self.get_object()
        password = request.data.get('password')

        if not room.password:
            return Response({"success": True}, status=status.HTTP_200_OK)

        # Так как authentication_classes=[], request.user будет Anonymous.
        # Это нормально, проверяем просто пароль.
        if password and room.check_password(password):
            return Response({"success": True}, status=status.HTTP_200_OK)
        
        return Response(
            {"success": False, "message": "Неверный пароль"}, 
            status=status.HTTP_403_FORBIDDEN
        )

    # Вспомогательный метод для проверки владения
    def check_owner(self, obj):
        if obj.owner != self.request.user:
            raise PermissionDenied("Доступ запрещен.")


class RoomConnectionView(APIView):
    def get(self, request, link):
        room = Room.objects.filter(link=link).first()
        if not room:
            return Response(
                {"detail": "Комната не найдена."}, status=status.HTTP_404_NOT_FOUND
            )

        # Получаем device_hash из query параметра или заголовка
        device_hash = request.query_params.get("device_hash") or request.headers.get(
            "X-Device-Hash"
        )
        # Запрос должен быть такой
        # GET /api/rooms/spy-room-123/connect/?device_hash=abc123
        if not device_hash:
            return Response(
                {
                    "detail": "Передай device_hash в query (?device_hash=...) или в заголовке X-Device-Hash."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_connection = RoomConnection.objects.filter(room=room, device_hash=device_hash).first()
        if old_connection:
            room_connection = old_connection
        else:

            if RoomConnection.objects.filter(room=room).count() >= room.num_of_players:
                return Response({"detail": "Комната заполнена!"}, status=status.HTTP_403_FORBIDDEN)

            taken_ids = RoomConnection.objects.filter(room=room).values_list('my_room_id', flat=True)
            all_possible_ids = set(range(1, room.num_of_players + 1))
            available_ids = list(all_possible_ids - set(taken_ids))
            random_player_number = random.choice(available_ids)

            if room.spy_id == random_player_number:
                room_connection = RoomConnection.objects.create(
                    room=room,
                    my_room_id=random_player_number,
                    device_hash=device_hash,
                )
                return Response({"detail": "Ты шпион!"}, status=status.HTTP_200_OK)
            else:
                # Присваиваем локацию для игрока (используем текущую локацию комнаты)
                try:
                    location_to_show = Locations.objects.get(id=room.current_location.id)
                except Locations.DoesNotExist:
                    return Response(
                        {"detail": "Локация не найдена."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            # Создаем RoomConnection
            room_connection = RoomConnection.objects.create(
                room=room,
                my_room_id=random_player_number,
                device_hash=device_hash,
            )

            # Добавляем локацию в ManyToManyField
            room_connection.location_to_show.set([location_to_show])

            # Сериализуем и возвращаем данные
        data = RoomConnectionSerializer(room_connection).data
        return Response(data, status=status.HTTP_201_CREATED)

class LocationsGroupListView(generics.ListAPIView):
    queryset = LocationsGroup.objects.all()
    serializer_class = LocationsGroupSerializer
    permission_classes = [AllowAny]