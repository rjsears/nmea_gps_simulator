# Connecting ForeFlight

ForeFlight is the easier of the two EFB targets to wire up because it discovers GPS sources automatically over UDP broadcast on port 49002. This guide walks through the end-to-end setup with both broadcast and unicast variants.

The protocol is **XGPS** - one ASCII line per second, format `XGPS{SimName},{lon},{lat},{alt_m},{track},{speed_ms}`. See [Network Protocol](../reference/network-protocol.md) for the wire-level reference.

## Prerequisites

- The simulator container running and reachable from the iPad's Wi-Fi.
- An iPad on the same Wi-Fi (or a routed segment, for unicast) running ForeFlight 11+.
- Either Stand-Alone, Sender, or Rebroadcaster mode active on the simulator.

## Setup option A: broadcast (recommended on the same Wi-Fi)

This is the path of least resistance. ForeFlight picks up the source from the local broadcast address.

### On the simulator (via UI)

1. Pick a mode that supports EFB output (Stand-Alone, Sender, or Rebroadcaster).
2. In the EFB block:
   - **EFB Output (Port 49002)** -> on.
   - **Broadcast** -> on.
   - **Simulator Name** -> the aircraft identifier you want shown in ForeFlight (e.g., `CL350`).
3. Leave **Garmin Pilot/ForeFlight (IP Address)** off (or also on - doesn't hurt).
4. Press **Start**.

### On the simulator (via env vars, headless)

```yaml
environment:
  - AUTO_START_MODE=standalone   # or sender, rebroadcaster
  - AUTO_START_EFB_ENABLED=true
  - AUTO_START_EFB_BROADCAST=true
  - AUTO_START_EFB_SIM_NAME=CL350
```

### On the iPad

1. Open ForeFlight.
2. **More** -> **Devices**.
3. Wait a few seconds. The simulator should appear as a device named **GPS** (or similar), with the simulator name visible in the source list.
4. ForeFlight starts using it as the position source immediately.

If it doesn't appear, the issue is almost always either AP isolation on the Wi-Fi or the iPad on a different subnet from the simulator host. See troubleshooting below.

## Setup option B: unicast (when broadcast won't reach)

When the iPad is on a different subnet, behind a router with no broadcast forwarding, or on a guest Wi-Fi with isolation, broadcast doesn't work. Use unicast to the iPad's specific IP.

### On the simulator (via UI)

1. EFB block -> on.
2. **Broadcast** -> off (or also on - doesn't conflict).
3. **Garmin Pilot/ForeFlight (IP Address)** -> on.
4. **EFB target IPs** -> the iPad's IP (e.g., `10.200.40.198`).
5. **Simulator Name** -> as before.

### On the simulator (via env vars)

```yaml
environment:
  - AUTO_START_EFB_ENABLED=true
  - AUTO_START_EFB_BROADCAST=false
  - AUTO_START_EFB_TARGET_IPS=10.200.40.198
  - AUTO_START_EFB_SIM_NAME=CL350
```

For multiple iPads or DHCP scopes, see [IP Range Parsing](ip-range-parsing.md) - same field, more powerful syntax.

### On the iPad

1. Find the iPad's IP address: **Settings** -> **Wi-Fi** -> tap the (i) next to the connected network. Record the IPv4 Address.
2. Set the iPad to a **DHCP reservation** or **static IP** so this address doesn't change. (Optional but recommended - if the iPad gets a new IP from DHCP, you'll need to update `AUTO_START_EFB_TARGET_IPS`.)
3. Open ForeFlight -> **More** -> **Devices**.
4. The simulator appears the same way as in broadcast mode.

## Verifying the link

| Where to look | What to expect |
|---------------|----------------|
| ForeFlight **Devices** screen | Lists the simulator name within ~5 s of pressing Start. |
| ForeFlight **map** | Aircraft cursor centers on the lat/lon you set in the simulator. |
| `tcpdump -i any 'udp port 49002' -X` on the iPad's gateway (or on the simulator host) | Shows the XGPS ASCII line being emitted, 1 Hz. |
| Simulator **Output Viewer** | Shows the NMEA stream - **does not show XGPS** (that's a different stream). |

The Output Viewer not showing XGPS confuses many first-time users. The viewer is for NMEA only; XGPS to UDP 49002 is a separate pipeline. To verify XGPS, drop to `tcpdump`.

## Common gotchas

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| ForeFlight never shows the simulator in Devices | AP isolation on the Wi-Fi; iPad on a different SSID; host firewall blocking outbound UDP 49002 | Confirm same SSID, same subnet. Disable AP isolation on the router. On a macOS host: System Preferences -> Network -> Firewall -> allow Docker. |
| Found in Devices, but the map cursor doesn't update | The XGPS frames are arriving but with stale coordinates. | Confirm the simulator's NMEA is also flowing (Output Viewer scrolling). If yes, the simulator state is stuck - press Stop / Start. |
| Found, map updates, but wrong altitude | XGPS sends altitude in **meters MSL**, not feet. The simulator handles the conversion, so if altitude looks wrong, it's likely a unit confusion downstream. ForeFlight displays correctly without intervention. | Sanity-check the simulator's altitude in the Status Display. |
| Simulator name shows as `LOFT GPS` instead of the value you set | The env var default kicks in when `AUTO_START_EFB_SIM_NAME` is unset but `AUTO_START_EFB_ENABLED=true`. | Set `AUTO_START_EFB_SIM_NAME` explicitly. |
| Two simulators on the same Wi-Fi, both broadcast on | ForeFlight will see two sources and arbitrarily pick one. | Give them distinct Simulator Names (or use unicast and target only one iPad per simulator). |
| ForeFlight shows position but no track / no speed | XGPS includes track and speed in every frame. If the iPad shows them as 0, the simulator probably has airspeed 0 (a stationary aircraft). Move it. | Set a non-zero airspeed in the simulator and confirm the cursor begins to move. |

## ForeFlight version notes

| ForeFlight version | XGPS support |
|--------------------|--------------|
| 9 and earlier | Limited or missing - use a newer version. |
| 10 | Works. |
| 11+ | Works; recommended. |

This is independent of iPad model - any iPad that can run a recent ForeFlight works as a target.

## Combining ForeFlight + Garmin Pilot

If you have both apps running (perhaps two iPads, or one iPad running both), enable both **Broadcast** and **Garmin Pilot/ForeFlight (IP Address)** with the Garmin iPad's IP. ForeFlight finds the source via broadcast; Garmin Pilot receives unicast. Single simulator, two consumers.

| Setting | Value |
|---------|-------|
| EFB output | on |
| Broadcast | on |
| IP targeting | on, target the Garmin Pilot iPad |
| Simulator name | `CL350` (both apps display it) |

## What's next

- [Connecting Garmin Pilot](connecting-garmin-pilot.md) - the unicast-required cousin.
- [IP Range Parsing](ip-range-parsing.md) - target multiple iPads or a whole DHCP scope.
- [Network Protocol](../reference/network-protocol.md) - XGPS wire format.
