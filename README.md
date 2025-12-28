# System Monitor Tray

A lightweight system tray application for Linux that displays CPU usage, RAM, temperatures, and top processes.

## Features

- **Circular arc icon** showing CPU usage percentage in real-time
- **Popup window** with:
  - CPU and RAM usage
  - Top 10 processes by CPU usage
  - Kill process button
  - Temperatures (CPU, AMD GPU, NVIDIA GPU)
- **High-DPI support** - crisp icons on all displays
- **Minimal resource usage**

## Screenshot

The tray icon shows a circular progress indicator with the CPU percentage in the center. Click to open the detailed monitor popup.

## Requirements

- Python 3.8+
- PyQt6
- psutil

## Installation

### Automatic (Recommended)

```bash
git clone https://github.com/tofunori/system-monitor-tray.git
cd system-monitor-tray
./install.sh
```

### Manual

1. Install dependencies:

**Fedora:**
```bash
sudo dnf install python3-pyqt6 python3-psutil
```

**Ubuntu/Debian:**
```bash
sudo apt install python3-pyqt6 python3-psutil
```

**Arch Linux:**
```bash
sudo pacman -S python-pyqt6 python-psutil
```

2. Copy the script:
```bash
sudo cp system-monitor-tray.py /usr/local/bin/system-monitor-tray
sudo chmod +x /usr/local/bin/system-monitor-tray
```

3. Run:
```bash
system-monitor-tray
```

## Usage

- **Left-click** on tray icon: Open/close the monitor popup
- **Right-click** on tray icon: Menu with quit option
- **X button** on process row: Kill that process

## Autostart

The install script automatically configures autostart. To manually add:

```bash
cp system-monitor.desktop ~/.config/autostart/
```

## License

MIT License
