"""
core.py — SolarProfiles data access class
"""
from __future__ import annotations

import importlib.resources
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Optional


# Locate the bundled CSV (works whether installed as a package or run from source)
def _data_path() -> Path:
    try:
        # Python 3.9+
        with importlib.resources.as_file(
            importlib.resources.files("solar_profiles").joinpath("../data/pvwatts_solar_profiles_jan1.csv")
        ) as p:
            if p.exists():
                return p
    except Exception:
        pass
    # Fallback: look relative to this file
    candidates = [
        Path(__file__).parent.parent / "data" / "pvwatts_solar_profiles_jan1.csv",
        Path(__file__).parent / "data" / "pvwatts_solar_profiles_jan1.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "Cannot find pvwatts_solar_profiles_jan1.csv. "
        "Make sure the data/ directory is present alongside the package."
    )


HOUR_COLS = [f"Hour_{h:02d}_Local_AC_W" for h in range(24)]


class SolarProfiles:
    """
    Access PVWatts solar generation profiles for every country.

    Parameters
    ----------
    csv_path : str or Path, optional
        Override the bundled CSV with a custom file.

    Examples
    --------
    >>> sp = SolarProfiles()
    >>> sp.countries[:5]
    ['Afghanistan', 'Albania', 'Algeria', ...]

    >>> sp.profile("Germany")
    Hour_00_Local_AC_W       0.0
    Hour_01_Local_AC_W       0.0
    ...
    Hour_12_Local_AC_W    1842.3
    ...

    >>> sp.hourly_array("Germany")
    array([0., 0., 0., ..., 1842.3, ..., 0.])

    >>> sp.compare(["Germany", "Australia", "Nigeria"])
       Hour  Germany  Australia  Nigeria
    0      0      0.0        0.0      0.0
    ...
    """

    def __init__(self, csv_path: Optional[str | Path] = None):
        path = Path(csv_path) if csv_path else _data_path()
        self._df = pd.read_csv(path)
        self._df = self._df.set_index("Country")

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def countries(self) -> list[str]:
        """Sorted list of all country names."""
        return sorted(self._df.index.tolist())

    @property
    def dataframe(self) -> pd.DataFrame:
        """Full raw DataFrame (countries as index)."""
        return self._df.copy()

    # ── Core accessors ───────────────────────────────────────────────────────

    def profile(self, country: str) -> pd.Series:
        """
        Return the 24-hour AC power profile (W) for a single country.

        Parameters
        ----------
        country : str
            Exact country name (see .countries for valid names).

        Returns
        -------
        pd.Series indexed by Hour_00_Local_AC_W … Hour_23_Local_AC_W
        """
        self._check(country)
        return self._df.loc[country, HOUR_COLS]

    def hourly_array(self, country: str) -> np.ndarray:
        """
        Return a numpy array of 24 AC power values (W) for a country.
        Index 0 = midnight local, index 12 = noon local.
        """
        return self.profile(country).to_numpy(dtype=float)

    def summary(self, country: str) -> dict:
        """Return metadata + daily summary stats for a country."""
        self._check(country)
        row = self._df.loc[country]
        arr = row[HOUR_COLS].to_numpy(dtype=float)
        return {
            "country": country,
            "latitude": float(row["Latitude"]),
            "longitude": float(row["Longitude"]),
            "utc_offset_h": int(row["UTC_Offset_h"]),
            "daily_energy_wh": float(row["Daily_Energy_Wh"]),
            "peak_ac_w": float(row["Peak_AC_W"]),
            "peak_hour_local": int(row["Peak_Hour_Local"]),
            "daylight_hours": int(np.sum(arr > 0)),
            "hourly_ac_w": arr.tolist(),
        }

    def compare(self, countries: list[str]) -> pd.DataFrame:
        """
        Return a tidy DataFrame comparing multiple countries hour-by-hour.

        Columns: Hour (0-23), then one column per country with AC power (W).
        """
        for c in countries:
            self._check(c)
        data = {"Hour": list(range(24))}
        for c in countries:
            data[c] = self.hourly_array(c).tolist()
        return pd.DataFrame(data)

    def top_n(self, n: int = 10, metric: str = "daily_energy") -> pd.DataFrame:
        """
        Return the top-N countries by a metric.

        Parameters
        ----------
        n : int
            Number of countries to return.
        metric : str
            One of 'daily_energy', 'peak_ac', 'daylight_hours'.
        """
        col_map = {
            "daily_energy": "Daily_Energy_Wh",
            "peak_ac": "Peak_AC_W",
            "daylight_hours": "Peak_Hour_Local",  # proxy; see below
        }
        if metric == "daylight_hours":
            arr = (self._df[HOUR_COLS] > 0).sum(axis=1)
            return (
                arr.sort_values(ascending=False)
                .head(n)
                .rename("Daylight_Hours")
                .reset_index()
            )
        col = col_map.get(metric)
        if col is None:
            raise ValueError(f"metric must be one of {list(col_map)}")
        return (
            self._df[col]
            .sort_values(ascending=False)
            .head(n)
            .reset_index()
            .rename(columns={col: metric})
        )

    def search(self, query: str) -> list[str]:
        """Case-insensitive partial match on country names."""
        q = query.lower()
        return [c for c in self.countries if q in c.lower()]

    def region_average(self, countries: list[str]) -> np.ndarray:
        """Return element-wise mean hourly profile across a list of countries."""
        arrays = np.array([self.hourly_array(c) for c in countries])
        return arrays.mean(axis=0)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _check(self, country: str):
        if country not in self._df.index:
            close = self.search(country)
            hint = f" Did you mean: {close[:3]}?" if close else ""
            raise KeyError(f"Country '{country}' not found.{hint}")

    def __repr__(self):
        return f"<SolarProfiles: {len(self.countries)} countries, Jan 1 local-time profiles>"
