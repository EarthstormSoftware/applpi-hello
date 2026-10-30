# Juggle Hello

The example app for [Juggle OS](https://github.com/EarthstormSoftware/juggle-os), and the starting point for new
ones. It's built on [App Base](https://github.com/EarthstormSoftware/app-base), the code the Earthstorm devices
share, so it has what every one of their pages has: the Device and MQTT tabs, a web password, updates over the
network, Home Assistant, and the Pi's own settings (Wi-Fi, its name through setup mode, a factory reset), which App
Base asks Juggle OS for. Its own part is small: one setting, a greeting, shown on its page with the Pi's health and
the OS it runs, kept through deploys and OS updates, and changed from the page, the API, MQTT or Home Assistant.

## What it needs

Juggle OS v0.7.0 or later, the first that knows `juggle` in `app.json` (an older one refuses it).

## Deploying it

On Windows, with the Pi set up by `juggle flash` (so SSH works with your key):

```powershell
.\deploy.ps1 <name>
```

It copies the app to the Pi, which replaces the app it had, starts this one and says whether it's running. Then it's
at `http://<name>.local`. Once it's running, `.\deploy.ps1 <name> -WiFi` sends a new version to the app itself,
without SSH (`-Password` if a web password is set): the Pi tries it, and goes back to the version it had if the new
one doesn't keep running.

## Starting a new app from it

1. Copy the repository (or download it as a ZIP) under a new name.
2. In `app\app.json`, give it its `name` (lowercase letters, digits and hyphens: a Pi keeps an app's settings only
   while the name stays the same) and a `version`. Add `"root": true` only if a library needs `/dev/mem`, and
   `"pwm": true` for WS2812 LEDs on GPIO 18.
3. In `app\product.py`, change `NAME`, and replace the greeting with the app's own settings and hooks. For a light,
   App Base's `device.py` lists the hooks, and
   [PlasmaStick Controller](https://github.com/EarthstormSoftware/plasmastick-controller) is one on a Pico W.
4. In `app\www\index.html`, replace the Hello tab with the app's own; the Device and MQTT tabs can stay as they are.
5. Change the tests in `tests\` to match, and the README.

## How it's laid out

Everything in `app\` goes to the Pi (`/data/app`), except App Base's Pico code:

| File | Is |
|---|---|
| `app.json` | The manifest: `juggle`, the Juggle OS version the app needs (`"1.0"`, see Juggle OS's [app contract](https://github.com/EarthstormSoftware/juggle-os/blob/main/docs/app-contract.md)), `name`, `version`, and `root` and `pwm` if it needs them. |
| `main.py` | Where it starts, with the OS's Python: `run(product)`. |
| `product.py` | What's this app's own: its name, its settings, and the hooks App Base calls (here `info`, `state`, `set`, `applied`, `HA_ENTITIES` and `ha_entity`). App Base's `device.py` lists them all. |
| `base\` | A copy of App Base, which the tests check is unchanged: a fix goes into App Base, then `..\app-base\update-base.ps1 -Product app` copies it in (`-Tag vX.Y.Z` for a release of App Base). |
| `www\index.html` | Its page, using App Base's `/base.css` and `/base.js`. |

The Pi runs it as the `app` user, which may use port 80 and the hardware (GPIO, I2C, SPI, the display, touch, serial),
and restarts it if it stops. It keeps its settings in the folder Juggle OS gives it (`/data/app-state`): the rest of
the Pi is read-only. Its log goes to the journal: `journalctl -u juggle-app` on the Pi.

## The page

| Tab | Has |
|---|---|
| Hello | The greeting and a box to change it, the Pi's health (up time, temperature, free memory, load, time), the app's version and the OS's |
| Device | The Pi's name, the web password, the log level, updates, the Pi's Wi-Fi and Wi-Fi fallback, setup mode, restart and reset |
| MQTT | The broker, the topic base and Home Assistant discovery |

## The API

From App Base, as every Earthstorm device's:

| Request | Does |
|---|---|
| `GET /api/info` | The app (`greeting` is Hello's), MQTT, the Pi and the OS |
| `GET`, `POST /api/config` | The settings: `{"hello": {"greeting": "..."}}` changes the greeting |
| `POST /api/restart`, `/api/reset` | Restarts the app; resets the settings (`{"confirm": true}`) |
| `GET`, `POST /api/update` | How the last update went; a new version of the app, as a tar (what `deploy.ps1 -WiFi` sends) |
| `POST /api/reboot` | Restarts the Pi |
| `GET`, `POST /api/wifi`, `GET /api/wifi/networks` | The Pi's Wi-Fi: a new network on trial, and the Wi-Fi fallback (setup mode when Wi-Fi doesn't connect) |
| `POST /api/setup-mode`, `/api/factory-reset` | Restarts the Pi in setup mode, to rename it; forgets the Pi's settings and starts setup mode (both `{"confirm": true}`) |

POSTs from other sites' pages are refused, and with a web password set every request needs it.

## MQTT

Under the topic base (`/home/device/{name}` unless changed):

| Topic | Is |
|---|---|
| `<base>/state` | The greeting, retained: `{"greeting": "..."}` |
| `<base>/set` | Changes it: `{"greeting": "..."}` |
| `<base>/status`, `<base>/info` | `online` or `offline`, and the Pi's health every minute, retained |
| `<base>/log` | Its warnings and errors |

With discovery on, Home Assistant finds the greeting as a text box, and the Pi's uptime, temperature, load and free
memory.

## Developing

`py -m pytest` runs the tests (Python 3.11 or later; no Pi needed). The app runs on a PC too:

```powershell
$env:PORT = 8080; py app\main.py
```

Its settings are then in `state\`, in the folder it's run from.

To release: copy in a tagged App Base, put the version in `app\app.json`, check it on a Pi, and tag `vX.Y.Z`.

## Licence

MIT. See [LICENSE](LICENSE). Microdot (in App Base) is MIT too: see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
