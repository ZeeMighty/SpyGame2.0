from django.contrib import admin

from .models import Locations, LocationsGroup, Room, RoomConnection

# admin.site.register(Room)
admin.site.register(Locations)
admin.site.register(LocationsGroup)
# admin.site.register(RoomConnection)

@admin.register(RoomConnection)
class RoomConnectionAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "my_room_id", "device_hash")
    list_display_links = ("id", "room")
    search_fields = ("id", "room")
    list_filter = ("id", "room")

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "spy_id", "current_location", "num_of_players")
    list_display_links = ("id", "name", "spy_id", "current_location", "num_of_players")
    search_fields = ("id", "name")
    list_filter = ("id", "name")

# @admin.register(CarModel)
# class CarModelAdmin(admin.ModelAdmin):
#     list_display = ("id", "name")
#     list_display_links = ("id", "name")
#     search_fields = ("id", "name")
#     list_filter = ("id", "name")