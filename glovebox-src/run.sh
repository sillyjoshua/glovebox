#!/usr/bin/env bash
# Glovebox launcher for Linux and macOS.
# Usage:  ./run.sh            (opens the web page)
#         ./run.sh --list     (any run.py option works)

# Work from the folder this script lives in, even if run from elsewhere.
cd "$(dirname "$0")" || exit 1

for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    if "$cmd" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
      exec "$cmd" run.py "$@"
    fi
  fi
done

echo "Python 3.8 or newer was not found."
echo "  Debian/Ubuntu:  sudo apt install python3"
echo "  macOS:          brew install python   (or https://www.python.org/downloads/)"
exit 1
