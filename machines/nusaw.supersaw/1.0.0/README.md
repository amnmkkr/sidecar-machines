# NUSAW 1.0.0

A supersaw machine for pads and stabs: seven PolyBLEP saws with a detune curve, drift and a filter. The engine is NuSaw's by Charles Vestal.

- Id: `nusaw.supersaw`, kind: machine
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 2
- Licence: MIT
- Source: https://github.com/trigcondition/sidecar-firmware (`plugins/nusaw`)

## Knobs

- Detune (DETN)
- Mix (MIX)
- Cutoff (CUT)
- Resonance (RES)
- Filter Env (ENV)
- Attack (ATK)
- Release (REL)
- Sub Osc (SUB)
- Tune (TUN)
- Decay (DEC)
- Sustain (SUS)
- Filt Decay (FDEC)
- Filt Sustain (FSUS)
- Velocity (VEL)
- Level (LEV)

## Credits and licence

The engine is NuSaw (Charles Vestal, MIT, https://github.com/saustin2010/mpc-vst-nusaw, from https://github.com/charlesvestal/schwung-nusaw), rewritten in C for one voice. The adaptation and glue are MIT, Copyright 2026 trigcondition and contributors.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
