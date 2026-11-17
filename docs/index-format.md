# index.json format

`tools/build_index.py` writes `index.json` from the manifests under `machines/`. It is the data source of the static
listing page in `site/` and the intended source of a future in-app catalog. Consumers must check `schema` and ignore
keys they do not know.

```json
{
  "schema": 1,
  "entries": [ { "...": "one per package file" } ],
  "latest": { "<id>": { "<board>": "<version>" } }
}
```

## `schema`

Integer, currently `1`. It changes only when an existing key changes meaning or is removed. Adding keys does not
change it.

## `entries`

One object per package file (one board of one version of one machine), sorted by `id`, then `version` (numerically),
then `board`. Published versions stay in the index; nothing is ever removed.

| key | type | meaning |
|---|---|---|
| `id` | string | The machine's id, as in the package header. Reserved by its first author (`registry/ids.json`). |
| `kind` | string | `machine` or `effect` (checked against the package: an API 3 `rmp3_plugin` of kind effect). |
| `version` | string | `a.b.c`, each part 0..255. |
| `compatible_from` | string | `a.b.c`: the oldest version whose saved projects this one still plays. |
| `name` | string | Display name (1 to 10 characters; the package carries the same text). |
| `short` | string | Short display name (1 to 4 characters; the package carries the same text). |
| `author` | string | The author's handle. |
| `licence` | string | SPDX identifier or expression of the machine. |
| `board` | string | `pi4`, `pi5` or `teensy`. |
| `api` | integer | The plugin API the package was built for (checked against the package header). |
| `source` | string, optional | `https://` URL of the source code. |
| `sha256` | string | Lowercase hex SHA-256 of the `.rmp` file. |
| `description` | string | What the machine does. |
| `demo` | string, optional | `https://` URL of demo audio. |
| `file` | string | Path of the `.rmp` file, relative to the repository (and site) root. |
| `size` | integer | Size of the `.rmp` file in bytes. |
| `readme` | string | Path of the version's `README.md`, relative to the root. |

Paths are relative so the index works under any base URL (GitHub Pages project sites included). A downloader must
verify `sha256` after fetching.

## `latest`

Maps each `id` to an object mapping each `board` that has a package to the highest `version` for that board.
A machine whose newest version has only a Pi build still lists an older Teensy version here.

## Stability

Keys are sorted and the file has no timestamp, so building twice from the same tree gives identical bytes.
