"""Tiny MP3 streams for the tests: complete chains of valid layer III frame headers over silent payloads (no encoder
needed). Frame lengths come from the bit rate, sample rate and padding bit, so each stream is a full frame chain to the
last byte, as a real encoder writes it."""
FRAME = 417   # MPEG-1, 128 kbit/s, 44.1 kHz, no padding: 144 * 128000 // 44100

# version bits (3 = MPEG-1, 2 = MPEG-2, 0 = MPEG-2.5) -> (bit rate table by index 1..14, sample rates by index 0..2, factor)
_TABLES = {
    3: ((32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320), (44100, 48000, 32000), 144),
    2: ((8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160), (22050, 24000, 16000), 72),
    0: ((8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160), (11025, 12000, 8000), 72),
}


def frame(version=3, br=9, sr=0, pad=0):
    """One frame (header + silence) with the given version bits, bit rate index, sample rate index and padding bit."""
    _, rates, factor = _TABLES[version]
    kbps = _TABLES[version][0][br - 1]
    n = factor * kbps * 1000 // rates[sr] + pad
    head = 0xFFE00000 | version << 19 | 1 << 17 | 1 << 16 | br << 12 | sr << 10 | pad << 9
    return head.to_bytes(4, "big") + b"\0" * (n - 4)


def id3v2(payload=0, flags=0):
    """An ID3v2.4 tag header with a `payload` bytes body (plus a 10 byte footer when the footer flag is set)."""
    out = b"ID3\x04\x00" + bytes((flags,)) + bytes((payload >> 21 & 127, payload >> 14 & 127, payload >> 7 & 127,
                                                    payload & 127)) + b"\0" * payload
    return out + (b"3DI\x04\x00" + bytes((flags,)) + b"\0\0\0\0") * bool(flags & 0x10)


def make_mp3(frames=4, id3=0, version=3, vbr=False, id3v1=False, pad=False):
    """`frames` frames; `id3` > 0 puts an ID3v2 tag with that many payload bytes in front; `version` is the MPEG version
    bits (3, 2 or 0); `vbr` varies the bit rate from frame to frame; `pad` alternates the padding bit; `id3v1` appends a
    128 byte ID3v1 tag."""
    out = id3v2(id3) if id3 else b""
    if version == 3 and not vbr and not pad:
        body = frame() * frames          # the plain stream: 417 byte frames
    else:
        body = b"".join(frame(version, br=(5 + i % 6) if vbr else 9 if version == 3 else 8, pad=(i % 2) if pad else 0)
                        for i in range(frames))
    out += body
    if id3v1:
        out += b"TAG" + b"\0" * 125
    return out
