# BP303 1.0.0

A 303-style acid bass voice: saw/square blend into a diode-ladder style lowpass with envelope, accent, slide and a soft drive. The voice is BLACKPYRAMIDS_303's, built on Open303.

- Id: `bp303.bass`, kind: machine
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 2
- Licence: MIT
- Source: https://github.com/trigcondition/sidecar-firmware/tree/v0.5.1/plugins/bp303

## Knobs

- Cutoff (CUT)
- Resonance (RES)
- Env Mod (ENV)
- Decay (DEC)
- Accent (ACC)
- Saw>Square (WAVE)
- Slide Time (SLID)
- Volume (VOL)
- Tune (TUNE)

## Credits and licence

The voice is BLACKPYRAMIDS_303 from OT Kyoti FW (Zac Kyoti and contributors, MIT, https://github.com/Zac-Kyoti/octatrack-kyoti-fw), which began as a port of Open303 (Robin Schmidt, MIT, https://github.com/RobinSchmidt/Open303). The Sidecar port and glue are MIT, Copyright 2026 trigcondition and contributors. Not affiliated with any synthesizer maker.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
