# =============================================================
#  VERACIOUS DASHBOARD — BACKEND CONFIG
#  Edit this file to match your home network setup.
#  Then run: sudo systemctl restart veracious-stats
# =============================================================

# -------------------------------------------------------------
#  GENERAL
# -------------------------------------------------------------
STATS_PORT         = 8889   # Port the stats API runs on
CACHE_SECONDS      = 5      # How often to refresh fast stats (speeds)
SLOW_CACHE_SECONDS = 60     # How often to refresh slow stats


# -------------------------------------------------------------
#  MIKROTIK ROUTER
# -------------------------------------------------------------
MIKROTIK_ENABLED = False
# MIKROTIK_HOST    = '192.168.88.1'
# MIKROTIK_USER    = 'admin'
# MIKROTIK_PASS    = 'YOUR_PASSWORD'
# MIKROTIK_PORT    = 8728
# MIKROTIK_WAN_IF  = 'ether1'   # Your WAN interface name (check Winbox/WebFig)


# -------------------------------------------------------------
#  PI-HOLE v6
#  Password is the same one you use to log in to the web UI.
# -------------------------------------------------------------
PIHOLE_ENABLED = False
# PIHOLE_HOST    = 'http://192.168.88.XX:8080'
# PIHOLE_PASS    = 'YOUR_PASSWORD'


# -------------------------------------------------------------
#  PROXMOX
#  Create a read-only API token: Datacenter > API Tokens
#  Minimum permissions: Sys.Audit, VM.Audit on /
# -------------------------------------------------------------
PROXMOX_ENABLED    = False
# PROXMOX_HOST       = 'https://192.168.88.XX:8006'
# PROXMOX_USER       = 'root@pam'
# PROXMOX_TOKEN_ID   = 'dashboard'
# PROXMOX_TOKEN      = 'YOUR_API_TOKEN'
# PROXMOX_NODE       = 'pve'          # Your Proxmox node name
# PROXMOX_VERIFY_SSL = False


# -------------------------------------------------------------
#  TRUENAS (SCALE or CORE)
#  Generate API key: TrueNAS UI > Account > API Keys > Add
# -------------------------------------------------------------
TRUENAS_ENABLED = False
# TRUENAS_HOST    = 'http://192.168.88.XX'
# TRUENAS_API_KEY = 'YOUR_API_KEY'


# -------------------------------------------------------------
#  SYNOLOGY DSM
#  Use your regular DSM login credentials, or create a
#  dedicated read-only DSM user for the dashboard.
#  Tested on DSM 7.x.
# -------------------------------------------------------------
SYNOLOGY_ENABLED = False
# SYNOLOGY_HOST    = 'http://192.168.88.XX:5000'   # or :5001 for HTTPS
# SYNOLOGY_USER    = 'admin'
# SYNOLOGY_PASS    = 'YOUR_PASSWORD'


# -------------------------------------------------------------
#  UNIFI CONTROLLER
#  Works with self-hosted UniFi Network Application.
#  Set UNIFI_VERIFY_SSL = False for self-signed certificates.
# -------------------------------------------------------------
UNIFI_ENABLED    = False
# UNIFI_HOST       = 'https://192.168.88.XX:8443'
# UNIFI_USER       = 'admin'
# UNIFI_PASS       = 'YOUR_PASSWORD'
# UNIFI_SITE       = 'default'
# UNIFI_VERIFY_SSL = False


# -------------------------------------------------------------
#  PLEX
#  Get your token: https://www.plexopedia.com/plex-media-server/general/plex-token/
# -------------------------------------------------------------
PLEX_ENABLED = False
# PLEX_HOST    = 'http://192.168.88.XX:32400'
# PLEX_TOKEN   = 'YOUR_PLEX_TOKEN'


# -------------------------------------------------------------
#  JELLYFIN
#  Generate an API key: Dashboard > Advanced > API Keys > +
# -------------------------------------------------------------
JELLYFIN_ENABLED  = False
# JELLYFIN_HOST     = 'http://192.168.88.XX:8096'
# JELLYFIN_API_KEY  = 'YOUR_API_KEY'


# -------------------------------------------------------------
#  EMBY
#  Generate an API key: Dashboard > Advanced > API Keys > New Key
# -------------------------------------------------------------
EMBY_ENABLED  = False
# EMBY_HOST     = 'http://192.168.88.XX:8096'
# EMBY_API_KEY  = 'YOUR_API_KEY'


# -------------------------------------------------------------
#  AUDIOBOOKSHELF
#  Get your API token: Settings > Users > (your user) > API Token
# -------------------------------------------------------------
AUDIOBOOKSHELF_ENABLED = False
# AUDIOBOOKSHELF_HOST    = 'http://192.168.88.XX:13378'
# AUDIOBOOKSHELF_TOKEN   = 'YOUR_API_TOKEN'


# -------------------------------------------------------------
#  NAVIDROME
#  Uses the built-in Subsonic API. No extra setup required.
#  Credentials are your regular Navidrome username/password.
# -------------------------------------------------------------
NAVIDROME_ENABLED = False
# NAVIDROME_HOST    = 'http://192.168.88.XX:4533'
# NAVIDROME_USER    = 'admin'
# NAVIDROME_PASS    = 'YOUR_PASSWORD'


# -------------------------------------------------------------
#  IMMICH
#  Generate an API key: Account Settings > API Keys > New API Key
# -------------------------------------------------------------
IMMICH_ENABLED  = False
# IMMICH_HOST     = 'http://192.168.88.XX:2283'
# IMMICH_API_KEY  = 'YOUR_API_KEY'


# -------------------------------------------------------------
#  NEXTCLOUD
#  Requires the built-in serverinfo app (enabled by default).
#  Recommended: create an app password in Security settings
#  instead of using your main password.
# -------------------------------------------------------------
NEXTCLOUD_ENABLED = False
# NEXTCLOUD_HOST    = 'http://192.168.88.XX'
# NEXTCLOUD_USER    = 'admin'
# NEXTCLOUD_PASS    = 'YOUR_APP_PASSWORD'


# -------------------------------------------------------------
#  VAULTWARDEN
#  Requires ADMIN_TOKEN to be set in your Vaultwarden config.
#  Only exposes user count — no vault data is accessed.
# -------------------------------------------------------------
VAULTWARDEN_ENABLED      = False
# VAULTWARDEN_HOST         = 'http://192.168.88.XX:8080'
# VAULTWARDEN_ADMIN_TOKEN  = 'YOUR_ADMIN_TOKEN'


# -------------------------------------------------------------
#  BLUEBUBBLES
#  Password is the server password set in the BlueBubbles
#  Server app on your Mac under Settings > Connection & Security.
# -------------------------------------------------------------
BLUEBUBBLES_ENABLED = False
# BLUEBUBBLES_HOST    = 'http://192.168.88.XX:1234'
# BLUEBUBBLES_PASS    = 'YOUR_SERVER_PASSWORD'


# -------------------------------------------------------------
#  MEALIE
#  Generate an API token: User Settings > API Tokens > Generate
# -------------------------------------------------------------
MEALIE_ENABLED = False
# MEALIE_HOST    = 'http://192.168.88.XX:9925'
# MEALIE_TOKEN   = 'YOUR_API_TOKEN'


# -------------------------------------------------------------
#  HOME ASSISTANT
#  Generate a Long-Lived Access Token:
#  Profile > Long-Lived Access Tokens > Create Token
# -------------------------------------------------------------
HA_ENABLED = False
# HA_HOST    = 'http://192.168.88.XX:8123'
# HA_TOKEN   = 'YOUR_LONG_LIVED_ACCESS_TOKEN'


# -------------------------------------------------------------
#  PORTAINER
#  Generate an API token: Account > Access Tokens > Add access token
# -------------------------------------------------------------
PORTAINER_ENABLED = False
# PORTAINER_HOST    = 'http://192.168.88.XX:9000'
# PORTAINER_TOKEN   = 'YOUR_API_TOKEN'


# -------------------------------------------------------------
#  OLLAMA
#  No authentication required by default.
# -------------------------------------------------------------
OLLAMA_ENABLED = False
# OLLAMA_HOST    = 'http://192.168.88.XX:11434'


# -------------------------------------------------------------
#  OPEN WEBUI
#  OPENWEBUI_TOKEN is optional — only needed if auth is enabled.
#  Generate token: User Settings > Account > API Key
# -------------------------------------------------------------
OPENWEBUI_ENABLED = False
# OPENWEBUI_HOST    = 'http://192.168.88.XX:3000'
# OPENWEBUI_TOKEN   = 'YOUR_API_TOKEN'


# -------------------------------------------------------------
#  GRAFANA
#  Generate a service account token:
#  Administration > Service Accounts > Add service account token
# -------------------------------------------------------------
GRAFANA_ENABLED = False
# GRAFANA_HOST    = 'http://192.168.88.XX:3000'
# GRAFANA_TOKEN   = 'YOUR_SERVICE_ACCOUNT_TOKEN'
