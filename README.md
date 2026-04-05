# ⬡ Veracious Dashboard

A fast, self-hosted home network dashboard with live stats.
Zero cloud dependencies. Zero build tools. Just Python and a browser.

---

## Table of Contents

- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [File Structure](#file-structure)
- [Step-by-Step Setup](#step-by-step-setup)
  - [Step 1 — Run the installer](#step-1--run-the-installer)
  - [Step 2 — Configure your integrations](#step-2--configure-your-integrations)
  - [Step 3 — Add your services to the UI](#step-3--add-your-services-to-the-ui)
  - [Step 4 — Restart the stats service](#step-4--restart-the-stats-service)
- [Supported Integrations](#supported-integrations)
  - [Network & Infrastructure](#network--infrastructure)
  - [NAS & Storage](#nas--storage)
  - [Media Servers](#media-servers)
  - [Music & Audiobooks](#music--audiobooks)
  - [Photos](#photos)
  - [Communication](#communication)
  - [Smart Home & Automation](#smart-home--automation)
  - [Cloud & Self-Hosted Apps](#cloud--self-hosted-apps)
  - [AI & Machine Learning](#ai--machine-learning)
  - [Monitoring & Containers](#monitoring--containers)
- [Customizing the UI (index.html)](#customizing-the-ui-indexhtml)
  - [Adding a Service Card](#adding-a-service-card)
  - [Adding a Group](#adding-a-group)
  - [Stat Keys Reference](#stat-keys-reference)
  - [Using Transforms](#using-transforms)
- [Adding a New Backend Integration](#adding-a-new-backend-integration)
- [Service Management](#service-management)
- [Accessing From Other Devices](#accessing-from-other-devices)
- [Troubleshooting](#troubleshooting)
- [Requirements](#requirements)

---

## Quick Start

```bash
git clone <your-repo> veracious-dashboard
cd veracious-dashboard
bash setup.sh
```

- **Dashboard**: http://localhost:8888
- **Stats API**: http://localhost:8889/stats

---

## How It Works

Veracious has two components that run as background system services:

**`veracious-dashboard`** serves `index.html` on port 8888 using Python's built-in HTTP server. The dashboard is a single HTML file with no build step — just edit and refresh.

**`veracious-stats`** runs `stats.py` on port 8889. This is a Flask API that polls your self-hosted services in the background and caches the results. The frontend fetches from this API on a timer and updates the stat values on each card without reloading the page.

Stats are split into two caches:

| Cache | Default interval | What it contains |
|-------|-----------------|------------------|
| Fast  | Every 5 seconds  | Network speeds (MikroTik upload/download) |
| Slow  | Every 60 seconds | Everything else (Pi-hole, HA, Plex, etc.) |

Both intervals can be changed in `config.py` and in the `CONFIG` object at the top of `index.html`.

---

## File Structure

```
veracious-dashboard/
├── index.html    ← Dashboard UI — add your services here
├── stats.py      ← Stats collector backend — add new integrations here
├── config.py     ← Your credentials and IPs — edit this
├── setup.sh      ← One-time installer
└── README.md
```

---

## Step-by-Step Setup

### Step 1 — Run the installer

```bash
bash setup.sh
```

This installs Python dependencies, creates two systemd services (`veracious-dashboard` and `veracious-stats`), and starts them automatically. Both services are enabled to start on boot.

### Step 2 — Configure your integrations

Open `config.py`. For each service you want stats from:

1. Set `SERVICE_ENABLED = True`
2. Uncomment the config lines below it
3. Fill in your IP address, port, and credentials

Each integration section in `config.py` includes a comment explaining exactly where to find the required credentials.

**Example — enabling Pi-hole:**
```python
PIHOLE_ENABLED = True
PIHOLE_HOST    = 'http://192.168.1.100:8080'
PIHOLE_PASS    = 'yourpassword'
```

### Step 3 — Add your services to the UI

Open `index.html` and scroll to the `CONFIG` object near the top of the `<script>` block. This is the only section you need to edit. Add your services following the examples already there. See [Customizing the UI](#customizing-the-ui-indexhtml) for full details and a stat key reference.

### Step 4 — Restart the stats service

Whenever you change `config.py`, restart the stats backend:

```bash
sudo systemctl restart veracious-stats
```

Changes to `index.html` take effect immediately on the next browser refresh — no restart needed.

---

## Supported Integrations

### Network & Infrastructure

| Service | Stats | Notes |
|---------|-------|-------|
| **MikroTik** | WAN upload MB/s, download MB/s, DHCP device count | Requires `routeros-api` Python package (installed by `setup.sh`). Uses the RouterOS API on port 8728. |
| **Pi-hole v6** | Queries blocked today, block rate %, blocklist size | Uses the Pi-hole v6 REST API with session auth. Not compatible with Pi-hole v5. |
| **UniFi** | Connected client count | Works with self-hosted UniFi Network Application. Set `UNIFI_VERIFY_SSL = False` for self-signed certs. |

### NAS & Storage

| Service | Stats | Notes |
|---------|-------|-------|
| **TrueNAS** (SCALE/CORE) | Pool count, pool health, disk count | Uses the TrueNAS v2 REST API. Generate an API key in Account > API Keys. |
| **Synology DSM** | Volume count, used storage GB, total storage GB, used % | Uses the Synology Web API (DSM 7.x). You can use your regular DSM credentials or create a dedicated read-only user. |

### Media Servers

| Service | Stats | Notes |
|---------|-------|-------|
| **Plex** | Active streams | Requires your Plex token. See [how to find your Plex token](https://www.plexopedia.com/plex-media-server/general/plex-token/). |
| **Jellyfin** | Active streams, library count | Generate an API key in Dashboard > Advanced > API Keys. |
| **Emby** | Active streams, library count | Generate an API key in Dashboard > Advanced > API Keys. |

### Music & Audiobooks

| Service | Stats | Notes |
|---------|-------|-------|
| **Navidrome** | Artist count, playlist count | Uses the built-in Subsonic-compatible API. No extra setup — just your Navidrome username and password. |
| **Audiobookshelf** | Library count, active listening sessions | Get your API token from Settings > Users > (your user) > API Token. |

### Photos

| Service | Stats | Notes |
|---------|-------|-------|
| **Immich** | Photo count, video count, storage used GB | Generate an API key in Account Settings > API Keys. |

### Communication

| Service | Stats | Notes |
|---------|-------|-------|
| **BlueBubbles** | Total chat count, server version | BlueBubbles lets you send and receive iMessages from any device via a Mac server. The password is set in the BlueBubbles Server app under Settings > Connection & Security. |

### Smart Home & Automation

| Service | Stats | Notes |
|---------|-------|-------|
| **Home Assistant** | Entity count, automation count | Generate a Long-Lived Access Token in your HA profile under Long-Lived Access Tokens. |
| **Mealie** | Recipe count, meals planned today | Generate an API token in User Settings > API Tokens. |

### Cloud & Self-Hosted Apps

| Service | Stats | Notes |
|---------|-------|-------|
| **Nextcloud** | Active users (last 24h), total file count, storage used GB | Requires the built-in `serverinfo` app (enabled by default). Use an app password rather than your main password (Settings > Security > Devices & sessions). |
| **Vaultwarden** | User count | Requires `ADMIN_TOKEN` to be set in your Vaultwarden environment. Only the user count is exposed — no vault data is accessed. |

### AI & Machine Learning

| Service | Stats | Notes |
|---------|-------|-------|
| **Ollama** | Loaded model count | No authentication required by default. Just set the host and port. |
| **Open WebUI** | Model count | `OPENWEBUI_TOKEN` is optional — only needed if authentication is enabled. Generate a token in User Settings > Account > API Key. |

### Monitoring & Containers

| Service | Stats | Notes |
|---------|-------|-------|
| **Proxmox** | CPU %, RAM %, running VM count | Create a read-only API token in Datacenter > API Tokens. Minimum required permissions: `Sys.Audit` and `VM.Audit` on `/`. |
| **Portainer** | Running containers, total containers | Generate an API token in Account > Access Tokens. Targets endpoint ID 1 by default. |
| **Grafana** | Dashboard count | Generate a service account token in Administration > Service Accounts. |

---

## Customizing the UI (index.html)

All configuration lives in the `CONFIG` object near the top of the `<script>` block in `index.html`. Everything below the `/* APP */` comment is the rendering engine — you don't need to touch it.

### Adding a Service Card

```js
{
  name:        "My Service",
  url:         "http://192.168.1.XX:PORT",      // Opens when card is clicked
  icon:        "🔧",                             // Any emoji or Unicode character
  description: "What it does",
  tags:        ["category"],                     // Small labels shown on the card
  checkUrl:    "http://192.168.1.XX:PORT",       // Pinged for online/offline status dot
  stats: [
    { key: "stat_key", label: "Label", endpoint: "slow" },
    { key: "stat_key", label: "Label", endpoint: "fast" },
    { key: "stat_key", label: "Label", endpoint: "slow", transform: "v => v + '%'" },
  ],
},
```

**Field reference:**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name on the card |
| `url` | Yes | URL opened when the card is clicked |
| `icon` | No | Emoji or character shown next to the name |
| `description` | No | Short description shown below the name |
| `tags` | No | Array of strings shown as small labels |
| `checkUrl` | No | URL pinged to determine online/offline status. If omitted, no status dot is shown. |
| `stats` | No | Array of stat items pulled from the API (see below) |

**Stat item fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `key` | Yes | The stat key returned by the API (see [Stat Keys Reference](#stat-keys-reference)) |
| `label` | Yes | Label displayed under the value |
| `endpoint` | Yes | `"fast"` (updates every 5s) or `"slow"` (updates every 60s) |
| `transform` | No | A JavaScript arrow function to format the value before display |

### Adding a Group

Groups are sections that contain multiple service cards. Add them to the `groups` array:

```js
{
  name: "My Group",
  icon: "◈",
  services: [
    // service objects go here
  ],
},
```

### Stat Keys Reference

These are all the keys currently returned by the stats API. Use them in the `key` field of a stat item.

**Fast stats** (`endpoint: "fast"`) — updated every 5 seconds:

| Key | Description |
|-----|-------------|
| `mikrotik_up_mbps` | WAN upload speed in MB/s |
| `mikrotik_down_mbps` | WAN download speed in MB/s |
| `mikrotik_devices` | Active DHCP lease count |

**Slow stats** (`endpoint: "slow"`) — updated every 60 seconds:

| Key | Description |
|-----|-------------|
| `pihole_blocked` | Queries blocked today |
| `pihole_percent` | Block rate as a decimal (e.g. `14.2`) |
| `pihole_total` | Total queries today |
| `pihole_gravity` | Number of domains in the blocklist |
| `proxmox_cpu_pct` | Node CPU usage as a decimal (e.g. `23.5`) |
| `proxmox_mem_pct` | Node RAM usage as a decimal |
| `proxmox_vms` | Number of running VMs |
| `truenas_pools` | Number of storage pools |
| `truenas_healthy` | `"Yes"` or `"No"` |
| `truenas_disks` | Total disk count |
| `synology_volumes` | Number of volumes |
| `synology_used_pct` | Storage used % |
| `synology_used_gb` | Storage used in GB |
| `synology_total_gb` | Total storage in GB |
| `unifi_clients` | Connected client count |
| `plex_streams` | Active Plex streams |
| `jellyfin_streams` | Active Jellyfin streams |
| `jellyfin_libraries` | Jellyfin library count |
| `emby_streams` | Active Emby streams |
| `emby_libraries` | Emby library count |
| `audiobookshelf_libraries` | Audiobookshelf library count |
| `audiobookshelf_active` | Active listening sessions |
| `navidrome_artists` | Artist count |
| `navidrome_playlists` | Playlist count |
| `immich_photos` | Total photo count |
| `immich_videos` | Total video count |
| `immich_usage_gb` | Storage used in GB |
| `nextcloud_users` | Users active in last 24h |
| `nextcloud_files` | Total file count |
| `nextcloud_used_gb` | Storage used in GB |
| `vaultwarden_users` | Registered user count |
| `bluebubbles_chats` | Total chat count |
| `bluebubbles_version` | Server version string |
| `mealie_recipes` | Total recipe count |
| `mealie_today` | Meals on today's plan |
| `ha_entities` | Home Assistant entity count |
| `ha_automations` | Automation count |
| `portainer_running` | Running container count |
| `portainer_total` | Total container count |
| `ollama_models` | Loaded model count |
| `openwebui_models` | Available model count |
| `grafana_dashboards` | Dashboard count |

### Using Transforms

The `transform` field accepts any JavaScript arrow function as a string. The raw API value is passed as `v`.

```js
// Append a unit
{ key: "mikrotik_up_mbps", label: "Upload", endpoint: "fast", transform: "v => v + ' MB/s'" }

// Append a percent sign
{ key: "proxmox_cpu_pct", label: "CPU", endpoint: "slow", transform: "v => v + '%'" }

// Convert a raw number to a friendlier format
{ key: "pihole_gravity", label: "Blocklist", endpoint: "slow", transform: "v => (v/1000).toFixed(0) + 'k'" }

// Round to one decimal
{ key: "synology_used_gb", label: "Used", endpoint: "slow", transform: "v => v.toFixed(1) + ' GB'" }
```

---

## Adding a New Backend Integration

To add stats from a service not yet supported, follow this pattern:

**1. Add config variables to `config.py`:**
```python
MYSERVICE_ENABLED = False
# MYSERVICE_HOST    = 'http://192.168.1.XX:PORT'
# MYSERVICE_TOKEN   = 'YOUR_API_TOKEN'
```

**2. Add a collector function to `stats.py`:**
```python
def get_myservice_stats():
    if not cfg.MYSERVICE_ENABLED:
        return {}
    try:
        headers = {'Authorization': f'Bearer {cfg.MYSERVICE_TOKEN}'}
        res = requests.get(f'{cfg.MYSERVICE_HOST}/api/some/endpoint', headers=headers, timeout=5)
        data = res.json()
        return {
            'myservice_thing': data['some_value'],
        }
    except Exception as e:
        return {'myservice_error': str(e)}
```

**3. Register it in `update_slow_cache()` and the startup primer:**
```python
# In update_slow_cache():
data.update(get_myservice_stats())

# In _all_slow_fns list at the bottom:
get_myservice_stats,
```

**4. Use the new key in `index.html`:**
```js
stats: [
  { key: "myservice_thing", label: "Thing", endpoint: "slow" },
]
```

**5. Restart the stats service:**
```bash
sudo systemctl restart veracious-stats
```

---

## Service Management

| Task | Command |
|------|---------|
| Check dashboard status | `sudo systemctl status veracious-dashboard` |
| Check stats status | `sudo systemctl status veracious-stats` |
| Restart after config change | `sudo systemctl restart veracious-stats` |
| Stop everything | `sudo systemctl stop veracious-dashboard veracious-stats` |
| View stats logs (live) | `journalctl -u veracious-stats -f` |
| View dashboard logs | `journalctl -u veracious-dashboard -f` |
| Test full stats API | `curl http://localhost:8889/stats` |
| Test fast stats only | `curl http://localhost:8889/stats/fast` |
| Test slow stats only | `curl http://localhost:8889/stats/slow` |
| Health check | `curl http://localhost:8889/health` |

---

## Accessing From Other Devices

Find your machine's local IP:
```bash
hostname -I
```

Then open `http://YOUR_IP:8888` from any device on your network.

You'll also need to update the `statsBase` URL in `index.html` so the dashboard fetches stats from the correct address:

```js
const CONFIG = {
  statsBase: 'http://YOUR_IP:8889',   // ← change this
  ...
```

Otherwise, browsers on other devices will try to reach `localhost:8889` on themselves rather than your server.

---

## Troubleshooting

**Stats show `…` and never update**
The frontend can't reach the stats backend. Check:
- Is `veracious-stats` running? `sudo systemctl status veracious-stats`
- Is `statsBase` in `index.html` pointing to the correct IP/port?
- Check the logs: `journalctl -u veracious-stats -f`

**A specific stat shows an error in the API response**
Run `curl http://localhost:8889/stats` and look for keys ending in `_error`. The value will be the Python exception message, which usually indicates a wrong IP, wrong port, wrong credentials, or an incompatible API version.

**`config.py` syntax error / service won't start**
Common mistakes:
- `True`/`False` must be capitalized (Python is case-sensitive — `true` is not valid)
- Indentation errors from uncommented lines — make sure uncommented variables have no leading spaces
- Missing quotes around string values

Run this to check for syntax errors before restarting:
```bash
python3 -c "import config"
```

**Pi-hole stats aren't working**
This dashboard only supports Pi-hole **v6**. Pi-hole v5 uses a different API. Check your Pi-hole version in the web UI.

**Proxmox SSL errors**
Set `PROXMOX_VERIFY_SSL = False` in `config.py` if you're using a self-signed certificate (the default for Proxmox).

**UniFi/Synology SSL errors**
Similarly, set `UNIFI_VERIFY_SSL = False`. For Synology HTTPS, the stats collector already passes `verify=False`.

**Status dots show offline for everything**
Status dots are checked from your browser using `fetch()` in `no-cors` mode. If the service is online but the dot shows offline, the host may be blocking CORS preflight requests. This is cosmetic only — stats from the backend API are unaffected.

**Dashboard or stats service won't start after a reboot**
Check if Python or the project directory path changed. Re-run `setup.sh` to regenerate the service files with the current paths.

---

## Requirements

- Linux (tested on Linux Mint, Ubuntu, Debian)
- Python 3.8+
- Internet access for Google Fonts (optional — works offline with fallback fonts)

Python packages installed automatically by `setup.sh`:
- `flask`
- `requests`
- `routeros-api` (MikroTik only)
- `urllib3`
