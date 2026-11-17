# VOX 1.0.0

A sung or spoken vocal tract: a glottis into a 44-segment waveguide tract, played by knobs and notes. The DSP is Pink Trombone's by Neil Thapen.

- Id: `vox.trombone`, kind: machine
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 2
- Licence: MIT
- Source: https://github.com/trigcondition/sidecar-firmware (`plugins/vox`)

## Knobs

- Vowel (VOWL)
- Tongue (TONG)
- Constr Pos (CONS)
- Constr Dia (CDIA)
- Tenseness (TENS)
- Breath (BRTH)
- Vibrato (VIBR)
- Nasal (NASL)
- Attack (ATK)
- Release (REL)
- Glide (GLID)
- Wobble (WOBL)
- Vib Rate (VRAT)
- Velocity (VEL)
- Level (LEV)

## Credits and licence

The DSP is Pink Trombone v1.1 (Neil Thapen, MIT, https://dood.al/pinktrombone/), rewritten in C. The adaptation and glue are MIT, Copyright 2026 trigcondition and contributors.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
