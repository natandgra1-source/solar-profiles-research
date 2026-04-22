#!/usr/bin/env python3
"""
scripts/generate.py
Regenerate pvwatts_solar_profiles_jan1.csv using pvlib.

Usage:
    pip install pvlib pandas numpy
    python scripts/generate.py
"""
import sys
from pathlib import Path

# Allow running from repo root or scripts/
sys.path.insert(0, str(Path(__file__).parent.parent))

import pvlib
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

COUNTRIES = {
    "Afghanistan": (33.93, 67.71), "Albania": (41.15, 20.17),
    "Algeria": (28.03, 1.66), "Andorra": (42.55, 1.60),
    "Angola": (-11.20, 17.87), "Antigua and Barbuda": (17.07, -61.80),
    "Argentina": (-38.42, -63.62), "Armenia": (40.07, 45.04),
    "Australia": (-25.27, 133.78), "Austria": (47.52, 14.55),
    "Azerbaijan": (40.14, 47.58), "Bahamas": (25.03, -77.40),
    "Bahrain": (26.00, 50.55), "Bangladesh": (23.68, 90.36),
    "Barbados": (13.19, -59.54), "Belarus": (53.71, 27.95),
    "Belgium": (50.50, 4.47), "Belize": (17.19, -88.50),
    "Benin": (9.31, 2.32), "Bhutan": (27.51, 90.43),
    "Bolivia": (-16.29, -63.59), "Bosnia and Herzegovina": (43.92, 17.68),
    "Botswana": (-22.33, 24.68), "Brazil": (-14.24, -51.93),
    "Brunei": (4.54, 114.73), "Bulgaria": (42.73, 25.49),
    "Burkina Faso": (12.36, -1.53), "Burundi": (-3.37, 29.92),
    "Cabo Verde": (16.54, -23.04), "Cambodia": (12.57, 104.99),
    "Cameroon": (3.85, 11.50), "Canada": (56.13, -106.35),
    "Central African Republic": (6.61, 20.94), "Chad": (15.45, 18.73),
    "Chile": (-35.68, -71.54), "China": (35.86, 104.20),
    "Colombia": (4.57, -74.30), "Comoros": (-11.65, 43.33),
    "Congo (Brazzaville)": (-0.23, 15.83), "Congo (DRC)": (-4.04, 21.76),
    "Costa Rica": (9.75, -83.75), "Croatia": (45.10, 15.20),
    "Cuba": (21.52, -77.78), "Cyprus": (35.13, 33.43),
    "Czech Republic": (49.82, 15.47), "Denmark": (56.26, 9.50),
    "Djibouti": (11.83, 42.59), "Dominica": (15.41, -61.37),
    "Dominican Republic": (18.74, -70.16), "Ecuador": (-1.83, -78.18),
    "Egypt": (26.82, 30.80), "El Salvador": (13.79, -88.90),
    "Equatorial Guinea": (1.65, 10.27), "Eritrea": (15.18, 39.78),
    "Estonia": (58.60, 25.01), "Eswatini": (-26.52, 31.47),
    "Ethiopia": (9.15, 40.49), "Fiji": (-16.58, 179.41),
    "Finland": (61.92, 25.75), "France": (46.23, 2.21),
    "Gabon": (-0.80, 11.61), "Gambia": (13.44, -15.31),
    "Georgia": (42.32, 43.36), "Germany": (51.17, 10.45),
    "Ghana": (7.95, -1.02), "Greece": (39.07, 21.82),
    "Grenada": (12.12, -61.68), "Guatemala": (15.78, -90.23),
    "Guinea": (9.95, -11.19), "Guinea-Bissau": (11.80, -15.18),
    "Guyana": (4.86, -58.93), "Haiti": (18.97, -72.29),
    "Honduras": (15.20, -86.24), "Hungary": (47.16, 19.50),
    "Iceland": (64.96, -19.02), "India": (20.59, 78.96),
    "Indonesia": (-0.79, 113.92), "Iran": (32.43, 53.69),
    "Iraq": (33.22, 43.68), "Ireland": (53.41, -8.24),
    "Israel": (31.05, 34.85), "Italy": (41.87, 12.57),
    "Ivory Coast": (7.54, -5.55), "Jamaica": (18.11, -77.30),
    "Japan": (36.20, 138.25), "Jordan": (30.59, 36.24),
    "Kazakhstan": (48.02, 66.92), "Kenya": (-0.02, 37.91),
    "Kiribati": (-3.37, -168.73), "Kosovo": (42.60, 20.90),
    "Kuwait": (29.31, 47.48), "Kyrgyzstan": (41.20, 74.77),
    "Laos": (19.86, 102.50), "Latvia": (56.88, 24.60),
    "Lebanon": (33.85, 35.86), "Lesotho": (-29.61, 28.23),
    "Liberia": (6.43, -9.43), "Libya": (26.34, 17.23),
    "Liechtenstein": (47.14, 9.55), "Lithuania": (55.17, 23.88),
    "Luxembourg": (49.82, 6.13), "Madagascar": (-18.77, 46.87),
    "Malawi": (-13.25, 34.30), "Malaysia": (4.21, 109.68),
    "Maldives": (3.20, 73.22), "Mali": (17.57, -3.99),
    "Malta": (35.94, 14.38), "Marshall Islands": (7.13, 171.18),
    "Mauritania": (21.01, -10.94), "Mauritius": (-20.35, 57.55),
    "Mexico": (23.63, -102.55), "Micronesia": (7.43, 150.55),
    "Moldova": (47.41, 28.37), "Monaco": (43.73, 7.40),
    "Mongolia": (46.86, 103.85), "Montenegro": (42.71, 19.37),
    "Morocco": (31.79, -7.09), "Mozambique": (-18.67, 35.53),
    "Myanmar": (21.92, 95.96), "Namibia": (-22.96, 18.49),
    "Nauru": (-0.52, 166.93), "Nepal": (28.39, 84.12),
    "Netherlands": (52.13, 5.29), "New Zealand": (-40.90, 174.89),
    "Nicaragua": (12.87, -85.21), "Niger": (17.61, 8.08),
    "Nigeria": (9.08, 8.68), "North Korea": (40.34, 127.51),
    "North Macedonia": (41.61, 21.75), "Norway": (60.47, 8.47),
    "Oman": (21.51, 55.92), "Pakistan": (30.38, 69.35),
    "Palau": (7.51, 134.58), "Palestine": (31.95, 35.23),
    "Panama": (8.54, -80.78), "Papua New Guinea": (-6.31, 143.96),
    "Paraguay": (-23.44, -58.44), "Peru": (-9.19, -75.02),
    "Philippines": (12.88, 121.77), "Poland": (51.92, 19.15),
    "Portugal": (39.40, -8.22), "Qatar": (25.35, 51.18),
    "Romania": (45.94, 24.97), "Russia": (61.52, 105.32),
    "Rwanda": (-1.94, 29.87), "Saint Kitts and Nevis": (17.36, -62.78),
    "Saint Lucia": (13.91, -60.98),
    "Saint Vincent and the Grenadines": (12.98, -61.29),
    "Samoa": (-13.76, -172.10), "San Marino": (43.94, 12.46),
    "Sao Tome and Principe": (0.19, 6.61), "Saudi Arabia": (23.89, 45.08),
    "Senegal": (14.50, -14.45), "Serbia": (44.02, 21.01),
    "Seychelles": (-4.68, 55.49), "Sierra Leone": (8.46, -11.78),
    "Singapore": (1.35, 103.82), "Slovakia": (48.67, 19.70),
    "Slovenia": (46.15, 14.99), "Solomon Islands": (-9.65, 160.16),
    "Somalia": (5.15, 46.20), "South Africa": (-30.56, 22.94),
    "South Korea": (35.91, 127.77), "South Sudan": (6.88, 31.31),
    "Spain": (40.46, -3.75), "Sri Lanka": (7.87, 80.77),
    "Sudan": (12.86, 30.22), "Suriname": (3.92, -56.03),
    "Sweden": (60.13, 18.64), "Switzerland": (46.82, 8.23),
    "Syria": (34.80, 38.60), "Taiwan": (23.70, 120.96),
    "Tajikistan": (38.86, 71.28), "Tanzania": (-6.37, 34.89),
    "Thailand": (15.87, 100.99), "Timor-Leste": (-8.87, 125.73),
    "Togo": (8.62, 0.82), "Tonga": (-21.18, -175.20),
    "Trinidad and Tobago": (10.69, -61.22), "Tunisia": (33.89, 9.54),
    "Turkey": (38.96, 35.24), "Turkmenistan": (38.97, 59.56),
    "Tuvalu": (-7.11, 177.64), "Uganda": (1.37, 32.29),
    "Ukraine": (48.38, 31.17), "United Arab Emirates": (23.42, 53.85),
    "United Kingdom": (55.38, -3.44), "United States": (37.09, -95.71),
    "Uruguay": (-32.52, -55.77), "Uzbekistan": (41.38, 64.59),
    "Vanuatu": (-15.38, 166.96), "Vatican City": (41.90, 12.45),
    "Venezuela": (6.42, -66.59), "Vietnam": (14.06, 108.28),
    "Yemen": (15.55, 48.52), "Zambia": (-13.13, 27.85),
    "Zimbabwe": (-19.02, 29.15),
}


def pvwatts_jan1_local(lat, lon):
    tilt = min(abs(lat), 60)
    surface_azimuth = 180 if lat >= 0 else 0
    utc_offset_h = max(-12, min(14, round(lon / 15)))
    local_midnight_utc = (
        pd.Timestamp("2020-01-01 00:00:00", tz="UTC")
        - pd.Timedelta(hours=utc_offset_h)
    )
    times_utc = pd.date_range(local_midnight_utc, periods=24, freq="h")
    location = pvlib.location.Location(latitude=lat, longitude=lon, altitude=0, tz="UTC")
    solar_pos = location.get_solarposition(times_utc)
    clearsky = location.get_clearsky(times_utc, model="ineichen")
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt, surface_azimuth=surface_azimuth,
        solar_zenith=solar_pos["apparent_zenith"], solar_azimuth=solar_pos["azimuth"],
        dni=clearsky["dni"], ghi=clearsky["ghi"], dhi=clearsky["dhi"], albedo=0.25,
    )
    poa_global = poa["poa_global"].fillna(0).clip(lower=0)
    temp_cell = pvlib.temperature.sapm_cell(
        poa_global=poa_global, temp_air=pd.Series(10.0, index=times_utc),
        wind_speed=pd.Series(1.0, index=times_utc), a=-3.56, b=-0.0750, deltaT=3,
    )
    dc = pvlib.pvsystem.pvwatts_dc(
        g_poa_effective=poa_global, temp_cell=temp_cell, pdc0=4000.0, gamma_pdc=-0.0047,
    )
    ac = pvlib.inverter.pvwatts(
        pdc=dc * 0.86, pdc0=4000.0 / 1.2, eta_inv_nom=0.96,
    ).clip(lower=0)
    return ac.values, utc_offset_h


def main():
    out = Path(__file__).parent.parent / "data" / "pvwatts_solar_profiles_jan1.csv"
    out.parent.mkdir(exist_ok=True)

    rows = []
    total = len(COUNTRIES)
    for i, (country, (lat, lon)) in enumerate(COUNTRIES.items(), 1):
        ac, utc_off = pvwatts_jan1_local(lat, lon)
        row = {"Country": country, "Latitude": round(lat, 4),
               "Longitude": round(lon, 4), "UTC_Offset_h": utc_off}
        for h in range(24):
            row[f"Hour_{h:02d}_Local_AC_W"] = round(float(ac[h]), 2)
        row["Daily_Energy_Wh"] = round(float(np.sum(ac)), 2)
        row["Peak_AC_W"] = round(float(np.max(ac)), 2)
        row["Peak_Hour_Local"] = int(np.argmax(ac))
        rows.append(row)
        if i % 50 == 0 or i == total:
            print(f"  {i}/{total}  {country}")

    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\n✓  Saved {len(rows)} rows → {out}")


if __name__ == "__main__":
    main()
