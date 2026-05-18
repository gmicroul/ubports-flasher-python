# UBports Flasher - PyQt6 原生 GUI
# 离线刷机 Ubuntu Touch
# Run: python3 main.py

import sys
import json
import os
import threading
import urllib.request
import urllib.error
import subprocess
import signal

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QProgressBar,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame, QSpacerItem,
    QSizePolicy, QProgressDialog, QLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QRect, QPoint, QRectF
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPalette, \
    QLinearGradient, QBrush, QFontDatabase

# ===== 配置 =====
BASE_URL = "https://system-image.ubports.com"
CHANNEL = "26.04-1.x/arm64/android9plus/daily"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/ubports-flasher")

# ===== 设备名称映射 =====
DEVICE_NAMES = {
    "FP3": "Fairphone 3", "FP4": "Fairphone 4", "FP5": "Fairphone 5",
    "MI6": "Xiaomi Mi 6", "MIX2": "Xiaomi Mi Mix 2", "Mi9SE": "Xiaomi Mi 9 SE",
    "beryllium": "Poco F1", "bramble": "Pixel 4a 5G", "bullhead": "Nexus 5X",
    "cheeseburger": "OnePlus 5", "clover": "Xiaomi Mi Pad 4", "dumpling": "OnePlus 5T",
    "enchilada": "OnePlus 6(T)", "fajita": "OnePlus 6(T)", "flounder": "Nexus 9",
    "griffin": "Lenovo Zuk Z2 Pro", "guacamole": "OnePlus 7", "guacamoleb": "OnePlus 7",
    "hotdog": "OnePlus 7T Pro", "hotdogb": "OnePlus 7T", "harpia": "Moto G4 Play",
    "kuntao": "Lenovo P2", "lavender": "Xiaomi Redmi Note 7",
    "lmi": "Xiaomi Poco F2 Pro", "mata": "Essential Phone PH-1",
    "merlin": "Xiaomi Redmi Note 9", "mi8916": "Xiaomi Redmi 2",
    "oneplus3": "OnePlus 3", "pdx219": "Sony Xperia 5 II",
    "pdx237": "Sony Xperia 1 IV", "pdx239": "Sony Xperia 5 IV",
    "raphael": "Xiaomi Mi 9T Pro", "redfin": "Pixel 5",
    "sargo": "Pixel 3a", "sunfish": "Pixel 4a",
    "taimen": "Pixel 2 XL", "vince": "Xiaomi Redmi 5 Plus",
    "walleye": "Pixel 2", "wayne": "Xiaomi Mi 6X",
    "whyred": "Xiaomi Redmi Note 5",
    "flamingo": "Xiaomi Mi Pad 4 Plus",
    "pdx203": "Sony Xperia 1 II",
    "pdx206": "Sony Xperia 10 II",
    "barbet": "Pixel 5a",
    "kebab": "OnePlus 8T",
    "instantnoodle": "OnePlus 8",
    "instantnoodlep": "OnePlus 8 Pro",
    "lemonade": "OnePlus 9",
    "lemonadep": "OnePlus 9 Pro",
    "lemonades": "OnePlus 9R",
}

MANUFACTURERS = {
    "OnePlus": "OnePlus",
    "Google": "Google",
    "Xiaomi": "Xiaomi",
    "Sony": "Sony",
    "Fairphone": "Fairphone",
    "Motorola": "Motorola",
    "Lenovo": "Lenovo",
    "Essential": "Essential",
    "Nexus": "Nexus",
}

def get_device_name(codename):
    return DEVICE_NAMES.get(codename, codename)

def get_manufacturer(codename):
    name = get_device_name(codename)
    for prefix in ["OnePlus", "Pixel", "Nexus"]:
        if name.startswith(prefix):
            return prefix
    for mfr in ["Xiaomi", "Sony", "Fairphone", "Motorola", "Lenovo", "Essential"]:
        if mfr in name:
            return mfr
    for kw, m in [("Moto", "Motorola"), ("Redmi", "Xiaomi"), ("Mi ", "Xiaomi"), ("Poco", "Xiaomi"),
                  ("Zuk", "Lenovo"), ("P2", "Lenovo"), ("Volla", "Volla")]:
        if kw in name:
            return m
    return "Other"

def format_size(bytes_val):
    if bytes_val >= 1024**3:
        return f"{bytes_val / 1024**3:.1f} GB"
    return f"{bytes_val / 1024**2:.0f} MB"

def format_build(v):
    return f"#{v}"

def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'UBportsFlasher/0.1'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


# ===== 主题色 =====

# QFlowLayout 不再使用，保留为空类避免引用错误
class QFlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_list = []
    def addItem(self, item): self.item_list.append(item)
    def count(self): return len(self.item_list)
    def itemAt(self, index): return self.item_list[index] if 0 <= index < len(self.item_list) else None
    def takeAt(self, index): return self.item_list.pop(index) if 0 <= index < len(self.item_list) else None
    def expandingDirections(self): return Qt.Orientation(0)
    def hasHeightForWidth(self): return True
    def heightForWidth(self, width): return 0
    def minimumSize(self): return QSize()
    def sizeHint(self): return QSize()
    def setGeometry(self, rect): super().setGeometry(rect)


class Theme:
    BG_DARK = "#0f172a"
    BG_SIDEBAR = "#1e293b"
    BG_CARD = "#1e293b"
    BG_CARD_HOVER = "#334155"
    BG_INPUT = "#0f172a"
    TEXT_PRIMARY = "#f1f5f9"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"
    BORDER = "#334155"
    ACCENT = "#3b82f6"
    ACCENT_HOVER = "#2563eb"
    ACCENT_LIGHT = "#1d4ed8"
    GREEN = "#22c55e"
    GREEN_HOVER = "#16a34a"
    RED = "#ef4444"
    BORDER_INPUT = "#334155"
    BORDER_INPUT_FOCUS = "#3b82f6"


def apply_dark_theme(app):
    """Apply dark theme via palette"""
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Theme.BG_DARK))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(Theme.BG_INPUT))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Theme.BG_SIDEBAR))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Theme.BG_SIDEBAR))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Text, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(Theme.BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(Theme.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Theme.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # Global stylesheet
    app.setStyleSheet(f"""
        QMainWindow, QWidget {{ background: {Theme.BG_DARK}; color: {Theme.TEXT_PRIMARY}; }}
        QLabel {{ color: {Theme.TEXT_PRIMARY}; }}
        QLineEdit {{
            background: {Theme.BG_INPUT};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER_INPUT};
            border-radius: 8px;
            padding: 16px 24px;
            font-size: 32px;
            selection-background-color: {Theme.ACCENT};
        }}
        QLineEdit:focus {{ border: 2px solid {Theme.BORDER_INPUT_FOCUS}; }}
        QListWidget {{
            background: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            background: {Theme.BG_CARD};
            border-radius: 8px;
            margin: 8px 16px;
            padding: 16px;
        }}
        QListWidget::item:hover {{ background: {Theme.BG_CARD_HOVER}; }}
        QListWidget::item:selected {{ background: {Theme.ACCENT_LIGHT}; }}
        QScrollBar:vertical {{
            background: {Theme.BG_DARK};
            width: 8px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {Theme.BORDER};
            border-radius: 4px;
            min-height: 40px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QProgressBar {{
            background: {Theme.BG_CARD};
            border: none;
            border-radius: 4px;
            height: 6px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background: {Theme.ACCENT};
            border-radius: 4px;
        }}
        QPushButton {{
            border: none;
            border-radius: 8px;
            padding: 16px 40px;
            font-weight: bold;
            font-size: 40px;
        }}
    """)


# ===== 自定义控件 =====

class AvatarLabel(QLabel):
    """圆形设备头像（首字母）"""
    def __init__(self, letter, color="#3b82f6", size=56):
        super().__init__()
        self.letter = letter[0].upper()
        self.color = QColor(color)
        self.size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.size, self.size, self.size // 2, self.size // 2)
        painter.setPen(QColor("#ffffff"))
        font = QFont()
        font.setPixelSize(self.size // 2)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.letter)


class ChipButton(QPushButton):
    """可切换的筛选芯片"""
    def __init__(self, text, active=False):
        super().__init__(text)
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(200)
        self._update_style()

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style()

    def _update_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.ACCENT_LIGHT};
                    color: #ffffff;
                    border: 1px solid {Theme.ACCENT_LIGHT};
                    border-radius: 16px;
                    padding: 8px 24px;
                    font-size: 32px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.BG_CARD};
                    color: {Theme.TEXT_SECONDARY};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 16px;
                    padding: 8px 24px;
                    font-size: 32px;
                }}
                QPushButton:hover {{
                    background: {Theme.BG_CARD_HOVER};
                    color: {Theme.TEXT_PRIMARY};
                }}
            """)


class PrimaryButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.ACCENT}, stop:1 #6366f1);
                color: white;
                font-size: 34px;
                font-weight: bold;
                padding: 16px 32px;
                border-radius: 12px;
                border: none;
                text-align: left;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #4f46e5);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1d4ed8, stop:1 #4338ca);
            }}
            QPushButton:disabled {{
                background: #1e293b;
                color: #475569;
            }}
        """)
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Theme.ACCENT}, stop:1 #6366f1);
                color: white;
                padding: 20px 48px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 32px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Theme.ACCENT_HOVER}, stop:1 #4f46e5);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1d4ed8, stop:1 #4338ca);
            }}
        """)


class SecondaryButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                padding: 16px 40px;
                border-radius: 8px;
                font-size: 40px;
            }}
            QPushButton:hover {{
                background: {Theme.BG_CARD_HOVER};
                border-color: {Theme.ACCENT};
            }}
        """)


class SuccessButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.GREEN};
                color: white;
                padding: 20px 48px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 32px;
            }}
            QPushButton:hover {{ background: {Theme.GREEN_HOVER}; }}
        """)

class DeviceCard(QFrame):
    """设备列表卡片"""
    clicked = pyqtSignal(dict)

    def __init__(self, device_data):
        super().__init__()
        self.device_data = device_data
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            DeviceCard {{
                background: {Theme.BG_CARD};
                border-radius: 10px;
                padding: 24px;
            }}
            DeviceCard:hover {{
                background: {Theme.BG_CARD_HOVER};
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(28)

        # Avatar
        codename = device_data["codename"]
        mfr = device_data.get("manufacturer", "?")
        avatar = AvatarLabel(mfr[0].upper(), Theme.ACCENT if mfr != "Other" else "#64748b")
        layout.addWidget(avatar)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        name_label = QLabel(device_data["name"])
        name_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 52px; font-weight: bold;")
        name_label.setWordWrap(False)
        name_label.setMinimumWidth(150)
        info_layout.addWidget(name_label)

        sub_label = QLabel(f"{codename} · {mfr}")
        sub_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 44px;")
        info_layout.addWidget(sub_label)

        layout.addLayout(info_layout, stretch=1)
        self.setLayout(layout)

    def mousePressEvent(self, event):
        self.clicked.emit(self.device_data)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.clicked.emit(self.device_data)
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet(f"""
            DeviceCard {{
                background: {Theme.BG_CARD_HOVER};
                border-radius: 10px;
                padding: 24px;
                border: 1px solid {Theme.ACCENT};
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(f"""
            DeviceCard {{
                background: {Theme.BG_CARD};
                border-radius: 10px;
                padding: 24px;
            }}
        """)
        super().leaveEvent(event)


# ===== 工作线程 =====

class FetchDevicesThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    item_fetched = pyqtSignal(dict)

    def run(self):
        try:
            data = http_get(f"{BASE_URL}/channels.json")
            channel_data = data.get(CHANNEL, {})
            if isinstance(channel_data, dict) and "error" in channel_data:
                self.error.emit(str(channel_data))
                return
            devices_data = channel_data.get("devices", {})

            # Priority devices first (OnePlus 6/6T)
            priority = {"enchilada", "fajita"}
            priority_devices = []
            other_devices = []

            for codename in devices_data:
                d = {
                    "codename": codename,
                    "name": get_device_name(codename),
                    "manufacturer": get_manufacturer(codename),
                }
                if codename in priority:
                    priority_devices.append(d)
                else:
                    other_devices.append(d)

            priority_devices.sort(key=lambda d: d["name"])
            other_devices.sort(key=lambda d: d["name"])

            # Emit priority first
            for d in priority_devices:
                self.item_fetched.emit(d)

            # Then emit rest in batches
            batch = []
            for d in other_devices:
                batch.append(d)
                if len(batch) >= 5:
                    for b in batch:
                        self.item_fetched.emit(b)
                    batch = []
            # remaining
            for b in batch:
                self.item_fetched.emit(b)

            self.finished.emit(priority_devices + other_devices)
        except Exception as e:
            self.error.emit(str(e))


class FetchDetailThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, codename):
        super().__init__()
        self.codename = codename

    def run(self):
        try:
            url = f"{BASE_URL}/{CHANNEL}/{self.codename}/index.json"
            data = http_get(url)
            images = data.get("images", [])
            # Deduplicate by version: merge files of same version, keep the one with most files
            version_map = {}
            for img in images:
                version = img.get("version", 0)
                files = []
                total_size = 0
                for f in img.get("files", []):
                    name = f.get("path", "")
                    size = f.get("size", 0)
                    # URL is relative to BASE_URL, not per-device
                    f_url = f"{BASE_URL}{name}" if name.startswith("/") else f"{BASE_URL}/{CHANNEL}/{self.codename}/{name}"
                    files.append({"name": name.split("/")[-1], "size": size, "url": f_url, "completed": False})
                    total_size += size
                    # Also add .asc signature file if present
                    sig = f.get("signature", "")
                    if sig:
                        sig_url = f"{BASE_URL}{sig}" if sig.startswith("/") else f"{BASE_URL}/{CHANNEL}/{self.codename}/{sig}"
                        sig_name = sig.split("/")[-1]
                        if sig_name not in {x["name"] for x in files}:
                            files.append({"name": sig_name, "size": 0, "url": sig_url, "completed": False})
                # Keep the version with the most files (full package, not delta)
                if version not in version_map or len(files) > len(version_map[version]["files"]):
                    version_map[version] = {
                        "desc": img.get("description", "unknown"),
                        "build": version,
                        "files": files,
                        "totalSize": total_size,
                    }

            # Add firmware files (boot.img + vbmeta.img) from cdimage
            codename = self.codename
            # Map device codename to firmware dir (enchilada/fajita share same firmware)
            firmware_map = {"enchilada": "enchilada_fajita", "fajita": "enchilada_fajita"}
            fw_dir = firmware_map.get(codename, codename)
            fw_base = f"https://cdimage.ubports.com/devices/{fw_dir}"

            channels = list(version_map.values())
            channels.sort(key=lambda c: c["build"], reverse=True)  # newest first

            # Add firmware files to every channel (they're device-specific, not version-specific)
            fw_files = [
                {"name": "boot.img", "size": 31580160, "url": f"{fw_base}/boot.img", "completed": False},
                {"name": "vbmeta.img", "size": 4096, "url": f"{fw_base}/vbmeta.img", "completed": False},
            ]
            for ch in channels:
                # Don't duplicate if already present
                existing_names = {f["name"] for f in ch["files"]}
                for fw in fw_files:
                    if fw["name"] not in existing_names:
                        ch["files"].append(fw.copy())
                        ch["totalSize"] += fw["size"]

            self.finished.emit(channels)
        except Exception as e:
            self.error.emit(str(e))


class DownloadWorker(QThread):
    progress = pyqtSignal(str, int, int, int)
    file_completed = pyqtSignal(str, int)
    all_completed = pyqtSignal(str)
    error = pyqtSignal(str)

    # Fastboot 文件列表
    FASTBOOT_FILES = {"boot.img", "vbmeta.img", "boot-working.img"}

    def __init__(self, files, dest_dir, fastboot_dir, recovery_dir, device_name):
        super().__init__()
        self.files = files
        self.dest_dir = dest_dir
        self.fastboot_dir = fastboot_dir
        self.recovery_dir = recovery_dir
        self.device_name = device_name
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _get_target_dir(self, filename):
        """按文件名分类到 fastboot 或 recovery 目录"""
        if filename in self.FASTBOOT_FILES:
            return self.fastboot_dir
        return self.recovery_dir

    def run(self):
        os.makedirs(self.dest_dir, exist_ok=True)
        os.makedirs(self.fastboot_dir, exist_ok=True)
        os.makedirs(self.recovery_dir, exist_ok=True)
        total_all = sum(f["size"] for f in self.files)
        completed_all = 0

        for f in self.files:
            if self._cancelled:
                # Clean up temp files
                for ext in [".tmp", ""]:
                    for p in [self.fastboot_dir, self.recovery_dir]:
                        fp = os.path.join(p, f["name"])
                        if os.path.exists(fp + ".tmp"):
                            os.remove(fp + ".tmp")
                self.error.emit("下载已取消")
                return
            file_url = f["url"]
            filename = f["name"]
            file_size = f["size"]
            # Place into correct directory
            target_dir = self._get_target_dir(filename)
            dest_path = os.path.join(target_dir, filename)

            # Skip if already downloaded
            if os.path.exists(dest_path) and os.path.getsize(dest_path) == file_size:
                self.file_completed.emit(filename, file_size)
                completed_all += file_size
                continue

            try:
                req = urllib.request.Request(file_url, headers={'User-Agent': 'UBportsFlasher/0.1'})
                with urllib.request.urlopen(req, timeout=600) as resp:
                    chunk_size = 65536
                    downloaded = 0
                    with open(dest_path + ".tmp", 'wb') as df:
                        while True:
                            if self._cancelled:
                                df.close()
                                os.remove(dest_path + ".tmp")
                                self.error.emit("下载已取消")
                                return
                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            df.write(chunk)
                            downloaded += len(chunk)
                            pct = int(downloaded * 100 / file_size) if file_size > 0 else 0
                            self.progress.emit(filename, pct, downloaded, file_size)

                    os.rename(dest_path + ".tmp", dest_path)
                    self.file_completed.emit(filename, file_size)
                    completed_all += file_size

            except Exception as e:
                self.error.emit(f"下载 {filename} 失败: {e}")
                return

        self.all_completed.emit(self.dest_dir)


# ===== 主窗口 =====

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UBports Flasher")
        self.resize(1100, 760)

        self.all_devices = []
        self.filtered_devices = []
        self.current_device = None
        self.current_channels = []

        # Central widget
        central = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

        # Content
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"background: {Theme.BG_DARK};")

        self._build_device_list_page()
        self._build_loading_page()
        self._build_detail_page()
        self._build_flash_page()

        self.content_stack.setCurrentWidget(self.loading_page)
        main_layout.addWidget(self.content_stack, stretch=1)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # Start loading
        QTimer.singleShot(100, self._load_devices)

    # ===== 侧边栏 =====

    def _build_sidebar(self):
        widget = QWidget()
        widget.setFixedWidth(380)
        widget.setStyleSheet(f"""
            background: {Theme.BG_SIDEBAR};
            border-right: 1px solid {Theme.BORDER};
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title = QLabel("UBports Flasher")
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 40px;
            font-weight: bold;
        """)
        title.setContentsMargins(24, 16, 24, 4)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        subtitle1 = QLabel("Ubuntu Touch")
        subtitle1.setStyleSheet(f"""
            color: {Theme.TEXT_MUTED};
            font-size: 28px;
        """)
        subtitle1.setContentsMargins(24, 0, 24, 0)
        subtitle1.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(subtitle1)

        subtitle2 = QLabel("离线刷机工具")
        subtitle2.setStyleSheet(f"""
            color: {Theme.TEXT_MUTED};
            font-size: 28px;
        """)
        subtitle2.setContentsMargins(24, 0, 24, 12)
        subtitle2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(subtitle2)

        # Nav items
        self.nav_devices = QLabel("📱  设备列表")
        self.nav_devices.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            background: {Theme.ACCENT_LIGHT};
            padding: 24px 40px;
            font-size: 32px;
            border-left: 3px solid {Theme.ACCENT};
        """)
        layout.addWidget(self.nav_devices)

        self.nav_downloads = QLabel("⬇️  下载管理")
        self.nav_downloads.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY};
            padding: 24px 40px;
            font-size: 32px;
        """)
        layout.addWidget(self.nav_downloads)

        # Spacer
        layout.addStretch()

        # Version
        ver = QLabel("v0.1.0 · Python Qt6")
        ver.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 34px; padding: 0 20px 16px;")
        layout.addWidget(ver)

        widget.setLayout(layout)
        return widget

    # ===== 页面构建 =====

    def _build_loading_page(self):
        self.loading_page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loading_label = QLabel("正在加载设备列表...")
        self.loading_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 50px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)

        self.loading_page.setLayout(layout)
        self.content_stack.addWidget(self.loading_page)

    def _build_device_list_page(self):
        self.device_list_page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 0)
        layout.setSpacing(24)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("设备列表")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 72px; font-weight: bold;")
        title_box.addWidget(title)

        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 40px;")
        title_box.addWidget(self.count_label)
        header.addLayout(title_box, stretch=1)
        layout.addLayout(header)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索设备名称、代号或制造商...")
        self.search_input.textChanged.connect(self._filter_devices)
        layout.addWidget(self.search_input)

        # Manufacturer chips
        self.mfr_chips = {}
        self.all_mfrs = ["All", "OnePlus", "Google", "Xiaomi", "Sony",
                         "Fairphone", "Motorola", "Lenovo", "Volla", "Essential", "Other"]

        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(8)
        chips_layout.setContentsMargins(0, 0, 0, 0)

        for mfr in self.all_mfrs:
            chip = ChipButton(mfr, active=(mfr == "All"))
            chip.toggled.connect(lambda checked, m=mfr: self._on_chip_toggled(m, checked))
            self.mfr_chips[mfr] = chip
            chips_layout.addWidget(chip)
        chips_layout.addStretch()

        layout.addLayout(chips_layout)
        self.selected_mfr = "All"

        # Scrollable device list
        self.device_scroll = QScrollArea()
        self.device_scroll.setWidgetResizable(True)
        self.device_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:horizontal {{
                background: {Theme.BG_DARK};
                height: 24px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: #334155;
                min-width: 40px;
                border-radius: 12px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: #475569;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
        """)

        self.device_container = QWidget()
        self.device_list_layout = QVBoxLayout()
        self.device_list_layout.setContentsMargins(0, 0, 0, 0)
        self.device_list_layout.setSpacing(8)
        self.device_list_layout.addStretch()
        self.device_container.setLayout(self.device_list_layout)
        self.device_scroll.setWidget(self.device_container)

        layout.addWidget(self.device_scroll, stretch=1)
        self.device_list_page.setLayout(layout)
        self.content_stack.addWidget(self.device_list_page)

    def _build_detail_page(self):
        self.detail_page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(48, 40, 48, 0)
        layout.setSpacing(16)

        # Top bar
        top_bar = QHBoxLayout()
        self.back_btn = SecondaryButton("←  返回")
        self.back_btn.clicked.connect(lambda: self.content_stack.setCurrentWidget(self.device_list_page))
        top_bar.addWidget(self.back_btn)

        self.detail_title = QLabel("")
        self.detail_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 62px; font-weight: bold; margin-left: 16px;")
        top_bar.addWidget(self.detail_title, stretch=1)
        layout.addLayout(top_bar)

        self.detail_sub = QLabel("")
        self.detail_sub.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 40px; padding-left: 84px;")
        layout.addWidget(self.detail_sub)

        # Detail content
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {Theme.BG_DARK};
                width: 24px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: #334155;
                min-height: 40px;
                border-radius: 12px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #475569;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self.detail_container = QWidget()
        self.detail_container_layout = QVBoxLayout()
        self.detail_container_layout.setContentsMargins(0, 16, 0, 0)
        self.detail_container_layout.setSpacing(16)
        self.detail_container_layout.addStretch()
        self.detail_container.setLayout(self.detail_container_layout)
        self.detail_scroll.setWidget(self.detail_container)

        layout.addWidget(self.detail_scroll, stretch=1)
        self.detail_page.setLayout(layout)
        self.content_stack.addWidget(self.detail_page)

    def _build_flash_page(self):
        self.flash_page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(48, 40, 48, 0)
        layout.setSpacing(16)

        top_bar = QHBoxLayout()
        self.flash_back = SecondaryButton("←  返回")
        self.flash_back.clicked.connect(lambda: self.content_stack.setCurrentWidget(self.detail_page))
        top_bar.addWidget(self.flash_back)

        self.flash_title = QLabel("")
        self.flash_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 62px; font-weight: bold; margin-left: 16px;")
        top_bar.addWidget(self.flash_title, stretch=1)
        layout.addLayout(top_bar)

        # Flash content
        self.flash_scroll = QScrollArea()
        self.flash_scroll.setWidgetResizable(True)
        self.flash_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {Theme.BG_DARK};
                width: 24px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: #334155;
                min-height: 40px;
                border-radius: 12px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #475569;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self.flash_container = QWidget()
        self.flash_container_layout = QVBoxLayout()
        self.flash_container_layout.setContentsMargins(0, 16, 0, 0)
        self.flash_container_layout.setSpacing(16)
        self.flash_container_layout.addStretch()
        self.flash_container.setLayout(self.flash_container_layout)
        self.flash_scroll.setWidget(self.flash_container)

        layout.addWidget(self.flash_scroll, stretch=1)
        self.flash_page.setLayout(layout)
        self.content_stack.addWidget(self.flash_page)

    # ===== 数据加载 =====

    def _load_devices(self):
        self.content_stack.setCurrentWidget(self.loading_page)
        self.loading_label.setText("正在加载设备列表...")

        self.fetch_thread = FetchDevicesThread()
        self.fetch_thread.finished.connect(self._on_devices_loaded)
        self.fetch_thread.item_fetched.connect(self._on_device_fetched)
        self.fetch_thread.error.connect(self._on_devices_error)
        self.fetch_thread.start()

    def _on_device_fetched(self, device):
        """流式添加设备——每收到一个就插入列表"""
        self.all_devices.append(device)
        # 如果当前筛选匹配，直接添加到显示列表
        if self._matches_filter(device):
            card = DeviceCard(device)
            card.clicked.connect(self._on_device_click)
            self.device_list_layout.addWidget(card)

    def _on_devices_loaded(self, devices):
        self.content_stack.setCurrentWidget(self.device_list_page)
        self.count_label.setText(f"共 {len(devices)} 款设备")

    def _on_devices_error(self, msg):
        self.loading_label.setText(f"❌ 加载失败: {msg}")
        self.loading_label.setStyleSheet(f"color: {Theme.RED}; font-size: 44px;")

    def _matches_filter(self, d):
        """检查设备是否符合当前筛选条件"""
        mfr = self.selected_mfr
        keyword = self.search_input.text().strip().lower()
        if mfr != "All" and d["manufacturer"] != mfr:
            return False
        if keyword:
            return (keyword in d["name"].lower() or
                    keyword in d["codename"].lower() or
                    keyword in d["manufacturer"].lower())
        return True

    def _filter_devices(self):
        keyword = self.search_input.text().strip().lower()
        mfr = self.selected_mfr

        filtered = []
        for d in self.all_devices:
            if mfr != "All" and d["manufacturer"] != mfr:
                continue
            if keyword:
                if (keyword in d["name"].lower() or
                    keyword in d["codename"].lower() or
                    keyword in d["manufacturer"].lower()):
                    filtered.append(d)
            else:
                filtered.append(d)

        self.filtered_devices = filtered
        self._rebuild_device_list(filtered)
        self.count_label.setText(f"共 {len(filtered)}/{len(self.all_devices)} 款设备")

    def _rebuild_device_list(self, devices):
        # Remove all cards
        layout = self.device_list_layout
        while layout.count() > 1:  # keep stretch
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        for d in devices:
            card = DeviceCard(d)
            card.clicked.connect(self._on_device_click)
            layout.insertWidget(layout.count() - 1, card)

    def _on_chip_toggled(self, mfr, checked):
        if not checked:
            return
        self.selected_mfr = mfr
        for name, chip in self.mfr_chips.items():
            chip.setChecked(name == mfr)
        self._filter_devices()

    # ===== 设备详情 =====

    def _on_device_click(self, device_data):
        self.current_device = device_data
        self.detail_title.setText(device_data["name"])
        self.detail_sub.setText(f"{device_data['codename']} · {device_data['manufacturer']}")

        # Clear detail
        layout = self.detail_container_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Show loading
        loading_lbl = QLabel("正在加载频道信息...")
        loading_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 42px; padding: 40px;")
        loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.insertWidget(0, loading_lbl)

        self.content_stack.setCurrentWidget(self.detail_page)

        # Fetch in thread
        self.detail_thread = FetchDetailThread(device_data["codename"])
        self.detail_thread.finished.connect(self._on_detail_loaded)
        self.detail_thread.error.connect(self._on_detail_error)
        self.detail_thread.start()

    def _on_detail_loaded(self, channels):
        self.current_channels = channels
        layout = self.detail_container_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not channels:
            lbl = QLabel("该设备暂无可用频道")
            lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 42px; padding: 40px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.insertWidget(0, lbl)
            return

        for ch in channels:
            card = self._build_channel_card(ch)
            layout.insertWidget(layout.count() - 1, card)

    def _build_channel_card(self, channel):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_CARD};
                border-radius: 12px;
                padding: 32px;
            }}
            QFrame:hover {{
                background: {Theme.BG_CARD_HOVER};
                border: 1px solid {Theme.ACCENT};
            }}
        """)

        c_layout = QVBoxLayout()
        c_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        ch_name = QLabel(channel["desc"])
        ch_name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 44px; font-weight: bold;")
        header.addWidget(ch_name, stretch=1)

        build_label = QLabel(format_build(channel["build"]))
        build_label.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 40px; font-weight: bold;")
        header.addWidget(build_label)
        c_layout.addLayout(header)

        # Info
        info = QLabel(f"共 {len(channel['files'])} 个文件 · {format_size(channel['totalSize'])}")
        info.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 40px;")
        c_layout.addWidget(info)

        # Files list
        for f in channel["files"]:
            file_row = QHBoxLayout()
            file_row.setContentsMargins(0, 4, 0, 4)
            fname = QLabel(f["name"])
            fname.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 32px;")
            file_row.addWidget(fname, stretch=1)
            fsize = QLabel(format_size(f["size"]))
            fsize.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 32px;")
            file_row.addWidget(fsize)
            c_layout.addLayout(file_row)

        # Download button
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        d_btn = PrimaryButton("📥  下载并刷机")
        self._current_dl_btn = d_btn
        d_btn.clicked.connect(lambda checked, ch=channel, btn=d_btn: self._start_download(ch, btn))
        btn_row.addWidget(d_btn)

        # Cancel button (hidden until download starts)
        cancel_btn = QPushButton("✕  取消下载")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.RED};
                color: white;
                font-size: 34px;
                font-weight: bold;
                padding: 16px 32px;
                border-radius: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background: #dc2626;
            }}
        """)
        cancel_btn.clicked.connect(lambda checked, cb=cancel_btn: self._cancel_download(cb))
        cancel_btn.hide()
        btn_row.addWidget(cancel_btn)

        card.cancel_btn = cancel_btn
        card.download_btn = d_btn
        c_layout.addLayout(btn_row)

        card.setLayout(c_layout)
        return card

    def _on_detail_error(self, msg):
        layout = self.detail_container_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        lbl = QLabel(f"❌ 加载失败: {msg}")
        lbl.setStyleSheet(f"color: {Theme.RED}; font-size: 42px; padding: 40px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.insertWidget(0, lbl)

    # ===== 下载 =====

    def _start_download(self, channel, btn=None):
        # Disable button to prevent double-click
        if self._current_dl_btn:
            self._current_dl_btn.setEnabled(False)
        # Find the cancel button from the card
        card = btn.parent() if btn else None
        if card and hasattr(card, 'cancel_btn') and card.cancel_btn:
            card.cancel_btn.show()

        codename = self.current_device["codename"]
        self._download_codename = codename
        dest_dir = os.path.join(DOWNLOAD_DIR, codename)
        self.flash_title.setText(f"下载: {channel['desc']}")
        self.content_stack.setCurrentWidget(self.flash_page)

        # 分类目录
        fastboot_dir = os.path.join(dest_dir, f"fastboot-{codename}")
        recovery_dir = os.path.join(dest_dir, f"recovery-{codename}")
        os.makedirs(fastboot_dir, exist_ok=True)
        os.makedirs(recovery_dir, exist_ok=True)
        self._fastboot_dir = fastboot_dir
        self._recovery_dir = recovery_dir

        layout = self.flash_container_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Status
        self.dl_status = QLabel("准备下载...")
        self.dl_status.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 42px;")
        layout.insertWidget(layout.count() - 1, self.dl_status)

        # File progress rows
        self.dl_progress_bars = {}
        for f in channel["files"]:
            row = QVBoxLayout()
            row.setSpacing(4)
            row.setContentsMargins(0, 8, 0, 8)

            name_row = QHBoxLayout()
            fn = QLabel(f["name"])
            fn.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 40px;")
            name_row.addWidget(fn, stretch=1)

            sz = QLabel(format_size(f["size"]))
            sz.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 32px;")
            name_row.addWidget(sz)
            row.addLayout(name_row)

            bar = QProgressBar()
            bar.setMaximum(100)
            bar.setValue(0)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background: {Theme.BG_CARD};
                    border: none;
                    border-radius: 4px;
                    height: 6px;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Theme.ACCENT}, stop:1 #6366f1);
                    border-radius: 4px;
                }}
            """)
            row.addWidget(bar)
            self.dl_progress_bars[f["name"]] = bar

            layout.insertWidget(layout.count() - 1, self._make_widget_from_layout(row))

        # Total progress
        total_box = QVBoxLayout()
        total_box.setSpacing(8)
        total_box.setContentsMargins(0, 32, 0, 0)

        total_label = QLabel("总进度")
        total_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 42px; font-weight: bold;")
        total_box.addWidget(total_label)

        self.total_bar = QProgressBar()
        self.total_bar.setMaximum(100)
        self.total_bar.setValue(0)
        self.total_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.BG_CARD};
                border: none;
                border-radius: 6px;
                height: 10px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22c55e, stop:1 #16a34a);
                border-radius: 6px;
            }}
        """)
        total_box.addWidget(self.total_bar)

        self.total_text = QLabel("")
        self.total_text.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 40px;")
        total_box.addWidget(self.total_text)

        layout.insertWidget(layout.count() - 1, self._make_widget_from_layout(total_box))

        # Show directories
        dir_info = QLabel(f"📁  文件已分类:")
        dir_info.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 36px; padding-top: 16px;")
        layout.insertWidget(layout.count() - 1, dir_info)

        fb_label = QLabel(f"  fastboot-{codename}/  ← boot.img, vbmeta.img")
        fb_label.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 32px;")
        layout.insertWidget(layout.count() - 1, fb_label)

        rec_label = QLabel(f"  recovery-{codename}/  ← rootfs, device, 刷机脚本")
        rec_label.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 32px;")
        layout.insertWidget(layout.count() - 1, rec_label)

        # Start download worker
        self.dl_worker = DownloadWorker(channel["files"], dest_dir, self._fastboot_dir, self._recovery_dir, codename)
        self.dl_worker.progress.connect(self._on_dl_progress)
        self.dl_worker.file_completed.connect(self._on_dl_file_completed)
        self.dl_worker.all_completed.connect(self._on_dl_all_completed)
        self.dl_worker.error.connect(self._on_dl_error)
        self.dl_worker.start()

    def _cancel_download(self, cancel_btn=None):
        if hasattr(self, 'dl_worker') and self.dl_worker and self.dl_worker.isRunning():
            self.dl_worker.cancel()
            self.dl_worker.wait(5000)
            if cancel_btn:
                cancel_btn.hide()
            if self._current_dl_btn:
                self._current_dl_btn.setEnabled(True)

    def _hide_all_cancel_btns(self):
        for i in range(self.detail_container_layout.count()):
            item = self.detail_container_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if hasattr(w, 'cancel_btn') and w.cancel_btn:
                    w.cancel_btn.hide()
                if hasattr(w, 'download_btn') and w.download_btn:
                    w.download_btn.setEnabled(True)

    def _make_widget_from_layout(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

    def _on_dl_progress(self, filename, pct, downloaded, total):
        bar = self.dl_progress_bars.get(filename)
        if bar:
            bar.setValue(pct)

        # Update total
        total_done = sum(f["size"] for f in self.current_channels[0]["files"] if f.get("completed"))
        total_all = sum(f["size"] for f in self.current_channels[0]["files"])
        if total_all > 0:
            self.total_bar.setValue(int(total_done * 100 / total_all))
            self.total_text.setText(f"{format_size(total_done)} / {format_size(total_all)}")

        self.dl_status.setText(f"正在下载: {filename}")

    def _on_dl_file_completed(self, filename, size):
        for ch in self.current_channels:
            for f in ch["files"]:
                if f["name"] == filename:
                    f["completed"] = True
        bar = self.dl_progress_bars.get(filename)
        if bar:
            bar.setValue(100)

    def _on_dl_all_completed(self, dest_dir):
        # Re-enable download button
        if self._current_dl_btn:
            self._current_dl_btn.setEnabled(True)
        # Hide cancel button from all cards
        self._hide_all_cancel_btns()

        codename = self._download_codename
        fastboot_dir = self._fastboot_dir
        recovery_dir = self._recovery_dir

        # List actually downloaded files in recovery dir
        recovery_files = []
        for fn in os.listdir(recovery_dir):
            if fn.endswith(".tar.xz") and not fn.endswith(".asc"):
                asc = fn + ".asc"
                recovery_files.append((fn, asc if os.path.exists(os.path.join(recovery_dir, asc)) else None))
        recovery_files.sort()

        # Generate ubuntu_command for UBports Installer recovery
        ubuntu_cmd_path = os.path.join(recovery_dir, "ubuntu_command")
        with open(ubuntu_cmd_path, 'w') as f:
            f.write("format system\n")
            f.write("load_keyring image-master.tar.xz image-master.tar.xz.asc\n")
            f.write("load_keyring image-signing.tar.xz image-signing.tar.xz.asc\n")
            f.write("mount system\n")
            for fn, asc_fn in recovery_files:
                if asc_fn:
                    f.write(f"update {fn} {asc_fn}\n")
                else:
                    f.write(f"update {fn}\n")
            f.write("unmount system\n")
        # Generate flash-ubports.sh for TWRP
        flash_sh_path = os.path.join(recovery_dir, "flash-ubports.sh")
        sh_script = f"""#!/sbin/sh
# UBports Offline Flasher - {codename}
set -e
DIR=$(dirname "$0" 2>/dev/null)
[ -d "$DIR" ] || DIR="/usbstorage"
[ -d "$DIR" ] || DIR="/usb_otg"
[ -d "$DIR" ] || DIR="/sdcard"

echo "Flashing {codename}..."
# Fastboot 分区文件在上级目录
FASTBOOT_DIR="$DIR/fastboot-{codename}"
if [ -f "$FASTBOOT_DIR/boot.img" ]; then
    SLOT=$(getprop ro.boot.slot_suffix)
    dd if="$FASTBOOT_DIR/boot.img" of="/dev/block/bootdevice/by-name/boot$SLOT" bs=1M
fi
if [ -f "$FASTBOOT_DIR/vbmeta.img" ]; then
    dd if="$FASTBOOT_DIR/vbmeta.img" of="/dev/block/bootdevice/by-name/vbmeta$SLOT" bs=1M
fi
echo "Done! Reboot now."
"""
        with open(flash_sh_path, 'w') as f:
            f.write(sh_script)
        os.chmod(flash_sh_path, 0o755)
        layout = self.flash_container_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Success!
        success = QLabel("✅  全部下载完成!")
        success.setStyleSheet(f"color: {Theme.GREEN}; font-size: 62px; font-weight: bold; padding: 16px 0;")
        layout.insertWidget(layout.count() - 1, success)

        info = QLabel(f"文件保存在: {dest_dir}")
        info.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 32px;")
        layout.insertWidget(layout.count() - 1, info)

        info2 = QLabel("需要刷机请配合 ubports-offline-flasher.sh 使用")
        info2.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 40px;")
        layout.insertWidget(layout.count() - 1, info2)

        open_btn = SuccessButton("📂  打开下载目录")
        open_dir = os.path.join(DOWNLOAD_DIR, codename)
        open_btn.clicked.connect(lambda checked, d=open_dir: subprocess.run(["xdg-open", d]))
        layout.insertWidget(layout.count() - 1, open_btn)

        back_btn = SecondaryButton("←  返回设备列表")
        back_btn.clicked.connect(lambda: self.content_stack.setCurrentWidget(self.device_list_page))
        layout.insertWidget(layout.count() - 1, back_btn)

    def _on_dl_error(self, msg):
        self.dl_status.setText(f"❌ {msg}")
        self.dl_status.setStyleSheet(f"color: {Theme.RED}; font-size: 42px;")
        if self._current_dl_btn:
            self._current_dl_btn.setEnabled(True)
        self._hide_all_cancel_btns()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    # Set app-wide font
    font = QFont()
    font.setFamilies(["Ubuntu", "Noto Sans CJK SC", "Noto Sans", "sans-serif"])
    font.setPointSize(28)
    app.setFont(font)

    window = MainWindow()
    # 强制横屏
    screen = app.primaryScreen()
    if screen:
        geo = screen.geometry()
        # 强制横屏：宽 > 高
        w = max(geo.width(), geo.height())
        h = min(geo.width(), geo.height())
        window.resize(w, h)
        window.move(0, 0)
    window.show()
    window.showMaximized()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())