"""
Export the profiles file for the floor unit.

    uv run python manage.py export                    # writes ./profiles.jsonl
    uv run python manage.py export /Volumes/CIRCUITPY # straight onto the Pico
    uv run python manage.py export --style full       # U01-1 numbering
    uv run python manage.py export -                  # to stdout

Give a directory and the file is written inside it as profiles.jsonl; give a
file path and it is written there. The format is specified in
junior/docs/profiles-format.md.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from profiles import export, midi


class Command(BaseCommand):
    help = "Write profiles.jsonl, the file the floor unit plays back."

    def add_arguments(self, parser):
        parser.add_argument(
            "path", nargs="?", default=export.FILENAME,
            help=f"File or directory to write to, or - for stdout. Default: ./{export.FILENAME}",
        )
        parser.add_argument(
            "--style", choices=["core", "full"], default=None,
            help="Patch numbering on the floor unit's display. Default: GT1000_PATCH_STYLE setting.",
        )
        parser.add_argument(
            "--channel", type=int, default=None,
            help="MIDI channel 1-16 to build the bytes for. Default: GT1000_MIDI_CHANNEL setting.",
        )

    def handle(self, *args, **options):
        channel = options["channel"]
        if channel is not None and not 1 <= channel <= 16:
            raise CommandError("--channel must be 1 to 16")
        channel = channel or midi.channel()
        style = options["style"] or export.default_style()

        if options["path"] == "-":
            export.write_profiles(self.stdout, style, channel)
            return

        target = Path(options["path"])
        if target.is_dir():
            target = target / export.FILENAME
        try:
            with open(target, "w", encoding="utf-8", newline="\n") as f:
                count = export.write_profiles(f, style, channel)
        except OSError as e:
            raise CommandError(f"could not write {target}: {e}")
        self.stdout.write(self.style.SUCCESS(
            f"Wrote {count} song{'s' if count != 1 else ''} to {target} (style {style}, channel {channel})."
        ))
