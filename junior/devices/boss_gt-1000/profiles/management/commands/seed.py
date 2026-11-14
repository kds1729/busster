"""
Load the database with sample songs for trying out the simulator.

    uv run python manage.py seed            # song1, song2, song3 with 4, 5, 6 patches
    uv run python manage.py seed --seed 42  # same random patches every time

Patches are picked at random from the user area (U001-U250). If the GT-1000 is
connected over USB, each patch's name is read from it. Existing songs with the
same names are replaced; other songs are left alone.
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from profiles import midi
from profiles.models import USER_PATCHES, Slot, Song

SAMPLE_SONGS = [("song1", 4), ("song2", 5), ("song3", 6)]


class Command(BaseCommand):
    help = "Create song1, song2, song3 with 4, 5 and 6 random patches on switches 1-4, 1-5 and 1-6."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=None, help="Random seed for repeatable patch choices.")

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(options["seed"])
        for name, count in SAMPLE_SONGS:
            Song.objects.filter(name=name).delete()
            song = Song.objects.create(name=name)
            patches = rng.sample(range(USER_PATCHES), count)
            for position, patch in enumerate(patches, start=1):
                slot = Slot(song=song, position=position, patch=patch)
                try:
                    slot.patch_name = midi.read_patch_name(patch)
                except (ConnectionError, TimeoutError, OSError) as e:
                    self.stderr.write(f"  {slot.patch_core}: name not read ({e})")
                slot.save()
            shown = ", ".join(s.display_text() for s in song.slots.all())
            self.stdout.write(f"{name}: {shown}")
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(SAMPLE_SONGS)} songs."))
