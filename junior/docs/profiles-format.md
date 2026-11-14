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
{"format": "busster-junior-profiles", "version": 1, "exported": "2026-11-14T15:30:00Z", "device": "gt1000", "style": "core", "channel": 1, "song_count": 2}
```

| Field | Type | Meaning |
|---|---|---|
| `format` | string | Always `"busster-junior-profiles"`. The firmware refuses a file without it. |
| `version` | integer | Format version. This document describes version 1. The firmware refuses a version it does not know. |
| `exported` | string | When the file was written, ISO 8601, UTC. Informational. |
| `device` | string | Key of the exporter that wrote the file, e.g. `"gt1000"`. Informational. |
| `style` | string | Display style the patch numbers were written in, e.g. `"core"` or `"full"` for the GT-1000. Informational. |
| `channel` | integer | MIDI channel, 1-16, the bytes were built for. Informational. |
| `song_count` | integer | Number of song lines that follow. Lets the firmware size its lists before reading them. |

"Informational" means the firmware may show the value but must not act on it.
Everything the firmware needs to act on is already encoded in the slots.

## Lines 2 and on: one song profile per line

```json
{"name": "All Along the Watchtower", "artist": "Hendrix", "slots": [{"number": "U015", "patch_name": "CLEAN VERSE", "label": "Intro", "midi": "B0 00 00 B0 20 00 C0 0E"}, {"number": "U016", "patch_name": "CRUNCH", "label": "Verse", "midi": "B0 00 00 B0 20 00 C0 0F"}, null, null, null, null, null, null]}
```

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Song name as shown on the floor unit. Unique within the file. |
| `artist` | string | May be empty. Informational. |
| `slots` | array | Exactly 8 entries, one per footswitch, switch 1 first. An unassigned switch is `null`. |

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

## What the floor unit does with it

- On power-up, read the header, check `format` and `version`, then read the
  song lines.
- Show the first song and **immediately send slot 1's `midi`**. Selecting any
  song, by any means, always sends its slot 1 at once.
- Footswitch *n* sends `slots[n-1].midi`. A `null` slot does nothing.
- Up/down footswitches move through the songs in file order.

## GT-1000 exporter notes

The GT-1000 / GT-1000CORE exporter builds `midi` from the 0-based patch index
it stores, with the factory program map (MAP SEL = PROG, 125 patches per bank,
measured 2026-11-14 on a GT-1000CORE):

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
