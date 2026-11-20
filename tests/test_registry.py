import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import build_index  # noqa: E402
import check  # noqa: E402
import mp3gen  # noqa: E402
import previews  # noqa: E402
import rmpgen  # noqa: E402
import rmpverify  # noqa: E402


class VerifyTest(unittest.TestCase):
    def bad(self, text, **kw):
        with self.assertRaises(rmpverify.RmpError) as cm:
            rmpverify.verify(rmpgen.make_rmp(**kw))
        self.assertIn(text, str(cm.exception))

    def test_good_pi_and_teensy(self):
        i = rmpverify.verify(rmpgen.make_rmp())
        self.assertEqual((i["target"], i["id"], i["version"], i["api"], i["licence"]), ("pi", "test.sine", "1.0.0", 2, "MIT"))
        i = rmpverify.verify(rmpgen.make_rmp(target="teensy", fmt=2, data_start=0))
        self.assertEqual(i["target"], "teensy")

    def test_api3_only_on_pi(self):
        rmpverify.verify(rmpgen.make_rmp(api=3))
        self.bad("api 3", api=3, target="teensy")

    def test_bad_magic_short_format(self):
        self.bad("magic", mutate=lambda h: h.update(magic=0x12345678))
        with self.assertRaises(rmpverify.RmpError):
            rmpverify.verify(b"RMPA" + b"\0" * 10)
        self.bad("format", fmt=6)
        self.bad("format", fmt=4, target="teensy")
        self.bad("api", api=0)

    def test_id_rules(self):
        for pid in ("has space", "a/b", ".hidden", "a..b", "x" * 32):
            with self.assertRaises(rmpverify.RmpError, msg=pid):
                rmpverify.verify(rmpgen.make_rmp(pid=pid))
        self.bad("empty id", pid="")

    def test_sizes_and_entry(self):
        data = rmpgen.make_rmp()
        with self.assertRaises(rmpverify.RmpError):
            rmpverify.verify(data + b"\0\0\0\0")
        with self.assertRaises(rmpverify.RmpError):
            rmpverify.verify(data[:-4])
        self.bad("entry table", mutate=lambda h: h.update(entry_offset=4096 - 64))
        self.bad("entry table", mutate=lambda h: h.update(entry_offset=2))
        self.bad("over 1 MB", mutate=lambda h: h.update(bss_size=(1 << 20) + 1))
        self.bad("plus bss", bss=1 << 20)

    def test_crc_and_data_start(self):
        self.bad("CRC", mutate=lambda h: h.update(crc=1))
        self.bad("data_start", data_start=100)
        self.bad("data_start", data_start=0)
        self.bad("data_start", data_start=8192)

    def test_relocations(self):
        rmpverify.verify(rmpgen.make_rmp(relocs=[(8, 3), (16, 4)], insns={16: 0x90000000}))
        self.bad("type", relocs=[(8, 0)])
        self.bad("outside", relocs=[(4094, 4)])
        self.bad("misaligned", relocs=[(12, 3)])
        self.bad("type", target="teensy", relocs=[(8, 3)], data_start=0)

    def test_version(self):
        self.bad("newer", ver="1.0.0", compat="1.1.0")


class RegistryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_root = check.ROOT
        check.ROOT = self.tmp
        os.makedirs(os.path.join(self.tmp, "registry"))
        self.ids = {"test.sine": "alice"}
        self.write_ids()

    def tearDown(self):
        check.ROOT = self.old_root
        shutil.rmtree(self.tmp)

    def write_ids(self):
        with open(os.path.join(self.tmp, "registry", "ids.json"), "w") as f:
            json.dump(self.ids, f)

    def add(self, ver="1.0.0", board="pi5", pid="test.sine", author="alice", rmp=None, extra=None, drop=()):
        d = os.path.join(self.tmp, "machines", pid, ver)
        os.makedirs(d, exist_ok=True)
        data = rmp if rmp is not None else rmpgen.make_rmp(pid=pid, ver=ver, target="teensy" if board == "teensy" else "pi")
        m = dict(id=pid, kind="machine", version=ver, compatible_from=ver, name="Sine", short="SINE", author=author,
                 licence="MIT", board=board, api=2, sha256=hashlib.sha256(data).hexdigest(),
                 description="A sine.", source="https://example.org/sine")
        m.update(extra or {})
        for k in drop:
            m.pop(k)
        name = "manifest.json" if not os.path.exists(os.path.join(d, "manifest.json")) else "manifest.%s.json" % board
        with open(os.path.join(d, name), "w") as f:
            json.dump(m, f)
        with open(os.path.join(d, "%s-%s-%s.rmp" % (pid, ver, board)), "wb") as f:
            f.write(data)
        with open(os.path.join(d, "README.md"), "w") as f:
            f.write("# test\n")
        return d

    def run_check(self, d, newer=True, actor=None):
        return check.check_version_dir(d, self.ids, newer, actor)

    def test_good(self):
        self.assertEqual(self.run_check(self.add()), [])

    def test_two_boards_one_version(self):
        d = self.add(board="pi5")
        self.add(board="teensy")
        self.assertEqual(self.run_check(d), [])

    def test_unknown_and_missing_key(self):
        self.assertTrue(any("unknown" in e for e in self.run_check(self.add(extra={"x": 1}))))
        self.assertTrue(any("'description' is missing" in e for e in self.run_check(self.add(drop=("description",)))))

    def test_bad_values(self):
        for extra, text in (({"board": "pi3"}, "board"), ({"licence": "not a licence!"}, "licence"),
                            ({"author": "me@example.org"}, "author"), ({"source": "http://x.org/a"}, "source"),
                            ({"sha256": "abc"}, "sha256"), ({"compatible_from": "2.0.0"}, "compatible_from")):
            self.setUp_clean()
            errs = self.run_check(self.add(extra=extra))
            self.assertTrue(any(text in e for e in errs), (extra, errs))

    def setUp_clean(self):
        shutil.rmtree(os.path.join(self.tmp, "machines"), ignore_errors=True)

    def test_id_reservation(self):
        self.assertTrue(any("reserved by" in e for e in self.run_check(self.add(author="mallory"))))
        self.setUp_clean()
        self.ids = {}
        self.assertTrue(any("not reserved" in e for e in self.run_check(self.add())))

    def test_author_case_insensitive(self):
        self.assertEqual(self.run_check(self.add(author="Alice")), [])

    def test_version_must_be_newer(self):
        self.add(ver="1.2.0")
        d = self.add(ver="1.1.0")
        self.assertTrue(any("not newer" in e for e in self.run_check(d)))
        self.assertEqual(self.run_check(self.add(ver="1.3.0")), [])
        self.assertEqual(self.run_check(d, newer=False), [])

    def test_sha_mismatch(self):
        d = self.add()
        with open(os.path.join(d, "test.sine-1.0.0-pi5.rmp"), "ab") as f:
            f.write(b"\0")
        self.assertTrue(any("sha256" in e for e in self.run_check(d)))

    def test_package_checks_reach_the_rmp(self):
        errs = self.run_check(self.add(rmp=rmpgen.make_rmp(mutate=lambda h: h.update(crc=1))))
        self.assertTrue(any("CRC" in e for e in errs))

    def test_board_target_and_manifest_agree(self):
        self.assertTrue(any("needs a" in e for e in self.run_check(self.add(board="teensy", rmp=rmpgen.make_rmp(target="pi")))))
        self.setUp_clean()
        errs = self.run_check(self.add(rmp=rmpgen.make_rmp(ver="1.0.1")))
        self.assertTrue(any("version" in e for e in errs))
        self.setUp_clean()
        errs = self.run_check(self.add(rmp=rmpgen.make_rmp(licence="GPL-3.0-only")))
        self.assertTrue(any("licence" in e for e in errs))

    def test_directory_must_match(self):
        d = self.add(ver="1.0.0")
        m = os.path.join(d, "manifest.json")
        with open(m) as f:
            data = json.load(f)
        data["version"] = "1.0.1"
        with open(m, "w") as f:
            json.dump(data, f)
        self.assertTrue(any("does not match the directory" in e for e in self.run_check(d)))

    def test_stray_file(self):
        d = self.add()
        with open(os.path.join(d, "evil.sh"), "w") as f:
            f.write("x")
        self.assertTrue(any("unexpected file" in e for e in self.run_check(d)))

    def test_index(self):
        self.add(ver="1.0.0")
        self.add(ver="1.1.0")
        self.add(ver="1.1.0", board="teensy")
        idx = build_index.build()
        self.assertEqual(idx["schema"], 1)
        self.assertEqual(len(idx["entries"]), 3)
        self.assertEqual(idx["latest"], {"test.sine": {"pi5": "1.1.0", "teensy": "1.1.0"}})
        e = idx["entries"][-1]
        self.assertEqual(e["file"], "machines/test.sine/1.1.0/test.sine-1.1.0-teensy.rmp")
        self.assertEqual(e["size"], os.path.getsize(os.path.join(self.tmp, e["file"])))

    def test_ids_file(self):
        self.assertEqual(check.check_ids_file({"a.b": "alice"}), [])
        self.assertTrue(check.check_ids_file({"a b": "alice"}))
        self.assertTrue(check.check_ids_file({"ab": "a@b.c"}))
        self.assertTrue(any("differ only in case" in e for e in check.check_ids_file({"Ab.c": "x1", "aB.c": "x2"})))


class HardeningTest(RegistryTest):
    def errs(self, d, **kw):
        return self.run_check(d, **kw)

    def has(self, d, text, **kw):
        errs = self.errs(d, **kw)
        self.assertTrue(any(text in e for e in errs), errs)

    # 3: ownership tied to the pull request author
    def test_actor_must_own_the_id(self):
        d = self.add()
        self.assertEqual(self.run_check(d, actor="alice"), [])
        self.assertEqual(self.run_check(d, actor="ALICE"), [])
        self.has(d, "only that GitHub account", actor="mallory")

    # 5: fullmatch + ASCII, no trailing-newline or unicode digit bypass
    def test_regexes(self):
        for extra, text in (({"sha256": "a" * 64 + "\n"}, "sha256"), ({"author": "alice\n"}, "author"),
                            ({"licence": "MIT\n"}, "licence"), ({"version": "1.0.0\n"}, "version"),
                            ({"source": "https://example.org/a\n"}, "source"),
                            ({"compatible_from": "\u0661.0.0"}, "compatible_from")):
            self.setUp_clean()
            self.has(self.add(extra=extra), text)
        self.assertIsNone(rmpverify.parse_version("1.0.0\n"))
        self.assertIsNone(rmpverify.parse_version("\u0661.0.0"))

    def test_url_rules(self):
        for u in ("https://user@example.org/x", "https://user:pw@example.org/", "https://exämple.org/x",
                  "https://example.org/a b", "http://example.org/", "https://localhost/", "https://example.org/\u00e9"):
            self.assertFalse(check.URL_RE.fullmatch(u), u)
        for u in ("https://example.org", "https://github.com/trigcondition/x?y=1#z", "https://a.b-c.org:8443/p"):
            self.assertTrue(check.URL_RE.fullmatch(u), u)

    # 6: symlinks, special files, size caps
    def test_symlink_refused(self):
        d = self.add()
        rmp = os.path.join(d, "test.sine-1.0.0-pi5.rmp")
        real = os.path.join(self.tmp, "real.rmp")
        os.rename(rmp, real)
        os.symlink(real, rmp)
        self.has(d, "not a regular file")
        os.remove(rmp)
        os.rename(real, rmp)
        os.symlink(os.path.join(d, "README.md"), os.path.join(d, "manifest.pi4.json"))
        self.assertTrue(self.errs(d))

    def test_symlinked_directory_refused(self):
        d = self.add()
        link = os.path.join(self.tmp, "machines", "test.sine", "1.0.1")
        os.symlink(d, link)
        self.has(link, "not a machines")

    def test_fifo_refused(self):
        d = self.add()
        os.remove(os.path.join(d, "README.md"))
        os.mkfifo(os.path.join(d, "README.md"))
        self.has(d, "not a regular file")

    def test_size_caps(self):
        d = self.add()
        with open(os.path.join(d, "README.md"), "wb") as f:
            f.write(b"x" * (check.MAX_FILE + 1))
        self.has(d, "larger than")
        with self.assertRaises(rmpverify.RmpError):
            rmpverify.verify(b"\0" * (rmpverify.MAX_FILE + 1))

    def test_reloc_cap(self):
        with self.assertRaises(rmpverify.RmpError) as cm:
            rmpverify.verify(rmpgen.make_rmp(mutate=lambda h: h.update(reloc_count=1 << 20, manifest_size=0)))
        self.assertTrue(cm.exception)

    # 7: hostile manifests give messages, not tracebacks
    def test_unhashable_board_and_recursion(self):
        d = self.add(extra={"board": ["pi5"]})
        self.has(d, "board")
        self.setUp_clean()
        d = self.add()
        with open(os.path.join(d, "manifest.json"), "w") as f:
            f.write("[" * 100000)
        self.has(d, "cannot read manifest")

    def test_duplicate_keys_and_nan(self):
        d = self.add()
        with open(os.path.join(d, "manifest.json"), "w") as f:
            f.write('{"id": "a", "id": "b"}')
        self.has(d, "duplicate key")
        with open(os.path.join(d, "manifest.json"), "w") as f:
            f.write('{"api": NaN}')
        self.has(d, "cannot read manifest")

    # 8
    def test_case_insensitive_ids(self):
        self.assertTrue(check.check_ids_file({"Test.Sine": "a1", "test.sine": "a2"}))

    # 9/10 embedded name/short and kind
    def test_name_short_kind_compare(self):
        self.has(self.add(rmp=rmpgen.make_rmp(name="Other")), "name")
        self.setUp_clean()
        self.has(self.add(rmp=rmpgen.make_rmp(short="XX")), "short")
        self.setUp_clean()
        self.has(self.add(extra={"kind": "effect"}), "kind")
        self.setUp_clean()
        self.has(self.add(extra={"kind": "plugin"}), "kind")
        self.setUp_clean()
        self.assertEqual(self.run_check(self.add(extra={"kind": "effect", "api": 3},
                                                 rmp=rmpgen.make_rmp(api=3, kind="effect"))), [])

    def test_licence_tokens_and_namespaces(self):
        d = self.add(rmp=rmpgen.make_rmp(licence="MIT (Foo DSP: A. Person)"))
        self.assertEqual(self.run_check(d), [])
        self.setUp_clean()
        d = self.add(extra={"licence": "MIT AND CC0-1.0"}, rmp=rmpgen.make_rmp(licence="MIT; sample CC0-1.0"))
        self.assertEqual(self.run_check(d), [])
        self.setUp_clean()
        self.has(self.add(extra={"licence": "MIT AND CC0-1.0"}), "licence")
        self.setUp_clean()
        self.ids = {"fx.*": "alice", "other.x": "bob"}
        self.assertEqual(check.check_ids_file(self.ids), [])
        self.assertEqual(self.run_check(self.add(pid="fx.new")), [])           # alice's namespace, no entry needed
        self.setUp_clean()
        self.has(self.add(pid="fx.new", author="bob"), "reserved by")
        self.assertTrue(check.check_ids_file({"fx.*": "alice", "fx.mine": "bob"}))
        self.assertTrue(check.check_ids_file({"a*b": "alice"}))
        self.setUp_clean()
        self.has(self.add(pid="x*y", author="alice"), "'*'")

    def test_nested_namespaces(self):
        for ids in ({"fx.evil.*": "mallory", "fx.*": "alice"},          # order of the file does not matter
                    {"fx.*": "alice", "fx.bbd.*": "bob"},
                    {"a.*": "alice", "a.b.*": "bob"},
                    {"a.b.*": "bob", "a.*": "alice"},
                    {"a.*": "alice", "a.b.c": "bob"},
                    {"x.*": "alice", "x": "bob"}):                      # the bare root belongs to the namespace
            self.assertTrue(any("inside a namespace" in e for e in check.check_ids_file(ids)), ids)
        self.assertEqual(check.check_ids_file({"a.*": "alice", "a.b.*": "ALICE", "a.b.c": "alice", "ab": "bob"}), [])
        self.assertEqual(check.namespace_owner({"a.*": "o1", "a.b.*": "o1"}, "a.b.c"), "o1")

    def test_bare_namespace_root(self):
        self.ids = {"x.*": "alice"}
        self.assertEqual(self.run_check(self.add(pid="x", author="alice"), actor="alice"), [])
        self.setUp_clean()
        self.has(self.add(pid="x", author="mallory"), "reserved by")

    def test_name_limits(self):
        self.has(self.add(extra={"name": "x" * 11}), "name")

    # adding a board to a published version: only the id owner
    def test_add_board_to_published_version(self):
        self.add(board="pi5")
        d = self.add(board="teensy")
        self.assertEqual(self.run_check(d, actor="alice"), [])
        self.has(d, "only that GitHub account", actor="mallory")

    def test_tree_shape(self):
        self.add()
        open(os.path.join(self.tmp, "machines", "stray.txt"), "w").close()
        errs = []
        check.all_version_dirs(errs)
        self.assertTrue(any("stray.txt" in e for e in errs))


class PreviewTest(RegistryTest):
    def folder(self, files=None, ver="1.0.0", **kw):
        """A version with a preview/ folder; `files` maps a file name to bytes (default: one valid track)."""
        d = self.add(ver=ver, **kw)
        p = os.path.join(d, "preview")
        os.makedirs(p, exist_ok=True)
        for n, data in (files if files is not None else {"Intro.mp3": mp3gen.make_mp3()}).items():
            with open(os.path.join(p, n), "wb") as f:
                f.write(data)
        return d

    def has(self, d, text):
        errs = self.run_check(d)
        self.assertTrue(any(text in e for e in errs), (text, errs))

    def test_valid_folder(self):
        d = self.folder({"01 Kick.mp3": mp3gen.make_mp3(), "Pad (long).mp3": mp3gen.make_mp3(id3=300)})
        self.assertEqual(self.run_check(d), [])

    def test_no_folder_is_fine_and_eight_files_pass(self):
        self.assertEqual(self.run_check(self.add()), [])
        d = self.folder({"t%d.mp3" % i: mp3gen.make_mp3() for i in range(8)}, ver="1.0.1")
        self.assertEqual(self.run_check(d), [])

    def test_nine_files(self):
        self.has(self.folder({"t%d.mp3" % i: mp3gen.make_mp3() for i in range(9)}), "at most 8 are allowed")

    def test_empty_folder(self):
        self.has(self.folder({}), "is empty")

    def test_wrong_type(self):
        d = self.folder({"a.wav": mp3gen.make_mp3(), "b.MP3": mp3gen.make_mp3(), "c.mp3.txt": mp3gen.make_mp3(),
                         "noext": mp3gen.make_mp3()})
        self.has(d, "a.wav: must end in .mp3")
        self.has(d, "b.MP3: must end in .mp3")
        self.has(d, "c.mp3.txt: must end in .mp3")
        self.has(d, "noext: must end in .mp3")

    def test_bad_names(self):
        for n in ("a/b.mp3", "../a.mp3", "a\\b.mp3", "a\x00b.mp3", "\u2026.mp3"):   # cannot be files: the rule alone
            self.assertIsNotNone(previews.name_problem(n), n)
        for i, n in enumerate((".mp3", ".hidden.mp3", "a  b.mp3", " a.mp3", "a .mp3", "a..b.mp3", "-a.mp3",
                               "caf\u00e9.mp3", "a;b.mp3", "x" * 41 + ".mp3", "a\nb.mp3", "..mp3")):
            d = self.folder({n: mp3gen.make_mp3()}, ver="1.0.%d" % i)
            self.assertTrue(self.run_check(d), n)

    def test_name_limit_boundary_and_case_clash(self):
        self.assertIsNone(previews.name_problem("x" * 40 + ".mp3"))
        self.assertIsNone(previews.name_problem("Take 1.2 (b)+#_x-y.mp3"))
        d = self.folder({"Kick.mp3": mp3gen.make_mp3()}, ver="1.0.1")
        real = os.listdir
        try:   # a case-insensitive file system cannot hold both files: list them by hand
            previews.os.listdir = lambda p: ["Kick.mp3", "kick.mp3"]
            errs = previews.check_folder(os.path.join(d, "preview"), check.read_file, check.FileError)
        finally:
            previews.os.listdir = real
        self.assertTrue(any("apart from case" in e for e in errs), errs)

    def test_oversize_file_and_total(self):
        big = mp3gen.make_mp3(frames=(2 << 20) // mp3gen.FRAME + 1)
        self.has(self.folder({"big.mp3": big}), "larger than")
        ok = mp3gen.make_mp3(frames=(2 << 20) // mp3gen.FRAME - 1)
        self.assertLessEqual(len(ok), 2 << 20)
        self.assertEqual(self.run_check(self.folder({"a.mp3": ok}, ver="1.0.1")), [])
        d = self.folder({"t%d.mp3" % i: ok for i in range(6)}, ver="1.0.2")
        self.has(d, "together the files are")

    def test_fake_mp3(self):
        for data in (b"not audio at all" * 100, b"RIFF" + b"\0" * 600, mp3gen.make_mp3()[:200], b"\0" * 600,
                     b"\xff\xe0" + b"\0" * 600,                     # sync bits only: reserved version/layer
                     mp3gen.make_mp3(1) + b"junk" * 200,              # a frame, then garbage
                     b"ID3\x04\x00\x00\x7f\x7f\x7f\x7f" + b"\0" * 600):   # tag larger than the file
            d = self.folder({"fake.mp3": data}, ver="1.0.%d" % (len(data) % 200))
            self.assertTrue(self.run_check(d), data[:12])
            shutil.rmtree(d)
        self.has(self.folder({"fake.mp3": b"hello"}, ver="2.0.0"), "smaller than")
        self.has(self.folder({"wav.mp3": b"RIFF" + b"\0" * 600}, ver="2.0.1"), "no MP3")

    def test_nested_dir_and_symlinks(self):
        d = self.folder()
        os.mkdir(os.path.join(d, "preview", "Sub.mp3"))
        self.has(d, "Sub.mp3: not a regular file")
        d2 = self.folder({}, ver="1.0.5")
        os.rmdir(os.path.join(d2, "preview"))
        os.symlink(os.path.join(d, "preview"), os.path.join(d2, "preview"))
        self.has(d2, "must be a directory")
        d3 = self.folder(ver="1.0.6")
        os.symlink(os.path.join(d3, "preview", "Intro.mp3"), os.path.join(d3, "preview", "Link.mp3"))
        self.has(d3, "Link.mp3: not a regular file")

    def test_preview_as_file_and_other_folders(self):
        d = self.add()
        open(os.path.join(d, "preview"), "w").close()
        self.has(d, "must be a directory")
        d = self.add(ver="1.0.1")
        os.mkdir(os.path.join(d, "previews"))
        self.has(d, "unexpected file 'previews'")

    def test_index_previews(self):
        self.folder({"B two.mp3": mp3gen.make_mp3(), "A one.mp3": mp3gen.make_mp3(2)}, ver="1.1.0")
        self.add(ver="1.0.0")
        by = {e["version"]: e for e in build_index.build()["entries"]}
        self.assertNotIn("previews", by["1.0.0"])
        self.assertEqual(by["1.1.0"]["previews"], [
            {"name": "A one", "file": "machines/test.sine/1.1.0/preview/A one.mp3", "bytes": 2 * mp3gen.FRAME},
            {"name": "B two", "file": "machines/test.sine/1.1.0/preview/B two.mp3", "bytes": 4 * mp3gen.FRAME}])
        self.assertEqual(build_index.build()["schema"], 1)

    def test_previews_added_by_owner_only(self):
        d = self.folder()
        self.assertEqual(self.run_check(d, actor="alice"), [])
        self.has_actor(d, "only that GitHub account", "mallory")

    def has_actor(self, d, text, actor):
        self.assertTrue(any(text in e for e in self.run_check(d, actor=actor)))


class ApiParityTest(unittest.TestCase):
    """Rules of the Pi loader (apply_a64, rmp_manifest_read) and of rmp_pack.py (api3_flags)."""
    ADRP = 0x90000000
    NOP = 0xD503201F

    def bad(self, text, **kw):
        with self.assertRaises(rmpverify.RmpError) as cm:
            rmpverify.verify(rmpgen.make_rmp(**kw))
        self.assertIn(text, str(cm.exception))

    def test_adrp_good(self):
        rmpverify.verify(rmpgen.make_rmp(relocs=[(512, 4)], insns={512: self.ADRP | 5}))

    def test_adrp_not_adrp(self):
        self.bad("not an ADRP", relocs=[(512, 4)], insns={512: self.NOP})

    def test_adrp_unaligned_or_in_data_part(self):
        self.bad("4-aligned", relocs=[(514, 4)], insns={514: self.ADRP})
        self.bad("code part", relocs=[(4096, 4)], insns={4096: self.ADRP}, image_size=8192)

    def test_adrp_on_teensy_refused(self):
        self.bad("type", target="teensy", relocs=[(512, 4)], insns={512: self.ADRP}, data_start=0)

    def test_manifest_knob_table(self):
        rmpverify.verify(rmpgen.make_rmp(nknobs=0))
        self.bad("knobs", nknobs=33)
        self.bad("do not fit", nknobs=2)          # the 20 padding bytes hold less than 2 * 26

    def test_api3_consistency(self):
        i = rmpverify.verify(rmpgen.make_rmp(api=3))
        self.assertEqual(i["kind"], "machine")
        self.assertEqual(rmpverify.verify(rmpgen.make_rmp(api=3, kind="effect"))["kind"], "effect")
        self.bad("without its rmp3_plugin", api=3, v3=False)

    def test_api3_plugin_defects(self):
        good = bytearray(rmpgen.make_rmp(api=3))
        import zlib, struct

        # patch the plugin in the image, then fix the CRC
        def patched(off, fmt, *vals):
            b = bytearray(good)
            struct.pack_into(fmt, b, 96 + off, *vals)
            crc = zlib.crc32(bytes(b[96:])) & 0xFFFFFFFF
            struct.pack_into("<I", b, 72, crc)
            return bytes(b)
        for text, data in (("bad magic", patched(256, "<I", 0x11111111)),
                           ("bad magic or size", patched(260, "<I", 8)),
                           ("neither machine nor effect", patched(268, "<I", 9)),
                           ("not an rmp3_plugin", patched(64 + 32, "<Q", 260)),
                           ("not an rmp3_plugin", patched(64 + 32, "<Q", 4090))):
            with self.assertRaises(rmpverify.RmpError, msg=text) as cm:
                rmpverify.verify(data)
            self.assertIn(text.split(" or ")[0], str(cm.exception))

    def test_flags_and_entry_api(self):
        self.bad("flags", api=3, mutate=lambda h: h.update(flags=0))
        self.bad("flags", api=2, mutate=lambda h: h.update(flags=0x1000))
        self.bad("entry table's api", api=2, entry_api=1)


class GitModeTest(unittest.TestCase):
    """--changed: git lists the paths, no shell, glob-looking directory names stay literal."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old = check.ROOT

        def git(*a):
            subprocess.run(["git", "-C", self.tmp, "-c", "user.name=t", "-c", "user.email=t@example.org"] + list(a),
                           check=True, capture_output=True)
        self.git = git
        git("init", "-q", "-b", "main")
        os.makedirs(os.path.join(self.tmp, "registry"))
        os.makedirs(os.path.join(self.tmp, "machines"))
        self.write_ids({})
        git("add", "."); git("commit", "-q", "-m", "base")
        git("checkout", "-q", "-b", "pr")

    def tearDown(self):
        check.ROOT = self.old
        shutil.rmtree(self.tmp)

    def write_ids(self, ids):
        with open(os.path.join(self.tmp, "registry", "ids.json"), "w") as f:
            json.dump(ids, f)

    def submit(self, pid, ver="1.0.0", author="alice", good=True):
        d = os.path.join(self.tmp, "machines", pid, ver)
        os.makedirs(d)
        data = rmpgen.make_rmp(pid=pid, ver=ver)
        m = dict(id=pid, kind="machine", version=ver, compatible_from=ver, name="Sine", short="SINE", author=author,
                 licence="MIT", board="pi5", api=2, sha256=hashlib.sha256(data).hexdigest(), description="d")
        if not good:
            m["sha256"] = "0" * 64
        with open(os.path.join(d, "manifest.json"), "w") as f:
            json.dump(m, f)
        with open(os.path.join(d, "%s-%s-pi5.rmp" % (pid, ver)), "wb") as f:
            f.write(data)
        with open(os.path.join(d, "README.md"), "w") as f:
            f.write("x\n")

    def run_main(self, *extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check.main(["--root", self.tmp, "--changed", "main"] + list(extra))
        return rc, buf.getvalue()

    def commit(self):
        self.git("add", "registry", "machines"); self.git("commit", "-q", "-m", "pr")

    def test_good_pr(self):
        self.write_ids({"test.sine": "alice"})
        self.submit("test.sine")
        self.commit()
        rc, out = self.run_main("--actor", "alice")
        self.assertEqual(rc, 0, out)

    def test_pr_with_previews(self):
        self.write_ids({"test.sine": "alice"})
        self.submit("test.sine")
        p = os.path.join(self.tmp, "machines", "test.sine", "1.0.0", "preview")
        os.makedirs(p)
        with open(os.path.join(p, "Intro.mp3"), "wb") as f:
            f.write(mp3gen.make_mp3())
        self.commit()
        self.assertEqual(self.run_main("--actor", "alice")[0], 0)
        with open(os.path.join(p, "Bad.mp3"), "wb") as f:
            f.write(b"x" * 600)
        self.git("add", "machines"); self.git("commit", "-q", "-m", "bad")
        rc, out = self.run_main("--actor", "alice")
        self.assertEqual(rc, 1)
        self.assertIn("preview: Bad.mp3: no MP3", out)

    def test_wrong_actor(self):
        self.write_ids({"test.sine": "alice"})
        self.submit("test.sine")
        self.commit()
        rc, out = self.run_main("--actor", "mallory")
        self.assertEqual(rc, 1)
        self.assertIn("mallory", out)

    def test_glob_named_dir_is_not_collapsed(self):
        """An id such as [a]bc is a literal name: the bad package in it is checked, not the good `abc`."""
        self.write_ids({"abc": "alice", "[a]bc": "alice"})
        self.submit("abc")
        self.commit()
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--ff-only", "pr")   # abc is now published
        self.git("checkout", "-q", "-b", "pr2")
        self.submit("[a]bc", good=False)
        self.commit()
        rc, out = self.run_main("--actor", "alice")
        self.assertEqual(rc, 1, out)
        self.assertIn("[a]bc", out)
        self.assertIn("sha256", out)

    def test_published_file_change_refused(self):
        self.write_ids({"test.sine": "alice"})
        self.submit("test.sine")
        self.commit()
        self.git("checkout", "-q", "main"); self.git("merge", "-q", "--ff-only", "pr")
        self.git("checkout", "-q", "-b", "pr2")
        with open(os.path.join(self.tmp, "machines", "test.sine", "1.0.0", "README.md"), "w") as f:
            f.write("changed\n")
        self.commit()
        rc, out = self.run_main("--actor", "alice")
        self.assertEqual(rc, 1)
        self.assertIn("published file may not be changed", out)

    def test_cannot_reserve_for_someone_else(self):
        self.write_ids({"x.y": "bob"})
        self.commit()
        rc, out = self.run_main("--actor", "alice")
        self.assertEqual(rc, 1)
        self.assertIn("your own", out)

    def test_reservation_not_changeable(self):
        self.write_ids({"x.y": "alice"})
        self.commit()
        self.git("checkout", "-q", "main"); self.git("merge", "-q", "--ff-only", "pr")
        self.git("checkout", "-q", "-b", "pr2")
        self.write_ids({"x.y": "mallory"})
        self.commit()
        rc, out = self.run_main("--actor", "mallory")
        self.assertEqual(rc, 1)
        self.assertIn("may not be changed", out)

    def test_unreadable_base_ids_fail_closed(self):
        self.write_ids({"x.y": "alice"})
        self.commit()
        rc, out = self.run_main("--actor", "alice")
        self.assertEqual(rc, 0, out)
        # a base ref that does not exist must not be treated as "no reservations"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check.main(["--root", self.tmp, "--changed", "nosuchref", "--actor", "alice"])
        self.assertEqual(rc, 1)
        # base has a file git cannot parse as JSON
        self.git("checkout", "-q", "main")
        self.write_ids({})
        with open(os.path.join(self.tmp, "registry", "ids.json"), "w") as f:
            f.write("{broken")
        self.git("add", "registry"); self.git("commit", "-q", "-m", "broken base")
        self.git("checkout", "-q", "-b", "pr3")
        self.write_ids({"x.y": "alice"})
        self.commit()
        rc, out = self.run_main("--actor", "alice")
        self.assertEqual(rc, 1, out)

    def test_actor_required(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                check.main(["--root", self.tmp, "--changed", "main"])


@unittest.skipUnless(os.environ.get("RMP_GOLDEN_DIR"), "set RMP_GOLDEN_DIR to a folder of real .rmp files")
class GoldenTest(unittest.TestCase):
    """Real packages from the Sidecar firmware repository (GPL-2.0, so not copied into this MIT repository):
    every one must pass, except the named reject. RMP_GOLDEN_DIR=<dir> python3 -m unittest discover -s tests"""
    def test_real_packages(self):
        root = os.environ["RMP_GOLDEN_DIR"]
        seen = 0
        for dp, _dn, fn in os.walk(root):
            for n in sorted(fn):
                if n.endswith(".rmp") and not n.startswith("demo"):
                    with open(os.path.join(dp, n), "rb") as f:
                        rmpverify.verify(f.read())
                    seen += 1
        self.assertGreater(seen, 0)


if __name__ == "__main__":
    unittest.main()
