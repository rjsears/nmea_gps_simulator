# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_auth.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for authentication module."""

from unittest.mock import patch

from backend.auth import (
    verify_credentials,
    create_session,
    delete_session,
    get_session_user,
)


class TestVerifyCredentials:
    """Tests for credential verification."""

    def test_valid_credentials(self):
        with patch("backend.auth.get_settings") as mock_settings:
            mock_settings.return_value.username = "admin"
            mock_settings.return_value.password = "secret"

            assert verify_credentials("admin", "secret") is True

    def test_invalid_username(self):
        with patch("backend.auth.get_settings") as mock_settings:
            mock_settings.return_value.username = "admin"
            mock_settings.return_value.password = "secret"

            assert verify_credentials("wrong", "secret") is False

    def test_invalid_password(self):
        with patch("backend.auth.get_settings") as mock_settings:
            mock_settings.return_value.username = "admin"
            mock_settings.return_value.password = "secret"

            assert verify_credentials("admin", "wrong") is False


class TestSession:
    """Tests for session management."""

    def test_create_session(self):
        token = create_session("admin")
        assert isinstance(token, str)
        assert len(token) > 20  # Should be a substantial token

    def test_session_stored(self):
        from backend.auth import _sessions

        token = create_session("testuser")
        assert token in _sessions
        assert _sessions[token] == "testuser"

    def test_get_session_user(self):
        token = create_session("myuser")
        assert get_session_user(token) == "myuser"

    def test_get_session_user_invalid(self):
        assert get_session_user("invalid_token") is None

    def test_delete_session(self):
        token = create_session("deleteuser")
        delete_session(token)
        assert get_session_user(token) is None
