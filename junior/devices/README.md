# Devices

One directory per supported effects processor, named `<vendor>_<model>`.

Each device directory holds everything specific to that unit: how its patches
are numbered, which MIDI messages select a patch, how patch names are read back
if the unit supports it, and any port or settings quirks.

| Directory | Unit | Status |
|---|---|---|
| [boss_gt-1000/](boss_gt-1000/) | BOSS GT-1000 and GT-1000CORE | Working proof of concept (Django app) |
