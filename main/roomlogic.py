from .models import Room, UpdateHistory
from django.utils import timezone
from rest_framework.response import Response
from datetime import timedelta
from django.shortcuts import redirect
from rest_framework import status
import hashlib

class MyMixin:
    def generate_device_hash(self, request):
            """Создаем хеш устройства на основе IP и User-Agent"""
            ip = request.META.get('REMOTE_ADDR', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            device_string = f"{ip}_{user_agent}"
            return hashlib.sha256(device_string.encode()).hexdigest()
    
    def perform_update(self, serializer):
        instance = serializer.instance
        if instance.id_of_connected_player < instance.num_of_players:
            serializer.validated_data['id_of_connected_player'] = instance.id_of_connected_player + 1
        return super().perform_update(serializer)

def join_room(request, instance, serializer, device_hash):
    password = request.data.get('password', '')
    if instance.has_password() and not instance.check_password(password):
        return {"error": "Неверный пароль"}
    allowed_fields = []
    filtered_data = {
        key: value for key, value in request.data.items() 
        if key in allowed_fields
    }
    request._full_data = filtered_data
    recent_update = UpdateHistory.objects.filter(
        room=instance,
        device_hash=device_hash,
        updated_at__gte=timezone.now() - timedelta(minutes=55)
    )
# Возвращаяем на страницу отображения роли именно для этого устройства, в этой комнате
    if recent_update.exists():
        my_room_id = recent_update.get().my_room_id
        return f'/api/v1/rooms/{instance.link}/{my_room_id}/'
    elif serializer.is_valid():
        UpdateHistory.objects.create(room=instance, device_hash=device_hash, my_room_id=instance.id_of_connected_player)
        my_room_id = instance.id_of_connected_player
        return f'/api/v1/rooms/{instance.link}/{my_room_id}/'

def refresh_room(instance):
    instance.id_of_connected_player = 0
    UpdateHistory.objects.filter(room=instance).delete()