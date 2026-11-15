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
├── docs/        the profiles file format, the laptop-to-floor-unit interface
├── midi/        MIDI transport shared by all devices
├── simulator/   the floor-unit simulator
└── tests/       tests
```

The first device, and the current proof of concept, is the BOSS GT-1000 /
GT-1000CORE under [devices/boss_gt-1000/](devices/boss_gt-1000/).

The file the laptop exports and the floor unit plays back is specified in
[docs/profiles-format.md](docs/profiles-format.md).

## Status

**Laptop side: done** for the first floor-unit release. The GT-1000 app
configures songs, reads patch names from the unit, refreshes them on demand,
and exports `profiles.jsonl`. It also has a simulator page that stands in for
the hardware.

**Floor unit: not started.** It will be a Raspberry Pi Pico running
CircuitPython, with ten footswitches (eight patches plus song up/down), a
128x64 OLED, and a 5-pin MIDI OUT jack. The Pico mounts as a USB drive, so
uploading a new configuration is copying `profiles.jsonl` onto it. The firmware
reads that file and sends the MIDI bytes it contains; it knows nothing about any
particular effects processor.

The shared `midi/`, `simulator/` and `tests/` directories are placeholders
until a second device makes extracting the common parts worthwhile.
