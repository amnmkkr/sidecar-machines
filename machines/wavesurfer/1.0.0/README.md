# WAVESURFER 1.0.0

Bastl Instruments' Kastle 2 Wave Bard (MIT) as a sample player for the Pi: a user machine, stereo out, playing the
project's SAMPLES pool (bank A, files under `/Samples`). Made for vocals and chops as much as for drums.

- Id: `wavesurfer`, kind: machine
- Board: Pi 5 (tested on a Pi 5 with the Touch Display 2)
- Plugin API: 3
- Licence: MIT
- Source: https://github.com/amnmkkr/wavesurfer

## Knobs

- SRC page: Sample (SMPL), Pitch (PTCH), Length (LEN: right forward, left backwards), Bank (BANK, 1..16), FX (FX:
  left delay synced to the tempo, right chorus), Filter (FILT: DJ filter), Scale (SCAL), Root (ROOT)
- Page 2: Fine (FINE), Note Track (TRCK: 1 V/oct at the right), Vel>Sample (VSMP), Vel>Level (VLEV), First Slot (FRST:
  the pool row of bank 1), Bank Size (SIZE, 1..16), Tune (TUNE, +-24 semitones), Start (STRT: 128 steps over the
  sample; lock it per step to chop a vocal)

Bank b, sample n plays pool row FRST + (b - 1) x SIZE + (n - 1). Keep PTCH centred and transpose with TUNE: a note jump
of 6 semitones or more turns Wave Bard's quantizer on. Trigs closer than 20 ms are ignored, and a trig is ignored while
a sample plays backwards (Wave Bard's design).

## Credits and how it runs

Wave Bard (Vaclav Mach, Marek Mach) and the Kastle 2 DSP library: Copyright (c) 2023-2025 Bastl Instruments, MIT, from
https://github.com/bastl-instruments/kastle2, unchanged (Bastl's sample bank is not included). They run at the
Kastle's 44 kHz in its 48-sample blocks, then 12/11 up to 48 kHz; the Kastle's hardware layer is replaced by small
headers, and its sample file is a virtual one whose samples are pool rows. The Sidecar keeps one pool sample ready per
voice: WAVESURFER asks only for the one it plays next, and a trig waits up to 13 ms for it. Each voice uses about 140 KB
of arena. The port: Copyright 2026 amnmkkr, MIT. Not made or endorsed by Bastl Instruments.

## Build

Source and `build.sh` at https://github.com/amnmkkr/wavesurfer. This package was built with aarch64-linux-gnu-gcc
13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1); `bash build.sh` with that compiler makes the same file.

This is a community package listed in the registry; the trust notes in CONTRIBUTING.md apply: a machine is native code
with no sandbox.
