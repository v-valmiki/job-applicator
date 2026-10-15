import contextlib, io, json, os, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import history, resumes  # noqa: E402

ENVS = ("JOB_APPLICATOR_RESUMES_DIR", "JOB_APPLICATOR_LOCAL_DIR", "JOB_APPLICATOR_PROFILE")


class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.rd, self.ld, self.prof = t / "resumes", t / "local", t / "profile.yml"
        self.rd.mkdir()
        self._old = {k: os.environ.get(k) for k in ENVS}
        os.environ["JOB_APPLICATOR_RESUMES_DIR"] = str(self.rd)
        os.environ["JOB_APPLICATOR_LOCAL_DIR"] = str(self.ld)
        os.environ["JOB_APPLICATOR_PROFILE"] = str(self.prof)

    def tearDown(self):
        for k, v in self._old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.tmp.cleanup()

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = history.main(list(args))
        return code, out.getvalue()

    def test_resume_hash_and_archive(self):
        cv = self.rd / "cv.pdf"
        cv.write_bytes(b"one")
        r = history.log_application("Acme", "Intern", "http://x/1", "submitted", resume=str(cv))
        self.assertEqual(r["resume"], "cv.pdf")
        self.assertEqual(r["resume_sha256"], resumes.sha256_file(cv))
        self.assertEqual(resumes.find_version(r["resume_sha256"][:8]).read_bytes(), b"one")
        cv.write_bytes(b"two")  # file later changes; sent version still recoverable
        self.assertEqual(resumes.find_version(r["resume_sha256"][:8]).read_bytes(), b"one")

    def test_profile_version(self):
        self.assertIsNone(history.log_application("A", "T", "u", "skipped")["profile_version"])
        self.prof.write_text("name: x")
        r = history.log_application("A", "T", "u", "skipped")
        self.assertEqual(len(r["profile_version"]), 8)

    def test_applied_latest_and_summary(self):
        self.assertIsNone(history.applied("u1"))
        history.log_application("A", "T", "u1", "filled")
        history.log_application("A", "T", "u1", "submitted")
        history.log_application("B", "T", "u2", "blocked")
        self.assertEqual(history.applied("u1")["status"], "submitted")
        s = history.summary()
        self.assertEqual(s["counts"], {"submitted": 1, "blocked": 1})
        self.assertEqual(len(s["latest"]), 2)
        with self.assertRaises(ValueError):
            history.log_application("A", "T", "u", "bogus")

    def test_account_rejects_password(self):
        with self.assertRaises(ValueError):
            history.log_account("A", "http://p", "e@x.com", password="hunter2")
        with self.assertRaises(ValueError):
            history.log_account("A", "http://p", "e@x.com", passwd="x")
        self.assertEqual(self.cli("account", "--company", "A", "--portal-url", "p",
                                  "--email", "e", "--password", "x")[0], 2)
        self.assertFalse((self.ld / "accounts.jsonl").exists())
        history.log_account("A", "http://p", "e@x.com", note="n")
        rec = json.loads((self.ld / "accounts.jsonl").read_text().splitlines()[0])
        self.assertEqual(rec["email"], "e@x.com")

    def test_append_only(self):
        history.log_application("A", "T", "u", "filled")
        f = self.ld / "applications.jsonl"
        first = f.read_text()
        history.log_application("A", "T", "u", "submitted")
        second = f.read_text()
        self.assertTrue(second.startswith(first))
        self.assertEqual(len(second.splitlines()), 2)

    def test_cli(self):
        code, out = self.cli("log", "--company", "A", "--title", "T", "--url", "u", "--status", "filled")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "filled")
        self.assertEqual(self.cli("check", "--url", "u")[0], 0)
        self.assertEqual(self.cli("check", "--url", "nope")[0], 1)
        self.assertEqual(json.loads(self.cli("summary")[1])["counts"], {"filled": 1})


if __name__ == "__main__":
    unittest.main()
