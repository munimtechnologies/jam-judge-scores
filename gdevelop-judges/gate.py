# gate.py: wait until the pre-registration is public before any data is read. Apache-2.0.
# By MV2 of Munim, Inc.; made with AI agents (Anthropic Claude).
import sys
import time
import urllib.request

URL = ("https://raw.githubusercontent.com/munimtechnologies/jam-judge-scores/main/"
       "PREREGISTRATION-gdevelop-judges.md")


def main(max_minutes=50):
    t0 = time.time()
    while time.time() - t0 < max_minutes * 60:
        try:
            req = urllib.request.Request(URL, headers={"User-Agent": "MV2-Munim-gate/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8", "replace")
            if "**P1.**" in text and "**P6.**" in text:
                print("pre-registration is public:", URL, flush=True)
                return 0
        except Exception as e:
            print("not yet:", e, flush=True)
        time.sleep(60)
    print("pre-registration not public after %d minutes; reading no data" % max_minutes, flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
