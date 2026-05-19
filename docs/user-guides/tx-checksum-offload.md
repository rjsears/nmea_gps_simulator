# TX Checksum Offload Fix

On some Linux hosts (specifically: hosts with certain NIC chipsets that aggressively use **TX checksum offload**), `tcpdump` on the receiving end shows warnings like `bad udp cksum` for every packet coming **from** that host - even though the packets are intact at the application layer and the receiver processes them correctly.

This page explains why, when to care, and the persistent fix.

## The symptom

Running `tcpdump` on the Fleet Dashboard's host (or any UDP receiver):

```
21:43:00.012345 IP gps-host > dashboard-host: UDP, bad udp cksum 0x1234 -> 0xabcd!, length 142
21:43:01.014567 IP gps-host > dashboard-host: UDP, bad udp cksum 0x1234 -> 0xabcd!, length 142
```

Only packets **from the simulator host** show the warning. Packets from other hosts on the same segment look fine. The dashboard receives the data normally and the card shows the right position, but `tcpdump`'s warning is alarming and looks like real corruption.

## Why this happens

| Layer | What's going on |
|-------|-----------------|
| App | The simulator builds a UDP datagram with its payload and (eventually) a UDP checksum. |
| Kernel | The kernel offloads checksum calculation to the NIC because the NIC advertises TX checksum offload capability. |
| NIC | The NIC is supposed to compute the checksum on its way out the door. On certain chipsets with certain kernel versions, the NIC writes a **placeholder** value rather than the real checksum. |
| Wire | Packet goes out with a wrong UDP checksum. |
| Receiver kernel | The receiver computes the checksum, sees it's wrong, but **delivers the packet anyway** if the kernel is configured to trust UDP payloads (most are). |
| Receiver app | Sees the payload, processes it normally. |
| `tcpdump` | Records the wrong checksum and complains. |

The data is fine. The wire-level checksum is wrong. The receiving kernel ignores the wrong checksum and delivers anyway. This has been a known offload-glitch class for ~15 years.

!!! info "How we know it's offload and not real corruption"
    Real corruption causes occasional bad checksums (random, not every packet). Offload glitches cause **every** packet from one source to show the wrong checksum, consistently, while every packet from other sources looks fine. If the pattern is "this host's UDP is always wrong, this other host on the same switch is always right", it's offload.

## The fix

Disable TX checksum offload on the affected NIC.

### One-shot (lasts until reboot)

Find the interface name (usually `eth0`, `enp1s0`, `eno1`, etc.):

```bash
ip route | grep default | awk '{print $5}'
```

Then disable TX offload:

```bash
sudo ethtool -K <iface> tx off
```

For example, if the interface is `main`:

```bash
sudo ethtool -K main tx off
```

Confirm with `tcpdump` from the receiving host. The next packet should show `udp sum ok` instead of `bad udp cksum`.

### Persistent across reboots

A one-shot `ethtool` call doesn't survive reboot. To make it permanent, several options exist - pick the one that matches the host's distribution.

#### Option A - systemd-networkd `.link` file

If the host uses `systemd-networkd`, create `/etc/systemd/network/99-no-tx-offload.link`:

```
[Match]
Name=<iface>

[Link]
TCPSegmentationOffload=no
GenericSegmentationOffload=no
ChecksumOffload=no
```

Reboot or `systemctl restart systemd-networkd`.

#### Option B - NetworkManager dispatcher script

For Ubuntu / Debian hosts using NetworkManager, create `/etc/NetworkManager/dispatcher.d/99-no-tx-offload`:

```bash
#!/bin/sh
IFACE="$1"
ACTION="$2"
if [ "$ACTION" = "up" ] && [ "$IFACE" = "<iface>" ]; then
    /usr/sbin/ethtool -K "$IFACE" tx off
fi
```

`chmod +x` the file. NetworkManager runs it when the interface comes up.

!!! info "`networkd-dispatcher` is a separate package"
    Some Ubuntu Server installs use `networkd-dispatcher` (different from NetworkManager). The dispatcher path is `/etc/networkd-dispatcher/routable.d/`. Same script format. The script's name should start with a two-digit prefix so it sorts deterministically with the rest of the directory.

#### Option C - systemd one-shot service

Create `/etc/systemd/system/no-tx-offload.service`:

```
[Unit]
Description=Disable TX checksum offload
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/ethtool -K <iface> tx off
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now no-tx-offload.service
```

#### Option D - rc.local (if still in use)

Old-style Linux: append the `ethtool -K` command to `/etc/rc.local` before the `exit 0`. Only works on hosts where rc.local is enabled.

#### Option E - cron @reboot

If none of the above fit:

```bash
sudo crontab -e
# add:
@reboot /usr/sbin/ethtool -K <iface> tx off
```

Less elegant but bulletproof.

## When you don't need to fix it

| Situation | Action |
|-----------|--------|
| You don't use `tcpdump` and the app works fine | **Don't touch it.** The warning is cosmetic - the data is fine. Disabling offload is a small CPU cost. |
| You're running on a Mac, Raspberry Pi, or hosts without the offload glitch | **Don't touch it.** This isn't a problem on every host. |
| `tcpdump` warnings are annoying to wade through during debugging | Fix it. The cost is trivial. |

The author of this project hit this in real deployment with simulator hosts where every packet from the rebroadcaster looked broken in `tcpdump`. The fix above eliminated the warnings; the data was fine throughout.

## Verifying the fix

After applying:

```bash
# On the receiver host
sudo tcpdump -i any 'udp port 12001' -nn 2>&1 | head -5
```

Expected output now reads `udp sum ok` instead of `bad udp cksum`:

```
21:43:00.012345 IP gps-host > dashboard-host: UDP, length 142, udp sum ok
```

Repeat after a reboot to confirm persistence.

## Performance impact

Disabling TX checksum offload moves UDP checksum calculation back to the CPU. For 1 Hz traffic (one packet per second per simulator), the cost is unmeasurable. For high-traffic workloads, it can matter - but the simulator never produces high-traffic UDP, so it's fine.

If the same host runs **other** UDP-heavy workloads (a streaming server, a game server, etc.), you may want to find a more targeted fix - e.g., per-socket `SO_NO_CHECK` or a different NIC. For the simulator alone, just turn it off.

## What's next

- [Fleet Monitoring](fleet-monitoring.md) - where `tcpdump` warnings tend to surface.
- [Rebroadcaster Mode](../manual/mode-rebroadcaster.md) - the mode most likely to trigger this on heavy-traffic deployments.
- [Troubleshooting](../reference/troubleshooting.md) - other network gotchas.
