from datetime import timedelta

from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Room, UpdateHistory
from .roomlogic import (
    MyMixin, join_room, refresh_room,
    room_create, creator_id, set_id_of_connected_player
)
from .serializers import RoleSerializer, RoomSerializer


def good_redirect(link):
    response = redirect(link)
    response.status_code = 303
    return response

class RoomViewSet(viewsets.ModelViewSet, MyMixin):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    lookup_field = "link"
    http_method_names = ["get", "post", "put", "delete"]

    # Создавать новые комнаты могут только авторизованные пользователи
    def get_permissions(self):
        if self.request.method != "GET" and self.request.method != "PUT":
            return [permissions.IsAuthenticatedOrReadOnly()]
        return [permissions.AllowAny()]

    def create(self, request, *args, **kwargs):
        device_hash = self.generate_device_hash(request)
        modified_data = room_create(request)
        if modified_data != "error":
            serializer = self.get_serializer(data=modified_data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            my_id = creator_id(instance, device_hash)
            return good_redirect(f"/api/v1/rooms/{instance.link}/{my_id}")
        else:
            return Response({"error": "Не выбрана группа локаций"}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        device_hash = self.generate_device_hash(request)
        if instance.owner != request.user:
            data = join_room(request, instance, device_hash)
            if data != "error":
                serializer = self.get_serializer(instance, data=data["filtered_data"], partial=True)
                if serializer.is_valid():
                    id_of_connected_player = set_id_of_connected_player(serializer, device_hash)
                    if id_of_connected_player != "full":
                        serializer.validated_data["id_of_connected_player"] = id_of_connected_player
                        self.perform_update(serializer)
                        link = data["link"]
                        return good_redirect(link)
                    else:
                        return Response({"error": "Комната заполнена!"})

            else:
                return Response({"error": "Неверный пароль"})
        else:
            modified_data = refresh_room(instance, request, device_hash)
            serializer = self.get_serializer(instance, data=modified_data, partial=True)
            my_id = creator_id(instance, device_hash)
            if serializer.is_valid():
                self.perform_update(serializer)
                if my_id:
                    return good_redirect(f"/api/v1/rooms/{instance.link}/{my_id}")
                return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class RoleDetailView(APIView, MyMixin):
    def get(self, request, link, player_id, format=None):
        device_hash = self.generate_device_hash(request)
        print(device_hash)
        try:
            room = Room.objects.get(link=link)
            # УДАЛИТЬ 4 СТРОЧКИ НИЖЕ!!! НОРМАЛЬНЫЙ DEVICE HASH!
            # if request.user == room.owner:
            #     device_hash = "CreatorHASH"
            # else:
            #     device_hash = "JOINERhash"
            recent_update = UpdateHistory.objects.filter(
            room=room,
            device_hash=device_hash,
            updated_at__gte=timezone.now() - timedelta(minutes=55)
            )
            if recent_update.exists():
                recent_update = recent_update.get()
                if recent_update.my_room_id == player_id:
                    if room.spy_id != player_id:
                        instance = room.current_location
                        serializer = RoleSerializer(instance)
                        return Response(serializer.data)
                    else:
                        return Response({"your_role": "Spy"})
                else:
                    return good_redirect(f"/api/v1/rooms/{link}/{recent_update.my_room_id}")
            else:
                return Response({"error": "Вы не присоединились к комнате!"})
        except Room.DoesNotExist:
            return Response(
                {"error": "Объект не найден"}, 
                status=status.HTTP_404_NOT_FOUND
            )