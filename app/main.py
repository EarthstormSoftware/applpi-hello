"""Hello: the example Juggle OS app. A web page in the style of the Pico projects' pages, showing the Pi and the OS
it runs, with one setting (a greeting) kept in the app's state folder, so it outlasts deploys and OS updates.

  GET  /             the page
  GET  /api/info     the app, the Pi and the OS, as JSON (also for health checks)
  GET  /api/config   the settings
  POST /api/config   changes them: {"greeting": "..."}
"""

import json
import os
import socket
import subprocess
import time
from pathlib import Path

from microdot import Microdot, Response

HERE = Path(__file__).parent
APP = json.loads((HERE / "app.json").read_text(encoding="utf-8"))
# Juggle OS says where the app keeps what it writes; elsewhere (on a PC), a folder beside it
STATE = Path(os.environ.get("JUGGLE_STATE", HERE / "state"))
SETTINGS = STATE / "settings.json"
DEFAULTS = {"greeting": "Hello from Juggle OS"}
STARTED = time.monotonic()

app = Microdot()


def load_settings():
    try:
        return DEFAULTS | json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return dict(DEFAULTS)


def save_settings(settings):
    STATE.mkdir(parents=True, exist_ok=True)
    temporary = SETTINGS.with_suffix(".new")
    temporary.write_text(json.dumps(settings), encoding="utf-8")
    os.replace(temporary, SETTINGS)


def read(path, default=None):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return default


def os_info():
    release = dict(line.split("=", 1) for line in (read("/etc/juggle-release") or "").splitlines() if "=" in line)
    try:
        slot = subprocess.run(["/usr/lib/juggle/slot"], capture_output=True, text=True, timeout=5).stdout.strip()
    except OSError:
        slot = None
    return {"version": release.get("VERSION"), "build": release.get("BUILD_STAMP"), "slot": slot or None}


def memory_mib():
    fields = dict(line.split(":", 1) for line in (read("/proc/meminfo") or "").splitlines() if ":" in line)
    available = fields.get("MemAvailable", "").split()
    return int(available[0]) // 1024 if available else None


def origin_allowed(headers):
    """False for a POST a browser sent from another site's page. Browsers send Origin on such requests; scripts like
    curl send none and are allowed."""
    origin = headers.get("Origin")
    if not origin:
        return True
    return origin.split("://", 1)[-1].rstrip("/") == headers.get("Host", "")


@app.before_request
async def guard(request):
    if request.method == "POST" and not origin_allowed(request.headers):
        return "Cross-site request refused", 403, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/")
async def index(request):
    response = Response.send_file(str(HERE / "www" / "index.html"), content_type="text/html; charset=utf-8")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/info")
async def info(request):
    temperature = read("/sys/class/thermal/thermal_zone0/temp")
    return {
        "app": {"name": APP["name"], "version": APP["version"], "up_s": int(time.monotonic() - STARTED)},
        "device": {
            "name": socket.gethostname(),
            "up_s": int(float((read("/proc/uptime") or "0").split()[0])),
            "temperature_c": round(int(temperature) / 1000, 1) if temperature else None,
            "memory_free_mib": memory_mib(),
            "load": os.getloadavg()[0],
        },
        "os": os_info(),
        "greeting": load_settings()["greeting"],
    }


@app.get("/api/config")
async def get_config(request):
    return load_settings()


@app.post("/api/config")
async def set_config(request):
    try:
        updates = request.json
    except ValueError:
        updates = None
    if not isinstance(updates, dict) or set(updates) - set(DEFAULTS):
        return {"error": "Send a JSON object with greeting"}, 400
    greeting = updates.get("greeting")
    if not isinstance(greeting, str) or not 1 <= len(greeting.strip()) <= 64:
        return {"error": "The greeting must be 1 to 64 characters"}, 400
    settings = load_settings() | {"greeting": greeting.strip()}
    save_settings(settings)
    return settings


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    print(f"{APP['name']} {APP['version']} on port {port}, keeping its settings in {STATE}")
    # Every address, IPv4 and IPv6 (asyncio makes a socket for each): <name>.local can resolve to either
    app.run(host=None, port=port)
