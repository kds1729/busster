from unittest import mock

from django.test import TestCase
from django.urls import reverse

from . import midi
from .models import Slot, Song, format_patch_core, format_patch_full


class PatchFormattingTests(TestCase):
    def test_core_style(self):
        self.assertEqual(format_patch_core(0), "U001")
        self.assertEqual(format_patch_core(249), "U250")
        self.assertEqual(format_patch_core(250), "P001")
        self.assertEqual(format_patch_core(499), "P250")

    def test_full_style(self):
        self.assertEqual(format_patch_full(0), "U01-1")
        self.assertEqual(format_patch_full(4), "U01-5")
        self.assertEqual(format_patch_full(5), "U02-1")
        self.assertEqual(format_patch_full(249), "U50-5")
        self.assertEqual(format_patch_full(250), "P01-1")
        self.assertEqual(format_patch_full(499), "P50-5")


class MidiMessageTests(TestCase):
    def test_bank_and_program(self):
        # Measured on the GT-1000CORE: 125 patches per bank.
        self.assertEqual(midi.patch_to_bank_program(0), (0, 0))      # U001
        self.assertEqual(midi.patch_to_bank_program(1), (0, 1))      # U002
        self.assertEqual(midi.patch_to_bank_program(124), (0, 124))  # U125
        self.assertEqual(midi.patch_to_bank_program(125), (1, 0))    # U126
        self.assertEqual(midi.patch_to_bank_program(194), (1, 69))   # U195
        self.assertEqual(midi.patch_to_bank_program(249), (1, 124))  # U250
        self.assertEqual(midi.patch_to_bank_program(250), (2, 0))    # P001
        self.assertEqual(midi.patch_to_bank_program(499), (3, 124))  # P250

    def test_out_of_range_patch(self):
        with self.assertRaises(ValueError):
            midi.patch_to_bank_program(500)

    def test_message_bytes_channel_1(self):
        msgs = midi.patch_messages(129, ch=1)  # U130 -> bank 1, program 4
        self.assertEqual([m.bytes() for m in msgs], [[0xB0, 0, 1], [0xB0, 32, 0], [0xC0, 4]])


class SelectSlotViewTests(TestCase):
    def setUp(self):
        self.song = Song.objects.create(name="Test Song")
        self.slot = Slot.objects.create(song=self.song, position=1, patch=1, label="Clean")

    def test_unit_page_renders(self):
        r = self.client.get(reverse("profiles:unit"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Test Song")

    @mock.patch.object(midi.output, "send")
    def test_select_sends_patch(self, send):
        r = self.client.post(reverse("profiles:select_slot", args=[self.slot.id]))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["core"], "U002")
        self.assertEqual((data["bank"], data["program"]), (0, 1))
        send.assert_called_once()

    @mock.patch.object(midi.output, "send", side_effect=ConnectionError("no port"))
    def test_select_reports_missing_device(self, send):
        r = self.client.post(reverse("profiles:select_slot", args=[self.slot.id]))
        self.assertEqual(r.status_code, 503)
        self.assertFalse(r.json()["ok"])

    def test_select_requires_post(self):
        r = self.client.get(reverse("profiles:select_slot", args=[self.slot.id]))
        self.assertEqual(r.status_code, 405)


class SysexTests(TestCase):
    def test_checksum(self):
        # 20 3C 00 00 + 00 00 00 10 -> sum 0x6C -> 128-108 = 20 = 0x14
        self.assertEqual(midi.roland_checksum([0x20, 0x3C, 0, 0, 0, 0, 0, 0x10]), 0x14)

    def test_user_patch_addresses(self):
        self.assertEqual(midi.user_patch_address(0), (0x20, 0x00, 0, 0))
        self.assertEqual(midi.user_patch_address(127), (0x20, 0x7F, 0, 0))
        self.assertEqual(midi.user_patch_address(128), (0x21, 0x00, 0, 0))
        self.assertEqual(midi.user_patch_address(249), (0x21, 0x79, 0, 0))

    def test_rq1_frame(self):
        with self.settings(GT1000_DEVICE_ID=17):
            frame = midi.rq1_bytes((0x20, 0x3C, 0, 0), 16)
        self.assertEqual(frame, [0xF0, 0x41, 0x10, 0, 0, 0, 0x4F, 0x11, 0x20, 0x3C, 0, 0, 0, 0, 0, 0x10, 0x14, 0xF7])

    def test_parse_dt1_and_decode(self):
        name = b"GIG READY       "
        body = [0x41, 0x10, 0, 0, 0, 0x4F, 0x12, 0x20, 0x3C, 0, 0, *name, 0x00]
        address, payload = midi.parse_dt1(body)
        self.assertEqual(address, (0x20, 0x3C, 0, 0))
        self.assertEqual(midi.decode_name(payload), "GIG READY")

    def test_parse_rejects_other_messages(self):
        self.assertIsNone(midi.parse_dt1([0x7E, 0x10, 0x06, 0x02]))


class DisplayTextTests(TestCase):
    def test_display_with_and_without_name(self):
        song = Song.objects.create(name="s")
        slot = Slot.objects.create(song=song, position=1, patch=60, patch_name="GIG READY")
        self.assertEqual(slot.display_text(), "U061 - GIG READY")
        self.assertEqual(slot.display_text("full"), "U13-1 - GIG READY")
        slot.patch_name = ""
        self.assertEqual(slot.display_text(), "U061")


class AdminPatchNameTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser("t", "t@example.com", "pw")
        self.client.force_login(self.user)

    @mock.patch.object(midi, "read_patch_name", return_value="GIG READY")
    def test_slot_save_reads_name(self, read):
        song = Song.objects.create(name="s")
        r = self.client.post(reverse("admin:profiles_slot_add"), {"song": song.id, "position": 1, "patch": 60, "label": ""})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Slot.objects.get().patch_name, "GIG READY")
        read.assert_called_once_with(60)

    @mock.patch.object(midi, "read_patch_name", side_effect=ConnectionError("no unit"))
    def test_slot_save_without_unit_still_saves(self, read):
        song = Song.objects.create(name="s")
        r = self.client.post(reverse("admin:profiles_slot_add"), {"song": song.id, "position": 1, "patch": 60, "label": ""}, follow=True)
        self.assertEqual(Slot.objects.get().patch_name, "")
        self.assertContains(r, "could not read the patch name")


class ExportTests(TestCase):
    """The profiles file, as specified in junior/docs/profiles-format.md."""

    def setUp(self):
        from . import export

        self.export = export
        # Created out of alphabetical order on purpose; the file must sort by name.
        numb = Song.objects.create(name="Comfortably Numb", artist="Pink Floyd")
        Slot.objects.create(song=numb, position=1, patch=380, patch_name="GILMOUR LEAD", label="Solo")
        tower = Song.objects.create(name="All Along the Watchtower", artist="Hendrix")
        Slot.objects.create(song=tower, position=1, patch=14, patch_name="CLEAN VERSE", label="Intro")
        Slot.objects.create(song=tower, position=3, patch=15, patch_name="CRUNCH", label="")
        Song.objects.create(name="Empty Song")

    def lines(self, **kw):
        import json

        return [json.loads(line) for line in self.export.profile_lines(**kw)]

    def test_midi_hex_matches_spec_examples(self):
        self.assertEqual(self.export.midi_hex(14, 1), "B0 00 00 B0 20 00 C0 0E")    # U015
        self.assertEqual(self.export.midi_hex(380, 1), "B0 00 03 B0 20 00 C0 05")   # P131
        self.assertEqual(self.export.midi_hex(0, 2), "B1 00 00 B1 20 00 C1 00")     # channel 2

    def test_header(self):
        head = self.lines(style="core", channel=1)[0]
        self.assertEqual(head["format"], "busster-junior-profiles")
        self.assertEqual(head["version"], 1)
        self.assertEqual(head["device"], "gt1000")
        self.assertEqual(head["style"], "core")
        self.assertEqual(head["channel"], 1)
        self.assertEqual(head["song_count"], 3)
        self.assertRegex(head["exported"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_songs_in_name_order_with_eight_slots(self):
        lines = self.lines(style="core", channel=1)
        self.assertEqual([s["name"] for s in lines[1:]], ["All Along the Watchtower", "Comfortably Numb", "Empty Song"])
        for song in lines[1:]:
            self.assertEqual(len(song["slots"]), 8)
        self.assertEqual(lines[3]["slots"], [None] * 8)

    def test_slot_contents(self):
        tower = self.lines(style="core", channel=1)[1]
        self.assertEqual(tower["artist"], "Hendrix")
        self.assertEqual(tower["slots"][0], {
            "number": "U015", "patch_name": "CLEAN VERSE", "label": "Intro", "midi": "B0 00 00 B0 20 00 C0 0E",
        })
        self.assertIsNone(tower["slots"][1])
        self.assertEqual(tower["slots"][2]["number"], "U016")
        self.assertNotIn("patch", tower["slots"][0])  # the raw index stays on the laptop

    def test_full_style_numbers(self):
        numb = self.lines(style="full", channel=1)[2]
        self.assertEqual(numb["slots"][0]["number"], "P27-1")
        self.assertEqual(numb["slots"][0]["midi"], "B0 00 03 B0 20 00 C0 05")  # bytes don't depend on style

    def test_write_profiles_returns_song_count_and_ends_lines_with_newline(self):
        import io

        out = io.StringIO()
        count = self.export.write_profiles(out, style="core", channel=1)
        self.assertEqual(count, 3)
        text = out.getvalue()
        self.assertEqual(text.count("\n"), 4)
        self.assertTrue(text.endswith("\n"))

    def test_export_command_writes_file_into_directory(self):
        import io
        import json
        import tempfile
        from pathlib import Path

        from django.core.management import call_command

        with tempfile.TemporaryDirectory() as d:
            io_stdout = io.StringIO()
            call_command("export", d, style="core", channel=1, stdout=io_stdout)
            path = Path(d) / "profiles.jsonl"
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 4)
            self.assertEqual(json.loads(lines[0])["song_count"], 3)
            self.assertIn("Wrote 3 songs", io_stdout.getvalue())

    def test_export_command_rejects_bad_channel(self):
        from django.core.management import CommandError, call_command

        with self.assertRaises(CommandError):
            call_command("export", "-", channel=17)
