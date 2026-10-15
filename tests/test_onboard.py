import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import onboard

A = {"identity": {"first_name": "Ada", "last_name": "L", "email": "ada@gmail.com", "phone": "555-0100",
                  "city": "Austin", "state": "TX"},
     "education": {"school": "UT", "degree": "Bachelor's", "major": "CS", "graduation": "2027-05"},
     "work_authorization": {"authorized_to_work_us": True, "requires_sponsorship": False},
     "_sources": {"identity.email": "resume_swe.pdf"},
     "preferences": {"roles": "software,product", "seasons": "Summer,Fall", "years": "2027"},
     "accounts": {"email_strategy": "plus_alias"}}


class T(unittest.TestCase):
    def test_alias(self):
        self.assertEqual(onboard.alias_email("ada@gmail.com", "Acme Corp."), "ada+acmecorp@gmail.com")
        self.assertEqual(onboard.alias_email("ada+x@gmail.com", "Acme"), "ada+acme@gmail.com")

    def test_validate(self):
        self.assertEqual(onboard.validate(A), [])
        self.assertTrue(onboard.validate({}))
        bad = json.loads(json.dumps(A)); bad["preferences"]["roles"] = "wizard"
        self.assertTrue(onboard.validate(bad))
        bad = json.loads(json.dumps(A)); bad["accounts"]["email_strategy"] = "dedicated"
        self.assertTrue(onboard.validate(bad))

    def test_build(self):
        p = onboard.build_profile(A)
        self.assertEqual(p["identity"]["preferred_name"], "Ada")
        self.assertEqual(p["eeo"]["gender"], "decline_to_answer")
        self.assertIs(p["work_authorization"]["requires_sponsorship"], False)
        self.assertEqual(p["accounts"]["account_email_pattern"], "ada+<company>@gmail.com")
        self.assertNotIn("password", p["accounts"])
        self.assertEqual(p["accounts"]["password_handling"], "browser_password_manager")
        f = onboard.build_filters(A, {"source_url": "u"})
        self.assertIn("Software", f["categories"])
        self.assertNotIn("Quant", f["categories"])
        self.assertEqual(f["terms"], ["Summer 2027", "Fall 2027"])
        self.assertEqual(f["source_url"], "u")

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            ans = os.path.join(d, "a.json")
            with open(ans, "w") as fh:
                json.dump(A, fh)
            self.assertEqual(onboard.main(["--answers", ans, "--out-dir", d]), 0)
            self.assertTrue(os.path.exists(os.path.join(d, "profile.yml")))
            self.assertTrue(os.path.exists(os.path.join(d, "filters.json")))

    def test_gaps(self):
        g = onboard.gaps(A)
        self.assertEqual(g["required"], [])
        opt = [x["key"] for x in g["optional"]]
        self.assertIn("links.github", opt)
        self.assertIn("eeo.gender", opt)
        self.assertIn("prompt", g["optional"][0])
        g = onboard.gaps({"identity": {"first_name": "Ada"}})
        req = [x["key"] for x in g["required"]]
        self.assertIn("identity.phone", req)
        self.assertIn("education.school", req)
        self.assertNotIn("identity.first_name", req)
        # required key with a non-empty default is listed as optional (to confirm)
        self.assertIn("accounts.email_strategy", [x["key"] for x in g["optional"]])
        self.assertNotIn("accounts.dedicated_email", req)
        d = json.loads(json.dumps(A)); d["accounts"]["email_strategy"] = "dedicated"
        self.assertIn("accounts.dedicated_email", [x["key"] for x in onboard.gaps(d)["required"]])

    def test_sources_stripped(self):
        p = onboard.build_profile(A)
        self.assertNotIn("_sources", p)
        self.assertNotIn("resume_swe.pdf", json.dumps(p))

    def test_summary(self):
        s = onboard.summary(A)
        self.assertIn("Identity:", s)
        self.assertIn("Application defaults:", s)
        self.assertIn("Email: ada@gmail.com  (from: resume_swe.pdf)", s)
        self.assertIn("Requires sponsorship: No", s)
        self.assertIn("Authorized to work us: Yes", s)
        self.assertIn("(default)", s)
        self.assertNotIn("MISSING", s)
        self.assertIn("Phone: MISSING", onboard.summary({"identity": {"first_name": "Ada"}}))

    def test_cli_gaps_summary(self):
        import contextlib, io
        with tempfile.TemporaryDirectory() as d:
            ans = os.path.join(d, "a.json")
            with open(ans, "w") as fh:
                json.dump({"identity": {"first_name": "Ada"}}, fh)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(onboard.main(["--answers", ans, "--gaps"]), 0)
            self.assertIn("identity.phone", [x["key"] for x in json.loads(buf.getvalue())["required"]])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(onboard.main(["--answers", ans, "--summary"]), 0)
            self.assertIn("MISSING", buf.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(onboard.main(["--answers", ans, "--out-dir", d]), 1)
            self.assertFalse(os.path.exists(os.path.join(d, "profile.yml")))
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                onboard.main(["--gaps"])

    def _run(self, *argv):
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = onboard.main(list(argv))
        return rc, buf.getvalue()

    def _write(self, path, obj):
        with open(path, "w") as fh:
            json.dump(obj, fh)

    def test_history_snapshot_and_resumes_preserved(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as loc:
            ans = os.path.join(d, "a.json"); self._write(ans, A)
            with mock.patch.dict(os.environ, {"JOB_APPLICATOR_LOCAL_DIR": loc}):
                self.assertEqual(self._run("--answers", ans, "--out-dir", d)[0], 0)
                self.assertFalse(os.path.exists(os.path.join(loc, "profile_history")))  # nothing to snapshot yet
                pp = os.path.join(d, "profile.yml")
                old = json.load(open(pp)); old["resumes"] = [{"file": "r.pdf"}]; self._write(pp, old)
                self.assertEqual(self._run("--answers", ans, "--out-dir", d)[0], 0)
                self.assertEqual(self._run("--answers", ans, "--out-dir", d)[0], 0)
                hist = sorted(os.listdir(os.path.join(loc, "profile_history")))
                self.assertEqual(len([h for h in hist if h.startswith("profile-") and h.endswith(".yml")]), 2)
                self.assertEqual(len([h for h in hist if h.startswith("filters-") and h.endswith(".json")]), 2)
                self.assertRegex(hist[0], r"-\d{8}T\d{6}Z")
                snap = [h for h in hist if h.startswith("profile-")][0]
                self.assertEqual(json.load(open(os.path.join(loc, "profile_history", snap)))["resumes"], [{"file": "r.pdf"}])
                self.assertEqual(json.load(open(pp))["resumes"], [{"file": "r.pdf"}])
                # explicit resumes key in answers wins
                self._write(ans, {**A, "resumes": []})
                self._run("--answers", ans, "--out-dir", d)
                self.assertEqual(json.load(open(pp))["resumes"], [])

    def test_from_profile_round_trip(self):
        from unittest import mock
        a = json.loads(json.dumps(A)); a["eeo"] = {"gender": "Female"}
        a["preferences"]["exclude_companies"] = "Foo, Bar"
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as loc, \
                mock.patch.dict(os.environ, {"JOB_APPLICATOR_LOCAL_DIR": loc}):
            orig = onboard.build_profile(a)
            pp, out = os.path.join(d, "profile.yml"), os.path.join(d, "ans.json")
            self._write(pp, orig)
            rc, text = self._run("--from-profile", pp)
            self.assertEqual(rc, 0)
            back = json.loads(text)
            self.assertEqual(back["eeo"]["race_ethnicity"], "")
            self.assertEqual(back["eeo"]["gender"], "Female")
            self.assertIs(back["work_authorization"]["requires_sponsorship"], False)
            self.assertNotIn("resumes", back); self.assertNotIn("account_email_pattern", back["accounts"])
            self.assertEqual(onboard.validate(back), [])
            self.assertEqual(onboard.build_profile(back), orig)
            rc, text = self._run("--from-profile", pp, "--out", out)
            self.assertEqual(text, ""); self.assertEqual(json.load(open(out)), back)
            # default path is <out-dir>/profile.yml
            self.assertEqual(json.loads(self._run("--from-profile", "--out-dir", d)[1]), back)

    def test_password_keys_rejected(self):
        for path in (("password",), ("accounts", "password"), ("accounts", "portals", "x_Password")):
            bad = json.loads(json.dumps(A)); d = bad
            for k in path[:-1]:
                d = d.setdefault(k, {})
            d[path[-1]] = "hunter2"
            self.assertTrue(any("password" in p for p in onboard.validate(bad)), path)
        bad = json.loads(json.dumps(A)); bad["accounts"]["portals"] = [{"password": "x"}]
        self.assertTrue(onboard.validate(bad))

    def test_env_default(self):
        ok = json.loads(json.dumps(A)); ok["accounts"]["password_handling"] = "env_default"
        self.assertEqual(onboard.validate(ok), [])
        self.assertEqual(onboard.build_profile(ok)["accounts"]["password_handling"], "env_default")
        self.assertEqual(onboard.validate({**ok, "_sources": {"accounts.password_handling": "x"}}), [])
        ok["accounts"]["password_handling"] = "plaintext"
        self.assertTrue(onboard.validate(ok))
        self.assertIn("env_default", [q for q in onboard.QUESTIONS if q[0] == "accounts.password_handling"][0][1])


if __name__ == "__main__":
    unittest.main()
