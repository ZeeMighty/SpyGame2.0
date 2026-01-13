
from dataclasses import field
from rest_framework import serializers

from .models import Locations, Room, LocationsGroup
from django.contrib.auth.hashers import make_password


class LocationsGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationsGroup
        fields = ['id', 'name']

class LocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = ['location', 'description']

# class RoomListSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(
#         write_only=True, 
#         required=False,
#         allow_blank=True,
#         style={"input_type": "password"}
#     )
#     locations_group_name = LocationsGroupSerializer(source="locations_group", read_only=True)
#     class Meta:
#         model = Room
#         fields = ["name", "num_of_players", "owner", "locations_group_name", "password"]
    
#     def validate_password(self, value):
#         room = self.instance
#         if value and room.password != value:
#             raise serializers.ValidationError("Неверный пароль")
#         return value

class RoomSerializer(serializers.ModelSerializer):
    locations_group_name = LocationsGroupSerializer(source="locations_group", read_only=True)
    current_location_name = LocationsSerializer(source="current_location", read_only=True)

    class Meta:
        model = Room
        fields = "__all__"
    
    def validate_password(self, value):
        if value and len(value) < 3:
            raise serializers.ValidationError("Пароль должен быть не менее 3 символов.")
        return value

    def create(self, validated_data):
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(password)
        room = Room.objects.create(**validated_data)
        return room

    def update(self, instance, validated_data):
        password = validated_data.get('password')
        if password:
            validated_data['password'] = make_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
