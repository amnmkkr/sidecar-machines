# TAPEDELAY2 1.0.0

Airwindows' TapeDelay2 (Chris Johnson, MIT) as a send effect for the Pi: mono in, stereo wet out, on a send FX slot
(UFX1..UFX4). A tape loop whose speed sets the delay time, so a TIME change bends the pitch of the repeats, with a
resonant band-pass in the feedback loop and tape flutter.

- Id: `tapedelay2`, kind: effect
- Board: Pi 5 (tested on a Pi 5 with the Touch Display 2)
- Plugin API: 3
- Licence: MIT
- Source: https://github.com/amnmkkr/tapedelay2

## Knobs

- Time (TIME): 0..63 free, TapeDelay2's Time, about 70 ms .. 1.84 s; 64..127 synced to the Rytm's tempo: 1/16, 1/8T,
  1/8, 1/4T, 1/8D, 1/4, 1/4D, 1/2
- Regen (REGN): the feedback
- Freq (FREQ): the band-pass in the loop and on the output; its resonance follows it, 75 % at the dark end to 45 % at
  the bright end. A change glides over about 30 ms
- Flutter (FLUT): the tape wobble; the two sides wobble half a cycle apart

## Credits and changes

TapeDelay2: Copyright (c) 2016 airwindows (Chris Johnson), MIT, from https://github.com/airwindows/airwindows. Its
signal path runs unchanged at 48 kHz; with the resonance at 0 and the soft clip off, the port matches Airwindows'
own code to 126..141 dB (the tape as 32-bit floats). Changed for a send slot's four knobs: Reso follows Freq, Dry/Wet
is wet only, TIME can sync, FREQ glides, the output is x3.79 into a soft clip above 0.8. The port: Copyright 2026
amnmkkr, MIT. Not made or endorsed by Airwindows.

## Build

Source and `build.sh` at https://github.com/amnmkkr/tapedelay2. This package was built with aarch64-linux-gnu-gcc
13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1); `bash build.sh` with that compiler makes the same file.

This is a community package listed in the registry; the trust notes in CONTRIBUTING.md apply: an effect is native code
with no sandbox.
