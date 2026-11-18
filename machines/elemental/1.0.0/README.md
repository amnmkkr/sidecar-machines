# ELEMENTAL 1.0.0

A modal synthesis voice: the DSP of Elements, Emilie Gillet's modal synthesizer for Mutable Instruments, run unchanged
at its own 32 kHz and resampled to the Sidecar's 48 kHz. Struck, bowed and blown resonators, a string and sympathetic
strings, its reverb and the hidden "ominous" voice.

- Id: `elemental`, kind: machine
- Board: Pi 5 (tested on a Pi 5 with the Touch Display 2)
- Plugin API: 3 only (the voice lives in the arena, about 175 KB per voice), stereo
- Licence: MIT
- Source: https://github.com/amnmkkr/elemental

## Playing it

A trig is Elements' gate: its start strikes, and the bow and blow exciters play while the trig is held, so the trig
length shapes bowed and blown notes. The trig's note is the pitch; velocity is Elements' STRENGTH (accent).

## Knobs

Page 1:

- Geometry (GEOM), Brightness (BRIT), Damping (DAMP), Position (POS): the resonator
- Space (SPCE): stereo spread, then reverb
- Strike (STRK), Bow (BOW), Blow (BLOW): the three exciters' levels

Page 2 (ELMT MORE):

- Contour (CONT): the exciter envelope's shape
- Mallet (MALT): the mallet samples, then the particles
- Strike Tmbr (STKT), Flow (FLOW), Blow Timbre (BLWT), Bow Timbre (BOWT)
- Tune (TUNE): plus or minus 24 semitones
- Type (TYPE): MODAL, STRING, STRINGS (the resonator models), OMINOUS (the hidden voice)

The defaults are Elements' own startup patch: a struck modal voice. Elements' FM control is left out: the trig's note
sets the pitch.

## Credits and licence

The DSP is Elements by Emilie Gillet (Mutable Instruments), with stmlib, Copyright 2014 Emilie Gillet, MIT, used
unchanged from https://github.com/pichenettes/eurorack. The Sidecar glue and the 32 to 48 kHz resampler: Copyright 2026
amnmkkr, MIT. Not affiliated with or endorsed by Mutable Instruments or Emilie Gillet; the names appear only to credit
where the DSP comes from.

## Build

Source and `build.sh` at https://github.com/amnmkkr/elemental. This package was built with aarch64-linux-gnu-gcc 13.3.0
(Ubuntu 13.3.0-6ubuntu2~24.04.1); `bash build.sh` with that compiler makes the same file.

This is a community package listed in the registry; the trust notes in CONTRIBUTING.md apply: a machine is native code
with no sandbox.
