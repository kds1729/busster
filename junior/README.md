# BUSSter Junior

A song-based patch selector for multi-effects processors.

Dial up a song and have a bank of eight footswitches loaded with the patches
that song needs, so stepping through the sounds in a song is one button press
each. Configuration happens on a laptop and is uploaded to a floor unit that
only plays it back.

## Layout

```
junior/
├── devices/     one directory per supported effects processor
├── docs/        the profiles file format and the floor-unit enclosure
├── midi/        MIDI transport shared by all devices
├── simulator/   the floor-unit simulator
└── tests/       tests
```

The first device, and the current proof of concept, is the BOSS GT-1000 /
GT-1000CORE under [devices/boss_gt-1000/](devices/boss_gt-1000/).

The file the laptop exports and the floor unit plays back is specified in
[docs/profiles-format.md](docs/profiles-format.md). The floor unit's enclosure,
switch layout and display are specified in [docs/enclosure.md](docs/enclosure.md).

## Status

**Laptop side: done** for the first floor-unit release. The GT-1000 app
configures songs, reads patch names from the unit, refreshes them on demand,
and exports `profiles.jsonl`. It also has a simulator page that stands in for
the hardware.

**Floor unit: designed, not built.** It is a one-bend aluminium chassis on
wooden wedge ribs over a rigid base, with ten footswitches (eight patches on a gentle
arc plus song up/down), one RGB LED per patch switch, a 5 inch 800x480 colour display on an ESP32-S3
board (Sunton ESP32-8048S050C) running CircuitPython, and a 5-pin MIDI OUT jack.
In the rare case of a song with more than eight patches, switch 8 pages through
them seven at a time instead (red LED). The board mounts as a USB drive, so
uploading a new configuration is copying `profiles.jsonl` onto it. The firmware
reads that file and sends the MIDI bytes it contains; it knows nothing about any
particular effects processor. See [docs/enclosure.md](docs/enclosure.md).

The shared `midi/`, `simulator/` and `tests/` directories are placeholders
until a second device makes extracting the common parts worthwhile.
