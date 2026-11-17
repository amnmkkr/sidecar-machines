# MODEL E 1.1.0

A three-oscillator voice with a ladder filter, contours, glide and noise, for basses and leads. The oscillators are ModelDigi's bank. Free software: GPL-2.0-or-later.

- Id: `modele.voice`, kind: machine
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 2
- Licence: GPL-2.0-or-later
- Source: https://github.com/trigcondition/sidecar-firmware (`plugins/modele`)

## Knobs

- Osc 1 (OSC1)
- Osc 2 (OSC2)
- Osc 3 (OSC3)
- Osc 2 Tune (TUN2)
- Osc 3 Tune (TUN3)
- Osc 1<>2 Mix (MIX)
- Noise<>Osc 3 (O3NZ)
- Osc 3 Mod (MOD)
- Cutoff (CUT)
- Emphasis (EMPH)
- Contour Amt (CONT)
- Glide<>Atk (G<>A)
- Decay (DEC)
- Sustain (SUS)
- Mode (MODE)
- Level (LEV)

## Credits and licence

The oscillator bank is ModelDigi (https://github.com/simonjohansson/ModelDigi, GPL-2.0-or-later), built in unchanged, so this machine as a whole is GPL-2.0-or-later, Copyright (C) 2026 trigcondition and contributors. The complete corresponding source is plugins/modele in the source repository linked above (the plugin, the vendored ModelDigi files, and the SDK and packer that build it). Whoever passes the binary on passes that on too. 'Model D' names the layout the voice follows; not affiliated with any synthesizer maker.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
