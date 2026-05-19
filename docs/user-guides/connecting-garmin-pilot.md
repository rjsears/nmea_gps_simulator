# Connecting Garmin Pilot

Garmin Pilot also accepts the **XGPS** protocol on UDP 49002, but it does **not** auto-discover via broadcast - it only accepts unicast. You must know the iPad's IP and set it explicitly.

Everything else - the wire format, the per-tick cadence, the Simulator Name behavior - is identical to [Connecting ForeFlight](connecting-foreflight.md).

## The one critical difference

| App | Discovery |
|-----|-----------|
| ForeFlight | Broadcast on UDP 49002, plus unicast |
| **Garmin Pilot** | **Unicast only** on UDP 49002 |

Enabling **Broadcast** alone won't reach Garmin Pilot, no matter how clean the network is. The simulator must send a unicast packet directly to the iPad's IP.

## Setup

### On the simulator (via UI)

1. Pick a mode that supports EFB output (Stand-Alone, Sender, or Rebroadcaster).
2. In the EFB block:
   - **EFB Output (Port 49002)** -> on.
   - **Broadcast** -> off (or also on; not used by Garmin Pilot but doesn't hurt).
   - **Garmin Pilot/ForeFlight (IP Address)** -> on.
   - **EFB target IPs** -> the iPad's IP (e.g., `10.200.40.198`).
   - **Simulator Name** -> the aircraft identifier (e.g., `CL350`).
3. Press **Start**.

### On the simulator (via env vars, headless)

```yaml
environment:
  - AUTO_START_MODE=standalone   # or sender, rebroadcaster
  - AUTO_START_EFB_ENABLED=true
  - AUTO_START_EFB_BROADCAST=false
  - AUTO_START_EFB_TARGET_IPS=10.200.40.198
  - AUTO_START_EFB_SIM_NAME=CL350
```

### On the iPad

1. **Settings** -> **Wi-Fi** -> (i) next to the connected network. Record the IPv4 address.
2. Configure DHCP reservation or set the iPad to a static IP so the address is stable.
3. Open Garmin Pilot.
4. **Home** -> **Settings** -> **Connext** (or look for the GPS source dropdown - menu paths vary by version).
5. Garmin Pilot lists the simulator within a few seconds. Pick it.

## Finding the iPad's IP without going through Settings

If you can't get to Wi-Fi Settings on the iPad (locked-down kiosk mode, no admin access), you have a few options:

| Approach | How |
|----------|-----|
| Check the router's DHCP lease table | Most consumer routers expose `<router-ip>` over HTTP with a list of leases. Look for the iPad's MAC (visible in **Settings** -> **General** -> **About**). |
| `arp -a` from the simulator host | Lists every device that's responded to ARP recently. The iPad will appear by MAC. |
| Network scanner app (Fing, etc.) on a phone | Quick on-the-fly enumeration. |

Once you have the IP, set it as a DHCP reservation so it doesn't change.

## Multiple iPads or rotating DHCP

For a fleet of iPads, you have two options:

| Pattern | Setting |
|---------|---------|
| Fixed IPs, named individually | `AUTO_START_EFB_TARGET_IPS=10.200.40.198, 10.200.40.199, 10.200.40.200` |
| DHCP scope, send to every IP in the range | `AUTO_START_EFB_TARGET_IPS=10.200.40.10-10.200.40.30` (Each iPad picks up its own packets; the rest are silently dropped by the OS.) |

See [IP Range Parsing](ip-range-parsing.md) for full syntax.

## Verifying the link

| Where to look | What to expect |
|---------------|----------------|
| Garmin Pilot's GPS source screen | The Simulator Name appears within ~5 s of pressing Start. |
| Garmin Pilot's map | Aircraft cursor follows the simulator's lat/lon. |
| `tcpdump -i any 'host <ipad-ip> and udp port 49002'` on the simulator host | XGPS lines flowing once per second. |
| Simulator's Output Viewer | NMEA is flowing - but XGPS is **not** shown here (different stream). |

## Common gotchas

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Broadcast on, no IP set, Garmin Pilot doesn't see anything | Garmin Pilot doesn't accept broadcast. | Add the iPad's IP to **EFB target IPs**. |
| IP set correctly, still nothing | iPad is on a different VLAN or subnet, with no L3 path to the simulator host. | Confirm with `ping <ipad-ip>` from the simulator host. If ping fails, the route is broken - fix the network before debugging the app. |
| IP set correctly, host firewall on macOS | macOS firewall sometimes silently drops outbound UDP. | System Preferences -> Network -> Firewall -> allow Docker (or temporarily disable the firewall to confirm). |
| IP changes daily | iPad is on DHCP and pulling a new lease each day. | Switch to DHCP reservation, or use an IP range that covers the lease pool. |
| Simulator name shows blank or "LOFT GPS" | `AUTO_START_EFB_SIM_NAME` not set, or sim name field empty in the UI. | Set it explicitly. |
| Two simulators driving the same iPad | Both unicast to the iPad's IP; iPad sees two source streams. Garmin Pilot picks one (usually the first to arrive each tick). | Don't do this. One simulator per iPad. |

## Mixed ForeFlight + Garmin Pilot

If you have iPads running each app on the same network:

| Setting | Value |
|---------|-------|
| EFB output | on |
| Broadcast | on (so ForeFlight picks up automatically) |
| IP targeting | on, target only the Garmin Pilot iPad's IP |
| Simulator Name | `CL350` |

ForeFlight discovers via broadcast. Garmin Pilot receives unicast. Single simulator, both apps happy.

## Garmin Pilot version notes

XGPS support in Garmin Pilot has been stable for years. Any reasonably recent version (10.x+) works. Older versions might require enabling "Use external GPS" or similar in app settings - check the menu if the source doesn't appear.

## What's next

- [Connecting ForeFlight](connecting-foreflight.md) - the broadcast-friendly cousin.
- [IP Range Parsing](ip-range-parsing.md) - target multiple iPads.
- [Network Protocol](../reference/network-protocol.md) - XGPS wire format.
