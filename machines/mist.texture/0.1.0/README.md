# MIST 0.1.0

A granular texture machine: clouds, smears, frozen pads and wavetable grains, with a built-in oscillator at the trig's note. The DSP is Beads' by Emilie Gillet.

- Id: `mist.texture`, kind: machine
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 3
- Licence: MIT
- Source: https://github.com/trigcondition/sidecar-firmware (`plugins/mist`)

## Knobs

- Time (TIME)
- Size (SIZE)
- Density (DENS)
- Pitch (PTCH)
- Shape (SHAP)
- Feedback (FDBK)
- Spread (SPRD)
- Dry/Wet (MIX)
- Reverb (RVB)
- Freeze (FRZ)
- Quality (QUAL)
- Bank (BANK)
- Wave (WAVE)
- Time Random (TRND)
- Pitch Rand (PRND)
- Engine (ENG)

## Credits and licence

The DSP is Beads' (Emilie Gillet, MIT, https://github.com/pichenettes/eurorack, with stmlib). The adaptation and glue are MIT, Copyright 2026 trigcondition and contributors. Mutable Instruments is a registered trademark of its owner; MIST is not a Mutable Instruments product.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
