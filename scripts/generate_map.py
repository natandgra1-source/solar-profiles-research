"""
scripts/generate_map.py
Generates an interactive choropleth HTML map using folium + country GeoJSON.
Run:  python scripts/generate_map.py
Output: docs/solar_map.html
"""
import json
import math
import urllib.request
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).parent.parent / "data" / "solar_seasonal_profiles.csv"
OUT_PATH  = Path(__file__).parent.parent / "docs" / "solar_map.html"

SEASONS = {
    "Winter (Jan 1)":  "Winter_Jan1",
    "Spring (Apr 1)":  "Spring_Apr1",
    "Summer (Jul 1)":  "Summer_Jul1",
    "Autumn (Oct 1)":  "Autumn_Oct1",
}

def color_scale(value, vmin, vmax):
    """Map value to a hex color from deep blue → amber → red."""
    t = max(0, min(1, (value - vmin) / (vmax - vmin))) if vmax > vmin else 0
    if t < 0.5:
        r = int(29 + (245 - 29) * t * 2)
        g = int(78 + (158 - 78) * t * 2)
        b = int(216 + (11 - 216) * t * 2)
    else:
        r = int(245 + (239 - 245) * (t - 0.5) * 2)
        g = int(158 + (68  - 158) * (t - 0.5) * 2)
        b = int(11  + (68  - 11)  * (t - 0.5) * 2)
    return f"#{r:02x}{g:02x}{b:02x}"

def generate_map():
    df = pd.read_csv(DATA_PATH)
    country_data = {row["Country"]: row for _, row in df.iterrows()}

    # Download Natural Earth GeoJSON (low-res countries)
    geojson_url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
    print("Downloading GeoJSON...")
    try:
        with urllib.request.urlopen(geojson_url, timeout=15) as r:
            geojson = json.loads(r.read())
        print(f"  Got {len(geojson['features'])} features")
    except Exception as e:
        print(f"  Could not download GeoJSON: {e}")
        print("  Generating marker-based map instead...")
        geojson = None

    # Pre-compute color ranges per season
    ranges = {}
    for label, key in SEASONS.items():
        col = f"{key}_Daily_Wh"
        vals = df[col].dropna()
        ranges[key] = (vals.min(), vals.max())

    # Build HTML
    season_keys = list(SEASONS.values())
    season_labels = list(SEASONS.keys())

    # Build per-season JS data arrays for circle markers (works without GeoJSON)
    markers_js = {}
    for label, key in SEASONS.items():
        col_wh = f"{key}_Daily_Wh"
        col_pk = f"{key}_Peak_W"
        vmin, vmax = ranges[key]
        markers = []
        for _, row in df.iterrows():
            wh = row[col_wh]
            pk = row[col_pk]
            color = color_scale(wh, vmin, vmax)
            # Build hourly tooltip
            hourly = ", ".join(f"{row[f'{key}_Hour_{h:02d}_W']:.0f}" for h in range(24))
            markers.append({
                "lat": row["Latitude"],
                "lon": row["Longitude"],
                "country": row["Country"],
                "wh": round(wh),
                "pk": round(pk),
                "color": color,
                "hourly": hourly,
            })
        markers_js[key] = markers

    markers_json = json.dumps(markers_js)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>🌞 Global Solar Profiles Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Segoe UI', sans-serif; background:#0f172a; color:#e2e8f0; }}
  #map {{ width:100vw; height:100vh; }}
  #panel {{
    position:absolute; top:16px; left:16px; z-index:1000;
    background:rgba(15,23,42,0.95); border:1px solid #1e3a5f;
    border-radius:10px; padding:16px 20px; min-width:260px;
    backdrop-filter:blur(8px);
  }}
  #panel h2 {{ font-size:1.1rem; color:#f59e0b; margin-bottom:4px; }}
  #panel p {{ font-size:0.72rem; color:#64748b; margin-bottom:12px; }}
  #panel select {{
    width:100%; background:#1e293b; border:1px solid #334155;
    color:#e2e8f0; padding:7px 10px; border-radius:6px;
    font-size:0.85rem; margin-bottom:10px; cursor:pointer;
  }}
  .legend {{ display:flex; align-items:center; gap:8px; margin-top:8px; }}
  .legend-bar {{
    flex:1; height:10px; border-radius:4px;
    background: linear-gradient(to right, #1d4ed8, #f59e0b, #ef4444);
  }}
  .legend span {{ font-size:0.7rem; color:#64748b; white-space:nowrap; }}
  #stats {{ margin-top:12px; padding-top:10px; border-top:1px solid #1e293b; }}
  .stat {{ display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:4px; }}
  .stat-val {{ color:#f59e0b; font-weight:600; }}
  #tooltip {{
    position:absolute; bottom:20px; right:16px; z-index:1000;
    background:rgba(15,23,42,0.97); border:1px solid #334155;
    border-radius:8px; padding:14px 18px; min-width:220px;
    display:none; backdrop-filter:blur(8px);
  }}
  #tooltip h3 {{ color:#f59e0b; font-size:1rem; margin-bottom:6px; }}
  #tooltip .row {{ display:flex; justify-content:space-between; font-size:0.8rem; margin:3px 0; }}
  #tooltip .val {{ color:#34d399; font-weight:600; }}
  #chart-wrap {{ margin-top:10px; }}
  .bar-row {{ display:flex; align-items:center; gap:4px; margin:2px 0; }}
  .bar-h {{ font-size:0.62rem; color:#64748b; width:28px; }}
  .bar {{ height:6px; border-radius:2px; background:#f59e0b; transition:width 0.3s; }}
  #gt-badge {{
    position:absolute; bottom:16px; left:16px; z-index:1000;
    background:rgba(15,23,42,0.9); border:1px solid #1e3a5f;
    border-radius:8px; padding:8px 14px; font-size:0.72rem; color:#64748b;
  }}
  #gt-badge strong {{ color:#f59e0b; }}
</style>
</head>
<body>
<div id="map"></div>

<div id="panel">
  <h2>🌞 Global Solar Profiles</h2>
  <p>PVWatts V8 · 4 kW DC · 197 Countries</p>
  <label style="font-size:0.72rem;color:#64748b;display:block;margin-bottom:4px">SELECT SEASON</label>
  <select id="seasonSelect">
    <option value="Winter_Jan1">❄️  Winter — January 1</option>
    <option value="Spring_Apr1">🌱  Spring — April 1</option>
    <option value="Summer_Jul1" selected>☀️  Summer — July 1</option>
    <option value="Autumn_Oct1">🍂  Autumn — October 1</option>
  </select>
  <div class="legend">
    <span id="legMin"></span>
    <div class="legend-bar"></div>
    <span id="legMax"></span>
  </div>
  <div id="stats">
    <div class="stat"><span>World average</span><span class="stat-val" id="statAvg">—</span></div>
    <div class="stat"><span>Highest</span><span class="stat-val" id="statTop">—</span></div>
    <div class="stat"><span>Lowest</span><span class="stat-val" id="statBot">—</span></div>
  </div>
</div>

<div id="tooltip">
  <h3 id="ttCountry"></h3>
  <div class="row"><span>Daily Energy</span><span class="val" id="ttWh"></span></div>
  <div class="row"><span>Peak Power</span><span class="val" id="ttPk"></span></div>
  <div id="chart-wrap"></div>
</div>

<div id="gt-badge">
  © 2026 <strong>Nathaniel Grange</strong> · Georgia Institute of Technology
</div>

<script>
const ALL_DATA = {markers_json};
const RANGES = {{
  "Winter_Jan1": [{df['Winter_Jan1_Daily_Wh'].min():.0f}, {df['Winter_Jan1_Daily_Wh'].max():.0f}],
  "Spring_Apr1": [{df['Spring_Apr1_Daily_Wh'].min():.0f}, {df['Spring_Apr1_Daily_Wh'].max():.0f}],
  "Summer_Jul1": [{df['Summer_Jul1_Daily_Wh'].min():.0f}, {df['Summer_Jul1_Daily_Wh'].max():.0f}],
  "Autumn_Oct1": [{df['Autumn_Oct1_Daily_Wh'].min():.0f}, {df['Autumn_Oct1_Daily_Wh'].max():.0f}],
}};

const map = L.map('map', {{ center: [20, 10], zoom: 2, zoomControl: true }});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '© CartoDB', maxZoom: 19
}}).addTo(map);

let circleLayer = L.layerGroup().addTo(map);

function fmt(n) {{ return n.toLocaleString('en', {{maximumFractionDigits:0}}); }}

function renderSeason(key) {{
  circleLayer.clearLayers();
  const data = ALL_DATA[key];
  const [vmin, vmax] = RANGES[key];
  let topC='', topV=0, botC='', botV=Infinity, sum=0;

  data.forEach(d => {{
    sum += d.wh;
    if (d.wh > topV) {{ topV=d.wh; topC=d.country; }}
    if (d.wh < botV) {{ botV=d.wh; botC=d.country; }}
    const t = (d.wh - vmin) / (vmax - vmin);
    const radius = 4 + t * 14;
    const circle = L.circleMarker([d.lat, d.lon], {{
      radius, color: d.color, fillColor: d.color,
      fillOpacity: 0.75, weight: 0.5, opacity: 0.9
    }});
    circle.on('mouseover', () => showTooltip(d));
    circle.on('mouseout', hideTooltip);
    circleLayer.addLayer(circle);
  }});

  document.getElementById('legMin').textContent = fmt(vmin) + ' Wh';
  document.getElementById('legMax').textContent = fmt(vmax) + ' Wh';
  document.getElementById('statAvg').textContent = fmt(sum / data.length) + ' Wh';
  document.getElementById('statTop').textContent = topC + ' · ' + fmt(topV) + ' Wh';
  document.getElementById('statBot').textContent = botC + ' · ' + fmt(botV) + ' Wh';
}}

function showTooltip(d) {{
  document.getElementById('ttCountry').textContent = d.country;
  document.getElementById('ttWh').textContent = fmt(d.wh) + ' Wh/day';
  document.getElementById('ttPk').textContent = fmt(d.pk) + ' W';
  const hrs = d.hourly.split(', ').map(Number);
  const peak = Math.max(...hrs);
  const bars = hrs.map((v, i) => {{
    const w = peak > 0 ? Math.round(v / peak * 80) : 0;
    return `<div class="bar-row"><span class="bar-h">${{String(i).padStart(2,'0')}}h</span><div class="bar" style="width:${{w}}px"></div><span style="font-size:0.62rem;color:#94a3b8;margin-left:4px">${{v>0?Math.round(v):''}}</span></div>`;
  }}).join('');
  document.getElementById('chart-wrap').innerHTML = bars;
  document.getElementById('tooltip').style.display = 'block';
}}

function hideTooltip() {{
  document.getElementById('tooltip').style.display = 'none';
}}

document.getElementById('seasonSelect').addEventListener('change', e => renderSeason(e.target.value));
renderSeason('Summer_Jul1');
</script>
</body>
</html>"""

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"✓ Map saved → {OUT_PATH}")

if __name__ == "__main__":
    generate_map()
