"""Static check of a Sidecar machine package (.rmp). Never executes or loads the plugin.

Applies the same rules as the Sidecar loader's header verification (rmp_verify_header and rmp_verify): header magic
RMP1 (Teensy, ARM) or RMPA (Pi, AArch64), format, plugin API, the id, the size arithmetic, the entry table inside the
image, the image limits, the CRC-32 of the body, and, as the packer and the loader do, the relocation table (apply_a64), the
manifest (rmp_manifest_read) and, for an RMPA API 3 package, the rmp3_plugin consistency (rmp_pack.py api3_flags).
"""
import re
import struct
import zlib

MAGIC_RMP1 = 0x31504D52   # "RMP1": ARM Thumb-2 image (Teensy)
MAGIC_RMPA = 0x41504D52   # "RMPA": AArch64 image (Pi)
HEADER_BYTES = 96
HEADER_FMT = "<IHH32sIIIIIIIII20s"
HEADER_KEYS = ["magic", "format", "api", "id", "version", "compatible_from", "image_size", "bss_size",
               "entry_offset", "reloc_count", "manifest_size", "flags", "crc32", "reserved"]
FORMAT_MIN, FORMAT_RMP1, FORMAT_RMPA = 1, 3, 5
API_MIN, API_RMP1, API_RMPA = 1, 2, 3
PLUGIN_BYTES = {"teensy": 72, "pi": 128}      # sizeof(rmp_plugin) per target
A64_ALIGN = 4096
MAX_IMAGE = 1 << 20
RELOC_TYPES = {"teensy": {0, 1, 2}, "pi": {3, 4}}
MANIFEST_HEAD_BYTES = {1: 64, 2: 64}           # formats 3..5: 84
MANIFEST_HEAD_BYTES_DEFAULT = 84
KNOB_BYTES = {1: 20, 2: 22}                    # formats 3..5: 26
KNOB_BYTES_DEFAULT = 26
MAX_KNOBS = 32
MAX_FILE = 2 << 20                             # no registry file may be larger (a package is at most about 1 MB)
MAX_RELOCS = 1 << 16
# plugin API 3 (sdk/rmp/rmp_api3.h): reserved[4] of the RMPA entry table points at an rmp3_plugin
RMP3_MAGIC, RMP3_BYTES, RMP3_KIND_MACHINE, RMP3_KIND_EFFECT = 0x33504D52, 136, 1, 2
RMP_HF_API3, RMP_HF_EFFECT = 0x1000, 0x2000
RMP_REL_ABS64, RMP_REL_ADRP = 3, 4


class RmpError(Exception):
    pass


def id_ok(s):
    """The id rule of the package header and of the installed file name."""
    if not isinstance(s, str) or not s or s[0] == "." or len(s) > 31 or ".." in s:
        return False
    return all(0x21 <= ord(c) <= 0x7E and c not in "/\\" for c in s)


def version_str(v):
    return "%d.%d.%d" % (v >> 16 & 255, v >> 8 & 255, v & 255)


def verify(data):
    """Return a dict describing the package, or raise RmpError with the first rule it breaks."""
    if len(data) > MAX_FILE:
        raise RmpError("file is larger than %d bytes" % MAX_FILE)
    if len(data) < HEADER_BYTES:
        raise RmpError("file is shorter than the 96-byte header")
    h = dict(zip(HEADER_KEYS, struct.unpack_from(HEADER_FMT, data, 0)))
    if h["magic"] == MAGIC_RMP1:
        target = "teensy"
    elif h["magic"] == MAGIC_RMPA:
        target = "pi"
    else:
        raise RmpError("bad magic (want RMP1 or RMPA)")
    table = PLUGIN_BYTES[target]
    if not FORMAT_MIN <= h["format"] <= (FORMAT_RMPA if target == "pi" else FORMAT_RMP1):
        raise RmpError("package format %d is not supported for %s" % (h["format"], target))
    if not API_MIN <= h["api"] <= (API_RMPA if target == "pi" else API_RMP1):
        raise RmpError("plugin api %d is not supported for %s" % (h["api"], target))
    raw_id = h["id"]
    if raw_id[0] == 0 or 0 not in raw_id:
        raise RmpError("empty id or id not NUL-terminated inside its 32 bytes")
    pid = raw_id.split(b"\0", 1)[0]
    try:
        pid = pid.decode("ascii")
    except UnicodeDecodeError:
        raise RmpError("id is not ASCII")
    if not id_ok(pid):
        raise RmpError("id %r breaks the id rules" % pid)
    need = HEADER_BYTES + h["image_size"] + 8 * h["reloc_count"] + h["manifest_size"]
    if need > len(data) or (need + 3) // 4 * 4 != len(data):
        raise RmpError("size mismatch: header says %d bytes of body, file has %d (no more, no less, padded to 4)"
                       % (need, len(data)))
    if h["image_size"] > MAX_IMAGE or h["bss_size"] > MAX_IMAGE:
        raise RmpError("image or bss over 1 MB")
    if h["image_size"] + h["bss_size"] > MAX_IMAGE:
        raise RmpError("image plus bss over 1 MB")
    if h["entry_offset"] & 3 or h["entry_offset"] + table > h["image_size"]:
        raise RmpError("entry table (%d bytes at %d) is not inside the %d-byte image"
                       % (table, h["entry_offset"], h["image_size"]))
    data_start = h["image_size"]
    if target == "pi":
        data_start = struct.unpack_from("<I", h["reserved"], 0)[0]
        if data_start == 0 or data_start & (A64_ALIGN - 1) or data_start > h["image_size"] \
                or h["entry_offset"] + table > data_start:
            raise RmpError("bad data_start %d (page aligned, inside the image, after the entry table)" % data_start)
    if h["reloc_count"] > MAX_RELOCS:
        raise RmpError("more than %d relocations" % MAX_RELOCS)
    if (zlib.crc32(data[HEADER_BYTES:]) & 0xFFFFFFFF) != h["crc32"]:
        raise RmpError("CRC-32 of the body does not match the header")
    # compatible_from may not be newer than version
    if h["compatible_from"] > h["version"]:
        raise RmpError("compatible_from is newer than version")
    rel0 = HEADER_BYTES + h["image_size"]
    for k in range(h["reloc_count"]):
        wt, _val = struct.unpack_from("<II", data, rel0 + 8 * k)
        off, typ = wt & 0x0FFFFFFF, wt >> 28
        if typ not in RELOC_TYPES[target]:
            raise RmpError("relocation %d has type %d, not valid for %s" % (k, typ, target))
        if off + 4 > h["image_size"]:
            raise RmpError("relocation %d at %#x is outside the image" % (k, off))
        if typ == RMP_REL_ABS64 and (off + 8 > h["image_size"] or off & 7 or off < data_start < off + 8):
            raise RmpError("relocation %d (ABS64) at %#x is outside the image, misaligned or straddles the "
                           "code/data boundary" % (k, off))
        if typ == RMP_REL_ADRP:
            # apply_a64: the instruction lies in the code part, 4-aligned, and must be an ADRP
            if off + 4 > data_start or off & 3:
                raise RmpError("relocation %d (ADRP_DATA) at %#x is not a 4-aligned word in the code part" % (k, off))
            insn = struct.unpack_from("<I", data, HEADER_BYTES + off)[0]
            if insn & 0x9F000000 != 0x90000000:
                raise RmpError("relocation %d (ADRP_DATA) at %#x is not an ADRP instruction" % (k, off))
    mpos = rel0 + 8 * h["reloc_count"]
    head = MANIFEST_HEAD_BYTES.get(h["format"], MANIFEST_HEAD_BYTES_DEFAULT)
    kb = KNOB_BYTES.get(h["format"], KNOB_BYTES_DEFAULT)
    if h["manifest_size"] < head:
        raise RmpError("embedded manifest (%d bytes) is shorter than its head (%d)" % (h["manifest_size"], head))
    nknobs = data[mpos + 63]
    if nknobs > MAX_KNOBS or head + nknobs * kb > h["manifest_size"]:
        raise RmpError("embedded manifest: %d knobs (at most %d) do not fit in its %d bytes"
                       % (nknobs, MAX_KNOBS, h["manifest_size"]))
    name, short, licence = struct.unpack_from("<10s4s48s", data, mpos)

    def text(b):
        s = b.split(b"\0", 1)[0]
        if any(not 0x20 <= c <= 0x7E for c in s):
            raise RmpError("embedded manifest text is not printable ASCII")
        return s.decode("ascii")

    image = data[HEADER_BYTES:HEADER_BYTES + h["image_size"]]
    entry = h["entry_offset"]
    if struct.unpack_from("<I", image, entry + 4)[0] != h["api"]:
        raise RmpError("the entry table's api (%d) differs from the header's (%d)"
                       % (struct.unpack_from("<I", image, entry + 4)[0], h["api"]))
    kind, want_flags = "machine", 0
    if target == "pi":
        kind, want_flags = _api3(image, entry, h["api"])
    if h["flags"] & (RMP_HF_API3 | RMP_HF_EFFECT) != want_flags:
        raise RmpError("header flags %#x disagree with the entry table (API 3 flags should be %#x)"
                       % (h["flags"], want_flags))

    return {"target": target, "kind": kind, "format": h["format"], "api": h["api"], "id": pid,
            "version": version_str(h["version"]), "compatible_from": version_str(h["compatible_from"]),
            "image_size": h["image_size"], "bss_size": h["bss_size"],
            "name": text(name), "short": text(short), "licence": text(licence)}


def _api3(image, entry, api):
    """(kind, header API 3 flags) of an RMPA image: the rules of rmp_pack.py api3_flags."""
    ptr = struct.unpack_from("<Q", image, entry + 64 + 8 * 4)[0]   # reserved[RMP_P_V3]
    if not ptr:
        if api >= 3:
            raise RmpError("an api 3 entry table without its rmp3_plugin in reserved[RMP_P_V3]")
        return "machine", 0
    if ptr % 8 or ptr + RMP3_BYTES > len(image):
        raise RmpError("reserved[RMP_P_V3] = %#x: not an rmp3_plugin inside the image" % ptr)
    magic, size, _minor, kind = struct.unpack_from("<IIII", image, ptr)
    if magic != RMP3_MAGIC or size < RMP3_BYTES:
        raise RmpError("the rmp3_plugin at %#x has a bad magic or size" % ptr)
    if kind not in (RMP3_KIND_MACHINE, RMP3_KIND_EFFECT):
        raise RmpError("the rmp3_plugin's kind %d is neither machine nor effect" % kind)
    if kind == RMP3_KIND_EFFECT and api < 3:
        raise RmpError("an effect must be API 3 (.api = 3)")
    if kind == RMP3_KIND_EFFECT:
        return "effect", RMP_HF_API3 | RMP_HF_EFFECT
    return "machine", RMP_HF_API3


VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)", re.ASCII)


def parse_version(s):
    """'a.b.c' to a tuple, each 0..255, or None."""
    m = VERSION_RE.fullmatch(s) if isinstance(s, str) else None
    if not m:
        return None
    t = tuple(int(x) for x in m.groups())
    return t if all(x <= 255 for x in t) else None
