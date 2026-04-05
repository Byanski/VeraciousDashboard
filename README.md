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

| Service        | Stats available                          |
|----------------|------------------------------------------|
| MikroTik       | WAN upload/download MB/s, device count   |
| Pi-hole v6     | Blocked today, block rate, blocklist size|
| Proxmox        | CPU %, RAM %, running VMs                |
| TrueNAS        | Pool count, health, disk count           |
| UniFi          | Connected client count                   |
| Plex           | Active streams                           |
| Home Assistant | Entity count, automation count           |
| Portainer      | Running containers, total containers     |
| Ollama         | Loaded model count                       |
| Open WebUI     | Model count                              |
| Grafana        | Dashboard count                          |

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
