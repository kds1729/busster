"""
End-to-end UI tests: real Chrome driving the simulator page against Django's
live test server and a throwaway test database.

Optional. Skipped unless E2E=1 is set:

    E2E=1 uv run python manage.py test profiles.tests_e2e
    E2E=1 E2E_HEADED=1 uv run python manage.py test profiles.tests_e2e   # watch it

Needs the "e2e" dependency group (uv sync --group e2e) and Google Chrome
installed. Nothing is sent to a GT-1000: the MIDI layer is mocked inside the
server process, which also lets the tests assert what would have been sent.
"""

import os
import unittest
from unittest import mock

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from . import midi
from .models import Slot, Song

# Playwright's sync API runs inside the test thread while the live server runs
# in another thread of the same process. Django guards against that by default.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

E2E = os.environ.get("E2E") == "1"
HEADED = os.environ.get("E2E_HEADED") == "1"

LED_GREEN = "rgb(62, 207, 142)"
LED_BLUE = "rgb(59, 139, 255)"
LED_OFF = "rgb(42, 46, 53)"
LED_RED = "rgb(255, 74, 74)"     # switch 8 while the song paginates

SONGS = {
    "song1": [(34, "CLEAN COMBO"), (145, "JAZZ FUNK CHORUS"), (216, "ORANGE JUICE"), (205, "SOULFUL GAIN")],
    "song2": [(195, "SPACED OUT"), (16, "PEDAL POWER"), (65, "DEFRETTER"), (30, "CRUNCHED"), (126, "GROOVY FUNK")],
    "song3": [(194, "FAT COMP LEAD"), (115, "SUPER OCTAVE"), (120, "DEEP PAD ECHO")],
}
FAKE_NAMES = {idx: name for slots in SONGS.values() for idx, name in slots}
FAKE_NAMES[60] = "GIG READY"


def bank_program(index):
    return divmod(index, midi.PROGRAMS_PER_BANK)


@unittest.skipUnless(E2E, "set E2E=1 to run the Chrome end-to-end tests")
class SimulatorE2ETests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from playwright.sync_api import sync_playwright

        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch(channel="chrome", headless=not HEADED)
        except Exception:  # no Google Chrome: fall back to Playwright's Chromium if installed
            cls.browser = cls.playwright.chromium.launch(headless=not HEADED)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        for name, slots in SONGS.items():
            song = Song.objects.create(name=name)
            for position, (patch, patch_name) in enumerate(slots, start=1):
                Slot.objects.create(song=song, position=position, patch=patch, patch_name=patch_name)

        self.sent = []  # list of (bank, program) in the order the server sent them

        def fake_send(messages):
            bank = next(m.value for m in messages if m.type == "control_change" and m.control == 0)
            program = next(m.program for m in messages if m.type == "program_change")
            self.sent.append((bank, program))

        self.send_patch = mock.patch.object(midi.output, "send", side_effect=fake_send)
        self.send_patch.start()
        self.addCleanup(self.send_patch.stop)

        self.read_patch = mock.patch.object(midi, "read_patch_name", side_effect=lambda i: FAKE_NAMES.get(i, f"PATCH {i}"))
        self.read_patch.start()
        self.addCleanup(self.read_patch.stop)

        self.context = self.browser.new_context(viewport={"width": 1280, "height": 720})
        self.page = self.context.new_page()
        self.addCleanup(self.context.close)

    # ---- helpers -----------------------------------------------------------

    def open_unit(self):
        self.page.goto(self.live_server_url + "/")
        self.page.wait_for_function("document.querySelectorAll('#patches .sw').length === 8")
        self.wait_sent(1)

    def wait_sent(self, count, timeout_ms=5000):
        """Wait until the server has sent `count` patch changes in total."""
        import time

        deadline = time.monotonic() + timeout_ms / 1000
        while len(self.sent) < count:
            if time.monotonic() > deadline:
                self.fail(f"expected {count} sends, got {len(self.sent)}: {self.sent}")
            self.page.wait_for_timeout(20)
        # ...and until the page has processed the reply, so the next press isn't dropped.
        self.page.wait_for_function("document.body.dataset.busy !== '1'", timeout=timeout_ms)

    def display(self):
        return self.page.locator("#lcd-song").inner_text(), self.page.locator("#lcd-label").inner_text()

    def led_colors(self):
        return self.page.eval_on_selector_all(
            "#patches .sw .led", "els => els.map(e => getComputedStyle(e).backgroundColor)"
        )

    def switch(self, n):
        return self.page.locator(f"#patches .sw[data-index='{n - 1}']")

    def press_switch(self, n):
        before = len(self.sent)
        self.switch(n).click()
        self.wait_sent(before + 1)
        return self.sent[before:]

    def change_song(self, direction, expect_name):
        before = len(self.sent)
        self.page.locator("#song-up" if direction == "down" else "#song-down").click()
        self.page.wait_for_function(f"document.querySelector('#lcd-song').textContent === '{expect_name}'")
        self.wait_sent(before + 1)

    def expect_switches(self, expected):
        """expected: dict position -> 'green' | 'blue' | 'red' | 'off'."""
        colors = self.led_colors()
        want = {"green": LED_GREEN, "blue": LED_BLUE, "red": LED_RED, "off": LED_OFF}
        for pos in range(1, 9):
            self.assertEqual(colors[pos - 1], want[expected.get(pos, "off")], f"switch {pos}")

    # ---- tests -------------------------------------------------------------

    def test_page_load_selects_first_song_and_switch_1(self):
        self.open_unit()
        self.assertEqual(self.display(), ("song1", "U035 - CLEAN COMBO"))
        self.expect_switches({1: "green", 2: "blue", 3: "blue", 4: "blue"})
        self.assertEqual(self.sent, [bank_program(34)])
        for n in range(5, 9):
            self.assertTrue(self.switch(n).is_disabled(), f"switch {n} should be inert")

    def test_song_down_loads_next_song_switch_1(self):
        self.open_unit()
        self.change_song("down", "song2")
        self.assertEqual(self.display(), ("song2", "U196 - SPACED OUT"))
        self.expect_switches({1: "green", 2: "blue", 3: "blue", 4: "blue", 5: "blue"})
        self.assertEqual(self.sent[-1], bank_program(195))

    def test_song_list_wraps_both_ways(self):
        self.open_unit()
        self.change_song("up", "song3")  # up from song1 wraps to the last song
        self.assertEqual(self.display(), ("song3", "U195 - FAT COMP LEAD"))
        self.change_song("down", "song1")  # and back
        self.assertEqual(self.display()[0], "song1")
        self.assertEqual(self.sent, [bank_program(34), bank_program(194), bank_program(34)])

    def test_pressing_a_switch_sends_its_patch_and_moves_the_green_led(self):
        self.open_unit()
        sent = self.press_switch(3)
        self.assertEqual(sent, [bank_program(216)])
        self.assertEqual(self.display(), ("song1", "U217 - ORANGE JUICE"))
        self.expect_switches({1: "blue", 2: "blue", 3: "green", 4: "blue"})

    def test_unassigned_switch_does_nothing(self):
        self.open_unit()
        before = list(self.sent)
        self.switch(7).click(force=True)
        self.page.wait_for_timeout(200)
        self.assertEqual(self.sent, before)
        self.assertEqual(self.display(), ("song1", "U035 - CLEAN COMBO"))

    def test_keyboard_shortcuts(self):
        self.open_unit()
        self.page.keyboard.press("2")
        self.wait_sent(2)
        self.assertEqual(self.display()[1], "U146 - JAZZ FUNK CHORUS")
        self.assertEqual(self.sent[-1], bank_program(145))
        self.page.keyboard.press("ArrowDown")
        self.page.wait_for_function("document.querySelector('#lcd-song').textContent === 'song2'")
        self.wait_sent(3)
        self.assertEqual(self.display(), ("song2", "U196 - SPACED OUT"))

    def test_pagination_switch_8_turns_the_page(self):
        # The rare song with more than eight patches: positions 1-7 are page 1,
        # 8-14 page 2, 15-21 page 3. "zz" so it sorts last.
        paged = Song.objects.create(name="zz paged", paginate=True)
        for position, patch in [(1, 10), (7, 11), (8, 12), (16, 13)]:
            Slot.objects.create(song=paged, position=position, patch=patch, patch_name=f"POS {position}")
        self.open_unit()
        self.change_song("up", "zz paged")            # up from song1 wraps to the last song
        self.assertEqual(self.sent[-1], bank_program(10))
        self.assertEqual(self.page.locator("#lcd-page").inner_text(), "1/3")
        self.expect_switches({1: "green", 7: "blue", 8: "red"})

        sends = len(self.sent)
        self.switch(8).click()                        # page 2: position 8 sits under switch 1
        self.page.wait_for_function("document.querySelector('#lcd-page').textContent === '2/3'")
        self.expect_switches({1: "blue", 8: "red"})   # the active slot is on page 1, so no green here
        self.assertEqual(self.press_switch(1), [bank_program(12)])
        self.assertEqual(self.display(), ("zz paged", "U013 - POS 8"))
        self.expect_switches({1: "green", 8: "red"})

        self.switch(8).click()                        # page 3: position 16 is switch 2
        self.page.wait_for_function("document.querySelector('#lcd-page').textContent === '3/3'")
        self.expect_switches({2: "blue", 8: "red"})
        self.switch(8).click()                        # and wraps to page 1
        self.page.wait_for_function("document.querySelector('#lcd-page').textContent === '1/3'")
        self.expect_switches({1: "blue", 7: "blue", 8: "red"})
        self.assertEqual(len(self.sent), sends + 1)   # turning pages sent nothing

        self.change_song("down", "song1")             # a plain song: no page readout, switch 8 not red
        self.assertEqual(self.page.locator("#lcd-page").inner_text(), "")
        self.expect_switches({1: "green", 2: "blue", 3: "blue", 4: "blue"})

    def test_midi_error_is_shown_on_display(self):
        self.send_patch.stop()
        failing = mock.patch.object(midi.output, "send", side_effect=ConnectionError("GT-1000 not found"))
        failing.start()
        self.addCleanup(failing.stop)
        self.page.goto(self.live_server_url + "/")
        self.page.wait_for_function("document.querySelector('#lcd-msg').textContent !== ''")
        self.assertIn("GT-1000 not found", self.page.locator("#lcd-msg").inner_text())

    def test_admin_creates_song_and_patch_name_is_read_from_unit(self):
        User.objects.create_superuser("admin", "admin@example.com", "pw")
        p = self.page
        p.goto(self.live_server_url + "/admin/login/")
        p.fill("#id_username", "admin")
        p.fill("#id_password", "pw")
        p.click("input[type=submit]")
        p.goto(self.live_server_url + "/admin/profiles/song/add/")
        p.fill("#id_name", "new song")
        p.fill("#id_slots-0-position", "1")
        p.fill("#id_slots-0-patch", "60")
        p.fill("#id_slots-0-label", "clean")
        p.click("input[name=_save]")
        p.wait_for_url("**/admin/profiles/song/")

        slot = Slot.objects.get(song__name="new song")
        self.assertEqual((slot.patch, slot.patch_name), (60, "GIG READY"))

        # "new song" sorts first alphabetically, so the unit loads it on start, name included.
        self.open_unit()
        self.assertEqual(self.display(), ("new song", "U061 - GIG READY"))
        self.assertEqual(self.sent[-1], bank_program(60))
