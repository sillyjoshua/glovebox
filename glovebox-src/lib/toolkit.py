"""Core logic for Glovebox. Standard library only, so it runs anywhere Python does."""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import webbrowser
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "tools" / "catalog.json"
INSTALL_DIR = ROOT / "installed"
STATE_FILE = ROOT / "installed" / ".state.json"

USER_AGENT = "glovebox/1.0 (+portable installer)"


def current_platform():
    if sys.platform.startswith("win"):
        return "win"
    if sys.platform == "darwin":
        return "mac"
    return "linux"


def load_catalog():
    with open(CATALOG, encoding="utf-8") as f:
        return json.load(f)["tools"]


def find_tool(tool_id):
    for tool in load_catalog():
        if tool["id"] == tool_id:
            return tool
    return None


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state):
    INSTALL_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def tool_dir(tool_id):
    return INSTALL_DIR / tool_id


def is_installed(tool_id):
    return load_state().get(tool_id, {}).get("status") == "installed"


def status_of(tool_id):
    return load_state().get(tool_id, {}).get("status", "empty")


def _safe_extract(zip_path, dest):
    """Extract a zip while refusing paths that would escape the destination."""
    dest = Path(dest).resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            target = (dest / member).resolve()
            if dest != target and dest not in target.parents:
                raise ValueError(f"Blocked unsafe path in archive: {member}")
        zf.extractall(dest)


def _download(url, out_path, progress=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp, open(out_path, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(64 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if progress and total:
                progress(done, total)


def install_tool(tool_id, progress=None, open_pages=True):
    """Install one tool. Returns (ok, message)."""
    tool = find_tool(tool_id)
    if tool is None:
        return False, f"Unknown tool: {tool_id}"

    dest = tool_dir(tool_id)
    dest.mkdir(parents=True, exist_ok=True)
    state = load_state()

    try:
        if tool["kind"] == "archive":
            with tempfile.TemporaryDirectory() as tmp:
                zip_path = Path(tmp) / "download.zip"
                _download(tool["url"], zip_path, progress)
                _safe_extract(zip_path, dest)
            state[tool_id] = {"status": "installed", "kind": "archive"}
            save_state(state)
            return True, f"{tool['name']} installed to {dest}"

        # 'page' and 'exe': we don't hold a stable direct link, so send the
        # person to the official page and leave a folder to drop the file in.
        (dest / "PUT_DOWNLOAD_HERE.txt").write_text(
            f"{tool['name']}\n\nDownload it from:\n{tool['url']}\n\n"
            f"Save or extract it into this folder, then run it from here.\n",
            encoding="utf-8",
        )
        if open_pages:
            try:
                webbrowser.open(tool["url"])
            except Exception:
                pass
        state[tool_id] = {"status": "queued", "kind": tool["kind"]}
        save_state(state)
        return True, f"{tool['name']}: opened the official page. Save the file into {dest}"

    except urllib.error.URLError as e:
        return False, f"{tool['name']}: network error ({e.reason})"
    except Exception as e:  # keep one bad tool from stopping a batch
        return False, f"{tool['name']}: {e}"


def mark_done(tool_id):
    """Mark a queued tool as installed once the person has placed the files."""
    state = load_state()
    if tool_id in state:
        state[tool_id]["status"] = "installed"
        save_state(state)


def install_many(tool_ids, progress=None, open_pages=True):
    results = []
    for tid in tool_ids:
        ok, msg = install_tool(tid, progress, open_pages)
        results.append((tid, ok, msg))
    return results


def build_zip(tool_ids, out_path):
    """Bundle chosen tools (or everything) into one zip with the launchers."""
    out_path = Path(out_path)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in ("lib", "web", "tools", "scripts"):
            for path in (ROOT / folder).rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    zf.write(path, path.relative_to(ROOT))
        for name in ("run.py", "run.sh", "run.bat", "README.md"):
            p = ROOT / name
            if p.exists():
                zf.write(p, name)
        for tid in tool_ids:
            d = tool_dir(tid)
            if d.exists():
                for path in d.rglob("*"):
                    if path.is_file():
                        zf.write(path, Path("installed") / path.relative_to(INSTALL_DIR))
    return out_path


def disk_free_mb():
    return shutil.disk_usage(ROOT).free // (1024 * 1024)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
