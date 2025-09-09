from ast import Return
import re
from xml.dom import NotFoundErr
from django.shortcuts import render
from rest_framework import permissions
from rest_framework import generics, mixins, viewsets
from .serializers import RoomSerializer, RoleSerializer
from .models import Locations, Room, UpdateHistory
from django.core.cache import cache
from django.conf import settings
from rest_framework.response import Response
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from django.shortcuts import redirect
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from .roomlogic import join_room, refresh_room, MyMixin

def good_redirect(link):
    response = redirect(link)
    response.status_code = 303
    return response

class RoomViewSet(viewsets.ModelViewSet, MyMixin):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    lookup_field = 'link'
    http_method_names = ['get', 'post', 'put', 'delete']

    # Создавать новые комнаты могут только авторизованные пользователи
    def get_permissions(self):
        if self.request.method != 'GET' and self.request.method != 'PUT':
            return [permissions.IsAuthenticatedOrReadOnly()]
        return [permissions.AllowAny()]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        device_hash = self.generate_device_hash(request)
        if instance.owner != request.user:
            link = join_room(request, instance, serializer, device_hash)
            if link != None and type(link) is not dict:
                self.perform_update(serializer)
                return good_redirect(link)
            elif type(link) is dict:
                return Response(link)
        else:
            refresh_room(instance)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class RoleDetailView(APIView, MyMixin):
    def get(self, request, link, player_id, format=None):
        device_hash = self.generate_device_hash(request)
        try:
            room = Room.objects.get(link=link)
            recent_update = UpdateHistory.objects.filter(
            room=room,
            device_hash=device_hash,
            updated_at__gte=timezone.now() - timedelta(minutes=55)
            )
            if recent_update.exists():
                if recent_update.get().my_room_id == player_id:
                    if room.spy_id != player_id:
                        instance = room.current_location
                        serializer = RoleSerializer(instance)
                        return Response(serializer.data)
                    else:
                        return Response({"your_role": "Spy"})
                else:
                    return good_redirect(f'/api/v1/rooms/{link}/{recent_update.my_room_id}')
            else:
                return Response({"error": "Вы не присоединились к комнате!"})
        except Room.DoesNotExist:
            return Response(
                {"error": "Объект не найден"}, 
                status=status.HTTP_404_NOT_FOUND
            )