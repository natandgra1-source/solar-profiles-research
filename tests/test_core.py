"""
tests/test_core.py — Unit tests for SolarProfiles
Run:  pytest tests/ -v
"""
import numpy as np
import pandas as pd
import pytest

from solar_profiles import SolarProfiles


@pytest.fixture(scope="module")
def sp():
    return SolarProfiles()


# ── Basic loading ─────────────────────────────────────────────────────────────

def test_loads(sp):
    assert len(sp.countries) == 197


def test_countries_sorted(sp):
    assert sp.countries == sorted(sp.countries)


# ── Profile shape & values ────────────────────────────────────────────────────

def test_profile_length(sp):
    p = sp.profile("Germany")
    assert len(p) == 24


def test_profile_non_negative(sp):
    arr = sp.hourly_array("Germany")
    assert (arr >= 0).all()


def test_night_hours_zero(sp):
    # Germany in Jan: hours 0-6 and 20-23 should be zero
    arr = sp.hourly_array("Germany")
    assert arr[0] == 0.0
    assert arr[23] == 0.0


def test_southern_hemi_peak_in_middle(sp):
    # Australia Jan 1 is midsummer — peak should be near noon
    arr = sp.hourly_array("Australia")
    peak_h = int(np.argmax(arr))
    assert 10 <= peak_h <= 14, f"Expected peak near noon, got hour {peak_h}"


def test_northern_winter_lower_than_summer(sp):
    # Germany produces less energy on Jan 1 than Australia (southern hemisphere summer)
    de = sp.summary("Germany")["daily_energy_wh"]
    au = sp.summary("Australia")["daily_energy_wh"]
    assert au > de


# ── Summary ───────────────────────────────────────────────────────────────────

def test_summary_keys(sp):
    s = sp.summary("France")
    expected = {
        "country", "latitude", "longitude", "utc_offset_h",
        "daily_energy_wh", "peak_ac_w", "peak_hour_local",
        "daylight_hours", "hourly_ac_w",
    }
    assert expected.issubset(s.keys())


def test_summary_hourly_length(sp):
    assert len(sp.summary("Japan")["hourly_ac_w"]) == 24


def test_daily_energy_consistent(sp):
    s = sp.summary("Brazil")
    arr = np.array(s["hourly_ac_w"])
    assert abs(arr.sum() - s["daily_energy_wh"]) < 0.1


# ── Compare ───────────────────────────────────────────────────────────────────

def test_compare_shape(sp):
    df = sp.compare(["Germany", "Australia", "Nigeria"])
    assert df.shape == (24, 4)  # Hour + 3 countries
    assert list(df.columns) == ["Hour", "Germany", "Australia", "Nigeria"]


def test_compare_hours_0_to_23(sp):
    df = sp.compare(["France", "Japan"])
    assert list(df["Hour"]) == list(range(24))


# ── Top N ─────────────────────────────────────────────────────────────────────

def test_top_n_length(sp):
    df = sp.top_n(5, "daily_energy")
    assert len(df) == 5


def test_top_daily_energy_descending(sp):
    df = sp.top_n(10, "daily_energy")
    vals = df["daily_energy"].tolist()
    assert vals == sorted(vals, reverse=True)


def test_top_peak_descending(sp):
    df = sp.top_n(10, "peak_ac")
    vals = df["peak_ac"].tolist()
    assert vals == sorted(vals, reverse=True)


# ── Search ────────────────────────────────────────────────────────────────────

def test_search_returns_matches(sp):
    results = sp.search("land")
    assert "Iceland" in results
    assert "Finland" in results


def test_search_case_insensitive(sp):
    r1 = sp.search("germany")
    r2 = sp.search("GERMANY")
    assert r1 == r2 == ["Germany"]


def test_search_no_results(sp):
    assert sp.search("xyzxyzxyz") == []


# ── Error handling ────────────────────────────────────────────────────────────

def test_bad_country_raises(sp):
    with pytest.raises(KeyError, match="not found"):
        sp.profile("Narnia")


def test_bad_metric_raises(sp):
    with pytest.raises(ValueError):
        sp.top_n(5, metric="unicorn")


# ── Region average ────────────────────────────────────────────────────────────

def test_region_average_shape(sp):
    avg = sp.region_average(["Germany", "France", "Italy"])
    assert avg.shape == (24,)


def test_region_average_between_extremes(sp):
    arrs = np.array([sp.hourly_array(c) for c in ["Germany", "France", "Italy"]])
    avg = sp.region_average(["Germany", "France", "Italy"])
    assert (avg >= arrs.min(axis=0)).all()
    assert (avg <= arrs.max(axis=0)).all()
