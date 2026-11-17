"""Build tiny, structurally valid .rmp packages for the tests (no toolchain, nothing is ever executed)."""
import struct
import zlib

MAGIC = {"teensy": 0x31504D52, "pi": 0x41504D52}


def version(s):
    a, b, c = (int(x) for x in s.split("."))
    return a << 16 | b << 8 | c


def make_rmp(pid="test.sine", ver="1.0.0", compat=None, target="pi", api=2, fmt=3, licence="MIT", name="Sine",
             short="SINE", image_size=4096, bss=256, relocs=(), data_start=None, mutate=None, kind="machine",
             insns=None, nknobs=0, entry_api=None, v3=True):
    """A package whose image is zeros; the entry table is at offset 0. `mutate(dict)` edits the header fields."""
    table = 128 if target == "pi" else 72
    image = bytearray(image_size)
    struct.pack_into("<I", image, 4, api if entry_api is None else entry_api)   # entry table: api at +4
    flags = 0
    if target == "pi" and api >= 3 and v3 or (target == "pi" and kind == "effect"):
        # reserved[4] of the entry table points at an rmp3_plugin (magic "RMP3", size 136, minor, kind)
        struct.pack_into("<Q", image, 64 + 8 * 4, 256)
        struct.pack_into("<IIII", image, 256, 0x33504D52, 136, 0, 2 if kind == "effect" else 1)
        flags = 0x1000 | (0x2000 if kind == "effect" else 0)
    for off, v in (insns or {}).items():
        struct.pack_into("<I", image, off, v)
    image = bytes(image)
    rel = b"".join(struct.pack("<II", off | typ << 28, 0) for off, typ in relocs)
    manifest = struct.pack("<10s4s48sBB", name.encode(), short.encode(), licence.encode(), 0, nknobs) + b"\0" * 20
    if fmt < 3:
        manifest = manifest[:64]
    body = image + rel + manifest
    body += b"\0" * (-len(body) % 4)
    if data_start is None:
        data_start = 4096 if target == "pi" else 0
    h = dict(magic=MAGIC[target], format=fmt, api=api, id=pid.encode(), version=version(ver),
             compatible_from=version(compat or ver), image_size=len(image), bss_size=bss, entry_offset=0,
             reloc_count=len(relocs), manifest_size=len(manifest), flags=flags, crc=zlib.crc32(body) & 0xFFFFFFFF,
             reserved=struct.pack("<I", data_start) + b"\0" * 16)
    assert table <= image_size
    if mutate:
        mutate(h)
    head = struct.pack("<IHH32sIIIIIIIII20s", h["magic"], h["format"], h["api"], h["id"], h["version"],
                       h["compatible_from"], h["image_size"], h["bss_size"], h["entry_offset"], h["reloc_count"],
                       h["manifest_size"], h["flags"], h["crc"], h["reserved"])
    return head + body
