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
MIKROTIK_PASS    = '11496Cameron#!'
MIKROTIK_PORT    = 8728
MIKROTIK_WAN_IF  = 'ether1'   # Your WAN interface name


# -------------------------------------------------------------
#  PI-HOLE v6  (uncomment to enable)
# -------------------------------------------------------------
PIHOLE_ENABLED = True
PIHOLE_HOST    = 'http://192.168.88.244:8080'
PIHOLE_PASS    = '11496Cameron#!'


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
# HA_TOKEN   = 'YOUR_LONG_LIVED_ACCESS_TOKEN'


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
# OPENWEBUI_TOKEN   = 'YOUR_API_TOKEN'   # Optional, if auth is enabled

OLLAMA_ENABLED = true
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
