# Glovebox

A portable folder of useful tools. Copy it to a USB stick, open a terminal in it, and run one file. A page opens in your browser where you can install every tool, or just the one or two you want.

## Start it

Pick whichever matches the computer you're on. They all do the same thing.

| System | Command |
|---|---|
| Windows | double-click `run.bat`, or `run.bat` in a terminal |
| Linux / macOS | `./run.sh` (first time: `chmod +x run.sh`) |
| Anything with Python | `python run.py` |

Then use the page that opens:

- **Click tools** to select them, then **Install selected**.
- **Install everything for this computer** installs every tool that supports your OS.
- **Download as zip** bundles the toolkit and everything installed so far into one file.

## Command line (no browser)

```
python run.py --list
python run.py --install sysinternals keepassxc
```

## How installs work

- Tools with a direct download link (Sysinternals) download and unpack into `installed/<tool>/`.
- For the rest, vendors change their download links often, so the toolkit opens the official page and creates `installed/<tool>/`. Save or extract the file there. The light turns amber ("Waiting for file"). Once you've put the files in that folder, click **I've added the files** on the tool and the light turns green.

Because of this, nothing is downloaded from a mirror or a link you didn't choose.

## Add your own tool

Open `tools/catalog.json` and add an entry:

```json
{
  "id": "mytool",
  "name": "My Tool",
  "category": "Files",
  "blurb": "One line on what it does.",
  "platforms": ["win", "linux"],
  "kind": "archive",
  "url": "https://example.com/mytool.zip",
  "size_mb": 5
}
```

`kind: "archive"` downloads and unzips the URL. `kind: "page"` opens the URL for you.

## Keeping it portable

- Nothing is written outside this folder except your browser opening a page.
- The web page only listens on `127.0.0.1`, so other computers on the network can't reach it.
- To run with no Python on the machine, put an embeddable Python in `installed/python_embed/`. `run.bat` looks for it there.

## Folder layout

```
run.py  run.sh  run.bat   launchers
lib/                      installer and web server (standard library only)
web/                      the page you see
tools/catalog.json        the list of tools
installed/                created on first install
```
