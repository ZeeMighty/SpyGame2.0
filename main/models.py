import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import MinValueValidator
from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=25)
    num_of_players = models.IntegerField(validators=[MinValueValidator(limit_value=3, message="Минимум 3 игрока")])
    id_of_connected_player = models.IntegerField(default=0)
    spy_id = models.IntegerField(default=0)
    link = models.SlugField(max_length=50, unique=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=False)
    locations_group = models.ForeignKey("LocationsGroup", on_delete=models.CASCADE)
    current_location = models.ForeignKey("Locations", on_delete=models.CASCADE)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def has_password(self):
        return bool(self.password)
    
    def save(self, *args, **kwargs):
        if not self.link:
            self.link = self.generate_unique_link()
        if self.password and not self.password.startswith("pbkdf2_sha256$"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def generate_unique_link(self):
        while True:
            link = f"room_{secrets.token_urlsafe(8)}"
            if not Room.objects.filter(link=link).exists():
                return link

    def __str__(self) -> str:
        return self.name
    
class Locations(models.Model):
    location = models.CharField(max_length=30)
    description = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.location

class LocationsGroup(models.Model):
    name = models.CharField(max_length=25)
    locations = models.ManyToManyField(Locations, blank=True, null=True)

    def __str__(self) -> str:
        return self.name
    
class UpdateHistory(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    my_room_id = models.IntegerField()
    device_hash = models.CharField(max_length=64)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["room", "device_hash"]),
            models.Index(fields=["updated_at"]),
        ]