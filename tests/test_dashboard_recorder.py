# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_dashboard_recorder.py
#
# Part of the "NMEA GPS Simulator" suite
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for the Fleet Dashboard flight data recorder and its API."""

import csv
import io
import json
import time
import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

from dashboard.backend import main as dashboard_main
from dashboard.backend.recorder import FlightRecorder, ms_to_iso

PACKET = {
    "lat": 33.1283,
    "lon": -117.2803,
    "alt_ft": 45000,
    "speed_kts": 420,
    "heading": 270,
    "timestamp": "2026-04-11T15:30:45.123456+00:00",
}


@pytest.fixture
def recorder(tmp_path):
    rec = FlightRecorder(str(tmp_path / "data" / "flight.db"), default_enabled=True)
    rec.register_sims(["CJ3", "Ultra"])
    return rec


def _insert(rec, name, ts_ms, **overrides):
    """Insert a row with a fixed receive time (bypassing the clock)."""
    data = {**PACKET, **overrides}
    rec._queue.put(
        (
            rec._sim_ids[name],
            ts_ms,
            data["lat"],
            data["lon"],
            data["alt_ft"],
            data["speed_kts"],
            data["heading"],
        )
    )
    rec.flush()


T0 = 1775921445000  # 2026-04-11T15:30:45Z


class TestFlightRecorder:
    def test_record_and_count(self, recorder):
        recorder.record("CJ3", PACKET)
        recorder.record("Ultra", PACKET)
        assert recorder.flush() == 2
        now = int(time.time() * 1000)
        assert recorder.count(now - 60000, now + 60000, None) == 2
        assert recorder.count(now - 60000, now + 60000, ["CJ3"]) == 1

    def test_disabled_sim_not_recorded(self, recorder):
        recorder.set_enabled("CJ3", False)
        recorder.record("CJ3", PACKET)
        assert recorder.flush() == 0

    def test_unknown_and_incomplete_packets_ignored(self, recorder):
        recorder.record("Nope", PACKET)
        recorder.record("CJ3", {"lat": 1.0})
        recorder.record("CJ3", {**PACKET, "alt_ft": "high"})
        assert recorder.flush() == 0

    def test_default_disabled(self, tmp_path):
        rec = FlightRecorder(str(tmp_path / "f.db"), default_enabled=False)
        rec.register_sims(["CJ3"])
        assert rec.is_enabled("CJ3") is False

    def test_toggle_persists(self, recorder):
        recorder.set_enabled("Ultra", False)
        reopened = FlightRecorder(recorder.db_path, default_enabled=True)
        reopened.register_sims(["CJ3", "Ultra", "CL350"])
        assert reopened.is_enabled("CJ3") is True
        assert reopened.is_enabled("Ultra") is False
        assert reopened.is_enabled("CL350") is True

    def test_set_enabled_unknown_sim(self, recorder):
        with pytest.raises(KeyError):
            recorder.set_enabled("Nope", True)

    def test_prune(self, recorder):
        recorder.retention_days = 30
        now = int(time.time() * 1000)
        _insert(recorder, "CJ3", now - 31 * 86400 * 1000)
        _insert(recorder, "CJ3", now - 1000)
        assert recorder.prune() == 1
        assert recorder.count(0, now + 1000, None) == 1

    def test_prune_disabled(self, recorder):
        _insert(recorder, "CJ3", 1000)
        assert recorder.prune() == 0

    def test_status(self, recorder):
        _insert(recorder, "CJ3", T0)
        _insert(recorder, "CJ3", T0 + 1000)
        status = recorder.status()
        assert status["first_ts"] == "2026-04-11T15:30:45.000Z"
        assert status["last_ts"] == "2026-04-11T15:30:46.000Z"
        assert status["db_size_bytes"] > 0
        by_name = {s["name"]: s for s in status["simulators"]}
        assert by_name["CJ3"]["recording"] is True
        assert by_name["Ultra"]["first_ts"] is None

    def test_writer_thread_flushes(self, recorder, monkeypatch):
        monkeypatch.setattr("dashboard.backend.recorder.FLUSH_INTERVAL_SEC", 0.05)
        recorder.start()
        recorder.record("CJ3", PACKET)
        deadline = time.time() + 2
        now = int(time.time() * 1000)
        while time.time() < deadline:
            if recorder.count(now - 60000, now + 60000, None):
                break
            time.sleep(0.05)
        recorder.stop()
        assert recorder.count(now - 60000, now + 60000, None) == 1

    def test_ms_to_iso(self):
        assert ms_to_iso(T0 + 7) == "2026-04-11T15:30:45.007Z"


class TestExports:
    @pytest.fixture
    def filled(self, recorder):
        _insert(recorder, "Ultra", T0 + 500, lat=34.0)
        _insert(recorder, "CJ3", T0)
        _insert(recorder, "CJ3", T0 + 1000, heading=275)
        return recorder

    def _export(self, rec, fmt, sims=None):
        return "".join(rec.export(fmt, T0 - 1000, T0 + 5000, sims))

    def test_csv(self, filled):
        rows = list(csv.DictReader(io.StringIO(self._export(filled, "csv"))))
        assert [r["sim"] for r in rows] == ["CJ3", "CJ3", "Ultra"]
        assert rows[0]["timestamp"] == "2026-04-11T15:30:45.000Z"
        assert float(rows[1]["heading"]) == 275
        assert float(rows[0]["alt_ft"]) == 45000

    def test_json(self, filled):
        data = json.loads(self._export(filled, "json"))
        assert len(data["positions"]) == 3
        assert data["positions"][0]["sim"] == "CJ3"
        assert data["positions"][0]["speed_kts"] == 420

    def test_json_empty(self, recorder):
        assert json.loads(self._export(recorder, "json"))["positions"] == []

    def test_xml(self, filled):
        root = ET.fromstring(self._export(filled, "xml", ["CJ3"]))
        positions = root.findall("position")
        assert len(positions) == 2
        assert positions[0].get("lat") == "33.1283"

    def test_gpx(self, filled):
        ns = {"g": "http://www.topografix.com/GPX/1/1"}
        root = ET.fromstring(self._export(filled, "gpx"))
        tracks = root.findall("g:trk", ns)
        assert [t.find("g:name", ns).text for t in tracks] == ["CJ3", "Ultra"]
        points = tracks[0].findall("g:trkseg/g:trkpt", ns)
        assert len(points) == 2
        assert points[0].find("g:ele", ns).text == "13716.0"
        assert points[0].find("g:time", ns).text == "2026-04-11T15:30:45.000Z"

    def test_kml(self, filled):
        ns = {"k": "http://www.opengis.net/kml/2.2"}
        root = ET.fromstring(self._export(filled, "kml"))
        marks = root.findall("k:Document/k:Placemark", ns)
        assert len(marks) == 2
        coords = marks[0].find("k:LineString/k:coordinates", ns).text.split()
        assert coords[0] == "-117.2803,33.1283,13716.0"

    def test_empty_gpx_and_kml_are_valid(self, recorder):
        ET.fromstring(self._export(recorder, "gpx"))
        ET.fromstring(self._export(recorder, "kml"))


class TestRecordingApi:
    @pytest.fixture
    def client(self, recorder, monkeypatch):
        monkeypatch.setattr(dashboard_main, "flight_recorder", recorder)
        _insert(recorder, "CJ3", T0)
        return TestClient(dashboard_main.app)

    def test_status(self, client):
        resp = client.get("/api/recording")
        assert resp.status_code == 200
        assert resp.json()["first_ts"] == "2026-04-11T15:30:45.000Z"

    def test_toggle(self, client, recorder):
        resp = client.put("/api/recording/CJ3", json={"enabled": False})
        assert resp.status_code == 200
        assert recorder.is_enabled("CJ3") is False

    def test_toggle_unknown(self, client):
        resp = client.put("/api/recording/Nope", json={"enabled": True})
        assert resp.status_code == 404

    def test_count(self, client):
        resp = client.get(
            "/api/recording/count",
            params={"start": "2026-04-11T15:00:00Z", "end": "2026-04-11T16:00:00Z"},
        )
        assert resp.json() == {"rows": 1}

    def test_count_naive_time_is_utc(self, client):
        resp = client.get(
            "/api/recording/count",
            params={"start": "2026-04-11T15:30:00", "end": "2026-04-11T15:31:00"},
        )
        assert resp.json() == {"rows": 1}

    def test_export(self, client):
        resp = client.get(
            "/api/recording/export",
            params={
                "start": "2026-04-11T15:00:00Z",
                "end": "2026-04-11T16:00:00Z",
                "format": "kml",
                "sims": "CJ3,Ultra",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith(
            "application/vnd.google-earth.kml+xml"
        )
        assert (
            'filename="flight_data_20260411T1500Z.kml"'
            in (resp.headers["content-disposition"])
        )
        assert "-117.2803,33.1283" in resp.text

    def test_export_bad_format(self, client):
        resp = client.get(
            "/api/recording/export",
            params={"start": "2026-04-11", "end": "2026-04-12", "format": "xls"},
        )
        assert resp.status_code == 400

    def test_bad_time(self, client):
        resp = client.get(
            "/api/recording/count", params={"start": "yesterday", "end": "now"}
        )
        assert resp.status_code == 400

    def test_end_before_start(self, client):
        resp = client.get(
            "/api/recording/count",
            params={"start": "2026-04-12", "end": "2026-04-11"},
        )
        assert resp.status_code == 400

    def test_not_running(self, monkeypatch):
        monkeypatch.setattr(dashboard_main, "flight_recorder", None)
        resp = TestClient(dashboard_main.app).get("/api/recording")
        assert resp.status_code == 503

    def test_fleet_state_includes_recording_flag(self, recorder, monkeypatch):
        from dashboard.backend.config import SimConfig

        monitor = dashboard_main.FleetMonitor()
        monitor.configure([SimConfig("CJ3", 12001), SimConfig("Other", 12002)])
        monitor.recorder = recorder
        flags = {s["name"]: s["recording"] for s in monitor.get_all_states()}
        assert flags == {"CJ3": True, "Other": False}
