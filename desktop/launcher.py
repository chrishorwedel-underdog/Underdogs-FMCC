"""FMCC Windows launcher: starts the bundled local database and the FMCC server, then opens the program window."""
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DATA = Path(os.environ.get("APPDATA", Path.home())) / "FMCC"
DB_PORT, APP_PORT = 27817, 8765


def wait_port(port: int, timeout: float = 30) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.3)
    return False


def start_database() -> subprocess.Popen:
    (DATA / "db").mkdir(parents=True, exist_ok=True)
    return subprocess.Popen([str(BASE / "mongodb" / "mongod.exe"), "--dbpath", str(DATA / "db"), "--port", str(DB_PORT), "--bind_ip", "127.0.0.1",
                             "--logpath", str(DATA / "db.log"), "--logappend"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def start_server():
    cfg = DATA / "config.json"
    if cfg.exists():
        import json
        os.environ.update({k: v for k, v in json.loads(cfg.read_text()).items() if isinstance(v, str)})
    os.environ.update({"MONGO_URL": f"mongodb://127.0.0.1:{DB_PORT}", "DB_NAME": "fmcc", "CORS_ORIGINS": f"http://127.0.0.1:{APP_PORT}",
                       "FMCC_READER": "fmsave", "FMCC_STATIC_DIR": str(BASE / "web"),
                       "FMCC_RELEASE_REPO": (BASE / "release_repo.txt").read_text().strip() if (BASE / "release_repo.txt").exists() else ""})
    sys.path.insert(0, str(BASE / "backend"))
    import uvicorn
    from server import app
    uvicorn.run(app, host="127.0.0.1", port=APP_PORT, log_level="warning")


def main():
    db = start_database()
    if not wait_port(DB_PORT):
        raise SystemExit("FMCC's local database didn't start. See %APPDATA%\\FMCC\\db.log")
    threading.Thread(target=start_server, daemon=True).start()
    wait_port(APP_PORT)
    import webview
    webview.create_window("FMCC", f"http://127.0.0.1:{APP_PORT}", width=1600, height=960, min_size=(1200, 760))
    try:
        webview.start()
    finally:
        db.terminate()


if __name__ == "__main__":
    main()
