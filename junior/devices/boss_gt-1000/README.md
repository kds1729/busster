# BUSSter Junior

**A song-based patch selector for the BOSS GT-1000 / GT-1000CORE**

Proof of concept: a laptop application that lets you dial up a song and have a bank
of eight footswitches loaded with the GT-1000 patches that song needs, so stepping
through the sounds in a song is one button press each.

This directory is a self-contained Django project. It is the configurator and
simulator for a floor unit that does not exist yet. See
[Where this is going](#where-this-is-going) for the plan.

---

## The problem

The GT-1000 is a superb multi-effects unit, but its patches are stored in whatever
order you made them. Playing live means a song might need U035, then U146, then
U217, then U205, and none of those are next to each other. Scrolling through the
patch list between parts of a song is not workable on stage.

## The idea

- On the laptop, create a **song** and assign a GT-1000 **patch** to each of up to
  **eight switches**, in the order the song needs them.
- On the floor, pick the song with **up/down switches**, and the unit loads
  switch 1's patch immediately. Each switch press loads its patch. That's it.
- All configuration happens on the laptop. The floor unit only holds the uploaded
  setlist, shows the current song and patch, and sends MIDI. No editing on the
  device.

This proof of concept runs entirely on the laptop. The web page stands in for the
floor unit, and the laptop sends the MIDI itself over USB.

---

## What was built

| Piece | What it does |
|---|---|
| **Django admin** | Create songs. For each song, assign a patch and an optional label to switches 1 to 8. |
| **Patch names from the unit** | When a switch is assigned, the laptop reads that patch's 16-character name from the GT-1000 over SysEx and stores it with the slot. The name travels with the config, so the floor unit never has to ask the unit for anything. |
| **Simulator page** | A picture of the floor unit: a display, eight patch switches in a row, and two song switches set apart. Mapped switches light blue, the active one green. Selecting a song sends switch 1's patch at once. Keyboard: `1`–`8` for switches, `↑`/`↓` for songs. |
| **MIDI layer** | Sends Bank Select + Program Change over USB with the mapping measured on the real unit, and reads patch names with Roland RQ1/DT1 SysEx. |
| **Seed command** | Loads three sample songs with random patches, reading names from the unit if it's connected. |
| **Tests** | 17 unit tests with MIDI mocked. 8 optional end-to-end tests that drive the page in real Google Chrome against a live test server. |

---

## What we learned about the GT-1000

Everything below was verified on a GT-1000CORE on 2026-11-14, firmware per
Roland's *GT-1000/GT-1000CORE MIDI Implementation* v4.01 (dated March 2026).

### Selecting a patch

Three messages, on the unit's RX channel (default 1):

```
CC#0  = bank          Bank Select MSB
CC#32 = 0             Bank Select LSB, always 0
Program Change = 0..124
```

**The map is 125 patches per bank, not 128.** With the unit's PROGRAM MAP at its
factory setting (MAP SEL = PROG) the layout is:

| Bank (CC#0) | Program 0 to 124 |
|---|---|
| 0 | U001 to U125 |
| 1 | U126 to U250 |
| 2 | P001 to P125 |
| 3 | P126 to P250 (assumed, not yet tested) |

Programs 125 to 127 in a bank clamp to that bank's last patch. So
`patch_index = bank * 125 + program`, where the index is 0 to 249 for user patches
and 250 to 499 for presets. A naive 128-per-bank assumption lands three patches
off in bank 1, which is exactly how this was discovered.

### Reading a patch name

Roland "Request Data 1" (RQ1) and "Data Set 1" (DT1):

```
request:  F0 41 dev 00 00 00 4F 11  aa bb cc dd  00 00 00 10  sum F7
reply:    F0 41 dev 00 00 00 4F 12  aa bb cc dd  <16 bytes>   sum F7
```

- `dev` is the unit's DEVICE ID minus 1 (the menu shows 1 to 32; the wire value is
  `00H` to `1FH`).
- Checksum: low 7 bits of `128 - (sum of address and size/data bytes) mod 128`.
- User patch *n* (0-based) lives at address `20+n//128, n%128, 00, 00`. Its first 16
  bytes are the name, ASCII 32 to 126, space padded.
- Presets aren't addressable that way, so for a preset the unit is switched to it
  and the temporary patch at `10 00 00 00` is read instead.

### Two units, two naming styles

The same MIDI works on both, but they display patches differently:

- **GT-1000CORE:** `U001` to `U250`, `P001` to `P250`.
- **Full-size GT-1000:** `U01-1` to `U50-5`, `P01-1` to `P50-5` (50 banks of 5).

The database stores the raw index and renders either style. The style is a
setting.

### Connections

- **USB** works out of the box on macOS with the unit's `USB DRIVER` set to
  `GENERIC`. CoreMIDI shows two ports, `GT-1000` and `GT-1000 DAW CTRL`; use the
  first. This is what the proof of concept uses.
- **5-pin / TRS MIDI** is what the floor unit will use, into the unit's MIDI IN. The
  CORE's MIDI jacks are 3.5 mm TRS, **Type A**. BOSS's own BMIDI adapters are
  correct. The full-size unit has 5-pin DIN jacks.
- A cheap LEKATO USB-C to 5-pin cable (vendor `6790`, product `29997`) **never got
  data into the unit** in either plug orientation, even though its OUT light
  blinked. The adapters and the unit's settings were ruled out. A Roland UM-ONE
  mk2 or similar is the sensible choice for testing the 5-pin path from a laptop.

---

## Running it

Requirements: Python 3.14, [uv](https://docs.astral.sh/uv/), a GT-1000 or
GT-1000CORE on USB (optional; without it the page shows an error on the display
instead of switching patches).

```bash
cd junior/devices/boss_gt-1000
uv sync                                   # installs Django, mido, python-rtmidi
uv run python manage.py migrate           # creates db.sqlite3
uv run python manage.py createsuperuser   # for the admin
uv run python manage.py seed              # optional: three sample songs
uv run python manage.py runserver
```

Then:

- **Simulator:** http://127.0.0.1:8000/
- **Admin:** http://127.0.0.1:8000/admin/ — add songs under *Setlist › Songs*.
  Each song has eight inline rows: switch number, patch index, label. The CORE and
  full-size patch numbers are shown read-only, and the patch name is filled from
  the unit when you save (a warning appears if the unit isn't connected; the slot
  still saves).

Patch index reminder: user patches are 0 to 249 (U001 is 0, U061 is 60), presets
are 250 to 499.

### Settings

At the bottom of `config/settings.py`:

| Setting | Default | Meaning |
|---|---|---|
| `GT1000_MIDI_PORT` | `"GT-1000"` | CoreMIDI port name to send to. |
| `GT1000_MIDI_CHANNEL` | `1` | Must match MENU › MIDI › MIDI SETTING › RX CH. |
| `GT1000_DEVICE_ID` | `17` | Must match DEVICE ID on the same screen. Used for SysEx. |
| `GT1000_PATCH_STYLE` | `"core"` | `"core"` for U001 style, `"full"` for U01-1 style. |

The Django secret key is read from `BUSSTER_SECRET_KEY` with a local-only default.
`DEBUG` is on; this is a single-user tool on a laptop, not a server.

### Tests

```bash
uv run python manage.py test setlist                      # 17 unit tests, MIDI mocked
E2E=1 uv run python manage.py test setlist.tests_e2e      # 8 Chrome end-to-end tests
E2E=1 E2E_HEADED=1 uv run python manage.py test setlist.tests_e2e   # watch the browser
```

The end-to-end suite needs the optional dependency group (`uv sync --group e2e`)
and Google Chrome. It launches its own headless Chrome, runs against Django's live
test server with a throwaway database, and mocks the MIDI layer inside the server
so each test can assert the exact bank and program that would have been sent. It
covers: load selects song 1 and switch 1; song down/up including wrap-around;
switch presses and LED states; inert unassigned switches; keyboard shortcuts; the
MIDI error path; and creating a song through the admin with the patch name read
from the (mocked) unit.

---

## Layout

```
junior/devices/boss_gt-1000/
├── manage.py
├── pyproject.toml / uv.lock         (uv-managed dependencies)
├── config/                          (Django project: settings, urls)
└── setlist/                         (the app)
    ├── models.py                    Song, Slot; patch number formatting for both units
    ├── midi.py                      bank/program mapping, patch-select send, SysEx name read
    ├── admin.py                     song editor; reads patch names on save
    ├── views.py / urls.py           simulator page, /api/select/<slot>/, /api/midi/
    ├── templates/setlist/unit.html  the simulator (self-contained HTML/CSS/JS)
    ├── management/commands/seed.py  sample data
    ├── tests.py                     unit tests
    └── tests_e2e.py                 optional Chrome end-to-end tests
```

### Data model

- **Song**: name (unique), artist, notes. Songs are listed alphabetically; that is
  the order the song switches scroll through.
- **Slot**: song, position 1 to 8, patch index 0 to 499, patch name (16 chars, from
  the unit), label (free text). One slot per position per song.

---

## Where this is going

Decisions made during the proof of concept:

1. **The laptop is the configurator; the floor unit only plays back.** Songs and
   patches are set up here and uploaded to the unit as a flat file. The unit has
   no editing workflow. The export format is the contract between the two halves
   and is the next thing to settle.
2. **The floor unit talks MIDI, not USB.** A MIDI OUT jack (5-pin DIN, or 3.5 mm TRS
   Type A for the CORE) into the unit's MIDI IN. It's a UART and two resistors on
   any microcontroller, works with both units, and leaves the unit's USB port free
   for Tone Studio. Connecting MIDI OUT back to the box is optional and would allow
   confirmation and name reads.
3. **Ten footswitches:** eight for patches plus song up and song down. A small
   display shows the song and the current patch, e.g. `U061 - GIG READY`.
4. **Microcontroller over Raspberry Pi.** Since nothing is edited on the device, a
   Pico/ESP32/Teensy's instant boot and immunity to power-loss corruption win over
   a Pi's ability to run this Django app directly.
5. **Device abstraction.** This code is deliberately tied to the GT-1000, the unit
   on hand. Before other processors are supported, the device-specific surface
   (patch naming and count, bank/program mapping, name read, display formatting)
   should sit behind an interface. Those pieces already live together in
   `midi.py` and the formatting functions in `models.py`.

Known gaps: bank 3 (P126 to P250) is assumed rather than measured; the 5-pin MIDI
path hasn't been exercised from the laptop for lack of a working interface; no
export command yet.
