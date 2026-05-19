# IP Range Parsing

Any place that takes a list of EFB target IPs (the UI's EFB IPs field, `AUTO_START_EFB_TARGET_IPS` env var) accepts a flexible mini-language for expressing one or many IP addresses. This page documents the syntax and the corner cases.

The parser lives at `backend/network/foreflight.py:parse_ip_list()`.

## Syntax

The grammar is informal but predictable:

```
<entry> = <ip>
        | <ip> - <ip>
<input> = <entry> [ , <entry> ]*
```

Whitespace around commas and dashes is ignored. Empty entries (extra commas) are skipped silently.

| Form | Example | Result |
|------|---------|--------|
| Single IP | `10.200.50.3` | `["10.200.50.3"]` |
| Multiple IPs | `10.200.50.3, 10.200.50.4` | `["10.200.50.3", "10.200.50.4"]` |
| IP range | `10.200.50.10-10.200.50.20` | 11 IPs from `.10` through `.20` inclusive |
| Mixed | `10.200.50.3, 10.200.50.10-10.200.50.20` | 12 IPs total |
| Whitespace tolerated | `  10.200.50.3 ,  10.200.50.4  ` | Same as `10.200.50.3, 10.200.50.4` |

The parser expands ranges greedily - a range of `/24` size (256 entries) will produce 256 individual `sendto` calls per tick. For most deployments that's fine; for very large ranges, consider broadcast instead.

## Range expansion - how it works

Ranges treat IPs as 32-bit integers. `10.200.50.10` becomes `(10 << 24) | (200 << 16) | (50 << 8) | 10 = 181_374_986`. The parser iterates from `start_int` to `end_int` inclusive and reassembles each integer back into dotted-quad form.

| Range | First IP | Last IP | Count |
|-------|----------|---------|-------|
| `10.0.0.1-10.0.0.5` | 10.0.0.1 | 10.0.0.5 | 5 |
| `10.0.0.250-10.0.1.5` | 10.0.0.250 | 10.0.1.5 | 12 (crosses the /24 boundary) |
| `192.168.1.10-192.168.1.10` | 192.168.1.10 | 192.168.1.10 | 1 (degenerate, but accepted) |

The range **does** cross subnet boundaries cleanly - the parser doesn't care about subnets, only integer order.

## Validation rules

| Input | Behavior |
|-------|----------|
| Empty string | Returns `[]` (no IPs). |
| Single comma `,` | Returns `[]`. Empty parts are skipped. |
| Trailing comma `10.0.0.1,` | Returns `["10.0.0.1"]`. |
| Malformed IP `10.0.0` | **Treated as a single IP literal.** The parser does not validate octets - it just splits on `.` and assembles. If the malformed form is later passed to `socket.sendto`, the socket layer raises an error per packet at send time. |
| Range with non-IPv4 endpoints | If the dash form can't be split into two IP-looking strings, the entry is logged as a warning and skipped. The other entries continue normally. |
| Reversed range `10.0.0.20-10.0.0.10` | Logged as a warning (`Invalid IP range (end < start)`) and skipped. |
| Bracket-IPv6 notation `[::1]` | Not supported. Treated as a literal entry, will fail at socket layer. |

!!! info "The parser is forgiving by design"
    For the EFB use case, a malformed entry blocking the whole list is worse than the entry silently failing at send time. So the parser accepts almost anything and lets the socket layer surface the per-IP failure. Watch the logs (`docker compose logs gps-emulator | grep -i efb`) if delivery to a specific iPad is missing.

## How the parsed list is used

For each tick, the EFB sender:

1. Builds the XGPS line once.
2. If broadcast is enabled, sends to `255.255.255.255:49002`.
3. For each IP in the parsed list, sends a unicast copy to `<ip>:49002`.

So a list of 10 IPs means 10 `sendto` calls per tick. At 1 Hz that's 10 packets/sec - trivial bandwidth.

## Worked examples

### Single iPad

```
AUTO_START_EFB_TARGET_IPS=10.200.40.198
```

One packet per tick to `10.200.40.198`.

### Three named iPads

```
AUTO_START_EFB_TARGET_IPS=10.200.40.198, 10.200.40.199, 10.200.40.200
```

Three packets per tick. Whitespace optional but readable.

### Whole training-room block

```
AUTO_START_EFB_TARGET_IPS=10.200.40.10-10.200.40.30
```

21 packets per tick. Useful when every iPad in the room runs Garmin Pilot and no one has fixed which IP they're getting from DHCP.

### Mixed: a few named iPads plus a backup range

```
AUTO_START_EFB_TARGET_IPS=10.200.40.198, 10.200.40.199, 10.200.50.10-10.200.50.20
```

13 packets per tick: 2 explicit + 11 in the range.

### Single-IP "range" (degenerate but valid)

```
AUTO_START_EFB_TARGET_IPS=10.200.40.198-10.200.40.198
```

One packet per tick. Functionally identical to just `10.200.40.198`, but legal syntax.

## When to use broadcast instead

Ranges are useful when you have **specific** target IPs to cover. If you want to cover **everything on the local segment**, prefer broadcast:

| Goal | Use |
|------|-----|
| ForeFlight, any iPad on the same Wi-Fi | Broadcast (`AUTO_START_EFB_BROADCAST=true`). No IP list needed. |
| Garmin Pilot, any iPad on the same Wi-Fi | **Range covering the iPad subnet** (Garmin Pilot can't accept broadcast). |
| ForeFlight or Garmin Pilot **outside** the local subnet | Range (broadcast doesn't cross routers). |

Broadcast and ranges are not mutually exclusive - turn on both, and a ForeFlight iPad picks up via broadcast while a Garmin Pilot iPad picks up via the range entry.

## Persistent state

| Setting | UI control | Env var | Persists? |
|---------|-----------|---------|-----------|
| EFB target IPs | EFB IP-targets field | `AUTO_START_EFB_TARGET_IPS` | Only if env var set |

The parsed list is re-evaluated every Start. Changing the field while running and pressing **Start** uses the new list.

## What's next

- [Connecting ForeFlight](connecting-foreflight.md) - end-to-end ForeFlight integration including target-IP choices.
- [Connecting Garmin Pilot](connecting-garmin-pilot.md) - same for Garmin Pilot.
- [Auto-Start](auto-start.md) - where `AUTO_START_EFB_TARGET_IPS` lives.
