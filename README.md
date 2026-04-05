# ⬡ Veracious Dashboard

A fast, self-hosted home network dashboard with live stats.
Zero cloud dependencies. Zero build tools. Just Python and a browser.

---

## Quick Start

```bash
git clone <your-repo> veracious-dashboard
cd veracious-dashboard
bash setup.sh
```

That's it. The setup script installs dependencies and creates two system services that auto-start on boot.

- **Dashboard**: http://localhost:8888
- **Stats API**: http://localhost:8889/stats

---

## File Structure

```
veracious-dashboard/
├── index.html    ← Dashboard UI — add your services here
├── stats.py      ← Stats collector backend — do not edit
├── config.py     ← Your passwords and IPs — edit this
├── setup.sh      ← One-time installer
└── README.md
```

---

## Setup Guide

### Step 1 — Edit config.py

Open `config.py` and fill in your details:

```python
MIKROTIK_ENABLED = True
MIKROTIK_HOST    = '192.168.1.1'      # Your router IP
MIKROTIK_USER    = 'admin'
MIKROTIK_PASS    = 'yourpassword'
```

Enable other integrations by setting `ENABLED = True` and uncommenting the config lines below.

### Step 2 — Edit index.html

Open `index.html` and scroll to the `CONFIG` object near the bottom.
Add your services following the existing examples. Each service can display stats from the backend by referencing stat keys.

### Step 3 — Restart the stats service

```bash
sudo systemctl restart veracious-stats
```

---

## Supported Integrations

| Service        | Stats available                                              |
|----------------|--------------------------------------------------------------|
| MikroTik       | WAN upload/download MB/s, device count                       |
| Pi-hole v6     | Blocked today, block rate, blocklist size                    |
| Proxmox        | CPU %, RAM %, running VMs                                    |
| TrueNAS        | Pool count, health, disk count                               |
| UniFi          | Connected client count                                       |
| Plex           | Active streams                                               |
| Home Assistant | Entity count, automation count                               |
| Portainer      | Running containers, total containers                         |
| Ollama         | Loaded model count                                           |
| Open WebUI     | Model count                                                  |
| Grafana        | Dashboard count                                              |
| **AMP**        | Total instances, running instances, total players, avg CPU/RAM % |
| **OctoPrint**  | State, print progress %, bed temp, hotend temp (per printer) |
| **Moonraker**  | State, print progress %, extruder temp, bed temp (per printer)|
| **Bambu (LAN)**| State, progress %, layer / total layers (per printer)        |
| **Obico**      | Total printers, active print count, state per printer        |

---

## Stat Keys Reference

### AMP
| Key | Description |
|-----|-------------|
| `amp_instances_total` | Total AMP instances |
| `amp_instances_running` | Currently running instances |
| `amp_players` | Total active players across all servers |
| `amp_cpu_pct` | Average CPU % across running instances |
| `amp_ram_pct` | Average RAM % across running instances |

### OctoPrint (per printer, replace `printer_1` with your printer name lowercased)
| Key | Description |
|-----|-------------|
| `octoprint_printer_1_state` | Print state (e.g. `Printing`, `Operational`) |
| `octoprint_printer_1_progress` | Progress % |
| `octoprint_printer_1_bed_temp` | Bed temperature °C |
| `octoprint_printer_1_hotend_temp` | Hotend temperature °C |
| `octoprint_printing` | Count of printers currently printing |
| `octoprint_total` | Total configured printers |

### Moonraker (per printer, replace `voron` with your printer name lowercased)
| Key | Description |
|-----|-------------|
| `moonraker_voron_state` | Print state (e.g. `printing`, `standby`) |
| `moonraker_voron_progress` | Progress % |
| `moonraker_voron_extruder_temp` | Extruder temperature °C |
| `moonraker_voron_bed_temp` | Bed temperature °C |
| `moonraker_printing` | Count of printers currently printing |
| `moonraker_total` | Total configured printers |

### Bambu (per printer, replace `x1_carbon` with your printer name lowercased)
| Key | Description |
|-----|-------------|
| `bambu_x1_carbon_state` | Print state (e.g. `RUNNING`, `IDLE`) |
| `bambu_x1_carbon_progress` | Progress % |
| `bambu_x1_carbon_layer` | Current layer number |
| `bambu_x1_carbon_total_layers` | Total layer count |
| `bambu_printing` | Count of printers currently printing |
| `bambu_total` | Total configured printers |

### Obico (per printer, replace `my_printer` with your printer name lowercased)
| Key | Description |
|-----|-------------|
| `obico_my_printer_state` | Print state text |
| `obico_my_printer_progress` | Progress % |
| `obico_active` | Count of active prints |
| `obico_total` | Total configured printers |

---

## Adding a New Service (index.html)

```js
{
  name:        "My Service",
  url:         "http://192.168.1.XX:PORT",
  icon:        "🔧",
  description: "What it does",
  tags:        ["category"],
  checkUrl:    "http://192.168.1.XX:PORT",
  stats: [
    { key: "stat_key", label: "Label", endpoint: "fast" },  // updates every 5s
    { key: "stat_key", label: "Label", endpoint: "slow" },  // updates every 60s
    { key: "stat_key", label: "Label", endpoint: "slow", transform: "v => v + '%'" },
  ],
},
```

### Example: AMP Game Server Panel

```js
{
  name:        "AMP",
  url:         "http://192.168.88.XX:8080",
  icon:        "🎮",
  description: "Game server manager",
  tags:        ["gaming"],
  checkUrl:    "http://192.168.88.XX:8080",
  stats: [
    { key: "amp_instances_running", label: "Running",  endpoint: "slow" },
    { key: "amp_players",           label: "Players",  endpoint: "slow" },
    { key: "amp_cpu_pct",           label: "Avg CPU",  endpoint: "slow", transform: "v => v + '%'" },
    { key: "amp_ram_pct",           label: "Avg RAM",  endpoint: "slow", transform: "v => v + '%'" },
  ],
},
```

### Example: OctoPrint (printer named "Printer 1" in config.py)

```js
{
  name:        "OctoPrint",
  url:         "http://192.168.88.XX",
  icon:        "🖨️",
  description: "FDM printer control",
  tags:        ["printing"],
  checkUrl:    "http://192.168.88.XX",
  stats: [
    { key: "octoprint_printer_1_state",    label: "State",    endpoint: "slow" },
    { key: "octoprint_printer_1_progress", label: "Progress", endpoint: "slow", transform: "v => v + '%'" },
    { key: "octoprint_printer_1_bed_temp", label: "Bed",      endpoint: "slow", transform: "v => v + '°'" },
  ],
},
```

### Example: Moonraker/Klipper (printer named "Voron" in config.py)

```js
{
  name:        "Voron",
  url:         "http://192.168.88.XX:7125",
  icon:        "🖨️",
  description: "Klipper printer",
  tags:        ["printing"],
  checkUrl:    "http://192.168.88.XX:7125",
  stats: [
    { key: "moonraker_voron_state",         label: "State",    endpoint: "slow" },
    { key: "moonraker_voron_progress",      label: "Progress", endpoint: "slow", transform: "v => v + '%'" },
    { key: "moonraker_voron_extruder_temp", label: "Hotend",   endpoint: "slow", transform: "v => v + '°'" },
    { key: "moonraker_voron_bed_temp",      label: "Bed",      endpoint: "slow", transform: "v => v + '°'" },
  ],
},
```

### Example: Bambu (printer named "X1 Carbon" in config.py)

```js
{
  name:        "X1 Carbon",
  url:         "http://192.168.88.XX",
  icon:        "🖨️",
  description: "Bambu Lab printer",
  tags:        ["printing"],
  checkUrl:    "http://192.168.88.XX",
  stats: [
    { key: "bambu_x1_carbon_state",        label: "State",    endpoint: "slow" },
    { key: "bambu_x1_carbon_progress",     label: "Progress", endpoint: "slow", transform: "v => v + '%'" },
    { key: "bambu_x1_carbon_layer",        label: "Layer",    endpoint: "slow" },
    { key: "bambu_x1_carbon_total_layers", label: "Total",    endpoint: "slow" },
  ],
},
```

## Adding a New Group (index.html)

```js
{
  name: "My Group",
  icon: "◈",
  services: [
    // services here
  ],
},
```

---

## Service Management

| Task                          | Command                                        |
|-------------------------------|------------------------------------------------|
| Check dashboard status        | `sudo systemctl status veracious-dashboard`    |
| Check stats status            | `sudo systemctl status veracious-stats`        |
| Restart after config change   | `sudo systemctl restart veracious-stats`       |
| View stats logs               | `journalctl -u veracious-stats -f`             |
| Test stats API                | `curl http://localhost:8889/stats`             |
| Test fast stats               | `curl http://localhost:8889/stats/fast`        |
| Test slow stats               | `curl http://localhost:8889/stats/slow`        |

---

## Stat Refresh Rates

- **Fast stats** (network speeds): every 5 seconds
- **Slow stats** (Pi-hole, HA, Plex etc): every 60 seconds
- **Status dots** (online/offline): every 60 seconds

These can be adjusted in the `CONFIG` object at the top of `index.html`.

---

## Access From Other Devices

Find your machine's IP:
```bash
hostname -I
```

Then open `http://YOUR_IP:8888` from any device on your network.

---

## Requirements

- Linux (tested on Linux Mint, Ubuntu, Debian)
- Python 3.8+
- Internet access for Google Fonts (optional — works offline with fallback fonts)
