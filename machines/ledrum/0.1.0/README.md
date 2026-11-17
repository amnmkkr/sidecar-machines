# LEDrum 0.1.0

A drum voice for kicks, toms, snares, hats and zaps: an oscillator with FM or additive mixing, a pitch envelope, a
multimode filter, an amp envelope with adjustable curve, transient samples and distortion. LEDrum is a modified port of
the drum voice in the open-source Erica Synths LXR-02 firmware.

- Id: `ledrum`, kind: machine
- Board: Pi 5 (tested on a Pi 5 with the Touch Display 2)
- Plugin API: 3 (dual package, API 2 and API 3)
- Licence: GPL-3.0-only
- Source: https://github.com/amnmkkr/ledrum

## Knobs

Pitch follows the trig note: a plain trig (note 60) plays at the TUNE pitch, other notes transpose it.

Page 1:

- Coarse Tune (TUNE): base pitch in semitones
- Fine Tune (FINE): plus or minus one semitone
- Waveform (WAVE): Sine, Tri, Saw, Rect, Noise, PWM
- Mod Tune (MOD): pitch of the sine modulator
- FM Amount (FM): FM depth, or the modulator level in Add mode
- Osc Mix (MIX): FM or Add
- Filter Freq (FREQ): cutoff, 30 Hz to about 19 kHz
- Filter Reso (RESO): resonance

Page 2 (LEDRUM MORE):

- Filter Type (FTYP): Off, LP, HP, BP, UBP, Notch
- Amp Attack (ATK): 0 is instant, up to about 300 ms
- Amp Decay (DEC): 8 ms to 5 s
- Amp Slope (SLP): curve of the decay
- Pitch Decay (PDEC): 3 ms to 1.5 s
- Pitch Amt (PAMT): pitch envelope depth, up to 72 semitones
- Transient (TRAN): Off, Offset (a short pitch snap) or one of the 12 LXR transient samples
- Distortion (DIST): waveshaper drive

## Credits and licence

LEDrum is a modified version of the drum voice in the open-source Erica Synths LXR-02 firmware (Copyright (C)
2012-2026 Erica Synths, GPL-3.0-only with the terms in its NOTICE.md). It uses the LXR wavetables and transient samples
unchanged. Changes from the original: rewritten for float processing at 48 kHz, new amp and pitch envelopes, a new
state-variable filter and a new knob mapping. The Sidecar port is by amnmkkr, GPL-3.0-only.

LEDrum is not affiliated with, endorsed by or approved by Erica Synths. "Erica Synths", "LXR" and "LXR-02" are used
only to credit where the code comes from.

## Build

The full source, build script and licence texts are at https://github.com/amnmkkr/ledrum. It builds with
`aarch64-linux-gnu-gcc` and the Sidecar SDK's packer (`tools/rmp_pack.py` from sidecar-firmware); see that README.

This is a community package listed in the registry; the trust notes in CONTRIBUTING.md apply: a machine is native code
with no sandbox.
