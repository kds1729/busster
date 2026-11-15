import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import midi
from .models import PAGE_SIZE, SLOT_COUNT, Slot, Song


def _song_payload(song: Song, style: str) -> dict:
    slots = [None] * song.slot_capacity   # 8, or a whole number of 7-slot pages
    for s in song.slots.all():
        slots[s.position - 1] = {
            "id": s.id,
            "patch": s.patch,
            "display": s.display_text(style),
            "label": s.label,
        }
    return {"id": song.id, "name": song.name, "artist": song.artist, "paginate": song.paginate, "slots": slots}


def unit(request):
    """The floor-unit simulator page."""
    style = getattr(settings, "GT1000_PATCH_STYLE", "core")
    songs = [_song_payload(s, style) for s in Song.objects.prefetch_related("slots").order_by("name")]
    return render(request, "profiles/unit.html",
                  {"songs_json": json.dumps(songs), "slot_count": SLOT_COUNT, "page_size": PAGE_SIZE})


@require_POST
def select_slot(request, slot_id: int):
    """Footswitch press: send the slot's patch to the GT-1000."""
    try:
        slot = Slot.objects.select_related("song").get(pk=slot_id)
    except Slot.DoesNotExist:
        return JsonResponse({"ok": False, "error": "No such slot"}, status=404)
    try:
        sent = midi.send_patch(slot.patch)
    except (ConnectionError, ValueError, OSError) as e:
        return JsonResponse({"ok": False, "error": str(e), "core": slot.patch_core, "full": slot.patch_full}, status=503)
    return JsonResponse({"ok": True, "core": slot.patch_core, "full": slot.patch_full, "display": slot.display_text(), **sent})


def midi_status(request):
    """Which MIDI outputs the laptop can see, and which one we'd use."""
    names = midi.output.available_names()
    return JsonResponse({"wanted": midi.port_name(), "available": names, "found": midi.output._find_name()})
