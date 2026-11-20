# Contributing a machine

This registry lists community-made machines (`.rmp` packages) for Sidecar. **They are community work, not tested or
endorsed by Sidecar.** Read the trust rules before you install anything.

## Trust rules

- A machine is **native code** that runs inside the Sidecar engine. There is no sandbox. A bad or buggy machine can
  crash the engine, stop audio or do anything the engine can do.
- On the Pi the engine does not yet guard a machine's setup calls (init, voice init, parameters, note on and off):
  a fault there stops the engine and reboots the board. Only the audio render call is guarded.
- Prefer machines with source. Read it, or build it yourself, and compare the SHA-256 in the manifest with your build
  or with the downloaded file.
- Only install from this registry or from someone you know. **Never install a `.rmp` sent to you in a direct
  message.**
- The checker here is a format check (header, sizes, CRC, relocation table, manifest table, API 3 consistency: the
  rules the Pi's loader and the packer apply). It does not tell you what the code does.
- Files must be regular files (no symbolic links) of at most 2 MB each (preview audio has its own limits, see
  [Previews](#previews)).

## How to submit

1. Fork the repository.
2. **Reserve your id** by adding `"your.id": "yourhandle"` to `registry/ids.json`. The id is the one in your
   package header: printable ASCII, 1 to 31 characters, no space, `/` or `\`, no leading `.`, no `..`. The value is
   **your GitHub login**. The first author to merge an id owns it; only that GitHub account can add to it: the checks
   compare the owner of the id with the author of the pull request, so nobody can submit under an id reserved by
   someone else. You can only reserve ids for your own account. Ids that differ only in case count as the same id.
   A namespace reservation `"prefix.*"` holds every id that starts with `prefix.` for its owner (the Sidecar project
   holds the ids of its built-in machine families this way: `sc.*`, `fx.*`, `rytm.*`, `befaco.*` and others). An id
   may not contain `*` itself.
   Existing reservations cannot be changed.
3. Add `machines/<id>/<version>/` containing:
   - `<id>-<version>-<board>.rmp`, with `<board>` one of `pi4`, `pi5`, `teensy`.
   - `manifest.json`, see below.
   - `README.md`: what it does, the knobs, credits, build instructions if you have source.
   - optional `preview/`: 1 to 8 `.mp3` files, see [Previews](#previews).
   A second board of the same version goes in the same directory as `manifest.<board>.json` plus its own `.rmp`.
   Adding a board to an already published version is allowed, and only by the owner of the id; the files already
   there may not change.
4. Run the checker and fix what it says:
   ```
   python3 tools/check.py machines/<id>/<version>
   ```
5. Open a pull request. The checks run automatically, with the checker of the base branch (a pull request cannot
   change the code that judges it). `tools/`, `tests/`, `site/`, `registry/` and `.github/` need the owner's review.

### manifest.json

```json
{
  "id": "your.machine",
  "kind": "machine",
  "version": "1.0.0",
  "compatible_from": "1.0.0",
  "name": "My Machine",
  "short": "MYMC",
  "author": "yourgithublogin",
  "licence": "MIT",
  "board": "pi5",
  "api": 2,
  "source": "https://github.com/yourhandle/your-machine",
  "sha256": "<sha256 of the .rmp file>",
  "description": "One or two sentences.",
  "demo": "https://example.org/demo.mp3"
}
```

`kind` is `machine` or `effect` and must match the package (an effect is an API 3 package). `name` is 1 to 10 and
`short` 1 to 4 printable ASCII characters and must equal the text inside the package. `author` must be the GitHub login
the id is reserved to. `source` and `demo` are optional. `source` is strongly preferred. `author` is a handle; no real name is needed and
please do not use an e-mail address. `id`, `kind`, `version`, `compatible_from`, `api`, `name` and `short` must match what is
inside the `.rmp` (the checker compares them); every SPDX identifier in `licence` must appear in the package's own
licence field (free text of up to 48 characters). `board` `pi4` and `pi5` take an RMPA (AArch64) package, `teensy` an
RMP1 package. Get the hash with `shasum -a 256 file.rmp`.

## Previews

A machine or effect can show short audio previews on the catalog page. Add a folder `preview/` inside the version
directory, next to the manifest:

```
machines/<id>/<version>/preview/
    01 Init patch.mp3
    02 Wide and slow.mp3
```

- 1 to 8 files, **`.mp3` only** (MPEG audio layer III; no other file types, no sub-folders, no links). The checker
  walks the whole file: an optional ID3v2 tag (at most 64 KB), then valid MP3 frames one after the other up to the
  end of the file, optionally followed by a 128-byte ID3v1 tag. A renamed `.wav`, a text file or anything with extra
  bytes added fails.
- At most **2 MB per file** and **10 MB per version** in total. A short loop or a few bars at 96 to 128 kbit/s fits
  easily. Previews are downloaded only when someone presses play.
- The file name without `.mp3` is the name shown in the player. Allowed: letters, digits, space and `_ - . ( ) + #`;
  1 to 40 characters; it starts with a letter or digit, does not end in a space or dot, has no double spaces and no
  `..`; names that differ only in case count as the same; Windows device names (`CON`, `PRN`, `AUX`, `NUL`,
  `COM1` to `COM9`, `LPT1` to `LPT9`, also in front of a dot) are refused. No hidden files, no non-ASCII characters.
- The player lists the files **sorted by file name** (plain character order), so use a numeric prefix like `01 `, `02 `
  to choose the order. The prefix is part of the displayed name.
- Record only audio you may share: previews are published under the same licence terms as the rest of your submission,
  and must not contain third-party material you have no right to.
- A preview folder can be added to an already published version by the id's owner (new files only, like a second
  board); existing files cannot change. The existing `demo` URL in the manifest keeps working next to previews.

## Versions

- Versions are `a.b.c`, each part 0 to 255, and each new version must be higher than every published one of that id.
- Published files are never edited or deleted. To fix something, publish a new version.
- `compatible_from` is the oldest version whose saved projects the new one still plays. Say so in the README when it
  moves up.

## Licence

Every machine carries its own licence in its manifest, as an SPDX identifier (`MIT`, `GPL-3.0-only`,
`LicenseRef-...` with the text in your README). By submitting you confirm you may distribute the package under it
and that its source, if given, matches the package. The repository tooling (`tools/`, `site/`) is MIT, see `LICENSE`.

## Removal

If a machine is harmful, infringes a licence, or its author asks, maintainers may remove it. The version stays
reserved.
