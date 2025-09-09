from django.contrib import admin

from .models import Locations, LocationsGroup, Room, UpdateHistory

admin.site.register(Room)
admin.site.register(Locations)
admin.site.register(LocationsGroup)
admin.site.register(UpdateHistory)

# @admin.register(Brand)
# class BrandAdmin(admin.ModelAdmin):
#     list_display = ("id", "name")
#     list_display_links = ("id", "name")
#     search_fields = ("id", "name")
#     list_filter = ("id", "name")

# @admin.register(CarModel)
# class CarModelAdmin(admin.ModelAdmin):
#     list_display = ("id", "name")
#     list_display_links = ("id", "name")
#     search_fields = ("id", "name")
#     list_filter = ("id", "name")