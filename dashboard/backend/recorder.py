# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# recorder.py
#
# Fleet Dashboard - Flight data recorder
# Stores incoming GPS packets in SQLite and exports them
#
# Richard J. Sears
# richardjsears@protonmail.com
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Flight data recorder.

Every GPS packet received from a simulator whose recording is enabled is
queued and written to SQLite in batches by a background thread, so the UDP
listener threads never touch the database.

Rows are keyed by the time the dashboard *received* the packet (UTC
milliseconds). Flight simulators often run on a scenario clock, so the
packet's own timestamp is not a reliable way to search by real date/time.
"""

import csv
import io
import json
import logging
import queue
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional
from xml.sax.saxutils import escape, quoteattr

logger = logging.getLogger(__name__)

EXPORT_FORMATS = {
    "csv": ("text/csv", "csv"),
    "json": ("application/json", "json"),
    "xml": ("application/xml", "xml"),
    "gpx": ("application/gpx+xml", "gpx"),
    "kml": ("application/vnd.google-earth.kml+xml", "kml"),
}

FEET_TO_METERS = 0.3048
FLUSH_INTERVAL_SEC = 1.0
PRUNE_INTERVAL_SEC = 3600.0
FIELDS = ("lat", "lon", "alt_ft", "speed_kts", "heading")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sims (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    recording INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS positions (
    sim_id INTEGER NOT NULL,
    ts_ms INTEGER NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    alt_ft REAL NOT NULL,
    speed_kts REAL NOT NULL,
    heading REAL NOT NULL,
    PRIMARY KEY (sim_id, ts_ms)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS positions_ts ON positions (ts_ms);
"""


def ms_to_iso(ts_ms: int) -> str:
    """Format UTC milliseconds as an ISO 8601 string (e.g. 2026-04-11T15:30:45.123Z)."""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts_ms % 1000:03d}Z"


class FlightRecorder:
    """Records GPS packets per simulator into a SQLite database."""

    def __init__(
        self,
        db_path: str,
        retention_days: int = 0,
        default_enabled: bool = False,
    ):
        self.db_path = db_path
        self.retention_days = retention_days
        self.default_enabled = default_enabled
        self._queue: queue.Queue = queue.Queue()
        self._enabled: dict[str, bool] = {}
        self._sim_ids: dict[str, int] = {}
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    # ---- Simulator registration / toggles ----

    def register_sims(self, names: list[str]) -> None:
        """Make sure every configured simulator has a row and load its toggle."""
        with self._lock, self._connect() as conn:
            for name in names:
                conn.execute(
                    "INSERT OR IGNORE INTO sims (name, recording) VALUES (?, ?)",
                    (name, int(self.default_enabled)),
                )
            for sim_id, name, recording in conn.execute(
                "SELECT id, name, recording FROM sims"
            ):
                self._sim_ids[name] = sim_id
                if name in names:
                    self._enabled[name] = bool(recording)

    def is_enabled(self, name: str) -> bool:
        return self._enabled.get(name, False)

    def set_enabled(self, name: str, enabled: bool) -> None:
        """Turn recording on or off for a simulator (persisted)."""
        with self._lock:
            if name not in self._enabled:
                raise KeyError(name)
            with self._connect() as conn:
                conn.execute(
                    "UPDATE sims SET recording = ? WHERE name = ?",
                    (int(enabled), name),
                )
            self._enabled[name] = enabled
        logger.info(f"Recording {'enabled' if enabled else 'disabled'} for {name}")

    # ---- Recording ----

    def record(self, name: str, data: dict) -> None:
        """Queue a GPS packet for writing if recording is enabled for this sim."""
        if not self._enabled.get(name):
            return
        try:
            values = tuple(float(data[f]) for f in FIELDS)
        except (KeyError, TypeError, ValueError):
            logger.debug(f"Not recording incomplete packet for {name}: {data}")
            return
        self._queue.put((self._sim_ids[name], int(time.time() * 1000)) + values)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._writer, daemon=True)
        self._thread.start()
        logger.info(f"Flight recorder writing to {self.db_path}")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self.flush()

    def flush(self) -> int:
        """Write all queued packets to the database. Returns rows written."""
        rows = []
        while True:
            try:
                rows.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if rows:
            with self._connect() as conn:
                conn.executemany(
                    "INSERT OR IGNORE INTO positions VALUES (?, ?, ?, ?, ?, ?, ?)",
                    rows,
                )
        return len(rows)

    def prune(self) -> int:
        """Delete rows older than the retention period. Returns rows deleted."""
        if self.retention_days <= 0:
            return 0
        cutoff = int((time.time() - self.retention_days * 86400) * 1000)
        with self._connect() as conn:
            deleted = conn.execute(
                "DELETE FROM positions WHERE ts_ms < ?", (cutoff,)
            ).rowcount
        if deleted:
            logger.info(f"Pruned {deleted} recorded positions older than retention")
        return deleted

    def _writer(self) -> None:
        last_prune = 0.0
        while not self._stop_event.wait(FLUSH_INTERVAL_SEC):
            try:
                self.flush()
                if time.time() - last_prune >= PRUNE_INTERVAL_SEC:
                    self.prune()
                    last_prune = time.time()
            except Exception as e:
                logger.error(f"Flight recorder write failed: {e}")

    # ---- Queries ----

    def _where(
        self, start_ms: int, end_ms: int, sims: Optional[list[str]]
    ) -> tuple[str, list]:
        clause = "p.ts_ms >= ? AND p.ts_ms <= ?"
        params: list = [start_ms, end_ms]
        if sims:
            clause += f" AND s.name IN ({','.join('?' * len(sims))})"
            params.extend(sims)
        return clause, params

    def status(self) -> dict:
        """Overall recorder status for the UI.

        Uses per-sim MIN/MAX lookups on the primary key (no full-table COUNT),
        so it stays fast with weeks of data.
        """
        sims = []
        with self._connect() as conn:
            for name, enabled in self._enabled.items():
                first, last = conn.execute(
                    "SELECT MIN(ts_ms), MAX(ts_ms) FROM positions WHERE sim_id = ?",
                    (self._sim_ids[name],),
                ).fetchone()
                sims.append(
                    {
                        "name": name,
                        "recording": enabled,
                        "first_ts": ms_to_iso(first) if first is not None else None,
                        "last_ts": ms_to_iso(last) if last is not None else None,
                    }
                )
        db_file = Path(self.db_path)
        db_size = sum(
            p.stat().st_size
            for p in db_file.parent.glob(db_file.name + "*")
            if p.is_file()
        )
        firsts = [s["first_ts"] for s in sims if s["first_ts"]]
        lasts = [s["last_ts"] for s in sims if s["last_ts"]]
        return {
            "db_size_bytes": db_size,
            "retention_days": self.retention_days,
            "first_ts": min(firsts) if firsts else None,
            "last_ts": max(lasts) if lasts else None,
            "simulators": sims,
        }

    def count(self, start_ms: int, end_ms: int, sims: Optional[list[str]]) -> int:
        clause, params = self._where(start_ms, end_ms, sims)
        with self._connect() as conn:
            return conn.execute(
                f"SELECT COUNT(*) FROM positions p JOIN sims s ON s.id = p.sim_id "
                f"WHERE {clause}",
                params,
            ).fetchone()[0]

    def iter_rows(
        self, start_ms: int, end_ms: int, sims: Optional[list[str]]
    ) -> Iterator[tuple]:
        """Yield (sim, ts_ms, lat, lon, alt_ft, speed_kts, heading), grouped by sim."""
        clause, params = self._where(start_ms, end_ms, sims)
        conn = self._connect()
        try:
            yield from conn.execute(
                f"SELECT s.name, p.ts_ms, p.lat, p.lon, p.alt_ft, p.speed_kts, "
                f"p.heading FROM positions p JOIN sims s ON s.id = p.sim_id "
                f"WHERE {clause} ORDER BY s.name, p.ts_ms",
                params,
            )
        finally:
            conn.close()

    # ---- Export ----

    def export(
        self, fmt: str, start_ms: int, end_ms: int, sims: Optional[list[str]]
    ) -> Iterator[str]:
        """Stream the selected rows in the requested format."""
        rows = self.iter_rows(start_ms, end_ms, sims)
        writer = {
            "csv": _export_csv,
            "json": _export_json,
            "xml": _export_xml,
            "gpx": _export_gpx,
            "kml": _export_kml,
        }[fmt]
        return writer(rows, ms_to_iso(start_ms), ms_to_iso(end_ms))


def _export_csv(rows: Iterator[tuple], start: str, end: str) -> Iterator[str]:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["sim", "timestamp", "lat", "lon", "alt_ft", "speed_kts", "heading"])
    for sim, ts_ms, *values in rows:
        w.writerow([sim, ms_to_iso(ts_ms), *values])
        if buf.tell() > 65536:
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate()
    yield buf.getvalue()


def _export_json(rows: Iterator[tuple], start: str, end: str) -> Iterator[str]:
    yield f'{{"start": "{start}", "end": "{end}", "positions": ['
    first = True
    for sim, ts_ms, lat, lon, alt_ft, speed_kts, heading in rows:
        item = json.dumps(
            {
                "sim": sim,
                "timestamp": ms_to_iso(ts_ms),
                "lat": lat,
                "lon": lon,
                "alt_ft": alt_ft,
                "speed_kts": speed_kts,
                "heading": heading,
            }
        )
        yield ("\n  " if first else ",\n  ") + item
        first = False
    yield "\n]}\n"


def _export_xml(rows: Iterator[tuple], start: str, end: str) -> Iterator[str]:
    yield '<?xml version="1.0" encoding="UTF-8"?>\n'
    yield f"<flight_data start={quoteattr(start)} end={quoteattr(end)}>\n"
    for sim, ts_ms, lat, lon, alt_ft, speed_kts, heading in rows:
        yield (
            f"  <position sim={quoteattr(sim)} timestamp="
            f'"{ms_to_iso(ts_ms)}" lat="{lat}" lon="{lon}" alt_ft="{alt_ft}" '
            f'speed_kts="{speed_kts}" heading="{heading}"/>\n'
        )
    yield "</flight_data>\n"


def _export_gpx(rows: Iterator[tuple], start: str, end: str) -> Iterator[str]:
    """GPX 1.1 with one track per simulator. Elevation is in meters."""
    yield (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" creator="LOFT Fleet Dashboard" '
        'xmlns="http://www.topografix.com/GPX/1/1">\n'
        f"  <metadata><desc>Recorded {escape(start)} to {escape(end)}</desc>"
        "</metadata>\n"
    )
    current = None
    for sim, ts_ms, lat, lon, alt_ft, speed_kts, heading in rows:
        if sim != current:
            if current is not None:
                yield "    </trkseg>\n  </trk>\n"
            yield f"  <trk>\n    <name>{escape(sim)}</name>\n    <trkseg>\n"
            current = sim
        yield (
            f'      <trkpt lat="{lat}" lon="{lon}">'
            f"<ele>{alt_ft * FEET_TO_METERS:.1f}</ele>"
            f"<time>{ms_to_iso(ts_ms)}</time>"
            f"<desc>{speed_kts:g} kts, heading {heading:g}</desc></trkpt>\n"
        )
    if current is not None:
        yield "    </trkseg>\n  </trk>\n"
    yield "</gpx>\n"


def _export_kml(rows: Iterator[tuple], start: str, end: str) -> Iterator[str]:
    """KML with one 3D flight path (absolute altitude) per simulator."""
    yield (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'
        f"  <name>Flight data {escape(start)} to {escape(end)}</name>\n"
        '  <Style id="track"><LineStyle><color>ff0000ff</color>'
        "<width>3</width></LineStyle></Style>\n"
    )
    current = None
    for sim, ts_ms, lat, lon, alt_ft, _speed, _heading in rows:
        if sim != current:
            if current is not None:
                yield "\n      </coordinates>\n    </LineString>\n  </Placemark>\n"
            yield (
                f"  <Placemark>\n    <name>{escape(sim)}</name>\n"
                "    <styleUrl>#track</styleUrl>\n    <LineString>\n"
                "      <altitudeMode>absolute</altitudeMode>\n      <coordinates>"
            )
            current = sim
        yield f"\n        {lon},{lat},{alt_ft * FEET_TO_METERS:.1f}"
    if current is not None:
        yield "\n      </coordinates>\n    </LineString>\n  </Placemark>\n"
    yield "</Document>\n</kml>\n"
