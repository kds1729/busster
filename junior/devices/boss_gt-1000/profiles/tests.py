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
