#!/bin/bash
# System Monitor Tray - Installation Script
# Supports: Fedora, Ubuntu/Debian, Arch Linux

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== System Monitor Tray - Installation ===${NC}"
echo ""

# Detect distribution
if [ -f /etc/fedora-release ]; then
    DISTRO="fedora"
elif [ -f /etc/debian_version ]; then
    DISTRO="debian"
elif [ -f /etc/arch-release ]; then
    DISTRO="arch"
else
    echo -e "${RED}Distribution non supportée. Installation manuelle requise.${NC}"
    exit 1
fi

echo -e "${YELLOW}Distribution détectée: $DISTRO${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Ne pas exécuter en tant que root. Utilisez un utilisateur normal avec sudo.${NC}"
    exit 1
fi

# Step 1: Install dependencies
echo -e "${GREEN}[1/3] Installation des dépendances...${NC}"
case $DISTRO in
    fedora)
        sudo dnf install -y python3-pyqt6 python3-psutil
        ;;
    debian)
        sudo apt update
        sudo apt install -y python3-pyqt6 python3-psutil
        ;;
    arch)
        sudo pacman -S --noconfirm python-pyqt6 python-psutil
        ;;
esac

# Step 2: Install script
echo ""
echo -e "${GREEN}[2/3] Installation du script...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sudo cp "$SCRIPT_DIR/system-monitor-tray.py" /usr/local/bin/system-monitor-tray
sudo chmod +x /usr/local/bin/system-monitor-tray

# Install desktop entry
sudo cp "$SCRIPT_DIR/system-monitor.desktop" /usr/share/applications/ 2>/dev/null || true

echo -e "${YELLOW}Script installé dans /usr/local/bin/${NC}"

# Step 3: Configure autostart
echo ""
echo -e "${GREEN}[3/3] Configuration de l'autostart...${NC}"
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/system-monitor-tray.desktop << 'EOF'
[Desktop Entry]
Name=System Monitor Tray
Comment=System tray monitor for CPU, RAM, processes
Exec=/usr/local/bin/system-monitor-tray
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=System;Monitor;
X-GNOME-Autostart-enabled=true
EOF

echo -e "${YELLOW}Autostart configuré${NC}"

# Done
echo ""
echo -e "${GREEN}=== Installation terminée ! ===${NC}"
echo ""
echo "Commande disponible:"
echo "  system-monitor-tray    - Lance le moniteur système"
echo ""
echo -e "${GREEN}Lancement...${NC}"
nohup /usr/local/bin/system-monitor-tray &>/dev/null &
