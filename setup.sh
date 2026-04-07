#!/bin/bash
# =============================================================
#  VERACIOUS DASHBOARD — Interactive Setup Script
#  Walks you through enabling each integration, fills
#  config.py automatically, installs deps, opens firewall.
#  Usage: bash setup.sh
# =============================================================

set -e

DASHBOARD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON=$(which python3)
USERNAME=$(whoami)
CONFIG="$DASHBOARD_DIR/config.py"

# ── Colours ──────────────────────────────────────────────────
C_RESET='\033[0m'
C_BOLD='\033[1m'
C_CYAN='\033[36m'
C_GREEN='\033[32m'
C_YELLOW='\033[33m'
C_DIM='\033[2m'

# ── Helpers ──────────────────────────────────────────────────
header() {
  echo ""
  echo -e "${C_CYAN}${C_BOLD}╔══════════════════════════════════════════╗${C_RESET}"
  echo -e "${C_CYAN}${C_BOLD}║  $1${C_RESET}"
  echo -e "${C_CYAN}${C_BOLD}╚══════════════════════════════════════════╝${C_RESET}"
  echo ""
}

section() {
  echo ""
  echo -e "${C_CYAN}── $1 ──────────────────────────────────────${C_RESET}"
}

ok()   { echo -e "  ${C_GREEN}✓${C_RESET} $1"; }
info() { echo -e "  ${C_DIM}$1${C_RESET}"; }
warn() { echo -e "  ${C_YELLOW}⚠  $1${C_RESET}"; }

ask_yes_no() {
  # ask_yes_no "Question text" → returns 0 (yes) or 1 (no)
  local prompt="$1"
  while true; do
    echo -en "  ${C_BOLD}$prompt${C_RESET} ${C_DIM}[y/N]${C_RESET} "
    read -r ans
    case "${ans,,}" in
      y|yes) return 0 ;;
      n|no|"") return 1 ;;
      *) echo "  Please enter y or n." ;;
    esac
  done
}

ask_input() {
  # ask_input "Prompt" "default_value" → stores in $REPLY
  local prompt="$1"
  local default="$2"
  if [ -n "$default" ]; then
    echo -en "  ${C_BOLD}$prompt${C_RESET} ${C_DIM}[$default]${C_RESET} "
  else
    echo -en "  ${C_BOLD}$prompt${C_RESET} "
  fi
  read -r REPLY
  if [ -z "$REPLY" ] && [ -n "$default" ]; then
    REPLY="$default"
  fi
}

# Patch a line in config.py: set_config KEY VALUE
# Handles both  KEY = 'VALUE'  and  # KEY = 'VALUE'  (uncomments too)
set_config() {
  local key="$1"
  local value="$2"
  # Escape for sed replacement (forward slashes, ampersands, etc.)
  local escaped_val
  escaped_val=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g')

  # If line exists (commented or not), replace it; otherwise append
  if grep -qE "^#?\s*${key}\s*=" "$CONFIG"; then
    sed -i -E "s|^#?\s*${key}\s*=.*|${key} = ${escaped_val}|" "$CONFIG"
  else
    echo "${key} = ${value}" >> "$CONFIG"
  fi
}

set_config_bool() {
  local key="$1"
  local value="$2"   # True or False
  if grep -qE "^#?\s*${key}\s*=" "$CONFIG"; then
    sed -i -E "s|^#?\s*${key}\s*=.*|${key} = ${value}|" "$CONFIG"
  else
    echo "${key} = ${value}" >> "$CONFIG"
  fi
}

# ─────────────────────────────────────────────────────────────

header "VERACIOUS DASHBOARD SETUP"
echo  "  Dashboard directory : $DASHBOARD_DIR"
echo  "  Python              : $PYTHON"
echo  "  User                : $USERNAME"
echo  "  Config              : $CONFIG"

# ── Backup config ─────────────────────────────────────────────
section "Backing up config.py"
cp "$CONFIG" "${CONFIG}.bak"
ok "Backup saved to config.py.bak"

# ── Python dependencies ───────────────────────────────────────
section "Installing core Python dependencies"
$PYTHON -m pip install flask requests routeros-api urllib3 --break-system-packages --quiet
ok "flask, requests, routeros-api, urllib3 installed"

# ─────────────────────────────────────────────────────────────
#  SERVICE CONFIGURATION WIZARD
# ─────────────────────────────────────────────────────────────

header "SERVICE CONFIGURATION WIZARD"
echo  "  Answer each prompt to configure your integrations."
echo  "  Press Enter to skip / accept the default shown in [brackets]."

# ── MikroTik ─────────────────────────────────────────────────
section "MikroTik Router"
info "Provides WAN speeds and DHCP device count."
if ask_yes_no "Enable MikroTik integration?"; then
  set_config_bool "MIKROTIK_ENABLED" "True"
  ask_input "Router IP" "192.168.88.1";            set_config "MIKROTIK_HOST" "'$REPLY'"
  ask_input "Username"  "admin";                   set_config "MIKROTIK_USER" "'$REPLY'"
  ask_input "Password"  "";                        set_config "MIKROTIK_PASS" "'$REPLY'"
  ask_input "API port"  "8728";                    set_config "MIKROTIK_PORT" "$REPLY"
  ask_input "WAN interface name" "ether1";         set_config "MIKROTIK_WAN_IF" "'$REPLY'"
  ok "MikroTik configured"
else
  set_config_bool "MIKROTIK_ENABLED" "False"
  info "Skipped."
fi

# ── Pi-hole ───────────────────────────────────────────────────
section "Pi-hole v6"
info "Provides DNS block stats."
if ask_yes_no "Enable Pi-hole integration?"; then
  set_config_bool "PIHOLE_ENABLED" "True"
  ask_input "Pi-hole URL (include port)" "http://192.168.88.244:8080"
  set_config "PIHOLE_HOST" "'$REPLY'"
  ask_input "Pi-hole password" ""
  set_config "PIHOLE_PASS" "'$REPLY'"
  ok "Pi-hole configured"
else
  set_config_bool "PIHOLE_ENABLED" "False"
  info "Skipped."
fi

# ── Proxmox ───────────────────────────────────────────────────
section "Proxmox"
info "Provides CPU, RAM, and running VM stats. Create an API token in Proxmox: Datacenter > API Tokens."
if ask_yes_no "Enable Proxmox integration?"; then
  set_config_bool "PROXMOX_ENABLED" "True"
  ask_input "Proxmox URL" "https://192.168.88.XX:8006"
  set_config "PROXMOX_HOST" "'$REPLY'"
  ask_input "Proxmox user (e.g. root@pam)" "root@pam"
  set_config "PROXMOX_USER" "'$REPLY'"
  ask_input "API token ID (e.g. dashboard)" "dashboard"
  set_config "PROXMOX_TOKEN_ID" "'$REPLY'"
  ask_input "API token secret" ""
  set_config "PROXMOX_TOKEN" "'$REPLY'"
  ask_input "Node name" "pve"
  set_config "PROXMOX_NODE" "'$REPLY'"
  set_config_bool "PROXMOX_VERIFY_SSL" "False"
  ok "Proxmox configured"
else
  set_config_bool "PROXMOX_ENABLED" "False"
  info "Skipped."
fi

# ── TrueNAS ───────────────────────────────────────────────────
section "TrueNAS"
info "Provides pool health and disk count. Generate an API key in TrueNAS: Account > API Keys."
if ask_yes_no "Enable TrueNAS integration?"; then
  set_config_bool "TRUENAS_ENABLED" "True"
  ask_input "TrueNAS URL" "http://192.168.88.XX"
  set_config "TRUENAS_HOST" "'$REPLY'"
  ask_input "API key" ""
  set_config "TRUENAS_API_KEY" "'$REPLY'"
  ok "TrueNAS configured"
else
  set_config_bool "TRUENAS_ENABLED" "False"
  info "Skipped."
fi

# ── UniFi ─────────────────────────────────────────────────────
section "UniFi Controller"
info "Provides connected client count."
if ask_yes_no "Enable UniFi integration?"; then
  set_config_bool "UNIFI_ENABLED" "True"
  ask_input "UniFi URL" "https://192.168.88.XX:8443"
  set_config "UNIFI_HOST" "'$REPLY'"
  ask_input "Username" "admin"
  set_config "UNIFI_USER" "'$REPLY'"
  ask_input "Password" ""
  set_config "UNIFI_PASS" "'$REPLY'"
  ask_input "Site name" "default"
  set_config "UNIFI_SITE" "'$REPLY'"
  set_config_bool "UNIFI_VERIFY_SSL" "False"
  ok "UniFi configured"
else
  set_config_bool "UNIFI_ENABLED" "False"
  info "Skipped."
fi

# ── Plex ──────────────────────────────────────────────────────
section "Plex Media Server"
info "Provides active stream count. Get token from: https://www.plexopedia.com/plex-media-server/general/plex-token/"
if ask_yes_no "Enable Plex integration?"; then
  set_config_bool "PLEX_ENABLED" "True"
  ask_input "Plex URL" "http://192.168.88.XX:32400"
  set_config "PLEX_HOST" "'$REPLY'"
  ask_input "Plex token" ""
  set_config "PLEX_TOKEN" "'$REPLY'"
  ok "Plex configured"
else
  set_config_bool "PLEX_ENABLED" "False"
  info "Skipped."
fi

# ── Home Assistant ────────────────────────────────────────────
section "Home Assistant"
info "Provides entity/automation counts + device controls panel."
info "Generate a Long-Lived Access Token in HA: Profile > Long-Lived Access Tokens."
if ask_yes_no "Enable Home Assistant integration?"; then
  set_config_bool "HA_ENABLED" "True"
  ask_input "HA URL" "http://192.168.88.253:8123"
  set_config "HA_HOST" "'$REPLY'"
  ask_input "Long-lived access token" ""
  set_config "HA_TOKEN" "'$REPLY'"
  ok "Home Assistant configured"
else
  set_config_bool "HA_ENABLED" "False"
  info "Skipped."
fi

# ── Portainer ─────────────────────────────────────────────────
section "Portainer"
info "Provides Docker container counts. Generate an API token: Account > Access Tokens."
if ask_yes_no "Enable Portainer integration?"; then
  set_config_bool "PORTAINER_ENABLED" "True"
  ask_input "Portainer URL" "http://192.168.88.XX:9000"
  set_config "PORTAINER_HOST" "'$REPLY'"
  ask_input "API token" ""
  set_config "PORTAINER_TOKEN" "'$REPLY'"
  ok "Portainer configured"
else
  set_config_bool "PORTAINER_ENABLED" "False"
  info "Skipped."
fi

# ── Open WebUI / Ollama ───────────────────────────────────────
section "Open WebUI + Ollama"
info "Provides local AI model counts."
if ask_yes_no "Enable Open WebUI integration?"; then
  set_config_bool "OPENWEBUI_ENABLED" "True"
  ask_input "Open WebUI URL" "http://192.168.88.XX:3000"
  set_config "OPENWEBUI_HOST" "'$REPLY'"
  ask_input "Open WebUI API token (leave blank if auth disabled)" ""
  set_config "OPENWEBUI_TOKEN" "'$REPLY'"
  ok "Open WebUI configured"
else
  set_config_bool "OPENWEBUI_ENABLED" "False"
  info "Skipped."
fi

if ask_yes_no "Enable Ollama integration?"; then
  set_config_bool "OLLAMA_ENABLED" "True"
  ask_input "Ollama URL" "http://192.168.88.XX:11434"
  set_config "OLLAMA_HOST" "'$REPLY'"
  ok "Ollama configured"
else
  set_config_bool "OLLAMA_ENABLED" "False"
  info "Skipped."
fi

# ── Grafana ───────────────────────────────────────────────────
section "Grafana"
info "Provides dashboard count. Generate API key: Configuration > API Keys."
if ask_yes_no "Enable Grafana integration?"; then
  set_config_bool "GRAFANA_ENABLED" "True"
  ask_input "Grafana URL" "http://192.168.88.XX:3000"
  set_config "GRAFANA_HOST" "'$REPLY'"
  ask_input "API token" ""
  set_config "GRAFANA_TOKEN" "'$REPLY'"
  ok "Grafana configured"
else
  set_config_bool "GRAFANA_ENABLED" "False"
  info "Skipped."
fi

# ── BlueBubbles ───────────────────────────────────────────────
section "BlueBubbles (iMessage relay)"
info "No API key needed — password is set in the BlueBubbles Server app."
if ask_yes_no "Enable BlueBubbles integration?"; then
  set_config_bool "BLUEBUBBLES_ENABLED" "True"
  ask_input "BlueBubbles URL" "http://192.168.88.XX:1234"
  set_config "BLUEBUBBLES_HOST" "'$REPLY'"
  ask_input "BlueBubbles server password" ""
  set_config "BLUEBUBBLES_PASS" "'$REPLY'"
  ok "BlueBubbles configured"
else
  set_config_bool "BLUEBUBBLES_ENABLED" "False"
  info "Skipped."
fi

# ── Immich ────────────────────────────────────────────────────
section "Immich (self-hosted photos)"
info "Generate API key in Immich: Account Settings > API Keys."
if ask_yes_no "Enable Immich integration?"; then
  set_config_bool "IMMICH_ENABLED" "True"
  ask_input "Immich URL" "http://192.168.88.XX:2283"
  set_config "IMMICH_HOST" "'$REPLY'"
  ask_input "API key" ""
  set_config "IMMICH_API_KEY" "'$REPLY'"
  ok "Immich configured"
else
  set_config_bool "IMMICH_ENABLED" "False"
  info "Skipped."
fi

# ── Unraid ────────────────────────────────────────────────────
section "Unraid"
info "Requires Unraid API plugin or Community Apps."
if ask_yes_no "Enable Unraid integration?"; then
  set_config_bool "UNRAID_ENABLED" "True"
  ask_input "Unraid URL" "http://192.168.88.XX"
  set_config "UNRAID_HOST" "'$REPLY'"
  ask_input "API key" ""
  set_config "UNRAID_API_KEY" "'$REPLY'"
  ok "Unraid configured"
else
  set_config_bool "UNRAID_ENABLED" "False"
  info "Skipped."
fi

# ── AMP (Game Servers) ────────────────────────────────────────
section "AMP — CubeCoders Game Server Manager"
info "Create a dedicated API user in AMP: Configuration > User Manager."
if ask_yes_no "Enable AMP integration?"; then
  set_config_bool "AMP_ENABLED" "True"
  ask_input "AMP panel URL" "http://192.168.88.XX:8080"
  set_config "AMP_HOST" "'$REPLY'"
  ask_input "AMP username" "admin"
  set_config "AMP_USER" "'$REPLY'"
  ask_input "AMP password" ""
  set_config "AMP_PASS" "'$REPLY'"
  set_config "AMP_INSTANCES" "[]"
  ok "AMP configured (auto-discovering all instances)"
else
  set_config_bool "AMP_ENABLED" "False"
  info "Skipped."
fi

# ── OctoPrint ─────────────────────────────────────────────────
section "OctoPrint (FDM printer control)"
info "Generate an API key in OctoPrint: Settings > API > API Key."
if ask_yes_no "Enable OctoPrint integration?"; then
  set_config_bool "OCTOPRINT_ENABLED" "True"
  ask_input "Printer name (e.g. Printer 1)" "Printer 1"
  OCTO_NAME="$REPLY"
  ask_input "Printer host URL" "http://192.168.88.XX"
  OCTO_HOST="$REPLY"
  ask_input "API key" ""
  OCTO_KEY="$REPLY"
  # Write the printers list
  python3 - <<PYEOF
import re, sys
entry = f"OCTOPRINT_PRINTERS = [\n    {{'name': '{OCTO_NAME}', 'host': '{OCTO_HOST}', 'key': '{OCTO_KEY}'}},\n]"
cfg = open('$CONFIG').read()
cfg = re.sub(r'^#?\s*OCTOPRINT_ENABLED\s*=.*', 'OCTOPRINT_ENABLED = True', cfg, flags=re.M)
if 'OCTOPRINT_PRINTERS' in cfg:
    cfg = re.sub(r'#?\s*OCTOPRINT_PRINTERS\s*=\s*\[[\s\S]*?\]', entry, cfg)
else:
    cfg += '\n' + entry + '\n'
open('$CONFIG', 'w').write(cfg)
PYEOF
  ok "OctoPrint configured (1 printer: $OCTO_NAME)"
else
  set_config_bool "OCTOPRINT_ENABLED" "False"
  info "Skipped."
fi

# ── Moonraker / Klipper ───────────────────────────────────────
section "Moonraker / Klipper"
info "Moonraker runs on port 7125 by default."
if ask_yes_no "Enable Moonraker integration?"; then
  set_config_bool "MOONRAKER_ENABLED" "True"
  ask_input "Printer name (e.g. Voron)" "Voron"
  MOON_NAME="$REPLY"
  ask_input "Printer host URL (include port)" "http://192.168.88.XX:7125"
  MOON_HOST="$REPLY"
  python3 - <<PYEOF
import re
entry = f"MOONRAKER_PRINTERS = [\n    {{'name': '{MOON_NAME}', 'host': '{MOON_HOST}', 'key': ''}},\n]"
cfg = open('$CONFIG').read()
cfg = re.sub(r'^#?\s*MOONRAKER_ENABLED\s*=.*', 'MOONRAKER_ENABLED = True', cfg, flags=re.M)
if 'MOONRAKER_PRINTERS' in cfg:
    cfg = re.sub(r'#?\s*MOONRAKER_PRINTERS\s*=\s*\[[\s\S]*?\]', entry, cfg)
else:
    cfg += '\n' + entry + '\n'
open('$CONFIG', 'w').write(cfg)
PYEOF
  ok "Moonraker configured (1 printer: $MOON_NAME)"
else
  set_config_bool "MOONRAKER_ENABLED" "False"
  info "Skipped."
fi

# ── Bambu Lab ─────────────────────────────────────────────────
section "Bambu Lab (LAN mode)"
info "LAN mode must be ON in the printer's network settings."
info "Serial number is on the sticker inside the door."
info "Access code is shown in the printer's LAN settings screen."
if ask_yes_no "Enable Bambu Lab integration?"; then
  set_config_bool "BAMBU_ENABLED" "True"
  $PYTHON -m pip install paho-mqtt --break-system-packages --quiet
  ok "paho-mqtt installed"
  ask_input "Printer name (e.g. X1 Carbon)" "X1 Carbon"
  BAMBU_NAME="$REPLY"
  ask_input "Printer IP address (no http://)" "192.168.88.XX"
  BAMBU_IP="$REPLY"
  ask_input "Serial number" ""
  BAMBU_SERIAL="$REPLY"
  ask_input "Access code (8 chars)" ""
  BAMBU_CODE="$REPLY"
  python3 - <<PYEOF
import re
entry = "BAMBU_PRINTERS = [\n    {\n        'name':         '" + BAMBU_NAME + "',\n        'host':         '" + BAMBU_IP + "',\n        'serial':       '" + BAMBU_SERIAL + "',\n        'access_code':  '" + BAMBU_CODE + "',\n        'port':         1883,\n    },\n]"
cfg = open('$CONFIG').read()
cfg = re.sub(r'^#?\s*BAMBU_ENABLED\s*=.*', 'BAMBU_ENABLED = True', cfg, flags=re.M)
if 'BAMBU_PRINTERS' in cfg:
    cfg = re.sub(r'#?\s*BAMBU_PRINTERS\s*=\s*\[[\s\S]*?\]', entry, cfg)
else:
    cfg += '\n' + entry + '\n'
open('$CONFIG', 'w').write(cfg)
PYEOF
  ok "Bambu configured (1 printer: $BAMBU_NAME)"
else
  set_config_bool "BAMBU_ENABLED" "False"
  info "Skipped."
fi

# ── Obico ─────────────────────────────────────────────────────
section "Obico (The Spaghetti Detective)"
info "Get API key from: obico.io > Account > API Key"
if ask_yes_no "Enable Obico integration?"; then
  set_config_bool "OBICO_ENABLED" "True"
  ask_input "Obico host" "https://app.obico.io"
  set_config "OBICO_HOST" "'$REPLY'"
  ask_input "API key" ""
  set_config "OBICO_API_KEY" "'$REPLY'"
  ok "Obico configured"
else
  set_config_bool "OBICO_ENABLED" "False"
  info "Skipped."
fi

# ─────────────────────────────────────────────────────────────
#  FIREWALL
# ─────────────────────────────────────────────────────────────
section "Firewall (UFW)"
info "Opening ports 8888 (dashboard) and 8889 (stats API)..."
if command -v ufw &>/dev/null; then
  sudo ufw allow 8888/tcp >/dev/null 2>&1 && ok "Port 8888/tcp allowed" || warn "ufw allow 8888/tcp failed (check sudo)"
  sudo ufw allow 8889/tcp >/dev/null 2>&1 && ok "Port 8889/tcp allowed" || warn "ufw allow 8889/tcp failed (check sudo)"
else
  warn "ufw not found — skipping firewall configuration."
  info "If you use a different firewall, manually open ports 8888 and 8889."
fi

# ─────────────────────────────────────────────────────────────
#  SYSTEMD SERVICES
# ─────────────────────────────────────────────────────────────
section "Creating systemd services"

sudo tee /etc/systemd/system/veracious-dashboard.service > /dev/null <<EOF
[Unit]
Description=Veracious Dashboard
After=network.target

[Service]
Type=simple
User=$USERNAME
WorkingDirectory=$DASHBOARD_DIR
ExecStart=$PYTHON -m http.server 8888
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
ok "Dashboard service created (port 8888)"

sudo tee /etc/systemd/system/veracious-stats.service > /dev/null <<EOF
[Unit]
Description=Veracious Dashboard Stats Collector
After=network.target

[Service]
Type=simple
User=$USERNAME
WorkingDirectory=$DASHBOARD_DIR
ExecStart=$PYTHON $DASHBOARD_DIR/stats.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
ok "Stats service created (port 8889)"

section "Enabling and starting services"
sudo systemctl daemon-reload
sudo systemctl enable veracious-dashboard veracious-stats
sudo systemctl restart veracious-dashboard veracious-stats
ok "Services enabled and started"

# ─────────────────────────────────────────────────────────────
#  DONE
# ─────────────────────────────────────────────────────────────

header "SETUP COMPLETE!"
MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo  "  Dashboard  : http://localhost:8888"
echo  "  Stats API  : http://localhost:8889/stats"
if [ -n "$MY_IP" ]; then
  echo  "  Network    : http://${MY_IP}:8888  (from other devices)"
fi
echo ""
echo  "  Next steps:"
echo  "  1. Edit index.html to uncomment the service cards you just enabled"
echo  "  2. Update the XX placeholder IPs in index.html to your real IPs"
echo  "  3. Run: sudo systemctl restart veracious-stats  (after any config change)"
echo  "  4. View logs: journalctl -u veracious-stats -f"
echo ""
echo  "  Config backup saved to: config.py.bak"
echo ""

# ── Service status ───────────────────────────────────────────
sleep 2
section "Service status"
sudo systemctl status veracious-dashboard --no-pager | grep "Active:" || true
sudo systemctl status veracious-stats     --no-pager | grep "Active:" || true
echo ""
