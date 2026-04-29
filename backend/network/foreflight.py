# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# foreflight.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 27th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""EFB (ForeFlight/Garmin Pilot) GPS data sender.

Sends XGPS position data to EFB apps on UDP port 49002.
Format: XGPSSimName,longitude,latitude,altitude_m,track,groundspeed_ms

- ForeFlight: receives via broadcast
- Garmin Pilot: receives via specific IP address

Reference: ForeFlight Simulator GPS Integration
"""

import socket
import logging

logger = logging.getLogger(__name__)

# EFB constants
EFB_PORT = 49002


def parse_ip_list(ip_string: str) -> list[str]:
    """Parse comma-separated IP addresses and ranges into a list of individual IPs.

    Supports formats:
    - Single IP: 10.200.50.3
    - Multiple IPs: 10.200.50.3, 10.200.50.4
    - IP range: 10.200.50.10-10.200.50.20
    - Mixed: 10.200.50.3, 10.200.50.10-10.200.50.20

    Args:
        ip_string: Comma-separated string of IPs and/or ranges

    Returns:
        List of individual IP addresses
    """
    if not ip_string:
        return []

    result = []
    parts = [p.strip() for p in ip_string.split(",") if p.strip()]

    for part in parts:
        if "-" in part and not part.startswith("-"):
            # This is a range like 10.200.50.10-10.200.50.20
            try:
                start_ip, end_ip = part.split("-", 1)
                start_ip = start_ip.strip()
                end_ip = end_ip.strip()

                # Parse the IPs into octets
                start_octets = [int(o) for o in start_ip.split(".")]
                end_octets = [int(o) for o in end_ip.split(".")]

                if len(start_octets) != 4 or len(end_octets) != 4:
                    logger.warning(f"Invalid IP range format: {part}")
                    continue

                # Convert to integers for comparison
                start_int = (
                    (start_octets[0] << 24)
                    + (start_octets[1] << 16)
                    + (start_octets[2] << 8)
                    + start_octets[3]
                )
                end_int = (
                    (end_octets[0] << 24)
                    + (end_octets[1] << 16)
                    + (end_octets[2] << 8)
                    + end_octets[3]
                )

                if end_int < start_int:
                    logger.warning(f"Invalid IP range (end < start): {part}")
                    continue

                # Generate all IPs in range
                for ip_int in range(start_int, end_int + 1):
                    ip = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
                    result.append(ip)

            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse IP range '{part}': {e}")
                continue
        else:
            # Single IP address
            result.append(part)

    logger.info(f"Parsed IP list: {len(result)} addresses from '{ip_string}'")
    return result


# Conversion factors
FEET_TO_METERS = 0.3048
KNOTS_TO_MS = 0.514444


class EFBSender:
    """Sends GPS position data to EFB apps (ForeFlight/Garmin Pilot) via UDP.

    Supports sending to multiple destinations simultaneously:
    - Broadcast for ForeFlight
    - Specific IP addresses for Garmin Pilot
    """

    def __init__(
        self,
        sim_name: str = "LOFT GPS",
        broadcast: bool = False,
        target_ips: list[str] | None = None,
    ):
        """Initialize EFB sender.

        Args:
            sim_name: Simulator name shown in EFB app (e.g., "CL350", "ULTRA")
            broadcast: If True, send to broadcast address (ForeFlight)
            target_ips: List of specific IP addresses (Garmin Pilot)
        """
        self.sim_name = sim_name
        self.broadcast = broadcast
        self.target_ips = target_ips or []
        self._socket: socket.socket | None = None
        self._setup_socket()

    def _setup_socket(self) -> None:
        """Create UDP socket, configured for broadcast if needed."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.broadcast:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        destinations = []
        if self.broadcast:
            destinations.append("broadcast")
        if self.target_ips:
            destinations.extend(self.target_ips)
        logger.info(
            f"EFB sender initialized: sim_name='{self.sim_name}', destinations={destinations}"
        )

    def create_xgps_message(
        self,
        lat: float,
        lon: float,
        altitude_ft: float,
        heading: float,
        speed_kts: float,
    ) -> str:
        """Create XGPS message for EFB apps.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            altitude_ft: Altitude in feet MSL
            heading: Track over ground in degrees true
            speed_kts: Ground speed in knots

        Returns:
            XGPS message string
        """
        # Convert units
        altitude_m = altitude_ft * FEET_TO_METERS
        speed_ms = speed_kts * KNOTS_TO_MS

        # Normalize heading
        track = heading % 360

        # Format: XGPSSimName,lon,lat,alt_m,track,speed_ms
        # Precision: 6 decimals for lat/lon (~0.1m), 1 decimal for altitude/speed, 2 for track
        message = f"XGPS{self.sim_name},{lon:.6f},{lat:.6f},{altitude_m:.1f},{track:.2f},{speed_ms:.1f}"

        return message

    def send(
        self,
        lat: float,
        lon: float,
        altitude_ft: float,
        heading: float,
        speed_kts: float,
    ) -> bool:
        """Send XGPS position to all configured destinations.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            altitude_ft: Altitude in feet MSL
            heading: Track over ground in degrees true
            speed_kts: Ground speed in knots

        Returns:
            True if sent successfully to at least one destination
        """
        if not self._socket:
            logger.error("EFB socket not initialized")
            return False

        message = self.create_xgps_message(lat, lon, altitude_ft, heading, speed_kts)
        success = False

        # Send to broadcast if enabled (ForeFlight)
        if self.broadcast:
            try:
                self._socket.sendto(message.encode(), ("<broadcast>", EFB_PORT))
                logger.debug(f"EFB XGPS broadcast: {message}")
                success = True
            except Exception as e:
                logger.error(f"Failed to broadcast EFB XGPS: {e}")

        # Send to each specific IP (Garmin Pilot)
        for ip in self.target_ips:
            try:
                self._socket.sendto(message.encode(), (ip.strip(), EFB_PORT))
                logger.debug(f"EFB XGPS sent to {ip}: {message}")
                success = True
            except Exception as e:
                logger.error(f"Failed to send EFB XGPS to {ip}: {e}")

        return success

    def close(self) -> None:
        """Close the UDP socket."""
        if self._socket:
            self._socket.close()
            self._socket = None
            logger.info("EFB sender closed")


# Backwards compatibility alias
ForeFlightSender = EFBSender
