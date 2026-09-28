import asyncio
import logging
import re
import subprocess
import time
from datetime import datetime, timezone

import pytest

from backend import main
from backend.config import SimConfig


def test_default_simulator_state_has_no_switch_check():
    state = main.SimulatorState("CJ3", 12001)

    assert state.switch_ip == ""
    assert state.switch_reachable is None
    state_dict = state.to_dict()
    assert "switch_ip" in state_dict
    assert "switch_reachable" in state_dict


def test_update_switch_records_result_and_timestamp():
    state = main.SimulatorState("CJ3", 12001)

    state.update_switch(True)
    assert state.switch_reachable is True
    assert isinstance(state.last_switch_check, float)

    state.update_switch(False)
    assert state.switch_reachable is False
    assert isinstance(state.last_switch_check, float)


def test_ping_host_returns_true_for_success_and_uses_expected_argv(monkeypatch):
    calls = []

    class Result:
        returncode = 0

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return Result()

    monkeypatch.setattr(main.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(main.subprocess, "run", fake_run)

    assert main.ping_host("10.1.1.1") is True
    assert calls == [
        (
            ["ping", "-c", "1", "-W", "1", "10.1.1.1"],
            {"capture_output": True, "timeout": 2},
        )
    ]


def test_ping_host_returns_false_for_nonzero_exit(monkeypatch):
    class Result:
        returncode = 1

    monkeypatch.setattr(main.subprocess, "run", lambda *args, **kwargs: Result())

    assert main.ping_host("10.1.1.1") is False


def test_ping_host_returns_false_on_timeout(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("ping", 2)

    monkeypatch.setattr(main.subprocess, "run", raise_timeout)

    assert main.ping_host("10.1.1.1") is False


def test_ping_host_returns_false_when_binary_is_missing(monkeypatch):
    def raise_missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(main.subprocess, "run", raise_missing)

    assert main.ping_host("10.1.1.1") is False


def test_configure_propagates_switch_ip():
    fleet_monitor = main.FleetMonitor()

    fleet_monitor.configure([SimConfig("CJ3", 12001, "Avionics", "10.200.10.6")])

    assert fleet_monitor.simulators[12001].switch_ip == "10.200.10.6"


def test_start_monitors_only_simulators_with_switch_ip(monkeypatch):
    fleet_monitor = main.FleetMonitor()
    fleet_monitor.configure(
        [
            SimConfig("CJ3", 12001, switch_ip="10.200.10.6"),
            SimConfig("Ultra", 12002),
        ]
    )
    calls = []

    def fake_ping_host(ip):
        calls.append(ip)
        return True

    monkeypatch.setattr(main, "ping_host", fake_ping_host)
    monkeypatch.setattr(fleet_monitor, "_listen", lambda port: None)
    monkeypatch.setattr(main, "SWITCH_PING_INTERVAL", 0.05)

    fleet_monitor.start()
    time.sleep(0.3)
    fleet_monitor.stop()

    assert calls
    assert set(calls) == {"10.200.10.6"}
    assert fleet_monitor.simulators[12001].switch_reachable is True
    assert fleet_monitor.simulators[12002].switch_reachable is None


def test_generated_at_is_none_until_fleet_monitor_is_evaluated():
    fleet_monitor = main.FleetMonitor()

    assert fleet_monitor.generated_at is None

    fleet_monitor.mark_evaluated()

    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", fleet_monitor.generated_at
    )
    assert fleet_monitor.generated_at == datetime.fromtimestamp(
        fleet_monitor.last_evaluated, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_start_records_initial_evaluation(monkeypatch):
    fleet_monitor = main.FleetMonitor()
    fleet_monitor.configure([SimConfig("CJ3", 12001)])

    monkeypatch.setattr(fleet_monitor, "_listen", lambda port: None)
    monkeypatch.setattr(main, "ping_host", lambda ip: False)

    fleet_monitor.start()
    try:
        assert fleet_monitor.last_evaluated is not None
    finally:
        fleet_monitor.stop()


def test_get_status_includes_generated_at_without_evaluating():
    previous_evaluation = main.fleet_monitor.last_evaluated
    main.fleet_monitor.mark_evaluated()
    evaluation_before_status = main.fleet_monitor.last_evaluated

    try:
        status = asyncio.run(main.get_status())
        second_status = asyncio.run(main.get_status())

        assert status["generated_at"] == main.fleet_monitor.generated_at
        assert "simulators" in status
        assert "timestamp" in status
        assert second_status["generated_at"] == main.fleet_monitor.generated_at
        assert main.fleet_monitor.last_evaluated == evaluation_before_status
    finally:
        main.fleet_monitor.last_evaluated = previous_evaluation


def test_evaluate_and_broadcast_marks_without_websocket_connections(monkeypatch):
    monkeypatch.setattr(main, "websocket_connections", set())
    monkeypatch.setattr(main.fleet_monitor, "last_evaluated", None, raising=False)

    asyncio.run(main.evaluate_and_broadcast())

    assert main.fleet_monitor.last_evaluated is not None


def test_evaluate_and_broadcast_does_not_mark_or_raise_when_evaluation_fails(
    monkeypatch, caplog
):
    last_evaluated_before = main.fleet_monitor.last_evaluated

    def raise_evaluation_error():
        raise RuntimeError("boom")

    monkeypatch.setattr(main.fleet_monitor, "get_all_states", raise_evaluation_error)

    with caplog.at_level(logging.ERROR):
        asyncio.run(main.evaluate_and_broadcast())

    assert main.fleet_monitor.last_evaluated == last_evaluated_before
    assert "evaluation failed" in caplog.text.lower()


def test_broadcast_loop_survives_a_failing_tick(monkeypatch):
    get_all_states_calls = []

    def fake_get_all_states():
        get_all_states_calls.append(None)
        if len(get_all_states_calls) == 1:
            raise RuntimeError("boom")
        return []

    monkeypatch.setattr(main.fleet_monitor, "get_all_states", fake_get_all_states)

    sleep_calls = []

    async def fake_sleep(_delay):
        sleep_calls.append(None)
        if len(sleep_calls) == 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)
    evaluation_timestamp = 1_234_567_890.0
    monkeypatch.setattr(main.time, "time", lambda: evaluation_timestamp)
    last_evaluated_before = main.fleet_monitor.last_evaluated

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(main.broadcast_state())

    assert len(get_all_states_calls) == 2
    assert len(sleep_calls) == 2
    assert main.fleet_monitor.last_evaluated is not None
    assert main.fleet_monitor.last_evaluated != last_evaluated_before
    assert main.fleet_monitor.last_evaluated == evaluation_timestamp
