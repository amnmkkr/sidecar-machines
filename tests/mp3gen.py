"""Tiny MPEG-1 layer III streams for the tests: valid frame headers over silent payloads (no encoder needed)."""
FRAME = 417   # 128 kbit/s, 44.1 kHz, no padding: 144 * 128000 // 44100


def make_mp3(frames=4, id3=0):
    """`frames` frames of 417 bytes; `id3` > 0 puts an ID3v2 tag with that many payload bytes in front."""
    out = b""
    if id3:
        out += b"ID3\x04\x00\x00" + bytes((id3 >> 21 & 127, id3 >> 14 & 127, id3 >> 7 & 127, id3 & 127)) + b"\0" * id3
    return out + (b"\xff\xfb\x90\x00" + b"\0" * (FRAME - 4)) * frames
