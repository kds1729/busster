from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    path("", views.unit, name="unit"),
    path("api/select/<int:slot_id>/", views.select_slot, name="select_slot"),
    path("api/midi/", views.midi_status, name="midi_status"),
]
