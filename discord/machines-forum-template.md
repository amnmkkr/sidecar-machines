# Machines forum: post template and rules

For a forum channel where people share machines (`.rmp` packages). The registry is the place a machine lives; the
forum is where it is discussed.

## Post template

Title: `<Machine name> <version> (<boards>)`

```
**What it is:** one or two sentences, what it sounds like or does.
**Boards:** Pi 4 / Pi 5 / Teensy
**Licence:** SPDX id (for example MIT)
**Source:** link to the source code (or "no source")
**Registry entry:** link to machines/<id>/<version>/ in the registry
**Sound demo:** link or attached clip
**Knobs / how to use it:** short list
**Known issues:**
```

## Posting rules

1. **Link to the registry entry, do not upload the `.rmp` to Discord.** A file in a chat has no checksum, no
   licence and no history. If it is not in the registry yet, open the pull request first.
2. Say which board and which Sidecar version you tested on. Say if you did not test it.
3. Prefer machines with source. Say so in the post if the source is available.
4. **Never send a `.rmp` in a direct message, and never install one you were sent.** Machines are native code with no
   sandbox.
5. A machine is community work, not tested by Sidecar. Nobody here can promise it is safe.
6. Report a broken machine in its post, with the version, the board and what happened. Do not post reproduction
   files from other people's machines without their consent.
7. New version: reply in the same post with the new registry link and what changed.
8. Be kind to first-time authors. Point to `CONTRIBUTING.md` instead of closing posts.
