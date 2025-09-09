from email.policy import default
from .models import Room, Locations
from rest_framework import serializers
import random
import string

class RoomSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    password = serializers.CharField(
        write_only=True, 
        required=False,
        allow_blank=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = Room
        # fields = ("title", "description", "price", "year", "brand", "model")
        fields = "__all__"
        extra_kwargs = {
            'link': {'read_only': True},
            'id_of_connected_player': {'read_only': False},
            'name': {'read_only': False},
            'num_of_players': {'read_only': False},
        }
    # def get_fields(self):
    #     fields = super().get_fields()
    #     request = self.context.get('request')
        
    #     if request and hasattr(request, 'user'):
    #         user = request.user
            
    #         if self.instance and user != self.instance.owner:
    #             excluded_fields = ['owner', 'spy_id', 'id_of_connected_player']
    #             for field in excluded_fields:
    #                 fields.pop(field, None)
    #     return fields

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = "__all__"