# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# auto_start.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 28th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Auto-start functionality for preconfigured operation modes."""

import asyncio
import logging
from typing import Optional

from .config import get_settings
from .state import get_app_state
from .rebroadcaster_runner import get_rebroadcaster_runner
from .receiver_runner import get_receiver_runner
from .emulator import get_emulator
from .websocket_manager import get_ws_manager

logger = logging.getLogger(__name__)

VALID_MODES = {"rebroadcaster", "sender", "receiver", "standalone"}


class AutoStartError(Exception):
    """Raised when auto-start configuration is invalid."""

    pass


def validate_auto_start_config() -> Optional[str]:
    """Validate auto-start configuration.

    Returns:
        None if valid, error message string if invalid
    """
    settings = get_settings()

    if not settings.auto_start_mode:
        return None  # Auto-start not enabled, nothing to validate

    mode = settings.auto_start_mode.lower()

    if mode not in VALID_MODES:
        return f"Invalid AUTO_START_MODE '{settings.auto_start_mode}'. Must be one of: {', '.join(sorted(VALID_MODES))}"

    # Validate EFB settings if enabled
    if settings.auto_start_efb_enabled:
        if (
            not settings.auto_start_efb_broadcast
            and not settings.auto_start_efb_target_ips
        ):
            return "AUTO_START_EFB_ENABLED is true but neither AUTO_START_EFB_BROADCAST nor AUTO_START_EFB_TARGET_IPS is set"

        if not settings.auto_start_efb_sim_name:
            return (
                "AUTO_START_EFB_ENABLED is true but AUTO_START_EFB_SIM_NAME is not set"
            )

    # Validate USB settings if enabled
    if settings.auto_start_usb_enabled and not settings.auto_start_usb_device:
        return "AUTO_START_USB_ENABLED is true but AUTO_START_USB_DEVICE is not set"

    # Validate UDP retransmit settings if enabled
    if settings.auto_start_udp_retransmit and not settings.auto_start_udp_retransmit_ip:
        return "AUTO_START_UDP_RETRANSMIT is true but AUTO_START_UDP_RETRANSMIT_IP is not set"

    return None


async def perform_auto_start(event_loop: asyncio.AbstractEventLoop) -> bool:
    """Perform auto-start if configured.

    Args:
        event_loop: The asyncio event loop for WebSocket broadcasts

    Returns:
        True if auto-start was performed, False if not configured

    Raises:
        AutoStartError: If configuration is invalid
    """
    settings = get_settings()

    if not settings.auto_start_mode:
        logger.info("Auto-start not configured (AUTO_START_MODE not set)")
        return False

    # Validate configuration
    error = validate_auto_start_config()
    if error:
        logger.error(f"Auto-start configuration error: {error}")
        raise AutoStartError(error)

    mode = settings.auto_start_mode.lower()
    logger.info(f"Auto-start enabled for mode: {mode}")

    # Get state and configure it
    state = get_app_state()

    # Set operating mode
    # Note: rebroadcaster requires receiver to also be true (UI shows rebroadcaster as sub-option of receiver)
    state.modes.standalone = mode == "standalone"
    state.modes.sender = mode == "sender"
    state.modes.receiver = mode == "receiver" or mode == "rebroadcaster"
    state.modes.rebroadcaster = mode == "rebroadcaster"

    # Configure network settings
    state.network.port = settings.auto_start_listen_port
    state.network.protocol = settings.auto_start_protocol

    # Configure EFB settings
    state.network.efb_enabled = settings.auto_start_efb_enabled
    state.network.foreflight_broadcast = settings.auto_start_efb_broadcast
    state.network.efb_ip_enabled = bool(settings.auto_start_efb_target_ips)
    state.network.efb_target_ips = settings.auto_start_efb_target_ips
    state.network.foreflight_sim_name = settings.auto_start_efb_sim_name

    # Configure USB output - only set device if USB is enabled
    state.modes.usb_output = settings.auto_start_usb_enabled
    if settings.auto_start_usb_enabled and settings.auto_start_usb_device:
        state.serial.device = settings.auto_start_usb_device
    else:
        state.serial.device = None

    # Configure UDP retransmit (rebroadcaster only)
    state.network.rebroadcast_udp = settings.auto_start_udp_retransmit
    state.network.rebroadcast_udp_ip = settings.auto_start_udp_retransmit_ip
    state.network.rebroadcast_udp_port = settings.auto_start_udp_retransmit_port
    state.network.rebroadcast_usb = settings.auto_start_usb_enabled

    # Build enabled sentences (default: GPGGA and GPRMC)
    enabled_sentences = {"GPGGA", "GPRMC"}

    # Get WebSocket manager
    ws_manager = get_ws_manager()

    # Start the appropriate runner
    try:
        if mode == "rebroadcaster":
            runner = get_rebroadcaster_runner()
            runner.set_ws_manager(ws_manager, event_loop)
            runner.start(
                port=settings.auto_start_listen_port,
                rebroadcast_usb=settings.auto_start_usb_enabled,
                serial_device=settings.auto_start_usb_device,
                baudrate=settings.serial_baudrate,
                enabled_sentences=enabled_sentences,
                efb_enabled=settings.auto_start_efb_enabled,
                foreflight_broadcast=settings.auto_start_efb_broadcast,
                efb_ip_enabled=bool(settings.auto_start_efb_target_ips),
                efb_target_ips=settings.auto_start_efb_target_ips,
                foreflight_sim_name=settings.auto_start_efb_sim_name or "LOFT GPS",
                rebroadcast_udp=settings.auto_start_udp_retransmit,
                rebroadcast_udp_ip=settings.auto_start_udp_retransmit_ip,
                rebroadcast_udp_port=settings.auto_start_udp_retransmit_port,
            )
            state.is_running = True
            logger.info(
                f"Auto-started rebroadcaster on port {settings.auto_start_listen_port}"
            )

        elif mode == "receiver":
            runner = get_receiver_runner()
            runner.set_ws_manager(ws_manager, event_loop)
            runner.start(
                port=settings.auto_start_listen_port,
                protocol=settings.auto_start_protocol,
                serial_device=settings.auto_start_usb_device
                if settings.auto_start_usb_enabled
                else None,
                enabled_sentences=enabled_sentences,
                baudrate=settings.serial_baudrate,
            )
            state.is_running = True
            logger.info(
                f"Auto-started receiver on port {settings.auto_start_listen_port}"
            )

        elif mode == "sender":
            emulator = get_emulator()
            emulator.set_ws_manager(ws_manager, event_loop)

            # Configure EFB for sender mode
            foreflight_config = None
            if settings.auto_start_efb_enabled:
                from .network.foreflight import parse_ip_list

                target_ips = []
                if settings.auto_start_efb_target_ips:
                    target_ips = parse_ip_list(settings.auto_start_efb_target_ips)

                foreflight_config = {
                    "sim_name": settings.auto_start_efb_sim_name or "LOFT GPS",
                    "broadcast": settings.auto_start_efb_broadcast,
                    "target_ips": target_ips,
                }

            emulator.start(
                lat=settings.default_lat,
                lon=settings.default_lon,
                altitude_ft=settings.default_alt_ft,
                speed_kts=settings.default_airspeed_kts,
                heading=settings.default_heading,
                serial_device=settings.auto_start_usb_device
                if settings.auto_start_usb_enabled
                else None,
                enabled_sentences=enabled_sentences,
                foreflight_config=foreflight_config,
                baudrate=settings.serial_baudrate,
            )
            state.is_running = True
            logger.info("Auto-started sender mode")

        elif mode == "standalone":
            emulator = get_emulator()
            emulator.set_ws_manager(ws_manager, event_loop)
            emulator.start(
                lat=settings.default_lat,
                lon=settings.default_lon,
                altitude_ft=settings.default_alt_ft,
                speed_kts=settings.default_airspeed_kts,
                heading=settings.default_heading,
                serial_device=settings.auto_start_usb_device,
                enabled_sentences=enabled_sentences,
                baudrate=settings.serial_baudrate,
            )
            state.is_running = True
            logger.info("Auto-started standalone mode")

        return True

    except Exception as e:
        logger.error(f"Auto-start failed: {e}")
        raise AutoStartError(f"Failed to auto-start {mode} mode: {e}")
