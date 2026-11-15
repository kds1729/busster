from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from . import midi
from .models import PAGE_SIZE, SLOT_COUNT, Slot, Song, format_patch_core, format_patch_full


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


class SimulatorPayloadTests(TestCase):
    def test_plain_song_has_eight_entries(self):
        from .views import _song_payload

        song = Song.objects.create(name="Plain")
        Slot.objects.create(song=song, position=3, patch=5)
        payload = _song_payload(song, "core")
        self.assertFalse(payload["paginate"])
        self.assertEqual(len(payload["slots"]), 8)
        self.assertEqual(payload["slots"][2]["display"], "U006")

    def test_paginating_song_has_whole_pages(self):
        from .views import _song_payload

        song = Song.objects.create(name="Paged", paginate=True)
        Slot.objects.create(song=song, position=9, patch=0)
        payload = _song_payload(song, "core")
        self.assertTrue(payload["paginate"])
        self.assertEqual(len(payload["slots"]), 14)
        self.assertIsNotNone(payload["slots"][8])

    def test_unit_page_passes_page_size(self):
        r = self.client.get(reverse("profiles:unit"))
        self.assertContains(r, "const PAGE_SIZE = 7;")


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


class PaginationModelTests(TestCase):
    def setUp(self):
        self.plain = Song.objects.create(name="Plain")
        self.paged = Song.objects.create(name="Paged", paginate=True)

    def test_constants(self):
        self.assertEqual((SLOT_COUNT, PAGE_SIZE), (8, 7))

    def test_plain_song_caps_positions_at_eight(self):
        Slot(song=self.plain, position=8, patch=0).full_clean()  # fine
        with self.assertRaises(ValidationError) as cm:
            Slot(song=self.plain, position=9, patch=0).full_clean()
        self.assertIn("position", cm.exception.message_dict)
        self.assertIn("pagination", cm.exception.message_dict["position"][0])

    def test_paginating_song_allows_any_position(self):
        Slot(song=self.paged, position=9, patch=0).full_clean()
        Slot(song=self.paged, position=21, patch=0).full_clean()

    def test_position_zero_still_rejected(self):
        with self.assertRaises(ValidationError):
            Slot(song=self.paged, position=0, patch=0).full_clean()

    def test_slot_without_song_validates_fields_only(self):
        # The admin validates inline slots before a new song is saved.
        Slot(position=12, patch=0).clean()

    def test_page_and_switch(self):
        s1 = Slot(song=self.paged, position=1)
        s7 = Slot(song=self.paged, position=7)
        s8 = Slot(song=self.paged, position=8)
        s15 = Slot(song=self.paged, position=15)
        self.assertEqual([(s.page, s.switch) for s in (s1, s7, s8, s15)], [(0, 1), (0, 7), (1, 1), (2, 1)])
        self.assertEqual((Slot(song=self.plain, position=8).page, Slot(song=self.plain, position=8).switch), (0, 8))

    def test_page_count_and_capacity(self):
        self.assertEqual((self.plain.page_count, self.plain.slot_capacity), (1, SLOT_COUNT))
        self.assertEqual((self.paged.page_count, self.paged.slot_capacity), (1, PAGE_SIZE))
        Slot.objects.create(song=self.paged, position=7, patch=0)
        self.assertEqual(self.paged.page_count, 1)
        Slot.objects.create(song=self.paged, position=8, patch=1)
        self.assertEqual((self.paged.page_count, self.paged.slot_capacity), (2, 2 * PAGE_SIZE))
        Slot.objects.create(song=self.paged, position=15, patch=2)
        self.assertEqual(self.paged.page_count, 3)
        # A plain song with 8 slots still has one page and a capacity of 8.
        for pos in range(1, 9):
            Slot.objects.create(song=self.plain, position=pos, patch=pos)
        self.assertEqual((self.plain.page_count, self.plain.slot_capacity), (1, SLOT_COUNT))


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


class AdminPaginationTests(TestCase):
    """Songs are edited with their slots inline; the position limit must follow
    the pagination box as posted, not as stored."""

    def setUp(self):
        from django.contrib.auth.models import User
        self.client.force_login(User.objects.create_superuser("t", "t@example.com", "pw"))
        self.song = Song.objects.create(name="s")

    def post_song(self, paginate, positions):
        data = {"name": "s", "artist": "", "notes": "", "paginate": "on" if paginate else "",
                "slots-TOTAL_FORMS": len(positions), "slots-INITIAL_FORMS": 0,
                "slots-MIN_NUM_FORMS": 0, "slots-MAX_NUM_FORMS": 1000}
        for i, pos in enumerate(positions):
            data.update({f"slots-{i}-position": pos, f"slots-{i}-patch": pos, f"slots-{i}-label": "",
                         f"slots-{i}-song": self.song.id})
        return self.client.post(reverse("admin:profiles_song_change", args=[self.song.id]), data)

    @mock.patch.object(midi, "read_patch_name", return_value="X")
    def test_position_nine_needs_pagination(self, read):
        r = self.post_song(False, [1, 9])
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Turn on pagination")
        self.assertEqual(Slot.objects.count(), 0)

    @mock.patch.object(midi, "read_patch_name", return_value="X")
    def test_pagination_and_slot_nine_in_the_same_submit(self, read):
        r = self.post_song(True, [1, 9, 15])
        self.assertEqual(r.status_code, 302)
        self.song.refresh_from_db()
        self.assertTrue(self.song.paginate)
        self.assertEqual(sorted(Slot.objects.values_list("position", flat=True)), [1, 9, 15])

    def test_change_page_shows_page_and_switch(self):
        self.song.paginate = True
        self.song.save()
        Slot.objects.create(song=self.song, position=9, patch=0)
        r = self.client.get(reverse("admin:profiles_song_change", args=[self.song.id]))
        self.assertContains(r, "page 2, switch 2")

    def test_standalone_slot_form_applies_limit(self):
        r = self.client.post(reverse("admin:profiles_slot_add"), {"song": self.song.id, "position": 9, "patch": 0, "label": ""})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Turn on pagination")


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
        self.assertEqual(head["version"], 2)
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
            self.assertFalse(song["paginate"])
        self.assertEqual(lines[3]["slots"], [None] * 8)

    def test_paginating_song_has_whole_pages(self):
        paged = Song.objects.create(name="Paged", paginate=True)
        Slot.objects.create(song=paged, position=1, patch=0)
        Slot.objects.create(song=paged, position=9, patch=1, patch_name="LEAD", label="Solo")
        song = next(s for s in self.lines(style="core", channel=1)[1:] if s["name"] == "Paged")
        self.assertTrue(song["paginate"])
        self.assertEqual(len(song["slots"]), 14)
        self.assertEqual(song["slots"][8]["number"], "U002")
        self.assertEqual([i for i, x in enumerate(song["slots"]) if x], [0, 8])

    def test_paginating_song_with_no_slots_has_one_page(self):
        Song.objects.create(name="Paged Empty", paginate=True)
        song = next(s for s in self.lines(style="core", channel=1)[1:] if s["name"] == "Paged Empty")
        self.assertEqual(song["slots"], [None] * 7)

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


class RefreshNamesTests(TestCase):
    def setUp(self):
        from .names import refresh_names

        self.refresh = refresh_names
        self.song = Song.objects.create(name="s")
        self.a = Slot.objects.create(song=self.song, position=1, patch=60, patch_name="OLD NAME")
        self.b = Slot.objects.create(song=self.song, position=2, patch=60, patch_name="OLD NAME")  # same patch
        self.c = Slot.objects.create(song=self.song, position=3, patch=61, patch_name="KEEP ME")
        self.preset = Slot.objects.create(song=self.song, position=4, patch=300, patch_name="FACTORY")

    @mock.patch.object(midi, "read_patch_name", side_effect=lambda i: {60: "NEW NAME", 61: "KEEP ME"}[i])
    def test_updates_changed_names_and_reads_each_patch_once(self, read):
        result = self.refresh(Slot.objects.all())
        self.assertEqual(read.call_count, 2)  # patches 60 and 61; preset skipped
        self.assertEqual(result.patches_read, 2)
        self.assertEqual(result.slots_checked, 3)
        self.assertEqual(result.changed, 2)
        self.assertEqual(Slot.objects.get(pk=self.a.pk).patch_name, "NEW NAME")
        self.assertEqual(Slot.objects.get(pk=self.b.pk).patch_name, "NEW NAME")
        self.assertEqual(Slot.objects.get(pk=self.c.pk).patch_name, "KEEP ME")
        self.assertEqual(Slot.objects.get(pk=self.preset.pk).patch_name, "FACTORY")
        self.assertIsNone(result.aborted)
        self.assertEqual(result.summary(), "2 patches read, 3 slots checked, 2 names changed")

    @mock.patch.object(midi, "read_patch_name", return_value="X")
    def test_presets_included_on_request(self, read):
        result = self.refresh(Slot.objects.all(), include_presets=True)
        self.assertEqual(sorted(c.args[0] for c in read.call_args_list), [60, 61, 300])
        self.assertEqual(result.slots_checked, 4)
        self.assertEqual(Slot.objects.get(pk=self.preset.pk).patch_name, "X")

    @mock.patch.object(midi, "read_patch_name", side_effect=ConnectionError("no unit"))
    def test_no_unit_aborts_after_first_read(self, read):
        result = self.refresh(Slot.objects.all())
        self.assertEqual(read.call_count, 1)
        self.assertEqual(result.aborted, "no unit")
        self.assertEqual(result.changed, 0)
        self.assertEqual(Slot.objects.get(pk=self.a.pk).patch_name, "OLD NAME")

    @mock.patch.object(midi, "read_patch_name", side_effect=[TimeoutError("slow"), "KEEP ME"])
    def test_single_failure_is_recorded_and_others_continue(self, read):
        result = self.refresh(Slot.objects.all())
        self.assertEqual(result.failures, {60: "slow"})
        self.assertEqual(result.patches_read, 1)
        self.assertEqual(result.changed, 0)
        self.assertEqual(Slot.objects.get(pk=self.a.pk).patch_name, "OLD NAME")

    @mock.patch.object(midi, "read_patch_name", side_effect=lambda i: {60: "NEW NAME", 61: "KEEP ME"}[i])
    def test_command_output(self, read):
        import io

        from django.core.management import call_command

        out = io.StringIO()
        call_command("refresh_names", stdout=out)
        text = out.getvalue()
        self.assertIn('s #1 U061: "OLD NAME" -> "NEW NAME"', text)
        self.assertIn("2 names changed", text)

    @mock.patch.object(midi, "read_patch_name", side_effect=ConnectionError("no unit"))
    def test_command_fails_without_unit(self, read):
        from django.core.management import CommandError, call_command

        with self.assertRaises(CommandError):
            call_command("refresh_names")

    @mock.patch.object(midi, "read_patch_name", side_effect=lambda i: {60: "NEW NAME", 61: "KEEP ME"}[i])
    def test_admin_action_on_songs(self, read):
        from django.contrib.auth.models import User

        self.client.force_login(User.objects.create_superuser("t", "t@example.com", "pw"))
        r = self.client.post(reverse("admin:profiles_song_changelist"),
                             {"action": "refresh_song_names", "_selected_action": [self.song.pk]}, follow=True)
        self.assertContains(r, "Patch names refreshed")
        self.assertContains(r, "is now &quot;NEW NAME&quot;")
        self.assertEqual(Slot.objects.get(pk=self.a.pk).patch_name, "NEW NAME")
