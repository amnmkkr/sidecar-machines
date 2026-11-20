"""Rules for the optional machines/<id>/<version>/preview/ folder (docs/index-format.md, CONTRIBUTING.md).

Never decodes or plays audio: it reads file headers only.
"""
import os
import re

FOLDER = "preview"
MAX_FILES = 8
MAX_FILE_BYTES = 2 << 20      # 2 MiB per file
MAX_TOTAL_BYTES = 10 << 20    # 10 MiB per version
MIN_FILE_BYTES = 256
MAX_NAME = 40                 # display name, without ".mp3"
MAX_ID3 = 64 * 1024           # an ID3v2 tag in front of the audio (tags, no cover art worth the space)
EXT = ".mp3"
# letters, digits, space and _ - . ( ) + # ; starts with a letter or digit, no trailing space or dot, one space at a time
NAME_RE = re.compile(r"[A-Za-z0-9](?:(?:[A-Za-z0-9_.()+#-]| (?! ))*[A-Za-z0-9_()+#-])?", re.ASCII)

_BITRATES = {   # kbit/s by bitrate index 1..14: MPEG-1 layer III, MPEG-2 and 2.5 layer III
    1: (32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320),
    2: (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160),
}
_RATES = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}   # by version bits


def name_problem(fname):
    """Why a file name is not allowed in a preview folder, or None."""
    if not fname.endswith(EXT):
        return "must end in .mp3 (lower case); only .mp3 files are allowed"
    disp = fname[:-len(EXT)]
    if not disp:
        return "has no name in front of .mp3"
    if len(disp) > MAX_NAME:
        return "name is longer than %d characters (without .mp3)" % MAX_NAME
    if not NAME_RE.fullmatch(disp):
        return ("name may only use letters, digits, space and _ - . ( ) + #, must start with a letter or "
                "digit, may not end in a space or dot, with no double spaces")
    if ".." in disp:
        return "name may not contain '..'"
    return None


def _frame(data, pos):
    """(frame length) of the MPEG audio layer III frame header at `pos`, or None when it is not a valid one."""
    if pos + 4 > len(data):
        return None
    h = int.from_bytes(data[pos:pos + 4], "big")
    if h >> 21 != 0x7FF:
        return None
    ver, layer = (h >> 19) & 3, (h >> 17) & 3
    br, sr, pad = (h >> 12) & 15, (h >> 10) & 3, (h >> 9) & 1
    if ver == 1 or layer != 1 or br in (0, 15) or sr == 3:
        return None
    kbps = _BITRATES[1 if ver == 3 else 2][br - 1]
    rate = _RATES[ver][sr]
    return (144 if ver == 3 else 72) * kbps * 1000 // rate + pad


def mp3_problem(data):
    """Why `data` is not an MP3 (MPEG audio layer III) file, or None. The first frame, after an optional ID3v2 tag,
    must be valid and be followed by another valid frame header (or end the file)."""
    pos = 0
    if data[:3] == b"ID3":
        sz = data[6:10]
        if len(data) < 10 or any(b & 0x80 for b in sz):
            return "damaged ID3 tag"
        pos = 10 + (sz[0] << 21 | sz[1] << 14 | sz[2] << 7 | sz[3]) + (10 if data[5] & 0x10 else 0)
        if pos - 10 > MAX_ID3:
            return "ID3 tag is larger than %d bytes (strip embedded pictures)" % MAX_ID3
    n = _frame(data, pos)
    if n is None:
        return "no MP3 (MPEG audio layer III) frame header where the audio should start"
    nxt = pos + n
    if nxt < len(data) and _frame(data, nxt) is None and len(data) - nxt > 128:   # up to 128 bytes: an ID3v1 tag
        return "the first MP3 frame is not followed by another one: not a valid MP3 stream"
    return None


def check_folder(pdir, read_file, FileError):
    """Problems ("name: message") of a preview directory. `read_file` and `FileError` come from check.py."""
    errs = []
    try:
        names = sorted(os.listdir(pdir))
    except OSError as e:
        return ["cannot list the folder: %s" % e.strerror]
    if not names:
        return ["is empty (delete the folder or add 1 to %d .mp3 files)" % MAX_FILES]
    if len(names) > MAX_FILES:
        errs.append("has %d files, at most %d are allowed" % (len(names), MAX_FILES))
    seen, total = {}, 0
    for n in names[:64]:
        why = name_problem(n)
        if why:
            errs.append("%s: %s" % (n, why))
            continue
        if n.casefold() in seen:
            errs.append("%s: same name as %s apart from case" % (n, seen[n.casefold()]))
        seen[n.casefold()] = n
        try:
            data = read_file(os.path.join(pdir, n), MAX_FILE_BYTES)
        except FileError as e:
            errs.append("%s: %s" % (n, e))
            continue
        total += len(data)
        if len(data) < MIN_FILE_BYTES:
            errs.append("%s: smaller than %d bytes" % (n, MIN_FILE_BYTES))
            continue
        why = mp3_problem(data)
        if why:
            errs.append("%s: %s" % (n, why))
    if total > MAX_TOTAL_BYTES:
        errs.append("together the files are %d bytes, at most %d are allowed" % (total, MAX_TOTAL_BYTES))
    return errs


def listing(pdir):
    """[{"name","file","bytes"}] for the index, sorted by file name; [] when there is no folder. `file` is the bare
    file name (the caller prefixes the path). Run check.py first."""
    if not os.path.isdir(pdir):
        return []
    return [{"name": n[:-len(EXT)], "file": n, "bytes": os.path.getsize(os.path.join(pdir, n))}
            for n in sorted(os.listdir(pdir))]
