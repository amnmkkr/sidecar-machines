#!/usr/bin/env python3
"""Build index.json from machines/ (format: docs/index-format.md). Reads only the manifests; run check.py first.

  build_index.py [-o index.json]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check  # noqa: E402
import rmpverify  # noqa: E402

SCHEMA = 1
KEYS = ("id", "kind", "version", "compatible_from", "name", "short", "author", "licence", "board", "api", "source", "sha256",
        "description", "demo")


def build():
    entries = []
    for vdir in check.all_version_dirs():
        rel = os.path.relpath(vdir, check.ROOT).replace(os.sep, "/")
        for mf in check.manifest_files(vdir):
            m = check.load_json(os.path.join(vdir, mf))
            e = {k: m[k] for k in KEYS if k in m}
            e["file"] = "%s/%s-%s-%s.rmp" % (rel, m["id"], m["version"], m["board"])
            e["size"] = len(check.read_file(os.path.join(check.ROOT, e["file"])))
            e["readme"] = rel + "/README.md"
            entries.append(e)
    entries.sort(key=lambda e: (e["id"], rmpverify.parse_version(e["version"]), e["board"]))
    latest = {}
    for e in entries:
        cur = latest.setdefault(e["id"], {}).get(e["board"])
        if cur is None or rmpverify.parse_version(e["version"]) > rmpverify.parse_version(cur):
            latest[e["id"]][e["board"]] = e["version"]
    return {"schema": SCHEMA, "entries": entries,
            "latest": {k: dict(sorted(v.items())) for k, v in sorted(latest.items())}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--output", default=os.path.join(check.ROOT, "index.json"))
    args = ap.parse_args(argv)
    idx = build()
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, sort_keys=True)
        f.write("\n")
    print("%s: %d entries, %d machines" % (os.path.basename(args.output), len(idx["entries"]), len(idx["latest"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
