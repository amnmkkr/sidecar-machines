#!/usr/bin/env python3
"""Validate registry submissions. Never executes a plugin.

  check.py machines/<id>/<version> [...]   check these version directories (a submission: also demands the version
                                           is newer than every other version of that id)
  check.py --all                           check every version directory (the registry as a whole)
  check.py --base origin/main ...          also refuse changes to published files and to existing id reservations,
                                           comparing against that git ref
  check.py --changed BASE --actor LOGIN    a pull request: git itself lists what changed since BASE (no shell
                                           lists of paths), the changed version directories are checked, published
                                           files may not change, and every id touched must be owned by LOGIN (the
                                           pull request's author); a new id is reserved by LOGIN
  --root DIR                               the registry tree to check (default: the tree this script is in). The
                                           pull request job runs the base branch's script against the pull
                                           request's tree.

Exit status 0 when everything passes, 1 otherwise. Every problem is printed as "path: message".
"""
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import previews  # noqa: E402
import rmpverify  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARDS = ("pi4", "pi5", "teensy")
REQUIRED = ("id", "kind", "version", "compatible_from", "name", "short", "author", "licence", "board", "api", "sha256",
            "description")
OPTIONAL = ("source", "demo")   # source is strongly preferred
HANDLE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,38}", re.ASCII)
_LIC = r"(?:LicenseRef-[A-Za-z0-9.-]+|[A-Za-z0-9][A-Za-z0-9.+-]*)"
SPDX_RE = re.compile(_LIC + r"(?: (?:AND|OR|WITH) " + _LIC + r")*", re.ASCII)
SHA_RE = re.compile(r"[0-9a-f]{64}", re.ASCII)
# https only, an ASCII host (no userinfo, no unicode), an optional port, an ASCII printable path without spaces
URL_RE = re.compile(r"https://(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z][A-Za-z0-9-]{0,61}"
                    r"(?::[0-9]{1,5})?(?:/[\x21-\x7e]*)?", re.ASCII)
MANIFEST_NAME_RE = re.compile(r"manifest\.[a-z0-9]+\.json", re.ASCII)
KINDS = ("machine", "effect")
MAX_FILE = rmpverify.MAX_FILE
MAX_ENTRIES = 64
SKIP_NAMES = {"README.md"}


class FileError(Exception):
    pass


def read_file(path, cap=MAX_FILE):
    """The bytes of a regular file of at most `cap` bytes; symlinks and other file types are refused."""
    try:
        st = os.lstat(path)
    except OSError as e:
        raise FileError("cannot read: %s" % e.strerror)
    if not stat.S_ISREG(st.st_mode):
        raise FileError("not a regular file (symbolic links and special files are refused)")
    if st.st_size > cap:
        raise FileError("larger than %d bytes" % cap)
    try:
        with open(path, "rb") as f:
            data = f.read(cap + 1)
    except OSError as e:
        raise FileError("cannot read: %s" % e.strerror)
    if len(data) > cap:
        raise FileError("larger than %d bytes" % cap)
    return data


def _no_dups(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError("duplicate key %r" % k)
        d[k] = v
    return d


def _no_const(name):
    raise ValueError("%s is not allowed in JSON" % name)


def load_json(path):
    """Strict JSON from a regular file: UTF-8, no duplicate keys, no NaN/Infinity. Raises FileError or ValueError."""
    data = read_file(path)
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_no_dups, parse_constant=_no_const)
    except (UnicodeDecodeError, RecursionError) as e:
        raise ValueError("not valid JSON (%s)" % type(e).__name__)


def real_dir(path):
    try:
        return stat.S_ISDIR(os.lstat(path).st_mode)
    except OSError:
        return False


def manifest_files(vdir):
    return sorted(n for n in os.listdir(vdir) if n == "manifest.json" or MANIFEST_NAME_RE.fullmatch(n))


def check_manifest(m, errs):
    """Schema of a manifest.json. Appends messages to errs."""
    if not isinstance(m, dict):
        errs.append("manifest is not a JSON object")
        return
    for k in sorted(set(m) - set(REQUIRED) - set(OPTIONAL)):
        errs.append("unknown manifest key %r" % k)
    for k in REQUIRED:
        if k not in m:
            errs.append("manifest key %r is missing" % k)
    if isinstance(m.get("id"), str) and "*" in m["id"]:
        errs.append("id %r contains '*' (reserved for namespace reservations in registry/ids.json)" % m["id"])
    if "id" in m and not rmpverify.id_ok(m["id"]):
        errs.append("id %r breaks the id rules (printable ASCII, no space, / or \\, no leading '.', no '..', "
                    "1..31 characters)" % (m["id"],))
    for k in ("version", "compatible_from"):
        if k in m and rmpverify.parse_version(m[k]) is None:
            errs.append("%s %r is not a.b.c with each part 0..255" % (k, m[k]))
    v, c = rmpverify.parse_version(m.get("version")), rmpverify.parse_version(m.get("compatible_from"))
    if v and c and c > v:
        errs.append("compatible_from is newer than version")
    if "kind" in m and m["kind"] not in KINDS:
        errs.append("kind %r is not one of %s" % (m["kind"], "|".join(KINDS)))
    for k, lim in (("name", 10), ("short", 4)):
        if k in m and (not isinstance(m[k], str) or not m[k].strip() or len(m[k]) > lim
                       or any(not 0x20 <= ord(c) <= 0x7E for c in m[k])):
            errs.append("%s must be 1..%d printable ASCII characters (the package carries the same text)" % (k, lim))
    if "description" in m and (not isinstance(m["description"], str) or not m["description"].strip()
                               or len(m["description"]) > 1000):
        errs.append("description must be a non-empty string of at most 1000 characters")
    if "author" in m:
        a = m["author"]
        if not isinstance(a, str) or not HANDLE_RE.fullmatch(a) or "@" in a:
            errs.append("author %r is not a handle (2..39 characters: letters, digits, _ . -; no e-mail)" % (a,))
    if "licence" in m and (not isinstance(m["licence"], str) or not SPDX_RE.fullmatch(m["licence"])
                                    or len(m["licence"]) > 48):
        errs.append("licence %r is not an SPDX identifier or expression (at most 48 characters)" % (m["licence"],))
    if "board" in m and m["board"] not in BOARDS:
        errs.append("board %r is not one of %s" % (m["board"], "|".join(BOARDS)))
    if "api" in m and (isinstance(m["api"], bool) or not isinstance(m["api"], int) or m["api"] < 1):
        errs.append("api must be a positive integer")
    if "sha256" in m and (not isinstance(m["sha256"], str) or not SHA_RE.fullmatch(m["sha256"])):
        errs.append("sha256 must be 64 lowercase hex digits")
    for k in OPTIONAL:
        if k in m and (not isinstance(m[k], str) or not URL_RE.fullmatch(m[k]) or len(m[k]) > 300):
            errs.append("%s must be an https:// URL" % k)


def check_version_dir(vdir, ids, enforce_newer, actor=None):
    """Check machines/<id>/<version>. Returns a list of "path: message" strings."""
    vdir = os.path.normpath(vdir)
    rel = os.path.relpath(vdir, ROOT)
    errs = []
    parts = rel.split(os.sep)
    if len(parts) != 3 or parts[0] != "machines" or not real_dir(vdir) or not real_dir(os.path.dirname(vdir)):
        return ["%s: not a machines/<id>/<version> directory (symbolic links are refused)" % rel]
    dir_id, dir_ver = parts[1], parts[2]
    if not rmpverify.id_ok(dir_id):
        errs.append("%s: directory name %r is not a valid id" % (rel, dir_id))
    if rmpverify.parse_version(dir_ver) is None:
        errs.append("%s: directory name %r is not a.b.c" % (rel, dir_ver))
    names = set(os.listdir(vdir))
    if len(names) > MAX_ENTRIES:
        return errs + ["%s: more than %d entries" % (rel, MAX_ENTRIES)]
    if "README.md" not in names:
        errs.append("%s: README.md is missing" % rel)
    mfiles = manifest_files(vdir)
    if not mfiles:
        errs.append("%s: no manifest.json" % rel)
    expected = set(SKIP_NAMES) | set(mfiles)
    boards_seen = set()
    for mf in mfiles:
        mrel = os.path.join(rel, mf)
        try:
            merrs, rmp_name = check_manifest_file(vdir, mf, dir_id, dir_ver, boards_seen, ids, actor)
        except Exception as e:   # a hostile file must give a message, never a traceback
            merrs, rmp_name = ["cannot check this manifest (%s)" % type(e).__name__], None
        if rmp_name:
            expected.add(rmp_name)
        errs += ["%s: %s" % (mrel, e) for e in merrs]
    if previews.FOLDER in names:
        expected.add(previews.FOLDER)
        errs += check_previews(rel, os.path.join(vdir, previews.FOLDER))
    for extra in sorted(names - expected):
        errs.append("%s: unexpected file %r (a version directory holds README.md, the manifest(s) and the .rmp "
                    "named <id>-<version>-<board>.rmp, and optionally a preview/ folder)" % (rel, extra))
    for n in sorted(names & expected - {previews.FOLDER}):
        try:
            read_file(os.path.join(vdir, n))
        except FileError as e:
            errs.append("%s: %s: %s" % (rel, n, e))
    if enforce_newer and not errs:
        errs += newer_than_others(rel, dir_id, dir_ver)
    return errs


def check_previews(rel, pdir):
    """The optional preview/ folder of a version directory (rules: tools/previews.py)."""
    prel = "%s/%s" % (rel.replace(os.sep, "/"), previews.FOLDER)
    if not real_dir(pdir):
        return ["%s: must be a directory (symbolic links are refused)" % prel]
    return ["%s: %s" % (prel, e) for e in previews.check_folder(pdir, read_file, FileError)]


def check_manifest_file(vdir, mf, dir_id, dir_ver, boards_seen, ids, actor):
    """(errors, expected .rmp name) for one manifest file of a version directory."""
    merrs = []
    try:
        m = load_json(os.path.join(vdir, mf))
    except (FileError, ValueError) as e:
        return ["cannot read manifest: %s" % e], None
    check_manifest(m, merrs)
    if not isinstance(m, dict):
        return merrs, None
    if m.get("id") != dir_id:
        merrs.append("id %r does not match the directory %r" % (m.get("id"), dir_id))
    if m.get("version") != dir_ver:
        merrs.append("version %r does not match the directory %r" % (m.get("version"), dir_ver))
    board = m.get("board")
    if isinstance(board, str):
        if board in boards_seen:
            merrs.append("board %r is in two manifests of this version" % board)
        boards_seen.add(board)
        if mf != "manifest.json" and mf != "manifest.%s.json" % board:
            merrs.append("file name does not match its board %r" % (board,))
    if merrs:
        return merrs, None
    rmp_name = "%s-%s-%s.rmp" % (m["id"], m["version"], m["board"])
    merrs += check_ownership(m, ids, actor)
    if not merrs:
        merrs += check_package(os.path.join(vdir, rmp_name), m)
    return merrs, rmp_name


def _covering(ids, mid, skip=None):
    """[(prefix length, owner)] of the namespace keys ("x.*") that cover `mid` (an id, or the prefix "q" of "q.*").
    A namespace "x.*" covers "x" itself and every id starting with "x.", whatever the order of the file."""
    probe = mid.casefold() + "."
    return [(len(k) - 1, v) for k, v in ids.items()
            if k != skip and isinstance(k, str) and k.endswith(".*") and probe.startswith(k[:-1].casefold())]


def namespace_owner(ids, mid):
    """The owner of the longest namespace reservation that covers `mid`, or None."""
    hits = _covering(ids, mid)
    return max(hits, key=lambda h: h[0])[1] if hits else None


def check_ownership(m, ids, actor=None):
    """The id's owner (registry/ids.json, or the namespace it falls in) is the author, and, in a pull request, the
    pull request's author."""
    owner = ids.get(m["id"]) or namespace_owner(ids, m["id"])
    if owner is None:
        return ["id %r is not reserved: add it to registry/ids.json with your GitHub login as the owner" % m["id"]]
    if owner.lower() != m["author"].lower():
        return ["id %r is reserved by %r, not by %r" % (m["id"], owner, m["author"])]
    if actor is not None and owner.lower() != actor.lower():
        return ["id %r is reserved by %r; only that GitHub account may add to it (this pull request is by %r)"
                % (m["id"], owner, actor)]
    return []


def check_package(path, m):
    name = os.path.basename(path)
    try:
        data = read_file(path)
    except FileError as e:
        return ["package file %s: %s" % (name, e)]
    errs = []
    got = hashlib.sha256(data).hexdigest()
    if got != m["sha256"]:
        errs.append("sha256 of %s is %s, the manifest says %s" % (name, got, m["sha256"]))
    try:
        info = rmpverify.verify(data)
    except rmpverify.RmpError as e:
        return errs + ["%s: %s" % (name, e)]
    except Exception as e:
        return errs + ["%s: cannot be parsed (%s)" % (name, type(e).__name__)]
    want_target = "teensy" if m["board"] == "teensy" else "pi"
    if info["target"] != want_target:
        errs.append("board %s needs a %s package, the file is %s" %
                    (m["board"], "RMP1" if want_target == "teensy" else "RMPA",
                     "RMP1" if info["target"] == "teensy" else "RMPA"))
    for k in ("id", "kind", "version", "compatible_from", "api", "name", "short"):
        if info[k] != m[k]:
            errs.append("%s: the package says %r, the manifest says %r" % (k, info[k], m[k]))
    # the package's licence field is free text (48 characters); every SPDX identifier of the manifest must be in it
    have = set(re.findall(r"[A-Za-z0-9][A-Za-z0-9.+-]*", info["licence"], re.ASCII))
    want = [t for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9.+-]*", m["licence"], re.ASCII) if t not in ("AND", "OR", "WITH")]
    if not want or any(t not in have for t in want):
        errs.append("licence: the package says %r, the manifest says %r (each identifier of the manifest's licence "
                    "must appear in the package's)" % (info["licence"], m["licence"]))
    return errs


def newer_than_others(rel, mid, ver):
    base = os.path.join(ROOT, "machines", mid)
    mine = rmpverify.parse_version(ver)
    for other in sorted(os.listdir(base)):
        t = rmpverify.parse_version(other)
        if other != ver and t is not None and t >= mine:
            return ["%s: version %s is not newer than the published %s" % (rel, ver, other)]
    return []


def check_ids_file(ids):
    errs = []
    if not isinstance(ids, dict):
        return ["registry/ids.json: must be a JSON object mapping id to owner"]
    seen = {}
    for k, v in sorted(ids.items()):
        ns = isinstance(k, str) and k.endswith(".*")
        if not rmpverify.id_ok(k[:-2] + "." if ns else k) or (not ns and "*" in k) or (ns and "*" in k[:-1]):
            errs.append("registry/ids.json: %r is not a valid id (a namespace is written \"prefix.*\")" % k)
        elif k.casefold() in seen:
            errs.append("registry/ids.json: %r and %r differ only in case" % (seen[k.casefold()], k))
        seen[k.casefold()] = k
        if isinstance(k, str) and isinstance(v, str):
            for _n, o in _covering(ids, k[:-2] if ns else k, skip=k):
                if isinstance(o, str) and o.lower() != v.lower():
                    errs.append("registry/ids.json: %r (%s) lies inside a namespace reserved by %r" % (k, v, o))
                    break
        if not isinstance(v, str) or not HANDLE_RE.fullmatch(v) or "@" in v:
            errs.append("registry/ids.json: owner %r of %r is not a handle" % (v, k))
    return errs


def git(*args):
    return subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True)


def changed_paths(base):
    """[(status, path)] from git itself: NUL-separated, no renames. Raises RuntimeError."""
    r = git("diff", "-z", "--name-status", "--no-renames", base + "...HEAD", "--", "machines", "registry")
    if r.returncode != 0:
        raise RuntimeError("cannot compare with %s: %s" % (base, r.stderr.decode("utf-8", "replace").strip()))
    fields = r.stdout.decode("utf-8", "surrogateescape").split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    if len(fields) % 2:
        raise RuntimeError("unexpected git diff output")
    return list(zip(fields[0::2], fields[1::2]))


def check_base(base, paths, actor=None):
    """Published files are immutable and id reservations are permanent, compared with git ref `base`."""
    errs = []
    for status, path in paths:
        if path.startswith("machines/") and status != "A":
            errs.append("%s: a published file may not be changed or removed (publish a new version instead)" % path)
    r = git("show", "%s:registry/ids.json" % base)
    try:
        if r.returncode != 0:
            # a base without the file is only acceptable when the base has no commit with it at all
            if git("cat-file", "-e", base + "^{commit}").returncode != 0:
                raise ValueError("base ref %s does not exist" % base)
            if git("ls-tree", "-r", "--name-only", base, "--", "registry/ids.json").stdout.strip():
                raise ValueError("cannot read registry/ids.json at %s" % base)
        old = json.loads(r.stdout.decode("utf-8")) if r.returncode == 0 else {}
        new = load_json(os.path.join(ROOT, "registry", "ids.json"))
        for k, v in old.items():
            if new.get(k) != v:
                errs.append("registry/ids.json: the reservation of %r (%s) may not be changed or removed" % (k, v))
        if actor is not None:
            for k, v in new.items():
                if k not in old and isinstance(v, str) and v.lower() != actor.lower():
                    errs.append("registry/ids.json: %r is reserved for %r; you can only reserve ids for your own "
                                "GitHub account (%s)" % (k, v, actor))
    except (FileError, ValueError, AttributeError) as e:
        errs.append("registry/ids.json: %s" % e)
    return errs


def changed_version_dirs(paths):
    """(version directories, errors) for the changed paths."""
    dirs, errs = set(), []
    for status, path in paths:
        parts = path.split("/")
        if parts[0] != "machines":
            continue
        if path == "machines/.gitkeep":
            continue
        if len(parts) < 4:
            errs.append("%s: files belong in machines/<id>/<version>/" % path)
            continue
        dirs.add(os.path.join(ROOT, *parts[:3]))
    return sorted(dirs), errs


def all_version_dirs(errs=None):
    out = []
    mroot = os.path.join(ROOT, "machines")
    if not real_dir(mroot):
        return out
    for mid in sorted(os.listdir(mroot)):
        mdir = os.path.join(mroot, mid)
        if mid == ".gitkeep":
            continue
        if not real_dir(mdir):
            if errs is not None:
                errs.append("machines/%s: only <id> directories belong here" % mid)
            continue
        for v in sorted(os.listdir(mdir)):
            vd = os.path.join(mdir, v)
            if real_dir(vd):
                out.append(vd)
            elif errs is not None:
                errs.append("machines/%s/%s: only <version> directories belong here" % (mid, v))
    return out


def main(argv=None):
    global ROOT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="*", help="machines/<id>/<version> directories")
    ap.add_argument("--all", action="store_true", help="check every version directory")
    ap.add_argument("--base", help="git ref to compare against (published files, id reservations)")
    ap.add_argument("--changed", metavar="BASE", help="check what changed since this git ref (a pull request)")
    ap.add_argument("--actor", help="the pull request author's GitHub login (required with --changed)")
    ap.add_argument("--root", help="the registry tree to check")
    args = ap.parse_args(argv)
    if args.root:
        ROOT = os.path.abspath(args.root)
    if not args.dirs and not args.all and not args.changed:
        ap.error("give version directories, --all or --changed")
    if args.changed and not args.actor:
        ap.error("--changed needs --actor")
    if args.actor is not None and not HANDLE_RE.fullmatch(args.actor):
        ap.error("--actor is not a GitHub login")
    try:
        ids = load_json(os.path.join(ROOT, "registry", "ids.json"))
    except (FileError, ValueError) as e:
        print("registry/ids.json: %s" % e)
        return 1
    errs = check_ids_file(ids)
    if errs:
        for e in errs:
            print(e)
        return 1
    if args.changed:
        try:
            paths = changed_paths(args.changed)
        except RuntimeError as e:
            print(e)
            return 1
        errs += check_base(args.changed, paths, args.actor)
        dirs, derrs = changed_version_dirs(paths)
        errs += derrs
    else:
        if args.base:
            try:
                errs += check_base(args.base, changed_paths(args.base))
            except RuntimeError as e:
                errs.append(str(e))
        dirs = all_version_dirs(errs) if args.all else [os.path.abspath(d) for d in args.dirs]
    for d in dirs:
        errs += check_version_dir(d, ids, enforce_newer=not args.all, actor=args.actor)
    for e in errs:
        print(e)
    if errs:
        print("%d problem(s)" % len(errs))
        return 1
    print("ok: %d version director%s checked" % (len(dirs), "y" if len(dirs) == 1 else "ies"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
