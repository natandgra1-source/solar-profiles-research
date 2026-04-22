"""
tests/test_api.py — FastAPI endpoint tests
Run:  pytest tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient

from solar_profiles.api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["countries_loaded"] == 197


def test_countries():
    r = client.get("/countries")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 197
    assert "Germany" in data["countries"]


def test_profile_valid():
    r = client.get("/profile/Germany")
    assert r.status_code == 200
    data = r.json()
    assert data["country"] == "Germany"
    assert len(data["hourly_profile"]) == 24
    assert data["unit"] == "watts_ac"


def test_profile_invalid():
    r = client.get("/profile/Narnia")
    assert r.status_code == 404


def test_summary_valid():
    r = client.get("/summary/Australia")
    assert r.status_code == 200
    s = r.json()
    assert s["country"] == "Australia"
    assert "daily_energy_wh" in s
    assert len(s["hourly_ac_w"]) == 24


def test_compare_valid():
    r = client.get("/compare?countries=Germany,France,Japan")
    assert r.status_code == 200
    data = r.json()
    assert len(data["data"]) == 24
    assert "Germany" in data["countries"]


def test_compare_too_few():
    r = client.get("/compare?countries=Germany")
    assert r.status_code == 400


def test_top_default():
    r = client.get("/top")
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) == 10


def test_top_custom():
    r = client.get("/top?n=5&metric=peak_ac")
    assert r.status_code == 200
    assert len(r.json()["results"]) == 5


def test_top_invalid_metric():
    r = client.get("/top?metric=unicorn")
    assert r.status_code == 400


def test_search():
    r = client.get("/search?q=land")
    assert r.status_code == 200
    assert "Iceland" in r.json()["matches"]


def test_all():
    r = client.get("/all")
    assert r.status_code == 200
    assert r.json()["count"] == 197
