# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# control_routes.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Control API routes (start/stop, position updates)."""

import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..models import ControlRequest, PositionUpdate, StatusResponse
from ..state import get_app_state
from ..emulator import get_emulator
from ..receiver_runner import get_receiver_runner
from ..rebroadcaster_runner import get_rebroadcaster_runner
from ..websocket_manager import get_ws_manager
from ..network.foreflight import parse_ip_list

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["control"])


@router.get("/status", response_model=StatusResponse)
async def get_status(user: str = Depends(get_current_user)) -> StatusResponse:
    """Get current emulator status."""
    state = get_app_state()
    emulator = get_emulator()
    receiver = get_receiver_runner()
    rebroadcaster = get_rebroadcaster_runner()

    # Update state from emulator if running
    if emulator.is_running:
        engine_state = emulator.get_current_state()
        if engine_state:
            state.lat = engine_state["lat"]
            state.lon = engine_state["lon"]
            state.altitude_ft = engine_state["altitude_ft"]
            state.speed_kts = engine_state["speed_kts"]
            state.heading = engine_state["heading"]
            # Also sync target values for multi-browser support
            state.target_altitude_ft = engine_state.get(
                "target_altitude_ft", state.target_altitude_ft
            )
            state.target_speed_kts = engine_state.get(
                "target_speed_kts", state.target_speed_kts
            )
            state.target_heading = engine_state.get(
                "target_heading", state.target_heading
            )

    # Check receiver connection status and update state from receiver engine
    if receiver.is_running:
        state.is_running = True
        # Store receiver reference so to_status_response can check connection
        state.receiver = receiver._receiver
        logger.info(
            f"Receiver running, _receiver={receiver._receiver}, is_connected={receiver._receiver.state.is_connected if receiver._receiver else 'N/A'}"
        )
        # Update state from receiver's engine (populated by received packets)
        if receiver._engine:
            engine_state = receiver._engine.get_state()
            logger.info(f"Receiver engine state: {engine_state}")
            if engine_state:
                state.lat = engine_state["lat"]
                state.lon = engine_state["lon"]
                state.altitude_ft = engine_state["altitude_ft"]
                state.speed_kts = engine_state["speed_kts"]
                state.heading = engine_state["heading"]
                # Also sync target values
                state.target_altitude_ft = engine_state.get(
                    "target_altitude_ft", state.target_altitude_ft
                )
                state.target_speed_kts = engine_state.get(
                    "target_speed_kts", state.target_speed_kts
                )
                state.target_heading = engine_state.get(
                    "target_heading", state.target_heading
                )
        else:
            logger.warning("Receiver running but no engine!")

    # Check rebroadcaster connection status and update state from rebroadcaster engine
    if rebroadcaster.is_running:
        state.is_running = True
        # Store receiver reference so to_status_response can check connection
        state.receiver = rebroadcaster._receiver
        logger.info(
            f"Rebroadcaster running, _receiver={rebroadcaster._receiver}, is_connected={rebroadcaster._receiver.state.is_connected if rebroadcaster._receiver else 'N/A'}"
        )
        # Update state from rebroadcaster's engine (populated by received packets)
        if rebroadcaster._engine:
            engine_state = rebroadcaster._engine.get_state()
            logger.info(f"Rebroadcaster engine state: {engine_state}")
            if engine_state:
                state.lat = engine_state["lat"]
                state.lon = engine_state["lon"]
                state.altitude_ft = engine_state["altitude_ft"]
                state.speed_kts = engine_state["speed_kts"]
                state.heading = engine_state["heading"]
                # Also sync target values
                state.target_altitude_ft = engine_state.get(
                    "target_altitude_ft", state.target_altitude_ft
                )
                state.target_speed_kts = engine_state.get(
                    "target_speed_kts", state.target_speed_kts
                )
                state.target_heading = engine_state.get(
                    "target_heading", state.target_heading
                )
        else:
            logger.warning("Rebroadcaster running but no engine!")

    return state.to_status_response()


@router.post("/control")
async def control(
    request: ControlRequest,
    user: str = Depends(get_current_user),
) -> dict:
    """Start or stop the emulator."""
    state = get_app_state()
    emulator = get_emulator()
    receiver = get_receiver_runner()
    rebroadcaster = get_rebroadcaster_runner()

    if request.action == "start":
        # Check if already running
        if emulator.is_running or receiver.is_running or rebroadcaster.is_running:
            return {"success": True, "message": "Already running"}

        # Build set of enabled NMEA sentences
        enabled = set()
        if state.nmea.gpgga:
            enabled.add("GPGGA")
        if state.nmea.gprmc:
            enabled.add("GPRMC")
        if state.nmea.gpgll:
            enabled.add("GPGLL")
        if state.nmea.gpgsa:
            enabled.add("GPGSA")
        if state.nmea.gpgsv:
            enabled.add("GPGSV")
        if state.nmea.gphdt:
            enabled.add("GPHDT")
        if state.nmea.gpvtg:
            enabled.add("GPVTG")
        if state.nmea.gpzda:
            enabled.add("GPZDA")

        # Determine if we need serial output
        # USB output is needed if usb_output mode is enabled
        needs_serial = state.modes.usb_output
        serial_device = state.serial.device if needs_serial else None

        try:
            ws_manager = get_ws_manager()
            event_loop = asyncio.get_event_loop()

            if state.modes.rebroadcaster:
                # Rebroadcaster mode: listen for GPS data and rebroadcast to multiple outputs
                rebroadcaster.set_ws_manager(ws_manager, event_loop)
                rebroadcaster.start(
                    port=state.network.port,
                    rebroadcast_usb=state.network.rebroadcast_usb,
                    serial_device=state.serial.device
                    if state.network.rebroadcast_usb
                    else None,
                    baudrate=state.serial.baudrate,
                    enabled_sentences=enabled,
                    efb_enabled=state.network.efb_enabled,
                    foreflight_broadcast=state.network.foreflight_broadcast,
                    efb_ip_enabled=state.network.efb_ip_enabled,
                    efb_target_ips=state.network.efb_target_ips,
                    foreflight_sim_name=state.network.foreflight_sim_name or "LOFT GPS",
                    rebroadcast_udp=state.network.rebroadcast_udp,
                    rebroadcast_udp_ip=state.network.rebroadcast_udp_ip,
                    rebroadcast_udp_port=state.network.rebroadcast_udp_port,
                )
                state.is_running = True
                logger.info(f"Rebroadcaster started - port: {state.network.port}")
                return {"success": True, "message": "Rebroadcaster started"}
            elif state.modes.receiver:
                # Receiver mode: listen for incoming GPS data and output NMEA
                receiver.set_ws_manager(ws_manager, event_loop)
                receiver.start(
                    port=state.network.port,
                    protocol=state.network.protocol,
                    serial_device=serial_device,
                    enabled_sentences=enabled,
                    baudrate=state.serial.baudrate,
                )
                state.is_running = True
                logger.info(
                    f"Receiver started - port: {state.network.port}, protocol: {state.network.protocol}, serial: {serial_device}"
                )
                return {"success": True, "message": "Receiver started"}
            else:
                # Standalone or Sender mode: generate NMEA from local position
                emulator.set_ws_manager(ws_manager, event_loop)

                # Configure network sender if in sender mode with NMEA output enabled
                sender_config = None
                if (
                    state.modes.sender
                    and state.network.target_ip
                    and state.network.nmea_output
                ):
                    sender_config = {
                        "target_ip": state.network.target_ip,
                        "port": state.network.port,
                        "protocol": state.network.protocol,
                        "nmea_output": state.network.nmea_output,
                    }

                # Configure EFB (ForeFlight/Garmin Pilot) sender if enabled
                # Works for both sender and standalone modes
                foreflight_config = None
                efb_enabled = state.network.efb_enabled
                foreflight_broadcast = state.network.foreflight_broadcast
                efb_ip_enabled = state.network.efb_ip_enabled
                efb_target_ips = state.network.efb_target_ips

                if efb_enabled and (foreflight_broadcast or efb_ip_enabled):
                    # Parse IPs/ranges for EFB targets
                    target_ips = []
                    if efb_ip_enabled and efb_target_ips:
                        target_ips = parse_ip_list(efb_target_ips)

                    foreflight_config = {
                        "sim_name": state.network.foreflight_sim_name or "LOFT GPS",
                        "broadcast": foreflight_broadcast,
                        "target_ips": target_ips,
                    }

                emulator.start(
                    lat=state.lat,
                    lon=state.lon,
                    altitude_ft=state.altitude_ft,
                    speed_kts=state.speed_kts,
                    heading=state.heading,
                    serial_device=serial_device,
                    enabled_sentences=enabled,
                    sender_config=sender_config,
                    foreflight_config=foreflight_config,
                    baudrate=state.serial.baudrate,
                )
                state.is_running = True
                # Store sender reference for status display
                if sender_config:
                    state.sender = emulator._sender
                logger.info(
                    f"Emulator started - serial: {serial_device}, sender: {sender_config}, sentences: {enabled}"
                )
                return {"success": True, "message": "Emulator started"}

        except Exception as e:
            logger.error(f"Failed to start: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    else:  # stop
        if rebroadcaster.is_running:
            rebroadcaster.stop()
        if receiver.is_running:
            receiver.stop()
        if emulator.is_running:
            emulator.stop()
        state.is_running = False
        logger.info("Stopped")
        return {"success": True, "message": "Stopped"}


@router.post("/position")
async def update_position(
    update: PositionUpdate,
    user: str = Depends(get_current_user),
) -> dict:
    """Update GPS position or target values."""
    state = get_app_state()
    emulator = get_emulator()

    # Update targets in emulator if running
    if emulator.is_running:
        if update.altitude_ft is not None:
            emulator.set_target_altitude(update.altitude_ft)
        if update.speed_kts is not None:
            emulator.set_target_speed(update.speed_kts)
        if update.heading is not None:
            emulator.set_target_heading(update.heading)

    # Update state values (used when starting emulator)
    state.set_position(
        lat=update.lat,
        lon=update.lon,
        altitude_ft=update.altitude_ft,
        speed_kts=update.speed_kts,
        heading=update.heading,
        airport_icao=update.airport_icao,
    )

    # Also update targets for gradual transitions
    state.set_targets(
        altitude_ft=update.altitude_ft,
        speed_kts=update.speed_kts,
        heading=update.heading,
    )

    return {"success": True}
