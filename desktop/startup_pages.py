"""FMCC's own loading and problem screens, shown in the program window before the app is ready."""
import base64
import html
import json
from pathlib import Path

STYLE = """
*{box-sizing:border-box}html,body{margin:0;height:100%;background:#0B0E14;color:#E6E9EF;font-family:'Segoe UI',system-ui,sans-serif}
.wrap{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;padding:32px;text-align:center}
img{width:120px;height:auto}.word{font-size:44px;font-weight:800;letter-spacing:2px;color:#4C8DFF}
.bar{width:220px;height:3px;background:#1C2330;border-radius:3px;overflow:hidden}
.bar i{display:block;width:40%;height:100%;background:#4C8DFF;border-radius:3px;animation:slide 1.3s ease-in-out infinite}
@keyframes slide{0%{transform:translateX(-110%)}100%{transform:translateX(280%)}}
.status{font-size:15px;color:#9AA3B2;min-height:20px}
.card{max-width:560px;background:#121722;border:1px solid #232B3A;border-radius:14px;padding:28px 30px;text-align:left}
h1{font-size:20px;margin:0 0 10px}p{margin:0 0 10px;line-height:1.5;color:#C5CBD6;font-size:15px}
.try{color:#E6E9EF}.btns{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
button{font:inherit;font-size:14px;padding:9px 16px;border-radius:999px;border:1px solid #2E384A;background:#1A2130;color:#E6E9EF;cursor:pointer;transition:background-color .15s}
button:hover{background:#232C3F}button.p{background:#4C8DFF;border-color:#4C8DFF;color:#08101F;font-weight:600}button.p:hover{background:#6A9FFF}
small{color:#6F7889;font-size:12px}
"""


def _logo(base: Path) -> str:
    f = base / "loading-logo.png"
    try:
        return f'<img src="data:image/png;base64,{base64.b64encode(f.read_bytes()).decode()}" alt="FMCC">'
    except OSError:
        return '<div class="word">FMCC</div>'


def loading(base: Path, status: str = "Starting FMCC\u2026") -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{STYLE}</style></head><body><div class='wrap'>{_logo(base)}"
            f"<div class='bar'><i></i></div><div class='status' id='status'>{html.escape(status)}</div></div>"
            "<script>window.setStatus=function(t){document.getElementById('status').textContent=t}</script></body></html>")


def problem(base: Path, title: str, why: str, fix: str, code: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{STYLE}</style></head><body><div class='wrap'>{_logo(base)}"
            f"<div class='card'><h1>{html.escape(title)}</h1><p>{html.escape(why)}</p><p class='try'>{html.escape(fix)}</p>"
            "<div class='btns'><button class='p' onclick='pywebview.api.retry()'>Try again</button>"
            "<button onclick='pywebview.api.open_log()'>Open log file</button>"
            "<button id='copy' onclick=\"pywebview.api.copy_details().then(function(){document.getElementById('copy').textContent='Copied'})\">Copy details</button></div>"
            f"<p style='margin-top:16px'><small>Problem code: {html.escape(code)}</small></p></div></div></body></html>")


def status_js(text: str) -> str:
    return f"window.setStatus && window.setStatus({json.dumps(text)})"
