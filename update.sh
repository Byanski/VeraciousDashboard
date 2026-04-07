#!/bin/bash
# =============================================================
#  VERACIOUS DASHBOARD — Updater
#  Pulls the latest version from GitHub, updates all files,
#  and preserves every value you set in config.py.
#
#  Usage: bash update.sh
#  Optional: bash update.sh --repo https://github.com/YOU/REPO
# =============================================================

set -e

DASHBOARD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$DASHBOARD_DIR/config.py"
PYTHON=$(which python3)

# ── Colours ──────────────────────────────────────────────────
C_RESET='\033[0m'
C_BOLD='\033[1m'
C_CYAN='\033[36m'
C_GREEN='\033[32m'
C_YELLOW='\033[33m'
C_RED='\033[31m'
C_DIM='\033[2m'

header() {
  echo ""
  echo -e "${C_CYAN}${C_BOLD}╔══════════════════════════════════════════╗${C_RESET}"
  echo -e "${C_CYAN}${C_BOLD}║  $1${C_RESET}"
  echo -e "${C_CYAN}${C_BOLD}╚══════════════════════════════════════════╝${C_RESET}"
  echo ""
}

section() { echo -e "\n${C_CYAN}── $1 ──────────────────────────────────────${C_RESET}"; }
ok()      { echo -e "  ${C_GREEN}✓${C_RESET} $1"; }
info()    { echo -e "  ${C_DIM}$1${C_RESET}"; }
warn()    { echo -e "  ${C_YELLOW}⚠  $1${C_RESET}"; }
die()     { echo -e "  ${C_RED}✗  $1${C_RESET}"; exit 1; }

# ── Parse args ───────────────────────────────────────────────
REPO_URL=""
for arg in "$@"; do
  case $arg in
    --repo=*) REPO_URL="${arg#*=}" ;;
    --repo)   shift; REPO_URL="$1" ;;
  esac
done

header "VERACIOUS DASHBOARD UPDATER"
echo "  Dashboard directory : $DASHBOARD_DIR"
echo "  Config              : $CONFIG"

# ── Sanity checks ─────────────────────────────────────────────
[ -f "$CONFIG" ] || die "config.py not found — are you running this from the dashboard directory?"
[ -f "$DASHBOARD_DIR/stats.py" ] || die "stats.py not found — are you running this from the dashboard directory?"

# ── Step 1: Back up config.py and index.html ─────────────────
section "Backing up your files"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$DASHBOARD_DIR/.update_backups/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"
cp "$CONFIG" "$BACKUP_DIR/config.py.bak"
cp "$DASHBOARD_DIR/index.html" "$BACKUP_DIR/index.html.bak"
ok "Backed up to .update_backups/$TIMESTAMP/"

# ── Step 2: Extract all user values from config.py ───────────
section "Reading your existing configuration"

# We use Python to safely parse the config and dump every
# top-level assignment as KEY=VALUE pairs to a temp file.
SAVED_VALUES="$BACKUP_DIR/saved_values.env"

$PYTHON - <<PYEOF
import ast, sys, re

config_path = "$CONFIG"
output_path = "$SAVED_VALUES"

with open(config_path, 'r') as f:
    source = f.read()

lines = source.splitlines()
saved = {}

for line in lines:
    # Skip blank lines and pure comments
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        continue

    # Match active assignments: KEY = VALUE (not commented out)
    m = re.match(r'^([A-Z][A-Z0-9_]+)\s*=\s*(.+)$', stripped)
    if not m:
        continue

    key = m.group(1)
    raw_val = m.group(2).split('#')[0].strip()  # strip inline comments

    saved[key] = raw_val

with open(output_path, 'w') as f:
    for k, v in saved.items():
        # Encode newlines so the shell file stays single-line-per-key
        safe = v.replace('\n', '\\n')
        f.write(f"{k}={safe}\n")

print(f"  Saved {len(saved)} config values.")
PYEOF

ok "Configuration values saved ($(wc -l < "$SAVED_VALUES") keys)"

# ── Step 3: Pull latest code ──────────────────────────────────
section "Downloading latest version"

if [ -d "$DASHBOARD_DIR/.git" ]; then
  # ── Git repo — just pull ──────────────────────────────────
  info "Git repository detected — running git pull..."
  cd "$DASHBOARD_DIR"
  git pull --ff-only || {
    warn "git pull failed. Your local changes may conflict."
    warn "Resolve conflicts manually, then re-run update.sh."
    exit 1
  }
  ok "Repository updated via git"

else
  # ── Not a git repo — download a zip from GitHub ──────────
  if [ -z "$REPO_URL" ]; then
    # Try to auto-detect from a marker file written at install time
    MARKER="$DASHBOARD_DIR/.veracious_repo"
    if [ -f "$MARKER" ]; then
      REPO_URL=$(cat "$MARKER")
      info "Using saved repo URL: $REPO_URL"
    else
      echo ""
      echo -e "  ${C_BOLD}No git repository found.${C_RESET}"
      echo -e "  Enter your GitHub repo URL (e.g. https://github.com/you/veracious-dashboard)"
      echo -en "  ${C_BOLD}Repo URL:${C_RESET} "
      read -r REPO_URL
      [ -z "$REPO_URL" ] && die "No repo URL provided — cannot update."
      echo "$REPO_URL" > "$MARKER"
      ok "Repo URL saved to .veracious_repo for future updates"
    fi
  fi

  # Strip trailing slash and .git suffix
  REPO_URL="${REPO_URL%/}"
  REPO_URL="${REPO_URL%.git}"

  ZIP_URL="${REPO_URL}/archive/refs/heads/main.zip"
  TMP_ZIP="/tmp/veracious_update_$TIMESTAMP.zip"
  TMP_DIR="/tmp/veracious_update_$TIMESTAMP"

  info "Downloading $ZIP_URL ..."
  if command -v curl &>/dev/null; then
    curl -fsSL "$ZIP_URL" -o "$TMP_ZIP" || die "Download failed. Check your repo URL and internet connection."
  elif command -v wget &>/dev/null; then
    wget -q "$ZIP_URL" -O "$TMP_ZIP" || die "Download failed. Check your repo URL and internet connection."
  else
    die "Neither curl nor wget found — cannot download update."
  fi
  ok "Downloaded update archive"

  info "Extracting..."
  mkdir -p "$TMP_DIR"
  unzip -q "$TMP_ZIP" -d "$TMP_DIR" || die "Failed to extract zip."

  # The zip extracts to a subdirectory like  repo-main/
  EXTRACTED=$(find "$TMP_DIR" -maxdepth 1 -mindepth 1 -type d | head -1)
  [ -z "$EXTRACTED" ] && die "Unexpected zip structure — could not find extracted directory."

  # Copy updated files (everything EXCEPT config.py — we'll handle that next)
  FILES_TO_UPDATE=("stats.py" "setup.sh" "update.sh" "README.md" "index.html")
  for f in "${FILES_TO_UPDATE[@]}"; do
    if [ -f "$EXTRACTED/$f" ]; then
      cp "$EXTRACTED/$f" "$DASHBOARD_DIR/$f"
      ok "Updated $f"
    else
      info "  $f not found in update — skipping"
    fi
  done

  # Copy the NEW config.py (template only — we'll re-inject values below)
  cp "$EXTRACTED/config.py" "$CONFIG"
  ok "Fetched fresh config.py template"

  # Cleanup
  rm -rf "$TMP_ZIP" "$TMP_DIR"
fi

# ── Step 4: Re-inject user values into the fresh config.py ───
section "Restoring your configuration values"

$PYTHON - <<PYEOF
import re, sys

config_path  = "$CONFIG"
values_path  = "$SAVED_VALUES"

# ── Load the saved values ────────────────────────────────────
saved = {}
with open(values_path, 'r') as f:
    for line in f:
        line = line.rstrip('\n')
        if '=' not in line:
            continue
        key, _, val = line.partition('=')
        saved[key.strip()] = val.replace('\\n', '\n')

# ── Load the new config template ────────────────────────────
with open(config_path, 'r') as f:
    new_source = f.read()

restored = 0
skipped  = 0

new_lines = new_source.splitlines()
out_lines  = []

i = 0
while i < len(new_lines):
    line = new_lines[i]

    # Match active OR commented-out simple assignments
    m = re.match(r'^(#\s*)?([A-Z][A-Z0-9_]+)\s*=\s*(.+)$', line)

    if m:
        is_commented = bool(m.group(1))
        key          = m.group(2)
        template_val = m.group(3).split('#')[0].strip()

        if key in saved:
            user_val = saved[key]

            # If the template line is a comment but user had it active → uncomment it
            # If the template line is active → keep it active with user's value
            out_lines.append(f"{key} = {user_val}")
            restored += 1
            i += 1
            continue

    out_lines.append(line)
    i += 1

with open(config_path, 'w') as f:
    f.write('\n'.join(out_lines) + '\n')

print(f"  Restored {restored} user values into the new config.py.")
if skipped:
    print(f"  Skipped  {skipped} keys (not found in new template — may be obsolete).")
PYEOF

ok "Configuration restored"

# ── Step 5: Restart services ──────────────────────────────────
section "Restarting services"

restart_service() {
  local svc="$1"
  if systemctl is-enabled "$svc" &>/dev/null; then
    sudo systemctl restart "$svc" && ok "$svc restarted" || warn "Failed to restart $svc"
  else
    info "$svc is not installed as a service — skipping"
  fi
}

restart_service veracious-stats
restart_service veracious-dashboard

# ── Done ──────────────────────────────────────────────────────
header "UPDATE COMPLETE!"
MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo  "  Dashboard  : http://localhost:8888"
echo  "  Stats API  : http://localhost:8889/stats"
[ -n "$MY_IP" ] && echo "  Network    : http://${MY_IP}:8888"
echo ""
echo  "  Your config.py values were preserved automatically."
echo  "  Backup of your previous files: .update_backups/$TIMESTAMP/"
echo ""
echo -e "  ${C_DIM}If something looks wrong, restore with:${C_RESET}"
echo -e "  ${C_DIM}  cp .update_backups/$TIMESTAMP/config.py.bak config.py${C_RESET}"
echo ""
