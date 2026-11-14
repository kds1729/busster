"""
Write the profiles file the floor unit plays back.

The format is specified in junior/docs/profiles-format.md. In short: JSON
Lines, a header line, then one line per song in display order. Every slot
carries the exact MIDI bytes to send, so the floor unit never has to know
anything about the GT-1000.
"""

import json
from datetime import datetime, timezone
from typing import IO, Iterator

from django.conf import settings

from . import midi
from .models import SLOT_COUNT, Song, format_patch_core, format_patch_full

FORMAT = "busster-junior-profiles"
VERSION = 1
DEVICE_KEY = "gt1000"
FILENAME = "profiles.jsonl"


def default_style() -> str:
    return getattr(settings, "GT1000_PATCH_STYLE", "core")


def midi_hex(index: int, channel: int) -> str:
    """The patch-select bytes as the file writes them: "B0 00 00 B0 20 00 C0 0E"."""
    data = [b for m in midi.patch_messages(index, ch=channel) for b in m.bytes()]
    return " ".join(f"{b:02X}" for b in data)


def slot_entry(slot, style: str, channel: int) -> dict:
    number = format_patch_full(slot.patch) if style == "full" else format_patch_core(slot.patch)
    return {
        "number": number,
        "patch_name": slot.patch_name,
        "label": slot.label,
        "midi": midi_hex(slot.patch, channel),
    }


def song_profile(song: Song, style: str, channel: int) -> dict:
    slots: list = [None] * SLOT_COUNT
    for slot in song.slots.all():
        slots[slot.position - 1] = slot_entry(slot, style, channel)
    return {"name": song.name, "artist": song.artist, "slots": slots}


def header(song_count: int, style: str, channel: int, exported: datetime | None = None) -> dict:
    exported = exported or datetime.now(timezone.utc)
    return {
        "format": FORMAT,
        "version": VERSION,
        "exported": exported.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "device": DEVICE_KEY,
        "style": style,
        "channel": channel,
        "song_count": song_count,
    }


def profile_lines(style: str | None = None, channel: int | None = None) -> Iterator[str]:
    """Yield the file one line at a time, without newlines."""
    style = style or default_style()
    channel = channel or midi.channel()
    songs = list(Song.objects.prefetch_related("slots").order_by("name"))
    yield json.dumps(header(len(songs), style, channel), ensure_ascii=False)
    for song in songs:
        yield json.dumps(song_profile(song, style, channel), ensure_ascii=False)


def write_profiles(out: IO[str], style: str | None = None, channel: int | None = None) -> int:
    """Write the whole file to `out`. Returns the number of songs written."""
    count = -1
    for count, line in enumerate(profile_lines(style, channel)):
        out.write(line + "\n")  # one write per line: Django's stdout wrapper adds its own newline otherwise
    return count
