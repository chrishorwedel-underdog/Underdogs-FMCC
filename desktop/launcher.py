"""FMCC Windows launcher: one copy at a time, a loading screen while the local database and server start in order,
a plain-words problem screen if they can't, and a clean shutdown of everything it started when the window closes."""
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DATA = Path(os.environ.get("FMCC_DATA_DIR") or Path(os.environ.get("APPDATA", Path.home())) / "FMCC")
LOGS = DATA / "logs"
LOG_FILE = LOGS / "fmcc-startup.log"
DB_PORT, APP_PORT = 27817, 8765
MUTEX_NAME = "FMCCSingleInstance"
TITLE = "FMCC"
RESTART_AS_ADMIN = {"wanted": False}
RESTART = {"wanted": False}
PENDING_INSTALL = {}
WINDOW = {}
log = logging.getLogger("fmcc.launcher")

# code: (title, why, what to try)
PROBLEMS = {
    "already_open": ("FMCC is already open", "Another copy of FMCC is still running, so this one can't start.",
                     "Switch to the open FMCC window, or close it and open FMCC again."),
    "port_busy": ("Another program is using FMCC's connection", "FMCC talks to itself through a private connection on your PC, and another program is using it right now.",
                  "Close other programs you've opened recently, or restart your PC, then press Try again."),
    "blocked": ("Windows security blocked part of FMCC", "Windows security or your antivirus stopped one of FMCC's own files from running.",
                "Allow FMCC in your antivirus or Windows Security (Virus & threat protection, Protection history), then press Try again."),
    "data_folder": ("FMCC can't write to its data folder", "FMCC keeps your careers and settings in your Windows user folder, and it can't save there right now.",
                    "Check your disk isn't full and that the FMCC folder in %APPDATA% isn't read-only, then press Try again."),
    "missing_file": ("Part of FMCC is missing", "A file FMCC needs isn't in its install folder. It may have been removed by an antivirus or an interrupted install.",
                     "Download FMCC again from the website and reinstall it. Your data is kept."),
    "database": ("FMCC's data store didn't start", "The part of FMCC that stores your data couldn't start.",
                 "Press Try again. If it keeps happening, restart your PC, and send the log file if it still won't start."),
    "server": ("FMCC didn't finish starting", "FMCC's engine stopped while it was starting.",
               "Press Try again. If it keeps happening, send the log file so the problem can be found."),
}


class Problem(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code, self.detail = code, detail


def setup_logging():
    LOGS.mkdir(parents=True, exist_ok=True)
    h = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[h])
    if sys.stdout is None or sys.stderr is None:  # no console in the packaged program; uvicorn needs real streams
        stream = open(LOGS / "fmcc-output.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or stream
        sys.stderr = sys.stderr or stream


def version() -> str:
    f = BASE / "version.txt"
    return f.read_text().strip() if f.exists() else "dev"


def single_instance() -> bool:
    """True if this is the only FMCC; otherwise bring the open window forward."""
    if os.name != "nt":
        return True
    import ctypes
    k32 = ctypes.windll.kernel32
    WINDOW["mutex"] = k32.CreateMutexW(None, False, MUTEX_NAME)
    if k32.GetLastError() != 183:
        return True
    u32 = ctypes.windll.user32
    h = u32.FindWindowW(None, TITLE)
    if h:
        u32.ShowWindow(h, 9)
        u32.SetForegroundWindow(h)
    return False


def port_free(port: int) -> bool:
    """Free unless something is listening (a just-closed earlier run doesn't count)."""
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0


def stop_leftovers():
    """Stop an FMCC data store left running by an earlier FMCC that didn't close cleanly."""
    import psutil
    db_dir = str(DATA / "db").lower()
    for p in psutil.process_iter(["name", "cmdline"]):
        try:
            if (p.info["name"] or "").lower() in ("mongod.exe", "mongod") and db_dir in " ".join(p.info["cmdline"] or []).lower():
                log.warning("Stopping a data store left over from an earlier run (pid %s)", p.pid)
                p.kill()
                p.wait(10)
        except (psutil.Error, OSError):
            continue


def check_install():
    for f in ("mongodb/mongod.exe", "web/index.html", "backend/server.py"):
        if not (BASE / f).exists():
            raise Problem("missing_file", f"Missing {f}")


def check_data_folder():
    try:
        (DATA / "db").mkdir(parents=True, exist_ok=True)
        probe = DATA / ".write-test"
        probe.write_text("ok")
        probe.unlink()
    except OSError as e:
        raise Problem("data_folder", repr(e)) from e


def _blocked(e: OSError) -> bool:
    return isinstance(e, PermissionError) or getattr(e, "winerror", None) in (5, 225, 1260, 4551)


def db_log_reason() -> str:
    try:
        tail = (DATA / "db.log").read_text(encoding="utf-8", errors="ignore")[-6000:].lower()
    except OSError:
        return "database"
    if "address already in use" in tail or "10048" in tail:
        return "port_busy"
    if "permission denied" in tail or "access is denied" in tail:
        return "data_folder"
    return "database"


class Engine:
    """Starts the data store, then the server, in order; stops both on close."""

    def __init__(self):
        self.db = None
        self.server = None
        self.thread = None
        self.error = None

    def start(self, status):
        check_install()
        check_data_folder()
        status("Getting your data ready\u2026")
        stop_leftovers()
        for port in (DB_PORT, APP_PORT):
            if not port_free(port):
                raise Problem("port_busy", f"Port {port} is in use")
        try:
            self.db = subprocess.Popen([str(BASE / "mongodb" / "mongod.exe"), "--dbpath", str(DATA / "db"), "--port", str(DB_PORT), "--bind_ip", "127.0.0.1",
                                        "--logpath", str(DATA / "db.log"), "--logappend"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except FileNotFoundError as e:
            raise Problem("missing_file", repr(e)) from e
        except OSError as e:
            raise Problem("blocked" if _blocked(e) else "database", repr(e)) from e
        self._wait(lambda: self._port_open(DB_PORT), 45, lambda: self.db.poll() is not None, "database")
        status("Starting FMCC\u2026")
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        self._wait(self._ready, 90, lambda: not self.thread.is_alive(), "server")
        log.info("FMCC %s is ready on port %s", version(), APP_PORT)

    @staticmethod
    def _port_open(port: int) -> bool:
        with socket.socket() as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0

    @staticmethod
    def _ready() -> bool:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{APP_PORT}/api/ping", timeout=2) as r:
                return r.status == 200
        except OSError:
            return False

    def _wait(self, ok, timeout: float, died, code: str):
        end = time.time() + timeout
        while time.time() < end:
            if ok():
                return
            if died():
                if code == "database":
                    raise Problem(db_log_reason(), f"The data store stopped (exit code {self.db.returncode})")
                raise self.error or Problem("server", "The server stopped while starting")
            time.sleep(0.3)
        raise Problem(db_log_reason() if code == "database" else "server", f"Timed out after {timeout:.0f}s")

    def _serve(self):
        try:
            cfg = DATA / "config.json"
            if cfg.exists():
                import json
                os.environ.update({k: v for k, v in json.loads(cfg.read_text()).items() if isinstance(v, str)})
            os.environ.update({"MONGO_URL": f"mongodb://127.0.0.1:{DB_PORT}", "DB_NAME": "fmcc", "CORS_ORIGINS": f"http://127.0.0.1:{APP_PORT}",
                               "FMCC_READER": "fmsave", "FMCC_STATIC_DIR": str(BASE / "web"), "FMCC_PROBE": str(BASE / "fmlibre" / "fmlibre-probe.exe"),
                               "FMCC_RELEASE_REPO": (BASE / "release_repo.txt").read_text().strip() if (BASE / "release_repo.txt").exists() else "",
                               "FMCC_VERSION": version()})
            sys.path.insert(0, str(BASE / "backend"))
            import uvicorn
            import connections_api
            import self_update
            from server import app
            connections_api.restart_hook = restart_as_admin
            self_update.install_hook = install_update
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=APP_PORT, log_level="warning", log_config=None))
            self.server.run()
        except ImportError as e:
            log.exception("A part of FMCC couldn't be loaded")
            self.error = Problem("missing_file", repr(e))
        except OSError as e:
            log.exception("The server couldn't start")
            self.error = Problem("port_busy" if getattr(e, "winerror", None) == 10048 or e.errno in (98, 10048) else "blocked" if _blocked(e) else "server", repr(e))
        except BaseException as e:  # noqa: BLE001 - anything else still needs a plain message on screen
            log.exception("The server stopped")
            self.error = Problem("server", repr(e))

    def stop(self):
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(10)
        if self.db and self.db.poll() is None:
            try:
                from pymongo import MongoClient
                MongoClient(f"mongodb://127.0.0.1:{DB_PORT}", serverSelectionTimeoutMS=3000).admin.command("shutdown")
            except Exception:  # noqa: BLE001 - shutdown always drops the connection
                pass
            try:
                self.db.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.db.kill()
        log.info("FMCC stopped")
        self.db = self.server = self.thread = None


ENGINE = Engine()
LAST = {}


def details() -> str:
    try:
        tail = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:]
    except OSError:
        tail = []
    import platform
    return "\n".join([f"FMCC {version()} on {platform.platform()}", f"Problem: {LAST.get('code')} - {LAST.get('detail')}", f"Log: {LOG_FILE}", ""] + tail)


class Api:
    def retry(self):
        if "server" in sys.modules:  # the engine already ran once in this copy; a fresh copy starts it cleanly
            RESTART["wanted"] = True
            WINDOW["w"].destroy()
            return
        threading.Thread(target=boot, args=(WINDOW["w"],), daemon=True).start()

    def open_log(self):
        if LOG_FILE.exists():
            os.startfile(str(LOG_FILE))  # noqa: S606 - opens the log in Notepad

    def copy_details(self):
        subprocess.run(["clip"], input=details().encode("utf-16"), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False)


def boot(window):
    import startup_pages as pages
    ENGINE.stop()
    window.load_html(pages.loading(BASE))
    time.sleep(0.3)
    try:
        ENGINE.start(lambda t: set_status(window, pages.status_js(t)))
        window.load_url(f"http://127.0.0.1:{APP_PORT}")
    except Problem as p:
        show_problem(window, p.code, p.detail)
    except Exception as e:  # noqa: BLE001
        log.exception("Unexpected startup problem")
        show_problem(window, "server", repr(e))


def set_status(window, js: str):
    try:
        window.evaluate_js(js)
    except Exception:  # noqa: BLE001 - the status line is only cosmetic
        pass


def show_problem(window, code: str, detail: str):
    import startup_pages as pages
    LAST.update(code=code, detail=detail)
    log.error("Startup problem %s: %s", code, detail)
    ENGINE.stop()
    window.load_html(pages.problem(BASE, *PROBLEMS[code], code))


def restart_as_admin():
    """Close this window; main() then stops everything and starts FMCC again with Windows' admin prompt."""
    RESTART_AS_ADMIN["wanted"] = True
    if WINDOW.get("w"):
        WINDOW["w"].destroy()


def install_update(path: str):
    """Close this window; main() then stops everything and runs the downloaded installer."""
    PENDING_INSTALL["path"] = path
    if WINDOW.get("w"):
        WINDOW["w"].destroy()


def selftest() -> int:
    """Used by the installer build: start everything without a window, check the app answers, stop."""
    try:
        ENGINE.start(lambda t: log.info(t))
        with urllib.request.urlopen(f"http://127.0.0.1:{APP_PORT}/", timeout=10) as r:
            ok = r.status == 200 and b"<html" in r.read(2000).lower()
        log.info("Self-test %s", "passed" if ok else "failed: the screens didn't load")
        return 0 if ok else 1
    except Problem as p:
        log.error("Self-test failed: %s %s", p.code, p.detail)
        return 1
    except Exception:  # noqa: BLE001
        log.exception("Self-test failed")
        return 1
    finally:
        ENGINE.stop()


def main():
    setup_logging()
    log.info("FMCC %s starting from %s", version(), BASE)
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    import webview
    import startup_pages as pages
    if not single_instance():
        log.info("FMCC is already open; brought its window to the front")
        return
    WINDOW["w"] = webview.create_window(TITLE, html=pages.loading(BASE), js_api=Api(), width=1600, height=960, min_size=(1200, 760), background_color="#0B0E14")
    try:
        webview.start(boot, WINDOW["w"])
    finally:
        ENGINE.stop()
    if PENDING_INSTALL.get("path"):
        import self_update
        self_update.run_installer(PENDING_INSTALL["path"])
        return
    if RESTART_AS_ADMIN["wanted"] or RESTART["wanted"]:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(WINDOW.pop("mutex", None))
        if RESTART_AS_ADMIN["wanted"]:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, None, None, 1)
        else:
            subprocess.Popen([sys.executable], close_fds=True)


if __name__ == "__main__":
    main()
