"""Tests for run_census.py (Apache-2.0). MV2 of Munim, Inc. Made with AI agents (Anthropic Claude)."""
import io
import unittest
import urllib.error
from unittest import mock

import jam_census
import run_census


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def http_error(code, retry_after=None):
    headers = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("https://itch.io/x", code, "err", headers, None)


class FetchTest(unittest.TestCase):
    def test_retries_429_with_retry_after_then_succeeds(self):
        calls = [http_error(429, "7"), FakeResp(b"ok page")]

        def fake_urlopen(req, timeout=30):
            c = calls.pop(0)
            if isinstance(c, Exception):
                raise c
            return c

        with mock.patch("urllib.request.urlopen", fake_urlopen), mock.patch("time.sleep") as sl:
            self.assertEqual(run_census.fetch("https://itch.io/x"), "ok page")
        sl.assert_called_once_with(7)

    def test_429_without_header_backs_off_30s(self):
        calls = [http_error(429), http_error(429), FakeResp(b"fine")]

        def fake_urlopen(req, timeout=30):
            c = calls.pop(0)
            if isinstance(c, Exception):
                raise c
            return c

        with mock.patch("urllib.request.urlopen", fake_urlopen), mock.patch("time.sleep") as sl:
            self.assertEqual(run_census.fetch("https://itch.io/x"), "fine")
        self.assertEqual([c.args[0] for c in sl.call_args_list], [30, 60])

    def test_404_gives_up_at_once(self):
        def fake_urlopen(req, timeout=30):
            raise http_error(404)

        with mock.patch("urllib.request.urlopen", fake_urlopen), mock.patch("time.sleep") as sl:
            with self.assertRaises(urllib.error.HTTPError):
                run_census.fetch("https://itch.io/x")
        sl.assert_not_called()

    def test_uses_census_user_agent(self):
        seen = {}

        def fake_urlopen(req, timeout=30):
            seen["ua"] = req.get_header("User-agent")
            return FakeResp(b"x")

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            run_census.fetch("https://itch.io/x")
        self.assertEqual(seen["ua"], jam_census.UA)
        self.assertIn("mv2@munimtech.com", seen["ua"])


if __name__ == "__main__":
    unittest.main()
