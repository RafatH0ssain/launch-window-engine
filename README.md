# Launch Window Engine

Pick a target orbit and the engine lists every launch window from Spaceport Nova Scotia (Canso, 45.3° N, 61.0° W). It solves for the moment the rocket reaches orbit rather than the moment it leaves the pad, then puts a weather probability on each window from two forecast ensembles. Every response carries the constants, site data and sources it was computed from.

**Live site:** https://rafath0ssain.github.io/launch-window-engine/

The API runs on a free host that sleeps when idle, so the first request after a pause takes about 30 seconds. Until it answers, the site shows recorded data behind an "offline" banner.

## What it does

- Finds launch windows for LEO, polar, sun-synchronous or custom orbits, with azimuth, window width and injection time.
- Says plainly when an orbit is out of reach: a 45.1° orbit from Canso returns the 26.8 m/s plane change it would cost, not an error.
- Scores each window's weather from the ECMWF and GEFS ensembles, and switches to climatology past day 5, where the forecast stops beating it.
- Shows a countdown, the ascent on a 3D globe, a ground-track map and the towns along the coast that will see the climb.
- Prices the expected delay of waiting for a later window.

## How well it works

- Four published SSO launch windows reproduce with an average miss of 1.3 minutes. Two more pass only after a vehicle-profile correction fitted to those same launches.
- The weather forecast was scored on 179 days of hindcasts against ERA5. It beats the seasonal average by 46% on day 1 and 15% on day 5, and loses to it after that.
- About 1,550 automated tests across the engine, weather layer, API and frontend.

## Layout

| Path | What it is |
|---|---|
| `backend/engine` | Orbital mechanics: reachability, J2 plane drift, windows solved at injection, hazard and conjunction screens |
| `backend/weather` | Ensemble launch-weather probability, climatology and the hindcast |
| `backend/api` | FastAPI service, `/v1` routes, provenance and citation ids |
| `backend/client` | `launchwin`, a Python client that returns pandas DataFrames |
| `tests/contract` | The JSON Schemas every part of the system is tested against |
| `Canso Launch Prototype.html` | The web app |

## Run it locally

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m uvicorn backend.api.app:app --port 8000
python3 -m http.server 8766
```

Then open http://localhost:8766/Canso%20Launch%20Prototype.html. The API docs are at http://localhost:8000/v1/docs, and `python scripts/integration_test.py` checks the whole stack end to end.

## Data sources

ECMWF and GEFS ensembles via Open-Meteo, Environment Canada's GEM model, Copernicus ERA5, CelesTrak, the Canso environmental assessment and the Cyclone-4M user guide.

## Team

Built by a team of five: Anand Lo, Het Jivani, Nafisah Nubah, Rafat Hossain and Akash Maity.
