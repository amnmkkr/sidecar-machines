# RAFFO 1.0.0

A four-oscillator mono synth with a Moog-style ladder lowpass, two envelopes and glide, for basses and leads. The DSP is RaffoSynth's.

- Id: `raffo.mono4`, kind: machine
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 2
- Licence: MIT
- Source: https://github.com/trigcondition/sidecar-firmware (`plugins/raffo`)

## Knobs

- Osc1 Wave (WAV1)
- Osc2+4 Wave (WAV2)
- Detune 2/4 (DTN2)
- Osc2+4 Mix (MIX)
- Sub Osc3 (SUB)
- Cutoff (CUT)
- Resonance (RES)
- Contour (ENV)
- Attack (ATK)
- Decay (DEC)
- Sustain (SUS)
- Release (REL)
- Filt Decay (FDEC)
- Filt Sustain (FSUS)
- Glide (GLID)
- Level (LEV)

## Credits and licence

The DSP is RaffoSynth (Nicolas Roulet and Julian Palladino, MIT, https://github.com/nicoroulet/RaffoSynth) as the Schwung module schwung-moog by Charles Vestal has it (MIT, https://github.com/charlesvestal/schwung-moog), rewritten in C. Upstream is MIT, so this machine is MIT. The adaptation and glue are MIT, Copyright 2026 trigcondition and contributors.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
