import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import discord_io as d

WEBHOOK = {"DISCORD_WEBHOOK_URL": "https://hook/x", "DISCORD_USER_ID": "", "DISCORD_BOT_TOKEN": "", "DISCORD_CHANNEL_ID": ""}
BOT = {**WEBHOOK, "DISCORD_USER_ID": "42", "DISCORD_BOT_TOKEN": "tok", "DISCORD_CHANNEL_ID": "7"}


def msg(id, content, author="42", ref=None, bot=False):
    return {"id": id, "content": content, "author": {"id": author, "bot": bot},
            "message_reference": {"message_id": ref} if ref else None}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for p in (mock.patch.dict(os.environ, {"JOB_APPLICATOR_LOCAL_DIR": self.tmp.name}),
                  mock.patch.object(d, "_http", self.fake_http),
                  mock.patch.object(d.time, "sleep", lambda s: None)):
            p.start(); self.addCleanup(p.stop)
        self.calls = []
        self.replies = [[]]  # successive GET responses; the last one repeats

    def fake_http(self, method, url, payload=None, headers=None):
        self.calls.append((method, url, payload, headers))
        if method == "POST":
            return 200, {"id": "100"}
        return 200, self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]

    def run_ask(self, cfg=BOT, kind="captcha", detail="hCaptcha", **kw):
        return d.ask(kind, "Acme", "SWE Intern", detail, "https://x", cfg=cfg, timeout=5, interval=0, **kw)


class TestFormat(unittest.TestCase):
    def test_mention_and_instructions(self):
        m = d.format_message("captcha", "Acme", "SWE", "hCaptcha", "https://u", "42")
        self.assertTrue(m.startswith("<@42> **CAPTCHA**: Acme - SWE"))
        self.assertIn("reply `done`", m); self.assertIn("`skip`", m); self.assertIn("https://u", m)

    def test_no_mention_and_question(self):
        m = d.format_message("question", "A", "B", "Why us?")
        self.assertFalse(m.startswith("<@")); self.assertIn("`answer:`", m)


class TestPing(Base):
    def test_webhook_no_reader(self):
        r = self.run_ask(cfg={**WEBHOOK, "DISCORD_USER_ID": "42"})
        self.assertEqual(r, {"status": "no_reader", "text": "", "message_id": "100"})
        _, url, payload, _ = self.calls[0]
        self.assertTrue(url.endswith("?wait=true"))
        self.assertEqual(payload["allowed_mentions"], {"users": ["42"]})
        self.assertEqual(len(self.calls), 1)

    def test_no_wait(self):
        self.assertEqual(self.run_ask(wait=False)["status"], "sent")

    def test_ping_returns_id(self):
        self.assertEqual(d.ping("error", "A", "B", "boom", cfg=WEBHOOK), "100")

    def test_bot_posts_with_auth(self):
        self.replies = [[msg("101", "done")]]
        self.run_ask()
        _, url, _, h = self.calls[0]
        self.assertIn("/channels/7/messages", url); self.assertEqual(h["Authorization"], "Bot tok")


class TestReplies(Base):
    def test_done(self):
        self.replies = [[], [msg("101", "Done")]]
        self.assertEqual(self.run_ask()["status"], "done")

    def test_skip(self):
        self.replies = [[msg("101", "skip")]]
        self.assertEqual(self.run_ask()["status"], "skipped")

    def test_answer_and_ignores_others(self):
        self.replies = [[msg("101", "hello", author="9"), msg("102", "answer: Because I like it")]]
        r = self.run_ask(kind="question", detail="Why?")
        self.assertEqual((r["status"], r["text"]), ("answered", "Because I like it"))

    def test_prefers_reference(self):
        self.replies = [[msg("101", "skip"), msg("102", "done", ref="100")]]
        self.assertEqual(self.run_ask()["status"], "done")

    def test_any_nonbot_when_no_user_id(self):
        self.replies = [[msg("101", "x", author="5", bot=True), msg("102", "done", author="5")]]
        self.assertEqual(self.run_ask(cfg={**BOT, "DISCORD_USER_ID": ""})["status"], "done")

    def test_timeout(self):
        r = d.ask("captcha", "A", "B", "x", cfg=BOT, timeout=0.02, interval=0.005)
        self.assertEqual(r["status"], "timeout")

    def test_429_retry(self):
        seq = [(429, {"retry_after": 0.01}), (200, {"id": "100"}), (429, {"retry_after": 0.01}),
               (200, [msg("101", "done")])]
        with mock.patch.object(d, "_http", lambda *a: seq.pop(0)):
            self.assertEqual(self.run_ask()["status"], "done")
        self.assertEqual(seq, [])

    def test_http_error_hides_secrets(self):
        with mock.patch.object(d, "_http", lambda *a: (500, None)):
            with self.assertRaises(RuntimeError) as c:
                self.run_ask()
        self.assertNotIn("tok", str(c.exception))


class TestCache(Base):
    def test_normalize(self):
        self.assertEqual(d.norm_question("  Why  do you want THIS job?! "), "why do you want this job")

    def test_cache_hit_skips_ping(self):
        self.replies = [[msg("101", "answer: Passion")]]
        self.assertEqual(self.run_ask(kind="question", detail="Why this job?")["status"], "answered")
        n = len(self.calls)
        r = self.run_ask(kind="question", detail="why   this JOB")
        self.assertEqual((r["status"], r["text"]), ("cached", "Passion"))
        self.assertEqual(len(self.calls), n)
        log = (Path(self.tmp.name) / "asks.jsonl").read_text().splitlines()
        self.assertEqual(len(log), 2)
        self.assertEqual(json.loads(log[1])["result"]["status"], "cached")


class TestConfig(unittest.TestCase):
    def test_env_file_and_override(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / ".env"
            f.write_text('# c\nDISCORD_WEBHOOK_URL="https://a"\nDISCORD_USER_ID=1\n')
            with mock.patch.object(d, "ENV_FILE", f), mock.patch.dict(os.environ, {"DISCORD_USER_ID": "2"}):
                os.environ.pop("DISCORD_WEBHOOK_URL", None)
                cfg = d.load_config()
        self.assertEqual((cfg["DISCORD_WEBHOOK_URL"], cfg["DISCORD_USER_ID"], cfg["DISCORD_BOT_TOKEN"]),
                         ("https://a", "2", ""))


if __name__ == "__main__":
    unittest.main()
