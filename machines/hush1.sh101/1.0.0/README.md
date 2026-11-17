# HUSH1 1.0.0

An SH-101-style mono synth for basses and leads: saw, pulse, sub and noise into a resonant lowpass with one ADSR. The DSP is HUSH ONE's by Charles Vestal.

- Id: `hush1.sh101`, kind: machine
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 2
- Licence: MIT
- Source: https://github.com/trigcondition/sidecar-firmware (`plugins/hush1`)

## Knobs

- Saw (SAW)
- Pulse (PULS)
- Pulse Width (PW)
- Sub Osc (SUB)
- Noise (NOIS)
- Cutoff (CUT)
- Resonance (RES)
- Filter Env (ENV)
- Attack (ATK)
- Decay (DEC)
- Sustain (SUS)
- Release (REL)
- Glide (GLID)
- Key Track (TRK)
- Level (LEV)
- VCA Mode (VCA)

## Credits and licence

The DSP is HUSH ONE (Charles Vestal, MIT, https://github.com/charlesvestal/schwung-hush1), rewritten in C. The adaptation and glue are MIT, Copyright 2026 trigcondition and contributors. Not affiliated with any synthesizer maker.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
