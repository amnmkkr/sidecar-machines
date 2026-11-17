# TPFM 1.0.0

A two-oscillator percussion voice in the style of classic semi-modular drum synths: FM from osc 1 into osc 2, hard
sync, noise, a 4-pole ladder filter with low-pass and high-pass modes, and pitch, filter and amp decays. Kicks, toms,
snares, metallic clangs and zaps.

- Id: `twinperc.perc`, kind: machine (user slots U1..U5)
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 2
- Licence: MIT
- Author: amnmkkr

Mono, one voice a track. Each hit ends with the amp decay (note off is ignored). A retrigger starts from the level that
is sounding, with a 0.3 ms ramp, so fast rolls do not click. The note sets the pitch, so p-lock notes for tuned toms.
Velocity scales the envelopes and the level.

## Knobs

| P | Short | Long | What it does |
|---|---|---|---|
| 1 | TUN1 | Osc1 Tune | centred, +-24 semitones |
| 2 | PEG1 | Osc1 P.Env | centred, +-48 semitones at the strike |
| 3 | TUN2 | Osc2 Tune | centred, +-24 semitones |
| 4 | PEG2 | Osc2 P.Env | centred, +-48 semitones |
| 5 | FM | FM 1>2 | osc 1 into osc 2's pitch, up to 4 octaves |
| 6 | PDEC | Pitch Decay | 2 ms .. 1.5 s |
| 7 | CUT | Cutoff | 20 Hz .. 16 kHz |
| 8 | RES | Resonance | self-oscillates from about 116 |
| 9 | WAVE | Waves/Sync | SAW SAW, SAW SQR, SQR SAW, SQR SQR, then the same four with osc 2 synced to osc 1 |
| 10 | BAL | Osc1<>Osc2 | centred oscillator balance |
| 11 | NOIS | Noise | noise into the mixer |
| 12 | FEG | HP<>LP Env | below 64 high-pass mode, above 64 low-pass; the distance from 64 is the envelope depth (up to 6 octaves) |
| 13 | FDEC | Filter Dec | 5 ms .. 2.5 s |
| 14 | FMOD | Noise>Cut | noise into the cutoff (grit, hats) |
| 15 | ADEC | Amp Decay | 10 ms .. 3.5 s |
| 16 | LEV | Level | |

Starting points: kick: PEG1 100, FM 0, PDEC 57, CUT 58, WAVE SAW SAW, BAL 12, NOIS 0, ADEC 74. Snare: PEG1 82, TUN2
83, FM 40, WAVE SYNC QQ, NOIS 96, FEG 30, FMOD 40, ADEC 56. Clang: TUN2 97, FM 92, CUT 92, RES 70, ADEC 78.

## Cost

State 140 B a voice, image 8 KB, no allocation and no host calls in render. Declared `cpu_permille` 70 (about 1.7 x
`sc_acid` measured on the same host).

## Testing

Checked on a desktop build: every knob at both ends, 300 random settings and fast retriggers stay finite and bounded
(peak at most 0.92), with no denormals and no retrigger clicks. Built with `aarch64-linux-gnu-gcc` and packed by the
Sidecar repository's `tools/rmp_pack.py`.

## Credits and licence

Written from scratch for the Sidecar; no code taken from elsewhere. MIT, Copyright 2026 amnmkkr. Inspired by the
layout of two-VCO semi-modular percussion synths; not affiliated with or endorsed by any manufacturer.

The registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
