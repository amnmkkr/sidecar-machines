# GALACTIC 0.1.0

Airwindows' Galactic reverb as a send effect (Plugin API 3): vibrato pre-delay, a tank of Householder-mixed delays, always fully wet.

- Id: `fx.galactic`, kind: effect (a send effect on the Rytm's UFX slots)
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 3
- Licence: MIT
- Source: https://github.com/trigcondition/sidecar-firmware (`plugins/ufx_galactic`)

## Knobs

- Replace (REPL)
- Brightness (BRT)
- Detune (DTUN)
- Bigness (BIG)

## Credits and licence

The algorithm is Galactic by Chris Johnson (Airwindows, MIT, https://github.com/airwindows/airwindows), ported to C. The port and glue are MIT, Copyright 2026 trigcondition and contributors.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
