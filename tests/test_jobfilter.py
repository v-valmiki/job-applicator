import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from jobfilter import is_us_location, matches

F = {"terms": ["Summer 2027"], "na_term_title_keywords": ["early career"], "categories": ["Software"],
     "title_exclude": ["phd"], "allowed_degrees": ["Bachelor's"], "us_only": True}


def job(**kw):
    base = {"active": True, "is_visible": True, "title": "SWE Intern", "terms": ["Summer 2027"],
            "category": "Software", "degrees": ["Bachelor's"], "locations": ["Austin, TX"], "company_name": "X"}
    base.update(kw)
    return base


class T(unittest.TestCase):
    def test_locations(self):
        for ok in ["NYC", "SF", "Austin, TX", "Remote in USA", "Arlington County, Arlington, VA", "Washington, DC"]:
            self.assertTrue(is_us_location(ok), ok)
        for bad in ["London, UK", "Toronto, ON, Canada", "Vancouver, BC, Canada", "Munich, Germany"]:
            self.assertFalse(is_us_location(bad), bad)

    def test_match(self):
        self.assertTrue(matches(job(), F))
        self.assertFalse(matches(job(locations=["London, UK"]), F))
        self.assertFalse(matches(job(terms=["Summer 2026"]), F))
        self.assertFalse(matches(job(degrees=["PhD"]), F))
        self.assertFalse(matches(job(title="PhD Intern"), F))
        self.assertFalse(matches(job(active=False), F))
        self.assertTrue(matches(job(terms=["N/A"], title="Early Career Program"), F))
        self.assertFalse(matches(job(terms=["N/A"]), F))


if __name__ == "__main__":
    unittest.main()
