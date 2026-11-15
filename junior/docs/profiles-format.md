# Profiles file format

The **profiles file** is the interface between the laptop and the floor unit.
The laptop app (one per supported device, see [`../devices/`](../devices/))
exports it; the floor unit reads it and does nothing else. A *profile* is the
complete configuration for one song: its name and the MIDI to send for each of
the eight footswitches.

- File name: `profiles.jsonl`
- Location on the floor unit: the root of its USB drive
- Encoding: UTF-8, Unix line endings
- Shape: [JSON Lines](https://jsonlines.org/) — one JSON object per line

Refreshing the floor unit means copying a new `profiles.jsonl` over the old one.
The unit reads the file every time it powers up. Nothing is ever "set in stone":
the file can be regenerated and copied as often as the owner likes, and no
firmware change is involved.

## Design rules

1. **The floor unit is device-agnostic.** The laptop works out the exact MIDI
   bytes for every switch and writes them into the file. The firmware sends
   them as given. It never computes bank numbers, program numbers, or anything
   else about the effects processor. A new device needs a new exporter on the
   laptop, not new firmware.
2. **One line per song, in display order.** The floor unit shows songs in file
   order and never sorts.
3. **Line-at-a-time parsing.** The firmware can read and decode one line at a
   time, so the file size is limited by flash, not by RAM.
4. **Text, not binary.** The file is readable and editable by hand and diffs
   cleanly.

## Line 1: the header

```json
{"format": "busster-junior-profiles", "version": 2, "exported": "2026-11-15T15:30:00Z", "device": "gt1000", "style": "core", "channel": 1, "song_count": 2}
```

| Field | Type | Meaning |
|---|---|---|
| `format` | string | Always `"busster-junior-profiles"`. The firmware refuses a file without it. |
| `version` | integer | Format version. This document describes version 2. The firmware refuses a version it does not know. |
| `exported` | string | When the file was written, ISO 8601, UTC. Informational. |
| `device` | string | Key of the exporter that wrote the file, e.g. `"gt1000"`. Informational. |
| `style` | string | Display style the patch numbers were written in, e.g. `"core"` or `"full"` for the GT-1000. Informational. |
| `channel` | integer | MIDI channel, 1-16, the bytes were built for. Informational. |
| `song_count` | integer | Number of song lines that follow. Lets the firmware size its lists before reading them. |

"Informational" means the firmware may show the value but must not act on it.
Everything the firmware needs to act on is already encoded in the slots.

## Lines 2 and on: one song profile per line

```json
{"name": "All Along the Watchtower", "artist": "Hendrix", "paginate": false, "slots": [{"number": "U015", "patch_name": "CLEAN VERSE", "label": "Intro", "midi": "B0 00 00 B0 20 00 C0 0E"}, {"number": "U016", "patch_name": "CRUNCH", "label": "Verse", "midi": "B0 00 00 B0 20 00 C0 0F"}, null, null, null, null, null, null]}
```

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Song name as shown on the floor unit. Unique within the file. |
| `artist` | string | May be empty. Informational. |
| `paginate` | boolean | Whether switch 8 pages through the slots instead of selecting a patch. See [Pagination](#pagination). |
| `slots` | array | One entry per slot position, position 1 first. An unassigned position is `null`. Exactly 8 entries when `paginate` is false; a multiple of 7 when it is true. |

### A slot

| Field | Type | Meaning |
|---|---|---|
| `number` | string | The patch number as the device writes it on its own display, e.g. `"U015"` or `"U03-5"`. Display only. |
| `patch_name` | string | The patch name as read from the device when the slot was assigned. May be empty if the name could not be read. Display only. |
| `label` | string | The owner's own note for the slot, e.g. `"Solo"`. May be empty. Display only. |
| `midi` | string | The bytes to send when the switch is pressed, as uppercase two-digit hex separated by single spaces. May contain any MIDI messages, including SysEx. Never empty. |

The patch index the laptop stores internally is deliberately **not** in the
file. The floor unit has no use for it, and leaving it out removes any
temptation to compute MIDI on the box.

`number`, `patch_name` and `label` are kept separate so the firmware can lay
them out to suit its screen. Nothing in the file is pre-formatted for a
particular display size.

## Pagination

Pagination is the exception, not the rule. Eight patches is plenty for almost
every song, and `paginate` stays `false` unless a song genuinely needs more. In
that rare case the song gives up switch 8 as a patch selector and uses it to
step through **pages** of seven patches:

| Page | Slot positions | Footswitch |
|---|---|---|
| 1 | 1-7 | 1-7 |
| 2 | 8-14 | 1-7 |
| 3 | 15-21 | 1-7 |

Position *n* is on page `(n - 1) // 7` (0-based) and under footswitch
`(n - 1) % 7 + 1`. The `slots` array is padded with `null` so that its length is
a whole number of pages, and it is never shorter than one page (7 entries). A
song with `paginate` false has exactly 8 entries and no pages.

Pressing switch 8 on a paginating song moves to the next page and wraps from the
last page back to the first. It sends nothing. Selecting a song always lands on
page 1. While the current song paginates, switch 8's LED is **red**; otherwise
switch 8 lights like the other seven. The display shows the current page and
the page count, for example `2/3`.

```json
{"name": "Comfortably Numb", "artist": "Pink Floyd", "paginate": true, "slots": [{"number": "U021", "patch_name": "CLEAN", "label": "Intro", "midi": "B0 00 00 B0 20 00 C0 14"}, null, null, null, null, null, null, {"number": "U022", "patch_name": "LEAD", "label": "Solo 1", "midi": "B0 00 00 B0 20 00 C0 15"}, null, null, null, null, null, null]}
```

Here position 8 is the first patch of page 2: the player presses switch 8 to
turn the page, then switch 1 to select it.

## What the floor unit does with it

- On power-up, read the header, check `format` and `version`, then read the
  song lines.
- Show the first song and **immediately send slot 1's `midi`**. Selecting any
  song, by any means, always sends its slot 1 at once.
- Footswitch *n* (1-7, or 1-8 when the song does not paginate) sends the
  `midi` of the slot at position `page * 7 + n` on a paginating song, or
  `slots[n-1].midi` otherwise. A `null` slot does nothing.
- On a paginating song, footswitch 8 advances the page (wrapping) and sends
  nothing. Switch 8's LED is red while such a song is selected.
- Up/down footswitches move through the songs in file order.

## GT-1000 exporter notes

The GT-1000 app writes the file with:

```bash
uv run python manage.py export [path-or-directory | -] [--style core|full] [--channel N]
```

Run `manage.py refresh_names` first if patches have been renamed on the unit,
so the names in the file are current. Both commands are described in the app's
[README](../devices/boss_gt-1000/README.md).

The exporter builds `midi` from the 0-based patch index it stores, with the
factory program map (MAP SEL = PROG, 125 patches per bank, measured 2026-11-14
on a GT-1000CORE):

```
bank    = index // 125
program = index % 125
midi    = Bn 00 bank   Bn 20 00   Cn program        (n = channel - 1)
```

So patch index 14 (U015) on channel 1 is `B0 00 00 B0 20 00 C0 0E`, and
index 380 (P131) is `B0 00 03 B0 20 00 C0 05`. Bank 3 (P126-P250) has not yet
been verified on hardware.

## Versioning

`version` goes up only when a change would make an older firmware misread the
file. Adding a new optional field does not need a new version; the firmware
ignores fields it does not know.

| Version | Change |
|---|---|
| 1 | First version. Exactly 8 slots per song. |
| 2 | Adds `paginate` per song; `slots` may be longer than 8 (a multiple of 7) when it is true. Version 1 firmware would misread the longer array, hence the bump. |
