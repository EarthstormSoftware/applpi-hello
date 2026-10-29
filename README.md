# ApplPi Hello

The example app for [ApplPi OS](https://github.com/EarthstormSoftware/applpi-os): a web page in the style of the
Pico projects' pages, showing the Pi (up time, temperature, memory, load) and the OS it runs, with one setting, a
greeting, that stays through deploys and OS updates. Copy it to start a new app.

## What it needs

ApplPi OS from the release after v0.6.0, the first that knows `applpi` in `app.json` (an older one refuses it).

## Deploying it

On Windows, with the Pi set up by `applpi flash` (so SSH works with your key):

```powershell
.\deploy.ps1 <name>
```

It copies the app to the Pi, which replaces the app it had, starts this one and says whether it's running. Then it's
at `http://<name>.local`.

## How an ApplPi OS app is laid out

Everything in `app\` goes to the Pi (`/data/app`):

| File | Is |
|---|---|
| `app.json` | The manifest: `applpi`, the ApplPi version the app needs (`"1.0"`, see ApplPi OS's [app contract](https://github.com/EarthstormSoftware/applpi-os/blob/main/docs/app-contract.md)), `name` (lowercase letters, digits and hyphens), `version`, and `root: true` if it must run as root (most apps don't). |
| `main.py` | Where it starts, run with the OS's Python. |
| `lib\` | Its pure-Python libraries (here Microdot), as on a Pico. Compiled ones come with the OS. |
| `www\` | Its web page. |

The Pi runs it as the `app` user, which may use port 80 and the hardware (GPIO, I2C, SPI, the display, touch, serial),
and restarts it if it stops. It keeps what it writes in the folder named by `APPLPI_STATE` (`/data/app-state`): the
rest of the Pi is read-only. Its output goes to the journal: `journalctl -u applpi-app` on the Pi.

On a PC, `python app\main.py` runs it too (with `PORT=8080` set, if port 80 is taken), keeping its settings in
`app\state\`.

## The API

| Request | Does |
|---|---|
| `GET /api/info` | The app, the Pi and the OS, as JSON. |
| `GET /api/config` | The settings. |
| `POST /api/config` | Changes them: `{"greeting": "..."}`. POSTs from other sites' pages are refused. |

## Licence

MIT. See [LICENSE](LICENSE). Microdot is MIT too: see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
