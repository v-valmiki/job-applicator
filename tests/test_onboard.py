import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import onboard

A = {"identity": {"first_name": "Ada", "last_name": "L", "email": "ada@gmail.com"},
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


if __name__ == "__main__":
    unittest.main()
