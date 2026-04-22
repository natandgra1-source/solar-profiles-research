#  Solar Profiles — Global PVWatts Atlas

> PVWatts-equivalent solar AC power generation profiles for **197 countries**, January 1st, 24-hour local-time resolution.

[![CI](https://github.com/YOUR_USERNAME/solar-profiles/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/solar-profiles/actions)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](#)


---

## What's in the data?

Each country entry contains:
- **24 hourly AC power values (W)** — Hour 00:00 → 23:00 in **local solar time**
- Geographic coordinates (lat/lon) and UTC offset
- Daily energy (Wh), peak power (W), and peak hour

**System parameters (matching PVWatts defaults):**

| Parameter | Value |
|---|---|
| System capacity | 4 kW DC |
| Module type | Standard crystalline silicon |
| Array type | Fixed open-rack |
| Tilt | `abs(latitude)`, capped at 60° |
| Azimuth | Equator-facing (180° N hemi, 0° S hemi) |
| DC/AC ratio | 1.2 |
| System losses | 14% |
| Irradiance model | Ineichen clear-sky |
| Date | January 1 |

---

## Quick start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/solar-profiles.git
cd solar-profiles
```

### 2. Install

```bash
# Core library only
pip install -e .

# With API server
pip install -e ".[api]"

# Everything (includes dev/test tools)
pip install -e ".[all]"
```

### 3. Use as a Python library

```python
from solar_profiles import SolarProfiles

sp = SolarProfiles()

# List all countries
print(sp.countries[:5])
# ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola']

# 24-hour profile as a numpy array
arr = sp.hourly_array("Germany")
# array([0., 0., ..., 1842.3, 2501.1, ..., 0.])

# Full metadata + stats
sp.summary("Australia")
# {'country': 'Australia', 'latitude': -25.27, 'longitude': 133.78,
#  'utc_offset_h': 9, 'daily_energy_wh': 23451.2, 'peak_ac_w': 3102.4,
#  'peak_hour_local': 12, 'daylight_hours': 13, 'hourly_ac_w': [...]}

# Compare multiple countries
df = sp.compare(["Germany", "Australia", "Nigeria"])
#    Hour  Germany  Australia  Nigeria
# 0     0      0.0        0.0      0.0
# ...

# Top 10 by daily energy
sp.top_n(10, metric="daily_energy")

# Regional average
import numpy as np
europe = ["Germany", "France", "Spain", "Italy", "Poland"]
avg = sp.region_average(europe)

# Search
sp.search("south")
# ['South Africa', 'South Korea', 'South Sudan']
```

### 4. REST API server

```bash
solar-profiles serve              # starts on http://localhost:8000
solar-profiles serve --port 9000  # custom port
```

Then open **http://localhost:8000/docs** for the interactive Swagger UI.

#### API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/countries` | List all 197 country names |
| GET | `/profile/{country}` | 24-hour profile for one country |
| GET | `/summary/{country}` | Full metadata + stats |
| GET | `/compare?countries=A,B,C` | Side-by-side hourly comparison |
| GET | `/top?n=10&metric=daily_energy` | Top-N ranking |
| GET | `/search?q=land` | Fuzzy country name search |
| GET | `/all` | Full dataset as JSON |

#### Example requests

```bash
# Single country profile
curl http://localhost:8000/profile/Germany

# Compare three countries
curl "http://localhost:8000/compare?countries=Germany,Australia,Nigeria"

# Top 5 by peak AC output
curl "http://localhost:8000/top?n=5&metric=peak_ac"

# Search for matches
curl "http://localhost:8000/search?q=land"
```

### 5. CLI

```bash
solar-profiles countries                    # list all
solar-profiles profile "New Zealand"        # ASCII chart
solar-profiles summary "Australia"          # stats
solar-profiles top --n 10 --metric peak_ac  # rankings
solar-profiles compare Germany France Japan # side-by-side table
solar-profiles search "south"               # search
```

### 6. Web dashboard

Open `docs/dashboard.html` in a browser **after** starting the API server:

```bash
solar-profiles serve &
open docs/dashboard.html
```

The dashboard features:
- Country selector with search
- Animated 24-hour bar chart
- Multi-country comparison line chart
- Full sortable rankings table

---

## Project structure

```
solar-profiles/
├── data/
│   └── pvwatts_solar_profiles_jan1.csv   # 197-country dataset
├── solar_profiles/
│   ├── __init__.py
│   ├── core.py       # SolarProfiles class
│   ├── api.py        # FastAPI REST server
│   └── cli.py        # Command-line interface
├── tests/
│   ├── test_core.py  # Unit tests
│   └── test_api.py   # API endpoint tests
├── docs/
│   └── dashboard.html  # Web UI
├── .github/
│   └── workflows/ci.yml
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Run tests

```bash
pytest tests/ -v
```

---

## Regenerating the data

The data was generated with `pvlib` using the PVWatts V8 algorithm. To regenerate (requires `pvlib`):

```bash
pip install pvlib
python scripts/generate.py   # outputs to data/
```

---



---

## Acknowledgements

Modelling approach based on [NREL PVWatts V8](https://pvwatts.nrel.gov/) / [pvlib-python](https://pvlib-python.readthedocs.io/). Country centroid coordinates from Natural Earth Data.
