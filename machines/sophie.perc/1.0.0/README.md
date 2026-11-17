# SOPHIE 1.0.0

Metallic FM percussion: kicks, clangs, zaps, bells and shards from a carrier and three modulators at non-integer ratios. The DSP is Sophie's v0.5.1 by Matt Estela.

- Id: `sophie.perc`, kind: machine
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 2
- Licence: MIT
- Source: https://github.com/trigcondition/sidecar-firmware (`plugins/sophie`)

## Knobs

- Tune (TUN)
- Model (MODL)
- Color (COLR)
- Metal (METL)
- Feedback (FDBK)
- Sweep (SWP)
- Decay (DEC)
- Crush (CRSH)
- Drive (DRV)
- Cutoff (CUT)
- Resonance (RES)
- Filter Type (FLT)
- Ring Time (RTIM)
- Ring Feedbk (RFB)
- Ring Mix (RMIX)
- Ring Tone (RTON)

## Credits and licence

The DSP is Sophie v0.5.1 (Matt Estela, MIT, https://github.com/mestela/schwung-sophie), rewritten in C for the Sidecar. The adaptation and glue are MIT, Copyright 2026 trigcondition and contributors.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
