#!/usr/bin/env python3
"""
System Monitor Tray - Moniteur système dans le system tray
Affiche les processus, températures et RAM en temps réel
"""

import sys
import os
import subprocess
import psutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction, QFont
from PyQt6.QtCore import QTimer, Qt, QPoint


class MonitorPopup(QWidget):
    """Fenêtre popup avec les informations système"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
            }
            QLabel {
                border: none;
            }
            QPushButton {
                background-color: #444444;
                border: 1px solid #666666;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton#killBtn {
                background-color: #aa4444;
                padding: 2px 6px;
                font-size: 10px;
            }
            QPushButton#killBtn:hover {
                background-color: #cc5555;
            }
            QTableWidget {
                background-color: #333333;
                border: 1px solid #555555;
                gridline-color: #444444;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #444444;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
            }
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("System Monitor")
        title.setFont(QFont("Sans", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("X")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #555555;")
        layout.addWidget(line)

        # Stats bar
        self.stats_layout = QHBoxLayout()
        self.cpu_label = QLabel("CPU: --%")
        self.ram_label = QLabel("RAM: --/-- GB")
        self.temp_label = QLabel("--°C")

        for label in [self.cpu_label, self.ram_label, self.temp_label]:
            label.setFont(QFont("Sans", 10, QFont.Weight.Bold))
            self.stats_layout.addWidget(label)

        layout.addLayout(self.stats_layout)

        # Process table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Processus", "CPU", "RAM", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 40)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(300)
        layout.addWidget(self.table)

        # Temperatures
        temp_layout = QHBoxLayout()
        temp_title = QLabel("Températures:")
        temp_title.setFont(QFont("Sans", 9, QFont.Weight.Bold))
        temp_layout.addWidget(temp_title)

        self.cpu_temp_label = QLabel("CPU: --°C")
        self.amd_temp_label = QLabel("AMD: --°C")
        self.nvidia_temp_label = QLabel("NVIDIA: --°C")

        for label in [self.cpu_temp_label, self.amd_temp_label, self.nvidia_temp_label]:
            temp_layout.addWidget(label)

        temp_layout.addStretch()
        layout.addLayout(temp_layout)

        self.setFixedWidth(450)

    def update_data(self, processes, cpu_percent, ram_used, ram_total, temps):
        """Met à jour les données affichées"""
        # Stats bar
        self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")
        self.ram_label.setText(f"RAM: {ram_used:.1f}/{ram_total:.1f} GB")

        cpu_temp = temps.get('cpu', 0)
        color = "#00ff00" if cpu_temp < 60 else "#ffaa00" if cpu_temp < 80 else "#ff4444"
        self.temp_label.setText(f"<span style='color:{color}'>{cpu_temp:.0f}°C</span>")

        # Process table
        self.table.setRowCount(len(processes))
        for i, proc in enumerate(processes):
            name_item = QTableWidgetItem(proc['name'][:25])
            cpu_item = QTableWidgetItem(f"{proc['cpu']:.1f}%")
            ram_item = QTableWidgetItem(f"{proc['ram']:.0f}MB")

            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, cpu_item)
            self.table.setItem(i, 2, ram_item)

            kill_btn = QPushButton("X")
            kill_btn.setObjectName("killBtn")
            kill_btn.setFixedSize(30, 20)
            kill_btn.clicked.connect(lambda checked, pid=proc['pid']: self.kill_process(pid))
            self.table.setCellWidget(i, 3, kill_btn)

        # Temperatures
        self.cpu_temp_label.setText(f"CPU: {temps.get('cpu', 0):.0f}°C")
        self.amd_temp_label.setText(f"AMD: {temps.get('amd', 0):.0f}°C")
        self.nvidia_temp_label.setText(f"NVIDIA: {temps.get('nvidia', 0):.0f}°C")

    def kill_process(self, pid):
        """Tue un processus"""
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            reply = QMessageBox.question(
                self, "Confirmer",
                f"Tuer le processus '{name}' (PID: {pid}) ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                proc.terminate()
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            QMessageBox.warning(self, "Erreur", "Permission refusée. Essayez avec sudo.")


class SystemMonitorTray:
    """Application principale avec icône system tray"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Créer l'icône tray
        self.tray = QSystemTrayIcon()
        self.update_tray_icon(0)
        self.tray.setToolTip("System Monitor")
        self.tray.activated.connect(self.on_tray_activated)

        # Menu clic droit
        self.menu = QMenu()
        quit_action = QAction("Quitter")
        quit_action.triggered.connect(self.quit)
        self.menu.addAction(quit_action)
        self.tray.setContextMenu(self.menu)

        # Popup
        self.popup = MonitorPopup()

        # Timer pour mise à jour
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(2000)  # 2 secondes

        # Première mise à jour
        self.update_data()

        self.tray.show()

    def create_arc_icon(self, cpu_percent):
        """Crée une icône avec arc circulaire selon le CPU% (haute définition)"""
        from PyQt6.QtGui import QPen

        # Haute résolution pour netteté
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        center = size // 2
        radius = 26
        thickness = 8

        # Cercle de fond (gris plus visible)
        pen = QPen(QColor("#707070"))
        pen.setWidth(thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)

        # Arc actif (blanc) - commence en haut (-90°), sens horaire
        if cpu_percent > 0:
            pen = QPen(QColor("#FFFFFF"))
            pen.setWidth(thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)

            # Qt utilise 1/16 de degré, commence à 90° (haut), sens anti-horaire
            start_angle = 90 * 16  # Haut
            span_angle = -int(cpu_percent * 3.6 * 16)  # Négatif = sens horaire

            painter.drawArc(
                center - radius, center - radius,
                radius * 2, radius * 2,
                start_angle, span_angle
            )

        # Pourcentage au centre
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Sans", 18, QFont.Weight.Bold)
        painter.setFont(font)
        text = f"{int(cpu_percent)}"
        painter.drawText(0, 0, size, size, Qt.AlignmentFlag.AlignCenter, text)

        painter.end()
        return QIcon(pixmap)

    def update_tray_icon(self, cpu_percent):
        """Met à jour l'icône selon le CPU%"""
        self.tray.setIcon(self.create_arc_icon(cpu_percent))

    def get_top_processes(self, n=10):
        """Récupère les top N processus par CPU"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                info = proc.info
                ram_mb = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'cpu': info['cpu_percent'] or 0,
                    'ram': ram_mb
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Trier par CPU et prendre les top N
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:n]

    def get_temperatures(self):
        """Récupère les températures"""
        temps = {'cpu': 0, 'amd': 0, 'nvidia': 0}

        # CPU (k10temp)
        try:
            k10temp = Path("/sys/class/hwmon")
            for hwmon in k10temp.iterdir():
                name_file = hwmon / "name"
                if name_file.exists() and "k10temp" in name_file.read_text():
                    temp_file = hwmon / "temp1_input"
                    if temp_file.exists():
                        temps['cpu'] = int(temp_file.read_text()) / 1000
                    break
        except:
            pass

        # AMD GPU (amdgpu)
        try:
            for hwmon in Path("/sys/class/hwmon").iterdir():
                name_file = hwmon / "name"
                if name_file.exists() and "amdgpu" in name_file.read_text():
                    temp_file = hwmon / "temp1_input"
                    if temp_file.exists():
                        temps['amd'] = int(temp_file.read_text()) / 1000
                    break
        except:
            pass

        # NVIDIA GPU
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                temps['nvidia'] = float(result.stdout.strip())
        except:
            pass

        return temps

    def update_data(self):
        """Met à jour toutes les données"""
        # CPU global
        cpu_percent = psutil.cpu_percent()
        self.update_tray_icon(cpu_percent)

        # RAM
        ram = psutil.virtual_memory()
        ram_used = ram.used / (1024**3)
        ram_total = ram.total / (1024**3)

        # Processus
        processes = self.get_top_processes()

        # Températures
        temps = self.get_temperatures()

        # Mettre à jour le popup si visible
        if self.popup.isVisible():
            self.popup.update_data(processes, cpu_percent, ram_used, ram_total, temps)

        # Tooltip
        self.tray.setToolTip(
            f"CPU: {cpu_percent:.0f}% | RAM: {ram_used:.1f}/{ram_total:.0f}GB | {temps['cpu']:.0f}°C"
        )

    def on_tray_activated(self, reason):
        """Gère le clic sur l'icône"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # Clic gauche
            if self.popup.isVisible():
                self.popup.hide()
            else:
                # Positionner en bas à droite de l'écran disponible
                screen = self.app.primaryScreen().availableGeometry()
                self.popup.adjustSize()
                x = screen.right() - self.popup.width() - 10
                y = screen.bottom() - self.popup.height() - 10
                self.popup.move(x, y)
                self.update_data()
                self.popup.update_data(
                    self.get_top_processes(),
                    psutil.cpu_percent(),
                    psutil.virtual_memory().used / (1024**3),
                    psutil.virtual_memory().total / (1024**3),
                    self.get_temperatures()
                )
                self.popup.show()
                self.popup.raise_()
                self.popup.activateWindow()

    def quit(self):
        """Quitte l'application"""
        self.tray.hide()
        self.app.quit()

    def run(self):
        """Lance l'application"""
        sys.exit(self.app.exec())


if __name__ == "__main__":
    monitor = SystemMonitorTray()
    monitor.run()
