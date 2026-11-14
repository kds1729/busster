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
