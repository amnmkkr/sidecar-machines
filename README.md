# sidecar-machines

A registry of community-made machines (`.rmp` packages) for Sidecar, with the tooling that keeps it consistent.
**Community machines are not tested or endorsed by Sidecar.** They are native code with no sandbox: read
[CONTRIBUTING.md](CONTRIBUTING.md) for the trust rules.

## Layout

```
machines/<id>/<version>/
    <id>-<a.b.c>-<board>.rmp      the package (board: pi4, pi5 or teensy)
    manifest.json                 id, version, compatible_from, name, short, author, licence, board, api,
                                  sha256, description, optional source and demo
    README.md
    preview/*.mp3                 optional audio previews, 1 to 8 files (CONTRIBUTING.md)
registry/ids.json                 id -> owner (GitHub login), plus "prefix.*" namespace reservations
tools/check.py                    validates a submission
tools/previews.py                 the rules for the preview/ folder (name and MP3 header checks)
tools/build_index.py              writes index.json (docs/index-format.md)
tools/rmpverify.py                static package check, same rules as the Sidecar loader's header verification
site/                             static listing page (plain HTML and JS), reads index.json
discord/machines-forum-template.md
```

## Tools

Python 3.9 or newer, no dependencies.

```
python3 tools/check.py machines/<id>/<version>   # a submission
python3 tools/check.py --all                     # the whole registry
python3 tools/build_index.py                     # writes index.json
python3 -m unittest discover -s tests
```

`check.py` never loads or executes a package. It checks the manifest schema, the id rules, the id reservation, that
the version is newer than every other one of that id, the SHA-256, and the `.rmp` itself: header magic (`RMP1` for
the Teensy, `RMPA` for the Pi), format, plugin API, board target, size arithmetic, the entry table inside the image,
image limits, the CRC-32, the relocation table and the embedded manifest head. It also compares id, version,
compatible_from, api and licence with the manifest. If the version has a `preview/` folder it checks that too: file count, names, sizes and the MP3 header of every
file (it never decodes audio). It is a format check, not a safety review.

With `--base <git ref>` it also refuses changes to published files and to existing id reservations.

## Try the site locally

```
mkdir _site && cp -r site/. _site/ && cp -r machines _site/machines
python3 tools/build_index.py -o _site/index.json
python3 -m http.server -d _site 8000
```

The workflow in `.github/workflows/check.yml` does the same and deploys to GitHub Pages from `main`.

## Repository setup (owner)

Branch protection on `main` must be on, with **Require review from Code Owners** (`.github/CODEOWNERS` puts the
owner on every path) and the `check` jobs as required status checks. Without it CODEOWNERS only suggests reviewers.

## Licence

The repository tooling (`tools/`, `site/`, `tests/`, `docs/`) is MIT, see [LICENSE](LICENSE). Each machine carries its
own licence in its manifest.
