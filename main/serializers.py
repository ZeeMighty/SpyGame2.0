from dataclasses import field

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Locations, LocationsGroup, Room, RoomConnection


class LocationsGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationsGroup
        fields = ["id", "name"]


class LocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = ["location", "description"]


class RoomSerializer(serializers.ModelSerializer):
    locations_group_name = LocationsGroupSerializer(
        source="locations_group", read_only=True
    )
    current_location_name = LocationsSerializer(source="current_location", read_only=True)
    link = serializers.SlugField(max_length=50, required=False)
    password = serializers.CharField(
        max_length=128, required=False, allow_blank=True, allow_null=True
    )
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    has_password = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            "name",
            "num_of_players",
            "has_password",
            "locations_group",
            "locations_group_name",
            "current_location_name",
            "link",
            "owner",
            "password"
        ]

    def get_has_password(self, obj):
        return bool(obj.password)

    def validate_password(self, value):
        if value and len(value) < 3:
            raise serializers.ValidationError("Пароль должен быть не менее 3 символов.")
        return value

    def create(self, validated_data):
        password = validated_data.get("password")
        if password:
            validated_data["password"] = make_password(password)
        room = Room.objects.create(**validated_data)
        return room

    def update(self, instance, validated_data):
        password = validated_data.get("password")
        if password:
            validated_data["password"] = make_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RoomMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "num_of_players", "link", "spy_id"]


class RoomConnectionSerializer(serializers.ModelSerializer):
    room = RoomMiniSerializer(read_only=True)
    location_to_show = LocationsSerializer(many=True, read_only=True)

    class Meta:
        model = RoomConnection
        fields = ["location_to_show", "room"]
