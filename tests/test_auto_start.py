# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_auto_start.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 29th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for auto_start module."""

import pytest
from unittest.mock import Mock, patch

from backend.auto_start import (
    validate_auto_start_config,
    perform_auto_start,
    AutoStartError,
    VALID_MODES,
)


class TestValidModes:
    """Tests for VALID_MODES constant."""

    def test_valid_modes_contains_expected(self):
        """Should contain all expected modes."""
        assert "rebroadcaster" in VALID_MODES
        assert "sender" in VALID_MODES
        assert "receiver" in VALID_MODES
        assert "standalone" in VALID_MODES
        assert len(VALID_MODES) == 4


class TestValidateAutoStartConfig:
    """Tests for validate_auto_start_config function."""

    @patch("backend.auto_start.get_settings")
    def test_no_auto_start_mode(self, mock_get_settings):
        """Should return None when auto_start_mode is not set."""
        mock_settings = Mock()
        mock_settings.auto_start_mode = None
        mock_get_settings.return_value = mock_settings

        result = validate_auto_start_config()
        assert result is None

    @patch("backend.auto_start.get_settings")
    def test_invalid_mode(self, mock_get_settings):
        """Should return error for invalid mode."""
        mock_settings = Mock()
        mock_settings.auto_start_mode = "invalid_mode"
        mock_get_settings.return_value = mock_settings

        result = validate_auto_start_config()
        assert result is not None
        assert "Invalid AUTO_START_MODE" in result
        assert "invalid_mode" in result

    @patch("backend.auto_start.get_settings")
    def test_valid_mode_standalone(self, mock_get_settings):
        """Should return None for valid standalone mode."""
        mock_settings = Mock()
        mock_settings.auto_start_mode = "standalone"
        mock_settings.auto_start_efb_enabled = False
        mock_settings.auto_start_usb_enabled = False
        mock_settings.auto_start_udp_retransmit = False
        mock_get_settings.return_value = mock_settings

        result = validate_auto_start_config()
        assert result is None

    @patch("backend.auto_start.get_settings")
    def test_efb_enabled_no_broadcast_or_ips(self, mock_get_settings):
        """Should return error when EFB enabled but no broadcast or IPs."""
        mock_settings = Mock()
        mock_settings.auto_start_mode = "sender"
        mock_settings.auto_start_efb_enabled = True
        mock_settings.auto_start_efb_broadcast = False
        mock_settings.auto_start_efb_target_ips = None
        mock_get_settings.return_value = mock_settings

        result = validate_auto_start_config()
        assert result is not None
        assert "AUTO_START_EFB_ENABLED" in result

    @patch("backend.auto_start.get_settings")
    def test_efb_enabled_no_sim_name(self, mock_get_settings):
        """Should return error when EFB enabled but no sim name."""
        mock_settings = Mock()
        mock_settings.auto_start_mode = "sender"
        mock_settings.auto_start_efb_enabled = True
        mock_settings.auto_start_efb_broadcast = True
        mock_settings.auto_start_efb_target_ips = None
        mock_settings.auto_start_efb_sim_name = None
        mock_get_settings.return_value = mock_settings

        result = validate_auto_start_config()
        assert result is not None
        assert "AUTO_START_EFB_SIM_NAME" in result

    @patch("backend.auto_start.get_settings")
    def test_usb_enabled_no_device(self, mock_get_settings):
        """Should return error when USB enabled but no device."""
        mock_settings = Mock()
        mock_settings.auto_start_mode = "standalone"
        mock_settings.auto_start_efb_enabled = False
        mock_settings.auto_start_usb_enabled = True
        mock_settings.auto_start_usb_device = None
        mock_settings.auto_start_udp_retransmit = False
        mock_get_settings.return_value = mock_settings

        result = validate_auto_start_config()
        assert result is not None
        assert "AUTO_START_USB_DEVICE" in result

    @patch("backend.auto_start.get_settings")
    def test_udp_retransmit_no_ip(self, mock_get_settings):
        """Should return error when UDP retransmit enabled but no IP."""
        mock_settings = Mock()
        mock_settings.auto_start_mode = "rebroadcaster"
        mock_settings.auto_start_efb_enabled = False
        mock_settings.auto_start_usb_enabled = False
        mock_settings.auto_start_udp_retransmit = True
        mock_settings.auto_start_udp_retransmit_ip = None
        mock_get_settings.return_value = mock_settings

        result = validate_auto_start_config()
        assert result is not None
        assert "AUTO_START_UDP_RETRANSMIT_IP" in result

    @patch("backend.auto_start.get_settings")
    def test_valid_efb_with_broadcast(self, mock_get_settings):
        """Should return None for valid EFB config with broadcast."""
        mock_settings = Mock()
        mock_settings.auto_start_mode = "sender"
        mock_settings.auto_start_efb_enabled = True
        mock_settings.auto_start_efb_broadcast = True
        mock_settings.auto_start_efb_target_ips = None
        mock_settings.auto_start_efb_sim_name = "LOFT GPS"
        mock_settings.auto_start_usb_enabled = False
        mock_settings.auto_start_udp_retransmit = False
        mock_get_settings.return_value = mock_settings

        result = validate_auto_start_config()
        assert result is None

    @patch("backend.auto_start.get_settings")
    def test_valid_efb_with_target_ips(self, mock_get_settings):
        """Should return None for valid EFB config with target IPs."""
        mock_settings = Mock()
        mock_settings.auto_start_mode = "sender"
        mock_settings.auto_start_efb_enabled = True
        mock_settings.auto_start_efb_broadcast = False
        mock_settings.auto_start_efb_target_ips = "192.168.1.100"
        mock_settings.auto_start_efb_sim_name = "LOFT GPS"
        mock_settings.auto_start_usb_enabled = False
        mock_settings.auto_start_udp_retransmit = False
        mock_get_settings.return_value = mock_settings

        result = validate_auto_start_config()
        assert result is None


class TestPerformAutoStart:
    """Tests for perform_auto_start function."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings with defaults."""
        settings = Mock()
        settings.auto_start_mode = None
        settings.auto_start_listen_port = 12000
        settings.auto_start_protocol = "udp"
        settings.auto_start_efb_enabled = False
        settings.auto_start_efb_broadcast = False
        settings.auto_start_efb_target_ips = None
        settings.auto_start_efb_sim_name = "LOFT GPS"
        settings.auto_start_usb_enabled = False
        settings.auto_start_usb_device = None
        settings.auto_start_udp_retransmit = False
        settings.auto_start_udp_retransmit_ip = None
        settings.auto_start_udp_retransmit_port = 12001
        settings.serial_baudrate = 115200
        settings.default_lat = 33.0
        settings.default_lon = -117.0
        settings.default_alt_ft = 5000
        settings.default_airspeed_kts = 120
        settings.default_heading = 270
        return settings

    @pytest.mark.asyncio
    @patch("backend.auto_start.get_settings")
    async def test_no_auto_start_configured(self, mock_get_settings, mock_settings):
        """Should return False when no auto-start configured."""
        mock_settings.auto_start_mode = None
        mock_get_settings.return_value = mock_settings

        mock_loop = Mock()
        result = await perform_auto_start(mock_loop)

        assert result is False

    @pytest.mark.asyncio
    @patch("backend.auto_start.get_settings")
    async def test_invalid_config_raises_error(self, mock_get_settings, mock_settings):
        """Should raise AutoStartError for invalid config."""
        mock_settings.auto_start_mode = "invalid"
        mock_get_settings.return_value = mock_settings

        mock_loop = Mock()
        with pytest.raises(AutoStartError) as exc_info:
            await perform_auto_start(mock_loop)

        assert "Invalid AUTO_START_MODE" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("backend.auto_start.get_ws_manager")
    @patch("backend.auto_start.get_emulator")
    @patch("backend.auto_start.get_app_state")
    @patch("backend.auto_start.get_settings")
    async def test_standalone_mode(
        self,
        mock_get_settings,
        mock_get_state,
        mock_get_emulator,
        mock_get_ws,
        mock_settings,
    ):
        """Should start standalone mode correctly."""
        mock_settings.auto_start_mode = "standalone"
        mock_get_settings.return_value = mock_settings

        mock_state = Mock()
        mock_state.modes = Mock()
        mock_state.network = Mock()
        mock_state.serial = Mock()
        mock_get_state.return_value = mock_state

        mock_emulator = Mock()
        mock_get_emulator.return_value = mock_emulator

        mock_ws = Mock()
        mock_get_ws.return_value = mock_ws

        mock_loop = Mock()
        result = await perform_auto_start(mock_loop)

        assert result is True
        assert mock_state.modes.standalone is True
        mock_emulator.set_ws_manager.assert_called_once_with(mock_ws, mock_loop)
        mock_emulator.start.assert_called_once()
        assert mock_state.is_running is True

    @pytest.mark.asyncio
    @patch("backend.auto_start.get_ws_manager")
    @patch("backend.auto_start.get_emulator")
    @patch("backend.auto_start.get_app_state")
    @patch("backend.auto_start.get_settings")
    async def test_sender_mode(
        self,
        mock_get_settings,
        mock_get_state,
        mock_get_emulator,
        mock_get_ws,
        mock_settings,
    ):
        """Should start sender mode correctly."""
        mock_settings.auto_start_mode = "sender"
        mock_get_settings.return_value = mock_settings

        mock_state = Mock()
        mock_state.modes = Mock()
        mock_state.network = Mock()
        mock_state.serial = Mock()
        mock_get_state.return_value = mock_state

        mock_emulator = Mock()
        mock_get_emulator.return_value = mock_emulator

        mock_ws = Mock()
        mock_get_ws.return_value = mock_ws

        mock_loop = Mock()
        result = await perform_auto_start(mock_loop)

        assert result is True
        assert mock_state.modes.sender is True
        mock_emulator.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.auto_start.get_ws_manager")
    @patch("backend.auto_start.get_emulator")
    @patch("backend.auto_start.get_app_state")
    @patch("backend.auto_start.get_settings")
    async def test_sender_mode_with_efb(
        self,
        mock_get_settings,
        mock_get_state,
        mock_get_emulator,
        mock_get_ws,
        mock_settings,
    ):
        """Should start sender mode with EFB config."""
        mock_settings.auto_start_mode = "sender"
        mock_settings.auto_start_efb_enabled = True
        mock_settings.auto_start_efb_broadcast = True
        mock_settings.auto_start_efb_sim_name = "TestSim"
        mock_settings.auto_start_efb_target_ips = "192.168.1.100"
        mock_get_settings.return_value = mock_settings

        mock_state = Mock()
        mock_state.modes = Mock()
        mock_state.network = Mock()
        mock_state.serial = Mock()
        mock_get_state.return_value = mock_state

        mock_emulator = Mock()
        mock_get_emulator.return_value = mock_emulator

        mock_ws = Mock()
        mock_get_ws.return_value = mock_ws

        mock_loop = Mock()

        with patch("backend.network.foreflight.parse_ip_list") as mock_parse:
            mock_parse.return_value = ["192.168.1.100"]
            result = await perform_auto_start(mock_loop)

        assert result is True
        # Check that emulator.start was called with foreflight_config
        call_kwargs = mock_emulator.start.call_args[1]
        assert call_kwargs["foreflight_config"] is not None
        assert call_kwargs["foreflight_config"]["sim_name"] == "TestSim"

    @pytest.mark.asyncio
    @patch("backend.auto_start.get_ws_manager")
    @patch("backend.auto_start.get_receiver_runner")
    @patch("backend.auto_start.get_app_state")
    @patch("backend.auto_start.get_settings")
    async def test_receiver_mode(
        self,
        mock_get_settings,
        mock_get_state,
        mock_get_runner,
        mock_get_ws,
        mock_settings,
    ):
        """Should start receiver mode correctly."""
        mock_settings.auto_start_mode = "receiver"
        mock_get_settings.return_value = mock_settings

        mock_state = Mock()
        mock_state.modes = Mock()
        mock_state.network = Mock()
        mock_state.serial = Mock()
        mock_get_state.return_value = mock_state

        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        mock_ws = Mock()
        mock_get_ws.return_value = mock_ws

        mock_loop = Mock()
        result = await perform_auto_start(mock_loop)

        assert result is True
        assert mock_state.modes.receiver is True
        mock_runner.set_ws_manager.assert_called_once_with(mock_ws, mock_loop)
        mock_runner.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.auto_start.get_ws_manager")
    @patch("backend.auto_start.get_rebroadcaster_runner")
    @patch("backend.auto_start.get_app_state")
    @patch("backend.auto_start.get_settings")
    async def test_rebroadcaster_mode(
        self,
        mock_get_settings,
        mock_get_state,
        mock_get_runner,
        mock_get_ws,
        mock_settings,
    ):
        """Should start rebroadcaster mode correctly."""
        mock_settings.auto_start_mode = "rebroadcaster"
        mock_get_settings.return_value = mock_settings

        mock_state = Mock()
        mock_state.modes = Mock()
        mock_state.network = Mock()
        mock_state.serial = Mock()
        mock_get_state.return_value = mock_state

        mock_runner = Mock()
        mock_get_runner.return_value = mock_runner

        mock_ws = Mock()
        mock_get_ws.return_value = mock_ws

        mock_loop = Mock()
        result = await perform_auto_start(mock_loop)

        assert result is True
        assert mock_state.modes.rebroadcaster is True
        assert mock_state.modes.receiver is True  # rebroadcaster implies receiver
        mock_runner.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.auto_start.get_ws_manager")
    @patch("backend.auto_start.get_emulator")
    @patch("backend.auto_start.get_app_state")
    @patch("backend.auto_start.get_settings")
    async def test_start_failure_raises_error(
        self,
        mock_get_settings,
        mock_get_state,
        mock_get_emulator,
        mock_get_ws,
        mock_settings,
    ):
        """Should raise AutoStartError when start fails."""
        mock_settings.auto_start_mode = "standalone"
        mock_get_settings.return_value = mock_settings

        mock_state = Mock()
        mock_state.modes = Mock()
        mock_state.network = Mock()
        mock_state.serial = Mock()
        mock_get_state.return_value = mock_state

        mock_emulator = Mock()
        mock_emulator.start.side_effect = Exception("Serial port not found")
        mock_get_emulator.return_value = mock_emulator

        mock_ws = Mock()
        mock_get_ws.return_value = mock_ws

        mock_loop = Mock()
        with pytest.raises(AutoStartError) as exc_info:
            await perform_auto_start(mock_loop)

        assert "Failed to auto-start standalone mode" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("backend.auto_start.get_ws_manager")
    @patch("backend.auto_start.get_emulator")
    @patch("backend.auto_start.get_app_state")
    @patch("backend.auto_start.get_settings")
    async def test_usb_enabled_sets_device(
        self,
        mock_get_settings,
        mock_get_state,
        mock_get_emulator,
        mock_get_ws,
        mock_settings,
    ):
        """Should set serial device when USB enabled."""
        mock_settings.auto_start_mode = "standalone"
        mock_settings.auto_start_usb_enabled = True
        mock_settings.auto_start_usb_device = "/dev/ttyUSB0"
        mock_get_settings.return_value = mock_settings

        mock_state = Mock()
        mock_state.modes = Mock()
        mock_state.network = Mock()
        mock_state.serial = Mock()
        mock_get_state.return_value = mock_state

        mock_emulator = Mock()
        mock_get_emulator.return_value = mock_emulator

        mock_ws = Mock()
        mock_get_ws.return_value = mock_ws

        mock_loop = Mock()
        result = await perform_auto_start(mock_loop)

        assert result is True
        assert mock_state.serial.device == "/dev/ttyUSB0"
        assert mock_state.modes.usb_output is True
