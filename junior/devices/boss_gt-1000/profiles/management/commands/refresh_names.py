"""
Re-read every used patch's name from the GT-1000 and update the slots.

    uv run python manage.py refresh_names             # user patches in every song
    uv run python manage.py refresh_names --presets   # presets too (switches the unit through them)

Run this before an export if patches have been renamed or overwritten on the
unit since the songs were set up.
"""

from django.core.management.base import BaseCommand, CommandError

from profiles.models import Slot
from profiles.names import refresh_names


class Command(BaseCommand):
    help = "Re-read patch names from the connected GT-1000 and update every slot whose name changed."

    def add_arguments(self, parser):
        parser.add_argument(
            "--presets", action="store_true",
            help="Also re-read preset patches. The unit is switched to each one to read its name.",
        )

    def handle(self, *args, **options):
        result = refresh_names(Slot.objects.select_related("song").order_by("song__name", "position"),
                               include_presets=options["presets"])
        if result.aborted:
            raise CommandError(result.aborted)
        for c in result.changes:
            self.stdout.write(f'{c.slot.song} #{c.slot.position} {c.slot.patch_core}: "{c.old}" -> "{c.new}"')
        for index, err in result.failures.items():
            self.stderr.write(f"patch index {index}: {err}")
        self.stdout.write(self.style.SUCCESS(result.summary() + "."))
