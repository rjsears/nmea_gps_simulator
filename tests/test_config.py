# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_config.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for configuration module."""

import os


def test_config_loads_defaults():
    """Config should have default values."""
    # Clear env vars to test defaults
    env_backup = {}
    for key in ["USERNAME", "PASSWORD", "DEFAULT_LAT", "DEFAULT_LON"]:
        env_backup[key] = os.environ.pop(key, None)

    # Re-import to get fresh config
    import importlib
    from backend import config

    importlib.reload(config)

    settings = config.get_settings()

    assert settings.default_lat == 33.1283
    assert settings.default_lon == -117.2803
    assert settings.default_alt_ft == 0
    assert settings.default_airspeed_kts == 0
    assert settings.default_heading == 360
    assert settings.altitude_rate_ft_per_2sec == 1000
    assert settings.airspeed_rate_kts_per_sec == 30
    assert settings.heading_rate_deg_per_sec == 3

    # Restore env vars
    for key, val in env_backup.items():
        if val is not None:
            os.environ[key] = val


def test_config_loads_from_env():
    """Config should load values from environment variables."""
    os.environ["USERNAME"] = "testuser"
    os.environ["PASSWORD"] = "testpass"
    os.environ["DEFAULT_LAT"] = "40.7128"

    import importlib
    from backend import config

    importlib.reload(config)

    settings = config.get_settings()

    assert settings.username == "testuser"
    assert settings.password == "testpass"
    assert settings.default_lat == 40.7128

    # Cleanup
    del os.environ["USERNAME"]
    del os.environ["PASSWORD"]
    del os.environ["DEFAULT_LAT"]
