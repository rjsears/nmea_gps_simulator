from backend.config import parse_simulator_config


def _clear_simulator_environment(monkeypatch):
    monkeypatch.delenv("SIMULATORS", raising=False)
    for index in range(1, 20):
        for suffix in ("NAME", "PORT", "GPS_SYSTEM", "SWITCH_IP"):
            monkeypatch.delenv(f"SIM_{index}_{suffix}", raising=False)


def test_switch_ip_is_parsed_from_individual_simulator_variables(monkeypatch):
    _clear_simulator_environment(monkeypatch)
    monkeypatch.setenv("SIM_1_NAME", "CJ3")
    monkeypatch.setenv("SIM_1_PORT", "12001")
    monkeypatch.setenv("SIM_1_GPS_SYSTEM", "Avionics")
    monkeypatch.setenv("SIM_1_SWITCH_IP", "10.200.10.6")

    simulators = parse_simulator_config()

    assert simulators[0].switch_ip == "10.200.10.6"


def test_missing_switch_ip_defaults_to_empty_string(monkeypatch):
    _clear_simulator_environment(monkeypatch)
    monkeypatch.setenv("SIM_1_NAME", "CJ3")
    monkeypatch.setenv("SIM_1_PORT", "12001")

    simulators = parse_simulator_config()

    assert simulators[0].switch_ip == ""


def test_switch_ip_surrounding_whitespace_is_stripped(monkeypatch):
    _clear_simulator_environment(monkeypatch)
    monkeypatch.setenv("SIM_1_NAME", "CJ3")
    monkeypatch.setenv("SIM_1_PORT", "12001")
    monkeypatch.setenv("SIM_1_SWITCH_IP", "  10.200.10.6  ")

    simulators = parse_simulator_config()

    assert simulators[0].switch_ip == "10.200.10.6"


def test_comma_separated_simulators_keep_default_switch_ip(monkeypatch):
    _clear_simulator_environment(monkeypatch)
    monkeypatch.setenv("SIMULATORS", "A:12001")

    simulators = parse_simulator_config()

    assert len(simulators) == 1
    assert simulators[0].name == "A"
    assert simulators[0].port == 12001
    assert simulators[0].switch_ip == ""
