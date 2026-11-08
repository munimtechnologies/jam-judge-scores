"""run_census.py: run the frozen jam_census.py with a politer download step (Apache-2.0).
MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents (Anthropic Claude).

Transport only. jam_census.py is imported unchanged from the public repo; this wrapper replaces just its
fetch() with one that waits and retries on "429 Too Many Requests" (honouring Retry-After) and gives up at
once on 404. Parsing, the sample, the statistics and every pre-registered threshold are untouched. The same
fetch() is used by MV2's prize_access.py 0.1 (munimtechnologies/jam-prize-access).

    python run_census.py --jam slapjam-ai-2 --out /out [--delay 5]
"""
import sys
import time
import urllib.error
import urllib.request

import jam_census


def fetch(url, tries=6):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": jam_census.UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:
                break
            wait = 5 * (i + 1)
            if e.code == 429:
                ra = e.headers.get("Retry-After") if e.headers else None
                wait = int(ra) if ra and ra.isdigit() else 30 * (i + 1)
            time.sleep(min(wait, 300))
        except Exception as e:
            last = e
            time.sleep(5 * (i + 1))
    raise last


def main():
    jam_census.fetch = fetch
    sys.argv = ["jam_census.py"] + sys.argv[1:]
    return jam_census.main()


if __name__ == "__main__":
    sys.exit(main())
