import contextlib, io, os, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import resumes  # noqa: E402


class ResumesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.rd, self.ld = t / "resumes", t / "local"
        self.rd.mkdir()
        self._old = {k: os.environ.get(k) for k in ("JOB_APPLICATOR_RESUMES_DIR", "JOB_APPLICATOR_LOCAL_DIR")}
        os.environ["JOB_APPLICATOR_RESUMES_DIR"] = str(self.rd)
        os.environ["JOB_APPLICATOR_LOCAL_DIR"] = str(self.ld)

    def tearDown(self):
        for k, v in self._old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.tmp.cleanup()

    def cli(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = resumes.main(list(args))
        return code, buf.getvalue()

    def test_lifecycle(self):
        (self.rd / "README.md").write_text("x")
        (self.rd / ".gitignore").write_text("*")
        f = self.rd / "cv.pdf"
        f.write_bytes(b"v1")
        self.assertEqual(resumes.status()["new"], ["cv.pdf"])
        self.assertEqual(self.cli("status")[0], 10)
        resumes.accept()
        st = resumes.status()
        self.assertEqual((st["unchanged"], st["new"], st["changed"]), (["cv.pdf"], [], []))
        self.assertEqual(self.cli("status")[0], 0)
        f.write_bytes(b"v2 longer")
        self.assertEqual(resumes.status()["changed"], ["cv.pdf"])
        self.assertEqual(self.cli("status")[0], 10)
        resumes.accept()
        arch = sorted(p.name for p in (self.rd / "archive").iterdir())
        self.assertEqual(len(arch), 2)
        self.assertEqual(resumes.status()["unchanged"], ["cv.pdf"])
        f.unlink()
        self.assertEqual(resumes.status()["removed"], ["cv.pdf"])
        resumes.accept()
        self.assertEqual(resumes.status()["removed"], [])
        self.assertIn("removed_at", resumes.load_manifest()["cv.pdf"])
        self.assertEqual(len(list((self.rd / "archive").iterdir())), 2)  # never deleted
        self.assertEqual(self.cli("status")[0], 0)
        # re-adding after removal counts as new
        f.write_bytes(b"v1")
        self.assertEqual(resumes.status()["new"], ["cv.pdf"])

    def test_find_version(self):
        f = self.rd / "cv.pdf"
        f.write_bytes(b"abc")
        resumes.accept()
        sha = resumes.load_manifest()["cv.pdf"]["sha256"]
        p = resumes.find_version(sha[:8])
        self.assertEqual(p.read_bytes(), b"abc")
        self.assertEqual(resumes.find_version(sha), p)
        self.assertIsNone(resumes.find_version("zzzzzzzz"))
        self.assertIsNone(resumes.find_version("ab"))
        self.assertEqual(self.cli("find", sha[:8])[0], 0)
        self.assertEqual(self.cli("find", "deadbeef")[0], 1)

    def test_archive_ignored(self):
        (self.rd / "archive").mkdir()
        (self.rd / "archive" / "old.pdf").write_bytes(b"x")
        self.assertEqual(resumes.status()["new"], [])

    def test_repo_gitignore_not_weakened(self):
        txt = (resumes.ROOT / "resumes" / ".gitignore").read_text()
        self.assertIn("*", txt.split())
        self.assertNotIn("!archive", txt)


if __name__ == "__main__":
    unittest.main()
