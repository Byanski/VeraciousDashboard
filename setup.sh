#!/bin/bash
# =============================================================
#  VERACIOUS DASHBOARD — Setup Script
#  Run this once to install everything.
#  Usage: bash setup.sh
# =============================================================

set -e

DASHBOARD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON=$(which python3)
USERNAME=$(whoami)

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║        VERACIOUS DASHBOARD SETUP         ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Dashboard directory : $DASHBOARD_DIR"
echo "Python              : $PYTHON"
echo "User                : $USERNAME"
echo ""

# ── Install Python dependencies ──────────────────────────────
echo "► Installing Python dependencies..."
$PYTHON -m pip install flask requests routeros-api urllib3 --break-system-packages --quiet
echo "  ✓ Dependencies installed"

# ── Dashboard service ─────────────────────────────────────────
echo ""
echo "► Creating dashboard service (port 8888)..."
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
echo "  ✓ Dashboard service created"

# ── Stats service ─────────────────────────────────────────────
echo ""
echo "► Creating stats collector service (port 8889)..."
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
echo "  ✓ Stats service created"

# ── Enable and start ──────────────────────────────────────────
echo ""
echo "► Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable veracious-dashboard veracious-stats
sudo systemctl restart veracious-dashboard veracious-stats
echo "  ✓ Services enabled and started"

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║              SETUP COMPLETE!             ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Dashboard : http://localhost:8888"
echo "  Stats API : http://localhost:8889/stats"
echo ""
echo "  Next steps:"
echo "  1. Edit config.py with your passwords and IPs"
echo "  2. Edit index.html to add your services"
echo "  3. Run: sudo systemctl restart veracious-stats"
echo ""

# ── Check status ──────────────────────────────────────────────
sleep 2
echo "► Service status:"
sudo systemctl status veracious-dashboard --no-pager | grep "Active:"
sudo systemctl status veracious-stats --no-pager | grep "Active:"
echo ""
