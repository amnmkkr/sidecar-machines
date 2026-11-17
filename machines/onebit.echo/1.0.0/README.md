# 1BIT ECHO 1.0.0

A lo-fi 1-bit delay as a send effect (Plugin API 3), modelled on the PT2399 echo chip as boutique dub delays use it.
The memory is a real 44,032-bit shift register written by a 1-bit adaptive delta modulator, and the delay time is set
only by the clock. Short times are clean; past about 350 ms the clock drops below the chip's rating and the repeats
get gritty, and at 2.4 s they are thoroughly lo-fi. Changing the time bends the pitch of the repeats, so p-locking TIME
gives dub pitch dives. Soft LED-style clips sit inside the loop, so high feedback saturates into self-oscillation
instead of blowing up. The return is silent when the memory is: no constant hiss on the send.

- Id: `onebit.echo`, kind: effect (a send effect on the Rytm's UFX slots)
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 3
- Licence: MIT
- Author: amnmkkr

Mono in (the sum of the sends), wet out on both sides. The track send level works as drive and punch-in.

## Knobs

| Rytm knob | Short | What it does |
|---|---|---|
| P2 | TIME | `FREE n` 30 ms .. 2.4 s, then `1/16` `1/8T` `1/8` `1/4T` `1/8D` `1/4` `1/4D` `1/2` at the Rytm's tempo |
| P3 | FDBK | repeats; self-oscillates from about 98 |
| P4 | TONE | centred: left raises a low cut in the loop, right lowers a high cut |
| P5 | MOD | centred: left is smooth clock drift (wow and flutter), right is a starved clock that jitters, browns out and stalls |

Defaults: TIME FREE 40 (about 485 ms), FDBK 76, TONE 64, MOD 64.

## Cost

State 5,660 B (the whole memory; no arena), image 8 KB, no allocation and no host calls in render. CPU depends on the
time, because a short time is a fast clock: about 5.6 x `fx.bbd` at 30 ms, 1.6 x at the default and less than BBD at
long times, measured on the same host. Declared `cpu_permille` 110 for the worst case.

## Testing

Checked on a desktop build: 840 renders over all four knobs on drums and full-scale noise stay finite and bounded,
with no denormals or DC, and live knob sweeps are clean. Measured echo times match the settings within 0.2 ms, and a
synced 1/4 at 120 BPM measures 500.2 ms. Built with `aarch64-linux-gnu-gcc` and packed by the Sidecar repository's
`tools/rmp_pack.py`.

## Credits and licence

Written from scratch for the Sidecar; no code taken from elsewhere. MIT, Copyright 2026 amnmkkr. PT2399 is a Princeton
Technology part; this is an independent model, not affiliated with or endorsed by Princeton Technology or any pedal
maker.

The registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
