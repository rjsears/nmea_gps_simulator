# Airport Lookup

The simulator ships with a built-in airport database (4,003 entries covering the US, Canada, Europe, and the Pacific). The UI exposes it through the **Position** panel's airport picker; the REST API exposes it through the `/api/airports/*` endpoints.

This page documents the database, the lookup behavior in the UI, and the API endpoints you'd use from a script. For the wider position-setting workflow, see [Navigation Controls](navigation-controls.md).

<!-- SCREENSHOT-PENDING: airport-lookup-01-search.png - Position panel with the airport search dropdown open showing 5+ results. -->

## What's in the database

`backend/airports.py` defines a single dictionary (`AIRPORTS`) keyed by ICAO code. Each entry is a tuple of `(name, lat, lon, elevation_ft)`.

| Region | Entries | ICAO prefix |
|--------|---------|-------------|
| Continental US + Alaska | 3,642 | `K*` |
| US Pacific (Hawaii, Guam, US territories) | 253 | `P*` |
| Europe (UK, Germany, France, Italy, Switzerland, Scandinavia, etc.) | 82 | `E*`, `L*` |
| Canada | 25 | `C*` |
| Other (Iceland, Greenland, etc.) | 1 | `B*` |
| **Total** | **4,003** | |

The database is **static** - baked into the Python package at build time. To add or remove entries, edit `backend/airports.py` and rebuild the image. There is no runtime "load from file" option, by design - the data is small enough to live in memory, lookups are O(1), and the static nature means a known build matches a known data set.

## The Position panel airport picker

| Behavior | Detail |
|----------|--------|
| **Input field** | Free text; auto-uppercased on each keystroke. |
| **Debounce** | 200 ms between the last keystroke and the search request. |
| **Search endpoint** | `GET /api/airports/search?q=<query>&limit=10` |
| **Search matches** | ICAO prefix match **and** name substring match (case-insensitive). |
| **Result limit** | 10 per query. |
| **Dropdown** | Shows ICAO + name for each result. Click to select. |

Selecting an airport:

1. Sets `lat`, `lon`, `altitude_ft`, `airport_icao` on the server.
2. Closes the dropdown.
3. Renders the selected-airport card (ICAO + name + elevation).
4. Marks "airport selected" so the Start button validation clears.

## The selected-airport card

Once you've picked an airport, a small blue panel appears under the search input:

| Element | Source |
|---------|--------|
| **ICAO** | The four-letter code (e.g., `KCRQ`). |
| **Name** | Full airport name (e.g., "McClellan-Palomar Airport"). |
| **Elevation** | Field elevation in feet with thousands separators. |

The card is informational only - there's no editing here. Type a new ICAO into the field above to change the selection.

## REST API for airport lookup

Three endpoints under `/api/airports`. They use the same backing dictionary as the UI, so the data is identical.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/airports/lookup/{icao}` | GET | Fetch one airport by exact ICAO. Returns 404 if not found. |
| `/api/airports/search` | GET | Search by ICAO prefix or name substring. `?q=` (required), `?limit=` (default 10). |
| `/api/airports/list` | GET | Return every airport in the database. Useful for client-side filtering or for populating a UI dropdown once. |

All three require an authenticated session unless `BYPASS_AUTH=true`.

### Response shape

```json
{
  "airport": {
    "icao": "KCRQ",
    "name": "McClellan-Palomar Airport",
    "lat": 33.1283,
    "lon": -117.2803,
    "elevation_ft": 331
  }
}
```

The search endpoint returns `{"airports": [...]}` - same shape per entry, wrapped in a list.

## Search behavior - what matches what

| Query | Matches |
|-------|---------|
| `KCRQ` | Exact ICAO match. |
| `KCR` | All ICAOs starting with `KCR`. |
| `palomar` | Names containing "palomar" (case-insensitive). |
| `los` | ICAOs starting with `LOS` **and** names containing "los" (which is a lot). |
| Single character `K` | Up to `limit` airports whose ICAO starts with `K`. Useful for the picker's UX, ugly for batch work. |
| Empty string | Returns an empty list (the front end doesn't fire requests for empty queries anyway). |

For complex queries the right approach is `/api/airports/list` followed by client-side filtering.

## When ICAO lookup fails

| Cause | What you see |
|-------|--------------|
| Mistyped ICAO | 404 from `/api/airports/lookup/{icao}`. In the UI: the dropdown shows "No airports found." |
| Airport exists in the real world but not in the database | Same as mistyped. The database is curated, not exhaustive - if it's a niche airport, add it to `backend/airports.py` and rebuild. |
| Lower-case ICAO | The UI uppercases as you type; if you're hitting the API directly, send uppercase to match the dictionary keys. The lookup endpoint normalizes to uppercase internally. |

## Adding more airports

The data file is a Python dictionary literal. Append your entries and rebuild:

```python
# backend/airports.py
AIRPORTS = {
    "KLAX": ("Los Angeles International Airport", 33.9425, -118.4081, 125),
    ...
    "KMYAIRPORT": ("My Custom Airport", 12.3456, -78.9012, 1234),
}
```

After rebuild and redeploy, both the UI picker and the REST endpoints see the new entry. No restart of the database is needed because there is no database - the dict is loaded on import.

!!! tip "Coordinates and elevation conventions"
    Latitude and longitude are decimal degrees (north and east positive). Elevation is feet MSL. The simulator uses this elevation as the **initial altitude** when an airport is picked, so accuracy here matters - a wrong elevation means your aircraft starts buried in the runway or floating above it.

## How the picker handles multi-browser sync

When a second browser is open and the first browser picks an airport, the second browser's picker syncs:

1. Server-side state `airport_icao` updates.
2. The WebSocket broadcasts the new state.
3. The second browser's `useStatus` hook fires.
4. The `PositionInput` component's `useEffect` notices the changed `airportIcao` prop.
5. It calls `api.lookupAirport(icao)` to fetch the full record (name, elevation) and renders the card.

The picker is careful **not** to overwrite what the operator is currently typing - if you start typing in a browser while another browser changes the selection, your keystrokes win.

## Persistent state

| Setting | UI control | Env var | Survives restart? |
|---------|-----------|---------|-------------------|
| Selected airport | Picker | (no var directly) | No - per run. |
| Default lat / lon | Picker (or env vars at boot) | `DEFAULT_LAT`, `DEFAULT_LON` | Yes (env var) |
| Default altitude (from elevation) | Picker sets it on selection | `DEFAULT_ALT_FT` | Yes (env var, used at boot before any airport is picked) |

## What's next

- [Navigation Controls](navigation-controls.md) - how the picker plugs into altitude/airspeed/heading.
- [API Reference](../reference/api-reference.md) - full Swagger UI link for the `/api/airports/*` endpoints.
