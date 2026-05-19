# Output Viewer

The **Output Viewer** is the full-width terminal-style panel at the bottom of the Dashboard. It shows live NMEA-0183 sentences being emitted (or, in Receiver mode, the incoming position packets being parsed). It is purely a display - you don't configure anything here, but it's the single most useful diagnostic in the UI.

<!-- SCREENSHOT-PENDING: output-viewer-01-overview.png - Output Viewer scrolling NMEA, time-prefixed lines, message count. -->

## The panel

| Element | What it does |
|---------|--------------|
| **Title** | `NMEA Output` in every mode except Receiver, where it changes to `NMEA Input`. |
| **Pause / Resume** button | Pauses (and resumes) the scrolling. While paused, new messages are dropped on the floor - they're not buffered. |
| **Clear** button (trash icon) | Wipes the visible buffer. Does not affect the underlying stream. |
| **Scroll area** | Dark terminal-style box, monospace font, ~18 visible lines. |
| **Message count** | "N messages (showing last 100)" - confirms the stream is live. |

## Idle states

| State | What you see |
|-------|--------------|
| Emulator stopped | `Start the emulator to see NMEA output` (or `... incoming NMEA data` in Receiver mode). |
| Just started, no data yet | `Waiting for data...` |
| Pause toggled on | Existing lines stay visible; no new ones appear; the pause icon turns yellow. |

## What appears in each mode

| Mode | Content |
|------|---------|
| Stand-Alone | Each NMEA sentence the local engine emits, one line per sentence, prefixed with the wall-clock timestamp. Sentences from one tick appear together (every ~1 s). |
| Sender | Same as Stand-Alone - whatever the engine emits is shown. The fact that it's also being published over UDP/TCP is invisible here; check the [Status Display](status-display.md) for network connection state. |
| Receiver | The **incoming** position packets after they've been parsed and synthesized into NMEA. The viewer shows the synthesized sentences, not the raw JSON. |
| Rebroadcaster | Same as Receiver. Output to USB / EFB / UDP retransmit is also invisible here; use `tcpdump` on the downstream host to confirm receipt, or watch the Status panel. |

## The line format

```
13:42:07  $GPGGA,134207.00,3307.6980,N,11716.8180,W,1,12,0.9,13716.0,M,-32.6,M,,*5F
13:42:07  $GPRMC,134207.00,A,3307.6980,N,11716.8180,W,450,090,180526,,,A*7B
13:42:07  $GPHDT,90,T*0F
13:42:08  $GPGGA,134208.00,3307.6987,N,11716.8174,W,1,12,0.9,13720.0,M,-32.6,M,,*5A
13:42:08  $GPRMC,134208.00,A,3307.6987,N,11716.8174,W,450,090,180526,,,A*7E
13:42:08  $GPHDT,90,T*0F
...
```

| Column | Meaning |
|--------|---------|
| Left timestamp | Browser-side `toLocaleTimeString` wall-clock. Useful for spotting cadence issues. |
| Sentence | The literal bytes that went on the wire to USB serial / TCP / UDP NMEA outputs. |

The viewer does not show:

- The XGPS frames sent to the EFB on UDP 49002 - those are a different stream entirely.
- The UDP retransmit position packets sent to the Fleet Dashboard - those are the original position JSON, not NMEA.
- The heartbeat packets sent to the Fleet Dashboard.

If you need to confirm those other streams, drop to `tcpdump` on the destination host. See [Troubleshooting](../reference/troubleshooting.md).

## Buffer behavior

| Detail | Value |
|--------|-------|
| Max visible messages | 100 |
| When buffer is full | Oldest messages drop off the top as new ones arrive (FIFO). |
| Pause behavior | New messages are **discarded**, not held. Resuming does not replay the missed messages. |
| Clear behavior | Local buffer empties. The underlying stream continues unchanged. |

This is intentional - the viewer is for "see what's happening right now", not "permanent log". For a permanent record, capture the bytes from the serial output, the WebSocket, or the network with `tcpdump`.

## How the viewer gets data

The viewer opens its own WebSocket connection to `/ws` when the emulator starts. The server publishes messages of the form:

```json
{"type": "nmea_output", "sentences": ["$GPGGA,...", "$GPRMC,...", "$GPHDT,..."]}
```

One such message per tick. The viewer splits the array, prefixes each sentence with the local timestamp, and pushes onto the buffer.

If the WebSocket disconnects mid-run, the viewer simply stops receiving messages. The reconnect logic in `useWebSocket.js` doesn't drive this viewer - the viewer opens its own socket and closes it on unmount. If the socket drops, the screen falls back to "Waiting for data...". A page refresh re-opens it.

!!! info "Two browsers, two streams"
    Each browser opens its own WebSocket to `/ws`, so two operators viewing the same simulator both see the live NMEA. They are independent reads of the same broadcast - one browser pausing doesn't affect the other.

## When the viewer is silent

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Started, viewer says "Waiting for data..." for more than a few seconds | The engine isn't ticking. Often: USB output enabled but serial open failed (Start error banner above). | Read the error banner; pick a valid device or disable USB. |
| Started in Receiver mode, no incoming sentences | The upstream Sender isn't reaching the Receiver. | Check `tcpdump` on the Receiver host; verify Sender's target IP/port and the firewall path. |
| Was scrolling, stopped abruptly mid-run | WebSocket disconnected (network blip, container restart). | Reload the page; the viewer re-opens its socket. |
| Scrolling looks slower than the 1 Hz expected | The browser tab is backgrounded (browsers throttle `setTimeout` and event handlers in inactive tabs). | Bring the tab to the foreground. |

## Worked example - using the viewer to debug a sender / receiver pair

You have a Sender at `10.200.40.10` and a Receiver at `10.200.40.20`. Receiver's viewer is empty even after Start.

| Check | What it tells you |
|-------|-------------------|
| Sender's viewer is scrolling | The Sender engine is running and emitting NMEA. (The UDP publish is separate; the viewer shows local sentences only.) |
| `tcpdump -i any 'udp port 12000' -X` on the Receiver host | Confirms whether packets are arriving at the host. If not, network / firewall issue. |
| `tcpdump` shows packets, but Receiver viewer is empty | Receiver process isn't binding the port (port collision, listening on wrong interface, container networking issue). |
| Receiver viewer says "Waiting for data..." with packets arriving | Receiver is running but unable to parse. Check the Receiver's Status display for the most recent error and consult [Troubleshooting](../reference/troubleshooting.md). |

## What's next

- [Status Display](status-display.md) - live numerical state alongside the byte stream.
- [Multi-Browser Sync](../user-guides/multi-browser-sync.md) - how the WebSocket fan-out works.
- [Troubleshooting](../reference/troubleshooting.md) - what to check when the viewer is silent or wrong.
