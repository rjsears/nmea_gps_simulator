# Welcome to the Simulator Manual

This is the operator's guide to the NMEA GPS Simulator web interface. It is organized **one page per UI tab or major area**, so you can find any control by walking down the left-hand navigation in the order you'd encounter it in the app.

If you're brand new to the project, start at [Overview](../getting-started/overview.md) and [Quick Start](../getting-started/quick-start.md) first. If you've already got a container running and just want to understand what a specific control does, you're in the right place.

## How this manual is organized

| Section | When to read it |
|---------|-----------------|
| **[Login](login.md)** | First time accessing the UI, or when reasoning about authentication / `BYPASS_AUTH`. |
| **[Dashboard Overview](dashboard-overview.md)** | Orientation - the main app layout, header, mode tabs, panels. |
| **Operating modes** ([Rebroadcaster](mode-rebroadcaster.md), [Sender](mode-sender.md), [Receiver](mode-receiver.md), [Stand-Alone](mode-standalone.md)) | One page per operating mode. Pick the one matching what you're doing. |
| **Per-feature pages** ([NMEA Sentences](nmea-sentences.md), [Serial Output](serial-output.md), [Navigation Controls](navigation-controls.md), [Output Viewer](output-viewer.md), [Status Display](status-display.md), [Airport Lookup](airport-lookup.md)) | Reference for cross-cutting UI features that show up in more than one mode. |
| **[Common UI Elements](common-ui.md)** | Header, theme toggle, multi-browser sync, help dialog - anything that lives outside the mode-specific panels. |
| **[Appendix](appendix.md)** | Troubleshooting tables, env-var reference, glossary, the security flag index used during screenshot capture. |

## Conventions in this manual

| Convention | Meaning |
|------------|---------|
| `!!! tip` / `!!! warning` / `!!! danger` / `!!! info` boxes | Tip is recommended-do; warning is unexpected behavior; danger is destructive; info is background context. Read them - the per-control tables are the floor, the admonitions are where most operators get tripped up. |
| Per-control reference tables | Every control on a panel gets a row with its default, valid values, and what changes when you flip it. |
| `<host>` placeholder | Stands in for the IP or hostname of the container running the simulator (or, in the dashboard manual, the dashboard container). |
| Screenshot at the top of each page | Overview shot of the panel under discussion. Detail screenshots inside the page only appear when a sub-state (modal open, edit form) is visually different. |
| Cross-links to env vars | When a UI control has a matching auto-start env var, the persistence table at the end of the page connects them. The authoritative env-var reference is [Environment Variables](../reference/env-vars.md). |

## A note on screenshots

Screenshots in this manual are captured from the **live running deployment**, not a mockup. If you see a value, a target IP, a simulator name in a screenshot, it was real - just sanitized after capture per the security-flag index in the appendix.

If your UI looks slightly different from a screenshot, check the page's footer line for the version it was captured against. Stale screenshots get rebuilt as features change.

## When you get stuck

| Symptom | Where to look |
|---------|---------------|
| The app loaded but the Start button stays disabled | The button's tooltip lists the missing field. Most common: no output selected, missing simulator name when EFB is on, no USB device when USB output is on. |
| EFB iPad never sees the simulator | [Connecting ForeFlight](../user-guides/connecting-foreflight.md) or [Connecting Garmin Pilot](../user-guides/connecting-garmin-pilot.md). |
| USB serial output never appears on the downstream device | [USB Serial (Bad Elf)](../user-guides/usb-serial-bad-elf.md). |
| Fleet Dashboard card stays gray | [Fleet Monitoring](../user-guides/fleet-monitoring.md) and [Health Chain](../dashboard-manual/health-chain.md). |
| Any other symptom | [Troubleshooting](../reference/troubleshooting.md) and the per-page Appendix at the end of this manual. |

## What's next

- [Login](login.md) - the first screen you'll see if `BYPASS_AUTH=false`.
- [Dashboard Overview](dashboard-overview.md) - the main app layout.
