# FXWIZARD 1.0.0

Bastl Instruments' Kastle 2 FX Wizard (MIT) as a send effect for the Pi: mono in, stereo out, on a send FX slot
(UFX1..UFX4). Nine effects: delay, flanger, freezer, panner, crusher, slicer, pitcher, replayer and shifter.

- Id: `fxwizard`, kind: effect
- Board: Pi 5 (tested on a Pi 5 with the Touch Display 2)
- Plugin API: 3
- Licence: MIT
- Source: https://github.com/amnmkkr/fxwizard

## Knobs

- Mode (MODE): DELAY, FLANGER, FREEZER, PANNER, CRUSHER, SLICER, PITCHER, REPLAY, SHIFTER
- Time (TIME), Feedback (FDBK), Amount (AMT): FX Wizard's own, with its own curves per mode

The Kastle's Stereo and Filter knobs and its CV attenuverters stay at FX Wizard's start values (mono, filter open, no
CV). FX Wizard keeps some dry signal at lower Amount; on a send that adds to the track's own.

## The Rytm's clock

The Kastle's clock pulses on every quarter note of the Rytm's tempo (following its song position while it plays). The
Kastle's trigger input fires every bar: the freezer and replayer grab a new loop, the delay syncs to the bar, the
envelopes fire and the LFOs restart.

## Credits and how it runs

FX Wizard (Marek Mach, Vaclav Mach) and the Kastle 2 DSP library: Copyright (c) 2023-2025 Bastl Instruments, MIT,
from https://github.com/bastl-instruments/kastle2, unchanged. They run at the Kastle's 44 kHz in its 48-sample blocks,
with 48 <-> 44 kHz converters around them (flat within 0.03 dB to 19 kHz, 3.1 ms, declared as latency); the Kastle's
hardware layer is replaced by small headers. The port: Copyright 2026 amnmkkr, MIT. Not made or endorsed by Bastl
Instruments.

## Build

Source and `build.sh` at https://github.com/amnmkkr/fxwizard. This package was built with aarch64-linux-gnu-gcc
13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1); `bash build.sh` with that compiler makes the same file.

This is a community package listed in the registry; the trust notes in CONTRIBUTING.md apply: an effect is native code
with no sandbox.
