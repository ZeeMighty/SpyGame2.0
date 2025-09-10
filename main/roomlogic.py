import hashlib
import random
from datetime import timedelta

from django.utils import timezone
from numpy import insert
from rest_framework.response import Response
from rest_framework import status

from .models import LocationsGroup, UpdateHistory


class MyMixin:
    def generate_device_hash(self, request):
            """Создаем хеш устройства на основе IP и User-Agent"""
            ip = request.META.get("REMOTE_ADDR", "")
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            device_string = f"{ip}_{user_agent}"
            return hashlib.sha256(device_string.encode()).hexdigest()
    
    def perform_update(self, serializer):
        serializer.validated_data.pop('current_location', None)
        return super().perform_update(serializer)

def set_id_of_connected_player(serializer):
    instance = serializer.instance
    if instance.id_of_connected_player < instance.num_of_players:
        current_id = instance.id_of_connected_player + 1
        id_list = UpdateHistory.objects.filter(room=instance).values_list('my_room_id', flat=True)
        if current_id in id_list:
            current_id += 1    
        return current_id
    else:
        return "full"

def room_create(request):
    try:
        locations_group = LocationsGroup.objects.get(id=request.data["locations_group"])
        all_valid_locations = list(locations_group.locations.all())
        if all_valid_locations:
            random_location = random.choice(all_valid_locations)
    except LocationsGroup.DoesNotExist:
        return "error"
    num_of_players = int(request.data["num_of_players"])
    spy_id = random.randint(1, num_of_players)

    modified_data = request.data.copy()
    modified_data["current_location"] = random_location.id
    modified_data["spy_id"] = spy_id
    modified_data["id_of_connected_player"] = 0
    return modified_data

def creator_id(instance, device_hash):
    random_id = random.randint(1, int(instance.num_of_players)-1)
    # УДАЛИТЬ СТРОЧКУ НИЖЕ!!! НОРМАЛЬНЫЙ DEVICE HASH!
    device_hash = "CreatorHASH"
    UpdateHistory.objects.create(room=instance, device_hash=device_hash, my_room_id=random_id)
    return random_id

def join_room(request, instance, device_hash):
    password = request.data.get("password", "")
    if instance.has_password() and not instance.check_password(password):
        return "error"
    allowed_fields = ["if_of_connected_player"]
    filtered_data = {
        key: value for key, value in request.data.items() 
        if key in allowed_fields
    }
    # УДАЛИТЬ СТРОЧКУ НИЖЕ!!! НОРМАЛЬНЫЙ DEVICE HASH!
    device_hash = "JOINERhash"
    recent_update = UpdateHistory.objects.filter(
        room=instance,
        device_hash=device_hash,
        updated_at__gte=timezone.now() - timedelta(minutes=55)
    )
# Возвращаяем на страницу отображения роли именно для этого устройства, в этой комнате
    if recent_update.exists():
        my_room_id = recent_update.get().my_room_id
        return {"link": f"/api/v1/rooms/{instance.link}/{my_room_id}/", "filtered_data": filtered_data}
    else:
        # УДАЛИТЬ СТРОЧКУ НИЖЕ!!! НОРМАЛЬНЫЙ DEVICE HASH!
        device_hash = "JOINERhash"
        UpdateHistory.objects.create(room=instance, device_hash=device_hash, my_room_id=instance.id_of_connected_player)
        my_room_id = instance.id_of_connected_player
        return {"link": f"/api/v1/rooms/{instance.link}/{my_room_id}/", "filtered_data": filtered_data}

def refresh_room(instance, request, device_hash):

    try:
        locations_group = LocationsGroup.objects.get(id=request.data["locations_group"])
        all_valid_locations = list(locations_group.locations.all())
        if all_valid_locations:
            random_location = random.choice(all_valid_locations)
    except LocationsGroup.DoesNotExist:
        return "error"
    num_of_players = int(request.data["num_of_players"])
    spy_id = random.randint(1, num_of_players)

    modified_data = request.data.copy()
    modified_data["current_location"] = random_location.id
    modified_data["spy_id"] = spy_id
    modified_data["id_of_connected_player"] = 0
    UpdateHistory.objects.filter(room=instance).delete()
    return modified_data