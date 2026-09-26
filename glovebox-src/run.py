#!/usr/bin/env python3
"""Glovebox launcher. Run:  python run.py

Options:
  --no-browser     don't open the browser automatically
  --port N         start looking for a free port at N (default 8765)
  --list           print the tool list and exit
  --install ID...  install tools from the command line, no web page
"""

import argparse
import sys

if sys.version_info < (3, 8):
    raise SystemExit("Glovebox needs Python 3.8 or newer.")

from lib import server, toolkit


def main():
    ap = argparse.ArgumentParser(description="Glovebox")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--install", nargs="+", metavar="ID")
    args = ap.parse_args()

    if args.list:
        plat = toolkit.current_platform()
        for t in toolkit.load_catalog():
            ok = "yes" if plat in t["platforms"] else "no "
            print(f"{t['id']:<24} {ok}  {toolkit.status_of(t['id']):<10} {t['name']}")
        return

    if args.install:
        for tid, ok, msg in toolkit.install_many(args.install):
            print(("OK   " if ok else "FAIL ") + msg)
        return

    server.run(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass  # e.g. output piped to `head`
