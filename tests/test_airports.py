# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_airports.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for airport lookup functions."""

from backend.airports import lookup_airport, search_airports, list_all_airports


class TestLookupAirport:
    """Tests for lookup_airport function."""

    def test_lookup_valid_airport(self):
        """Should return airport data for valid ICAO code."""
        result = lookup_airport("KLAX")
        assert result is not None
        assert result["icao"] == "KLAX"
        assert result["name"] == "Los Angeles International"
        assert "lat" in result
        assert "lon" in result
        assert "elevation_ft" in result

    def test_lookup_lowercase(self):
        """Should handle lowercase ICAO codes."""
        result = lookup_airport("klax")
        assert result is not None
        assert result["icao"] == "KLAX"

    def test_lookup_with_whitespace(self):
        """Should handle whitespace in input."""
        result = lookup_airport("  KLAX  ")
        assert result is not None
        assert result["icao"] == "KLAX"

    def test_lookup_invalid_airport(self):
        """Should return None for invalid ICAO code."""
        result = lookup_airport("XXXX")
        assert result is None

    def test_lookup_empty_string(self):
        """Should return None for empty string."""
        result = lookup_airport("")
        assert result is None


class TestSearchAirports:
    """Tests for search_airports function."""

    def test_search_by_icao(self):
        """Should find airports by ICAO code."""
        results = search_airports("LAX")
        assert len(results) > 0
        assert any(r["icao"] == "KLAX" for r in results)

    def test_search_by_name(self):
        """Should find airports by name."""
        results = search_airports("Los Angeles")
        assert len(results) > 0
        assert any("Los Angeles" in r["name"] for r in results)

    def test_search_case_insensitive(self):
        """Should search case-insensitively."""
        results = search_airports("los angeles")
        assert len(results) > 0

    def test_search_limit(self):
        """Should respect limit parameter."""
        results = search_airports("K", limit=5)
        assert len(results) <= 5

    def test_search_no_results(self):
        """Should return empty list for no matches."""
        results = search_airports("ZZZZZZZ")
        assert results == []

    def test_search_results_sorted(self):
        """Should return results sorted by ICAO code."""
        results = search_airports("International", limit=20)
        if len(results) > 1:
            icaos = [r["icao"] for r in results]
            assert icaos == sorted(icaos)


class TestListAllAirports:
    """Tests for list_all_airports function."""

    def test_returns_all_airports(self):
        """Should return all airports."""
        results = list_all_airports()
        assert len(results) > 50  # We have many airports

    def test_airports_have_required_fields(self):
        """Each airport should have required fields."""
        results = list_all_airports()
        for airport in results:
            assert "icao" in airport
            assert "name" in airport
            assert "lat" in airport
            assert "lon" in airport
            assert "elevation_ft" in airport

    def test_results_sorted_by_icao(self):
        """Should return airports sorted by ICAO code."""
        results = list_all_airports()
        icaos = [r["icao"] for r in results]
        assert icaos == sorted(icaos)
