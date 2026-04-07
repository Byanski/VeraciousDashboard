# =============================================================
#  VERACIOUS DASHBOARD — BACKEND CONFIG
#  Edit this file to match your home network setup.
#  Then run: sudo systemctl restart veracious-stats
# =============================================================

# -------------------------------------------------------------
#  GENERAL
# -------------------------------------------------------------
STATS_PORT = 8889          # Port the stats API runs on
CACHE_SECONDS = 5          # How often to refresh fast stats (speeds)
SLOW_CACHE_SECONDS = 60    # How often to refresh slow stats (pihole, etc)


# -------------------------------------------------------------
#  MIKROTIK ROUTER  (uncomment to enable)
# -------------------------------------------------------------
MIKROTIK_ENABLED = True
MIKROTIK_HOST    = '192.168.88.1'
MIKROTIK_USER    = 'admin'
MIKROTIK_PASS    = ''
MIKROTIK_PORT    = 8728
MIKROTIK_WAN_IF  = 'ether1'   # Your WAN interface name


# -------------------------------------------------------------
#  PI-HOLE v6  (uncomment to enable)
# -------------------------------------------------------------
PIHOLE_ENABLED = True
PIHOLE_HOST    = 'http://192.168.88.244:8080'
PIHOLE_PASS    = ''


# -------------------------------------------------------------
#  PROXMOX  (uncomment PROXMOX_ENABLED = True to enable)
#  Create an API token in Proxmox: Datacenter > API Tokens
# -------------------------------------------------------------
PROXMOX_ENABLED   = False
# PROXMOX_HOST      = 'https://192.168.88.XX:8006'
# PROXMOX_USER      = 'root@pam'
# PROXMOX_TOKEN_ID  = 'dashboard'
# PROXMOX_TOKEN     = 'YOUR_API_TOKEN'
# PROXMOX_NODE      = 'pve'        # Your Proxmox node name
# PROXMOX_VERIFY_SSL = False


# -------------------------------------------------------------
#  TRUENAS  (uncomment TRUENAS_ENABLED = True to enable)
#  Generate API key in TrueNAS: Account > API Keys
# -------------------------------------------------------------
TRUENAS_ENABLED = False
# TRUENAS_HOST    = 'http://192.168.88.XX'
# TRUENAS_API_KEY = 'YOUR_API_KEY'


# -------------------------------------------------------------
#  UNIFI CONTROLLER  (uncomment UNIFI_ENABLED = True to enable)
#  Uses local controller credentials
# -------------------------------------------------------------
UNIFI_ENABLED = False
# UNIFI_HOST    = 'https://192.168.88.XX:8443'
# UNIFI_USER    = 'admin'
# UNIFI_PASS    = 'YOUR_PASSWORD'
# UNIFI_SITE    = 'default'
# UNIFI_VERIFY_SSL = False


# -------------------------------------------------------------
#  PLEX  (uncomment PLEX_ENABLED = True to enable)
#  Get token from: https://www.plexopedia.com/plex-media-server/general/plex-token/
# -------------------------------------------------------------
PLEX_ENABLED = False
# PLEX_HOST    = 'http://192.168.88.XX:32400'
# PLEX_TOKEN   = 'YOUR_PLEX_TOKEN'


# -------------------------------------------------------------
#  HOME ASSISTANT  (uncomment HA_ENABLED = True to enable)
#  Generate Long-Lived Access Token in HA profile settings
# -------------------------------------------------------------
HA_ENABLED = True
HA_HOST    = 'http://192.168.88.253:8123'
HA_TOKEN   = ''


# -------------------------------------------------------------
#  PORTAINER  (uncomment PORTAINER_ENABLED = True to enable)
#  Generate API token in Portainer: Account > Access Tokens
# -------------------------------------------------------------
PORTAINER_ENABLED = False
# PORTAINER_HOST    = 'http://192.168.88.XX:9000'
# PORTAINER_TOKEN   = 'YOUR_API_TOKEN'


# -------------------------------------------------------------
#  OPEN WEBUI / OLLAMA  (uncomment to enable)
# -------------------------------------------------------------
OPENWEBUI_ENABLED = True
OPENWEBUI_HOST    = 'http://192.168.88.236:3000'
OPENWEBUI_TOKEN   = ''
   # Optional, if auth is enabled

OLLAMA_ENABLED = True
OLLAMA_HOST    = 'http://192.168.88.236:11434'


# -------------------------------------------------------------
#  UNRAID  (uncomment UNRAID_ENABLED = True to enable)
#  Requires Unraid API plugin or Community Apps
# -------------------------------------------------------------
UNRAID_ENABLED = False
# UNRAID_HOST    = 'http://192.168.88.XX'
# UNRAID_API_KEY = 'YOUR_API_KEY'


# -------------------------------------------------------------
#  GRAFANA  (uncomment GRAFANA_ENABLED = True to enable)
#  Generate API key in Grafana: Configuration > API Keys
# -------------------------------------------------------------
GRAFANA_ENABLED = False
# GRAFANA_HOST    = 'http://192.168.88.XX:3000'
# GRAFANA_TOKEN   = 'YOUR_API_TOKEN'


# =============================================================
#  MEDIA & MESSAGING
# =============================================================
 
# -------------------------------------------------------------
#  BLUEBUBBLES  (uncomment BLUEBUBBLES_ENABLED = True to enable)
#  BlueBubbles relays iMessage from a macOS machine to other devices.
#  The server runs on port 1234 by default (check your BB server settings).
#  The password is set in the BlueBubbles Server app under Settings > Password.
#  No API key needed — all requests use ?password= as a query parameter.
# -------------------------------------------------------------
BLUEBUBBLES_ENABLED = False
# BLUEBUBBLES_HOST    = 'http://192.168.88.XX:1234'   # Your BlueBubbles server IP:port
# BLUEBUBBLES_PASS    = 'YOUR_BLUEBUBBLES_PASSWORD'
 
 
# -------------------------------------------------------------
#  IMMICH  (uncomment IMMICH_ENABLED = True to enable)
#  Self-hosted Google Photos alternative. Runs on port 2283 by default.
#  Generate an API key in Immich: Account Settings > API Keys
#  The key needs the 'server.statistics' permission, or just use an admin key.
#  Note: requires Immich v1.118 or newer (uses /api/server/* endpoints).
# -------------------------------------------------------------
IMMICH_ENABLED  = False
# IMMICH_HOST     = 'http://192.168.88.XX:2283'
# IMMICH_API_KEY  = 'YOUR_IMMICH_API_KEY'


# =============================================================
#  GAME SERVERS
# =============================================================

# -------------------------------------------------------------
#  AMP (CubeCoders)  (uncomment AMP_ENABLED = True to enable)
#  AMP runs on port 8080 by default.
#  Create a dedicated API user in AMP: Configuration > User Manager
#  Give the user the "Super Admins" role or a role with API access.
#  AMP_INSTANCES: List of instance IDs to pull stats for.
#    Leave as [] to auto-discover all instances on this AMP install.
# -------------------------------------------------------------
AMP_ENABLED = False
# AMP_HOST      = 'http://192.168.88.XX:8080'   # Your AMP panel URL
# AMP_USER      = 'admin'
# AMP_PASS      = 'YOUR_AMP_PASSWORD'
# AMP_INSTANCES = []                              # e.g. ['abc123', 'def456'] or [] for all


# =============================================================
#  3D PRINTERS
# =============================================================

# -------------------------------------------------------------
#  OCTOPRINT  (uncomment OCTOPRINT_ENABLED = True to enable)
#  Generate an API key in OctoPrint: Settings > API > API Key
#  Add multiple printers by duplicating the block and changing
#  the variable suffix, e.g. OCTOPRINT_HOST_2, OCTOPRINT_KEY_2
#  then list them in OCTOPRINT_PRINTERS below.
# -------------------------------------------------------------
OCTOPRINT_ENABLED = False
# OCTOPRINT_PRINTERS = [
#     {'name': 'Printer 1', 'host': 'http://192.168.88.XX', 'key': 'YOUR_API_KEY'},
#     {'name': 'Printer 2', 'host': 'http://192.168.88.XY', 'key': 'YOUR_API_KEY'},
# ]


# -------------------------------------------------------------
#  MOONRAKER / KLIPPER  (uncomment MOONRAKER_ENABLED = True to enable)
#  Moonraker runs on port 7125 by default. No auth needed on
#  most local installs, but if you use API keys add them below.
#  Add multiple printers by listing them in MOONRAKER_PRINTERS.
# -------------------------------------------------------------
MOONRAKER_ENABLED = False
# MOONRAKER_PRINTERS = [
#     {'name': 'Voron',    'host': 'http://192.168.88.XX:7125', 'key': ''},
#     {'name': 'Ender 3',  'host': 'http://192.168.88.XY:7125', 'key': ''},
# ]


# -------------------------------------------------------------
#  BAMBU CONNECT (LAN mode)  (uncomment BAMBU_ENABLED = True to enable)
#  Requires Bambu LAN mode to be ON in your printer's network settings.
#  Serial number is on the sticker inside the door / on the box.
#  Access code is in the printer's LAN settings screen.
#  Port 1883 is the local MQTT port — do not change unless you know why.
#  pip install paho-mqtt  (added to setup.sh automatically)
# -------------------------------------------------------------
BAMBU_ENABLED = False
# BAMBU_PRINTERS = [
#     {
#         'name':         'X1 Carbon',
#         'host':         '192.168.88.XX',   # Printer IP — no http://
#         'serial':       'YOUR_SERIAL',      # e.g. 01P00A...
#         'access_code':  'YOUR_ACCESS_CODE', # 8-char code from LAN settings
#         'port':         1883,
#     },
# ]


# -------------------------------------------------------------
#  OBICO (The Spaghetti Detective)  (uncomment OBICO_ENABLED = True to enable)
#  Get your API key from: obico.io > Account > API Key
#  For self-hosted Obico, change OBICO_HOST to your server URL.
# -------------------------------------------------------------
OBICO_ENABLED = False
# OBICO_HOST    = 'https://app.obico.io'      # or 'http://192.168.88.XX:3334' if self-hosted
# OBICO_API_KEY = 'YOUR_OBICO_API_KEY'
