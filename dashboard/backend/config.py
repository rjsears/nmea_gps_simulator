# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# config.py
#
# Fleet Dashboard - Configuration
#
# Richard J. Sears
# richardjsears@protonmail.com
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Dashboard configuration from environment variables."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class SimConfig:
    """Configuration for a single simulator."""
    name: str
    port: int


@dataclass
class Settings:
    """Application settings."""
    host: str
    port: int
    simulators: list[SimConfig]


def parse_simulator_config() -> list[SimConfig]:
    """Parse simulator configuration from environment variables.

    Environment variables format:
        SIM_1_NAME=CL350
        SIM_1_PORT=12001
        SIM_2_NAME=Ultra
        SIM_2_PORT=12002
        ...

    Or use a single variable:
        SIMULATORS=CL350:12001,Ultra:12002,CJ3:12003
    """
    simulators = []

    # Try single SIMULATORS variable first
    sims_env = os.getenv("SIMULATORS", "")
    if sims_env:
        for entry in sims_env.split(","):
            entry = entry.strip()
            if ":" in entry:
                name, port_str = entry.split(":", 1)
                try:
                    simulators.append(SimConfig(name=name.strip(), port=int(port_str.strip())))
                except ValueError:
                    pass

    # If no SIMULATORS var, try individual SIM_N_NAME/SIM_N_PORT
    if not simulators:
        for i in range(1, 20):  # Support up to 20 sims
            name = os.getenv(f"SIM_{i}_NAME")
            port_str = os.getenv(f"SIM_{i}_PORT")
            if name and port_str:
                try:
                    simulators.append(SimConfig(name=name, port=int(port_str)))
                except ValueError:
                    pass

    # Default configuration if nothing specified
    if not simulators:
        simulators = [
            SimConfig(name="CL350", port=12001),
            SimConfig(name="Ultra", port=12002),
            SimConfig(name="CJ3", port=12003),
            SimConfig(name="PC-12", port=12004),
            SimConfig(name="King Air", port=12005),
            SimConfig(name="Citation X", port=12006),
        ]

    return simulators


@lru_cache
def get_settings() -> Settings:
    """Get application settings."""
    return Settings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        simulators=parse_simulator_config(),
    )
