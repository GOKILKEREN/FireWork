#!/usr/bin/env python3
"""FireStore v1.0 - Progress + Context Menu + Settings"""

import json
import os
import subprocess
import sys
from pathlib import Path

# === LANGUAGE ===
_LANG_RAW = (os.environ.get('LC_ALL') or os.environ.get('LC_MESSAGES')
             or os.environ.get('LANG') or 'en_US.UTF-8')
LANG = _LANG_RAW.split('.')[0].split('_')[0].lower()

TRANSLATIONS = {
    'id': {
        'all': 'Semua', 'featured': 'Aplikasi Unggulan', 'all_apps': 'Semua Aplikasi',
        'install': 'Install', 'open': 'Buka', 'update': 'Perbarui', 'uninstall': 'Hapus',
        'info': 'Info', 'settings': 'Pengaturan', 'search': 'Cari aplikasi...',
        'available': '{} aplikasi tersedia', 'count': '{} aplikasi',
        'confirm_title': 'Konfirmasi Hapus', 'confirm_text': 'Hapus {}?',
        'confirm_info': 'Aplikasi akan dihapus dari sistem.',
        'cancel': 'Batal', 'save': 'Simpan', 'close': 'Tutup',
        'settings_title': 'Pengaturan FireStore',
        'theme_label': 'Tema Warna', 'behavior': 'Perilaku',
        'auto_close': 'Tutup progress dialog otomatis setelah selesai',
        'show_log': 'Tampilkan log detail saat install/update/hapus',
        'install_confirm': 'Konfirmasi Install',
        'yes_install': 'Ya, Install', 'question_install': 'Install {}?',
        'category': 'Kategori', 'type': 'Tipe', 'status': 'Status',
        'source': 'Sumber', 'installed_at': 'Diinstall pada',
        'installed_sys': 'Terinstall di sistem', 'not_installed': 'Belum terinstall',
        'from_fs': 'FireStore', 'from_sys': 'Sistem (bukan via FireStore)',
        'starting': 'Memulai...', 'done': 'Selesai!',
        'failed': 'Gagal. Cek log di bawah.', 'info_title': 'Info',
    },
    'en': {
        'all': 'All', 'featured': 'Featured Apps', 'all_apps': 'All Apps',
        'install': 'Install', 'open': 'Open', 'update': 'Update', 'uninstall': 'Uninstall',
        'info': 'Info', 'settings': 'Settings', 'search': 'Search apps...',
        'available': '{} apps available', 'count': '{} apps',
        'confirm_title': 'Confirm Uninstall', 'confirm_text': 'Uninstall {}?',
        'confirm_info': 'App will be removed from the system.',
        'cancel': 'Cancel', 'save': 'Save', 'close': 'Close',
        'settings_title': 'FireStore Settings',
        'theme_label': 'Color Theme', 'behavior': 'Behavior',
        'auto_close': 'Auto-close progress dialog when finished',
        'show_log': 'Show detailed log during install/update/uninstall',
        'install_confirm': 'Confirm Install',
        'yes_install': 'Yes, Install', 'question_install': 'Install {}?',
        'category': 'Category', 'type': 'Type', 'status': 'Status',
        'source': 'Source', 'installed_at': 'Installed at',
        'installed_sys': 'Installed on system', 'not_installed': 'Not installed',
        'from_fs': 'FireStore', 'from_sys': 'System (not via FireStore)',
        'starting': 'Starting...', 'done': 'Done!',
        'failed': 'Failed. Check log below.', 'info_title': 'Info',
    },
}

def t(key, *args):
    d = TRANSLATIONS.get(LANG, TRANSLATIONS['en'])
    text = d.get(key, TRANSLATIONS['en'].get(key, key))
    return text.format(*args) if args else text

from PySide6.QtCore import Qt, QTimer, QSize, QProcess
from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QLineEdit,
    QDialog, QListWidget, QListWidgetItem, QPlainTextEdit,
    QProgressBar, QComboBox, QCheckBox, QMenu, QMessageBox
)

FIRESTORE_DIR = Path.home() / "FireStore"
CACHE_FILE = FIRESTORE_DIR / "metadata" / "apt-cache.json"
CATALOG_FILE = FIRESTORE_DIR / "metadata" / "desktop-catalog.json"
INSTALLED_FILE = FIRESTORE_DIR / "metadata" / "installed.json"
META_FILE = FIRESTORE_DIR / "metadata" / "firestore-installed.json"
ICONS_DIR = FIRESTORE_DIR / "metadata" / "icons"
SETTINGS_FILE = FIRESTORE_DIR / "settings.json"
BACKEND = FIRESTORE_DIR / "bin" / "firestore-backend.py"

LOGO_CANDIDATES = [
    Path.home() / "Documents" / "FireWork" / "FireWorkStore.png",
    Path.home() / "Documents" / "FireWork" / "FireWorkLogo.png",
    FIRESTORE_DIR / "metadata" / "icons" / "firework.png",
]

FEATURED_APPS = [
    'firefox-esr', 'chromium', 'thunderbird', 'vlc', 'gimp',
    'krita', 'audacity', 'obs-studio', 'blender', 'inkscape',
    'libreoffice', 'steam-installer', 'lutris', 'code',
    'telegram-desktop', 'discord', 'kdenlive', 'handbrake',
]

ICON_ALIAS = {
    'firefox-esr': 'firefox', 'chromium': 'chromium',
    'thunderbird': 'thunderbird', 'telegram-desktop': 'telegram',
    'discord': 'discord', 'obs-studio': 'obs', 'code': 'vscode',
    'steam-installer': 'steam',
}

FIREWINE_APPS = [
    {"id": "notepadpp", "name": "Notepad++", "category": "FireWine", "type": "exe", "file": "notepadpp.exe", "url": "", "description": "Text editor ringan", "rating": 4.7},
    {"id": "winrar", "name": "WinRAR", "category": "FireWine", "type": "exe", "file": "winrar.exe", "url": "", "description": "Arsip file", "rating": 4.8},
    {"id": "aimp", "name": "AIMP", "category": "FireWine", "type": "exe", "file": "aimp.exe", "url": "", "description": "Music player", "rating": 4.7},
    {"id": "foobar", "name": "foobar2000", "category": "FireWine", "type": "exe", "file": "foobar.exe", "url": "", "description": "Audio player ringan", "rating": 4.6},
    {"id": "photoshop", "name": "Photoshop CS6", "category": "FireWine", "type": "exe", "file": "photoshop.exe", "url": "", "description": "Editor gambar", "rating": 4.5},
    {"id": "msoffice", "name": "MS Office 2010", "category": "FireWine", "type": "exe", "file": "msoffice.exe", "url": "", "description": "Office suite", "rating": 4.4},
]

THEMES = {
    "orange": {"name": "FireWork Orange", "accent": "#FF6B00", "hover": "#FF8C32"},
    "blue":   {"name": "Ocean Blue",      "accent": "#1E90FF", "hover": "#4DA6FF"},
    "green":  {"name": "Forest Green",    "accent": "#2ECC71", "hover": "#52D98A"},
    "purple": {"name": "Royal Purple",    "accent": "#9B59B6", "hover": "#B07CC6"},
    "red":    {"name": "Crimson Red",     "accent": "#E74C3C", "hover": "#EC7063"},
}

DEFAULT_SETTINGS = {"theme": "orange", "auto_close": True, "show_log": True}
_SETTINGS = dict(DEFAULT_SETTINGS)


def load_settings():
    global _SETTINGS
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                _SETTINGS.setdefault(k, v)
            _SETTINGS.update(data)
        except Exception:
            _SETTINGS = dict(DEFAULT_SETTINGS)
    return _SETTINGS


def save_settings(s):
    global _SETTINGS
    _SETTINGS = dict(s)
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(_SETTINGS, f, indent=2)


def accent():
    t = THEMES.get(_SETTINGS.get("theme", "orange"), THEMES["orange"])
    return t["accent"]


def hover():
    t = THEMES.get(_SETTINGS.get("theme", "orange"), THEMES["orange"])
    return t["hover"]


# ============ SYSTEM STATE ============

_SYS_INSTALLED = None


def get_system_installed():
    global _SYS_INSTALLED
    if _SYS_INSTALLED is not None:
        return _SYS_INSTALLED
    installed = set()
    try:
        r = subprocess.run(
            ['dpkg-query', '-W', '-f=${Package} ${Status}\n'],
            capture_output=True, text=True, timeout=15
        )
        for line in r.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[1:4] == ['install', 'ok', 'installed']:
                installed.add(parts[0])
    except Exception:
        pass
    _SYS_INSTALLED = installed
    return installed


def refresh_system_installed():
    global _SYS_INSTALLED
    _SYS_INSTALLED = None


def is_installed_system(pkg_id):
    return pkg_id in get_system_installed()


def load_installed():
    if not INSTALLED_FILE.exists():
        return []
    try:
        with open(INSTALLED_FILE) as f:
            return json.load(f).get("installed", [])
    except Exception:
        return []


def load_meta():
    if not META_FILE.exists():
        return {"apps": {}}
    try:
        with open(META_FILE) as f:
            return json.load(f)
    except Exception:
        return {"apps": {}}


def get_install_info(app_id):
    return load_meta().get("apps", {}).get(app_id)


def load_cache():
    """Baca katalog desktop dari AppStream (1876 app) + fallback apt-cache."""
    apps = []
    if CATALOG_FILE.exists():
        try:
            with open(CATALOG_FILE) as f:
                apps = json.load(f)
        except Exception as e:
            print("Catalog error:", e)
    if not apps and CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            data = json.load(f)
        apps = data.get('apps', [])
    apps = FIREWINE_APPS + apps
    categories = {"Semua"}
    for a in apps:
        categories.add(a.get('category', 'Lainnya'))
    return {"categories": sorted(list(categories)), "apps": apps}


def load_system_apps():
    """apt-cache lengkap, cuma buat search system command."""
    if not CACHE_FILE.exists():
        return []
    try:
        with open(CACHE_FILE) as f:
            return json.load(f).get('apps', [])
    except Exception:
        return []


# ============ ICON ============

_ICON_CACHE = {}
_DESKTOP_APPS_FILE = FIRESTORE_DIR / "metadata" / "desktop-apps.json"
_DESKTOP_APPS = {}

# Subkategori spesifik -> mapping yang lebih akurat
FREEDESKTOP_CAT_MAP = {
    # Internet (dari subkategori Network)
    'WebBrowser':      'Internet',
    'Email':           'Internet',
    'InstantMessaging':'Internet',
    'IRCClient':       'Internet',
    'Feed':            'Internet',
    'FileTransfer':    'Internet',
    'P2P':             'Internet',
    'News':            'Internet',
    'Chat':            'Internet',
    'VideoConference': 'Internet',
    # Sisanya Network
    'Network':         'Network',
    'RemoteAccess':    'Network',
    'VPN':             'Network',
    'HamRadio':        'Network',
    'Dialup':          'Network',
    'Telephony':       'Network',
    # Multimedia
    'AudioVideo':      'Multimedia',
    'Audio':           'Multimedia',
    'Video':           'Multimedia',
    'Player':          'Multimedia',
    'Recorder':        'Multimedia',
    'TV':              'Multimedia',
    # Sisanya
    'Development':     'Development',
    'Education':       'Education',
    'Game':            'Gaming',
    'Office':          'Office',
    'Science':         'Education',
    'Settings':        'System',
    'System':          'System',
    'Utility':         'Lainnya',
    'Security':        'Security',
    'Graphics':        'Multimedia',
}


def category_for(app):
    """Ambil kategori dari app['category'] (hasil build-catalog) atau desktop file."""
    # Prioritas 1: kategori dari katalog AppStream (udah dipetakan dengan benar)
    cat = app.get('category')
    if cat and cat != 'Lainnya':
        return cat
    # Prioritas 2: desktop file lokal
    d = _DESKTOP_APPS.get(app['id'])
    if d and d.get('categories'):
        cats = [c.strip() for c in d['categories'].split(';') if c.strip()]
        # Pass 1: subkategori spesifik menang
        for c in cats:
            if c in ('WebBrowser', 'Email', 'InstantMessaging', 'IRCClient',
                     'Feed', 'FileTransfer', 'P2P', 'News', 'Chat', 'VideoConference'):
                return 'Internet'
        # Pass 2: kategori utama
        for c in cats:
            if c in FREEDESKTOP_CAT_MAP:
                return FREEDESKTOP_CAT_MAP[c]
    return 'Lainnya' 
if _DESKTOP_APPS_FILE.exists():
    try:
        with open(_DESKTOP_APPS_FILE) as f:
            _DESKTOP_APPS = json.load(f)
    except Exception:
        _DESKTOP_APPS = {}


def is_desktop_app(app):
    """App desktop beneran: punya .desktop file, atau FireWine custom."""
    if not app:
        return False
    if app.get('type') == 'exe':
        return True  # FireWine apps selalu tampil
    return app['id'] in _DESKTOP_APPS
_ICON_MAP_FILE = FIRESTORE_DIR / "metadata" / "icon-map.json"
_ICON_MAP = {}
if _ICON_MAP_FILE.exists():
    try:
        with open(_ICON_MAP_FILE) as f:
            _ICON_MAP = json.load(f)
    except Exception:
        _ICON_MAP = {}


def _resolve_icon(pkg_id):
    # 1. icon-map.json (hasil build-icon-map.py)
    if pkg_id in _ICON_MAP:
        p = ICONS_DIR / _ICON_MAP[pkg_id]
        if p.exists():
            return str(p)
    # 2. langsung nama pkg
    for ext in ('.png', '.svg', '.xpm'):
        p = ICONS_DIR / (pkg_id + ext)
        if p.exists():
            return str(p)
    # 3. alias manual
    alias = ICON_ALIAS.get(pkg_id)
    if alias:
        for ext in ('.png', '.svg', '.xpm'):
            p = ICONS_DIR / (alias + ext)
            if p.exists():
                return str(p)
    return None


_GENERIC_ICONS = {
    'application-x-executable', 'application-default-icon',
    'application-x-executable-symbolic', 'application-x-generic',
    'exec', 'unknown', 'application', 'binary', 'executable',
}

_ICON_VALID_CACHE = {}


def has_icon(pkg_id):
    """Strict: cek file ada DAN bisa di-load sebagai QPixmap."""
    if pkg_id in _ICON_VALID_CACHE:
        return _ICON_VALID_CACHE[pkg_id]
    path = _resolve_icon(pkg_id)
    if path:
        # Skip kalau nama file-nya generic (icon fallback system)
        stem = Path(path).stem.lower()
        if stem not in _GENERIC_ICONS:
            pm = QPixmap(path)
            if not pm.isNull() and pm.width() > 4 and pm.height() > 4:
                _ICON_VALID_CACHE[pkg_id] = True
                return True
    # Cek Qt theme (Papirus, dll)
    if pkg_id not in _GENERIC_ICONS:
        icon = QIcon.fromTheme(pkg_id)
        if not icon.isNull():
            pm = icon.pixmap(32, 32)
            if not pm.isNull() and pm.width() > 4:
                _ICON_VALID_CACHE[pkg_id] = True
                return True
    _ICON_VALID_CACHE[pkg_id] = False
    return False


_APP_ICON_LOOKUP = {}

def _build_icon_lookup(apps):
    for a in apps:
        aid = a.get('id')
        if aid and aid not in _APP_ICON_LOOKUP:
            _APP_ICON_LOOKUP[aid] = a.get('icon_name') or aid


def get_icon_pixmap(pkg_id, size=40, icon_name=None):
    cache_key = (pkg_id, icon_name)
    if cache_key in _ICON_CACHE:
        cached = _ICON_CACHE[cache_key]
        if cached is None:
            return None
        pm = cached.pixmap(size, size)
        return pm if not pm.isNull() else None
    # Nama-nama yang bakal dicoba (prioritas atas ke bawah)
    names = []
    if icon_name:
        names.append(icon_name)
    mapped = _APP_ICON_LOOKUP.get(pkg_id)
    if mapped and mapped not in names:
        names.append(mapped)
    if pkg_id not in names:
        names.append(pkg_id)
    if pkg_id in ICON_ALIAS and ICON_ALIAS[pkg_id] not in names:
        names.append(ICON_ALIAS[pkg_id])
    # 1. Folder lokal FireStore
    for name in names:
        for ext in ('.png', '.svg', '.xpm'):
            p = ICONS_DIR / (name + ext)
            if p.exists():
                icon = QIcon(str(p))
                if not icon.isNull():
                    pm = icon.pixmap(size, size)
                    if not pm.isNull():
                        _ICON_CACHE[cache_key] = icon
                        return pm
    # 2. Qt theme (Papirus/hicolor/Adwaita)
    for name in names:
        theme_icon = QIcon.fromTheme(name)
        if not theme_icon.isNull():
            pm = theme_icon.pixmap(size, size)
            if not pm.isNull():
                _ICON_CACHE[cache_key] = theme_icon
                return pm
    _ICON_CACHE[cache_key] = None
    return None

def _find_logo_path():
    for lp in LOGO_CANDIDATES:
        if lp.exists():
            return str(lp)
    return None


# ============ PROGRESS DIALOG ============

class ProgressDialog(QDialog):
    finished_ok = False

    def __init__(self, action, app, parent=None):
        super().__init__(parent)
        self.action = action
        self.app = app
        self.accent = accent()
        self.success = None
        self.target = 5
        self.current = 0
        titles = {"install": "Menginstall", "uninstall": "Menghapus", "update": "Mengupdate"}
        self.setWindowTitle(titles.get(action, action) + " " + app['name'])
        self.setModal(True)
        self.setMinimumSize(560, 380)
        self.setStyleSheet("QDialog { background-color: #1a1a1a; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        # Header: icon + name
        head = QHBoxLayout()
        il = QLabel(); il.setFixedSize(56, 56); il.setAlignment(Qt.AlignCenter)
        pm = get_icon_pixmap(app['id'], 48, app.get('icon_name'))
        if pm and not pm.isNull():
            il.setPixmap(pm)
        else:
            il.setText(str(app['name'])[0].upper())
            il.setStyleSheet("background-color:" + self.accent + ";color:white;border-radius:10px;font-size:24px;font-weight:bold;")
        head.addWidget(il)
        info = QVBoxLayout(); info.setSpacing(2)
        nm = QLabel(app['name'])
        nm.setStyleSheet("color:" + self.accent + ";font-size:18px;font-weight:bold;")
        info.addWidget(nm)
        self.status_label = QLabel("Memulai...")
        self.status_label.setStyleSheet("color:#cccccc;font-size:12px;")
        info.addWidget(self.status_label)
        head.addLayout(info); head.addStretch()
        layout.addLayout(head)

        # Progress bar
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(True)
        self.bar.setFixedHeight(22)
        self.bar.setStyleSheet("""
            QProgressBar { background-color:#2a2a2a; border:1px solid #3a3a3a;
                border-radius:6px; text-align:center; color:#fff; font-weight:bold; }
            QProgressBar::chunk { background-color:%s; border-radius:5px; }
        """ % self.accent)
        layout.addWidget(self.bar)

        # Log area (toggled by settings)
        if _SETTINGS.get("show_log", True):
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setStyleSheet("""
                QPlainTextEdit { background-color:#111; color:#aaffaa;
                    border:1px solid #333; border-radius:6px;
                    font-family:monospace; font-size:10px; padding:6px; }
            """)
            self.log.setMaximumBlockCount(500)
            layout.addWidget(self.log, 1)

        # Buttons
        btns = QHBoxLayout(); btns.addStretch()
        self.close_btn = QPushButton("Tutup")
        self.close_btn.setEnabled(False)
        self.close_btn.setStyleSheet("""
            QPushButton { background-color:%s; color:white; border:none;
                border-radius:6px; padding:8px 22px; font-weight:bold; }
            QPushButton:hover { background-color:%s; }
            QPushButton:disabled { background-color:#444; color:#888; }
        """ % (self.accent, hover()))
        self.close_btn.clicked.connect(self.accept)
        btns.addWidget(self.close_btn)
        layout.addLayout(btns)

        # Start process
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.on_output)
        self.proc.finished.connect(self.on_finished)
        self.proc.start(sys.executable, [str(BACKEND), action, app['id']])

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(60)

    def on_output(self):
        raw = bytes(self.proc.readAllStandardOutput()).decode('utf-8', errors='replace')
        for line in raw.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('[STATUS]'):
                msg = line[8:]
                self.status_label.setText(msg)
                low = msg.lower()
                if 'menyiapkan' in low: self.target = max(self.target, 8)
                elif 'mengunduh' in low or 'download' in low: self.target = max(self.target, 30)
                elif 'memasang' in low or 'unpack' in low: self.target = max(self.target, 55)
                elif 'konfigurasi' in low or 'menata' in low: self.target = max(self.target, 82)
                elif 'menyelesaikan' in low or 'trigger' in low: self.target = max(self.target, 95)
                elif 'selesai' in low or 'berhasil' in low: self.target = 100
                elif 'gagal' in low: self.target = 100
            elif line.startswith('[LOG]'):
                if _SETTINGS.get("show_log", True) and hasattr(self, 'log'):
                    self.log.appendPlainText(line[5:])
            elif line.startswith('[DONE]'):
                self.success = True
                self.target = 100
            elif line.startswith('[FAIL]'):
                self.success = False
                self.target = 100

    def animate(self):
        if self.current < self.target:
            step = max(1, (self.target - self.current) // 8)
            self.current = min(self.target, self.current + step)
            self.bar.setValue(self.current)

    def on_finished(self, code, status):
        self.timer.stop()
        self.success = (code == 0)
        self.bar.setValue(100)
        if self.success:
            self.finished_ok = True
            self.status_label.setText("Selesai!")
            self.status_label.setStyleSheet("color:#90ee90;font-size:12px;font-weight:bold;")
        else:
            self.status_label.setText("Gagal. Cek log di bawah.")
            self.status_label.setStyleSheet("color:#ff6666;font-size:12px;font-weight:bold;")
        self.close_btn.setEnabled(True)
        if self.success and _SETTINGS.get("auto_close", True):
            QTimer.singleShot(1200, self.accept)


# ============ SETTINGS DIALOG ============

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FireStore Settings")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet("""
            QDialog { background-color:#1a1a1a; }
            QLabel { color:#eee; font-size:13px; }
            QLabel#h1 { color:%s; font-size:18px; font-weight:bold; }
            QComboBox { background-color:#2a2a2a; color:#fff; border:1px solid #3a3a3a;
                border-radius:6px; padding:8px 12px; font-size:13px; }
            QComboBox::drop-down { border:none; width:24px; }
            QComboBox QAbstractItemView { background-color:#2a2a2a; color:#fff;
                selection-background-color:%s; border:1px solid #3a3a3a; }
            QCheckBox { color:#eee; font-size:13px; spacing:8px; }
            QCheckBox::indicator { width:18px; height:18px; border-radius:4px;
                border:1px solid #3a3a3a; background-color:#2a2a2a; }
            QCheckBox::indicator:checked { background-color:%s; border:1px solid %s; }
            QPushButton#primary { background-color:%s; color:white; border:none;
                border-radius:6px; padding:9px 22px; font-weight:bold; font-size:13px; }
            QPushButton#primary:hover { background-color:%s; }
            QPushButton#cancel { background-color:#3a3a3a; color:#cccccc; border:none;
                border-radius:6px; padding:9px 22px; font-weight:bold; font-size:13px; }
        """ % (accent(), accent(), accent(), accent(), accent(), hover()))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        h = QLabel("Pengaturan FireStore")
        h.setObjectName("h1")
        layout.addWidget(h)

        # Theme
        layout.addWidget(QLabel("Tema Warna"))
        self.theme_combo = QComboBox()
        for key, data in THEMES.items():
            self.theme_combo.addItem(data["name"], key)
        current = _SETTINGS.get("theme", "orange")
        idx = list(THEMES.keys()).index(current) if current in THEMES else 0
        self.theme_combo.setCurrentIndex(idx)
        layout.addWidget(self.theme_combo)

        layout.addSpacing(6)
        layout.addWidget(QLabel("Perilaku"))

        self.auto_close = QCheckBox("Tutup progress dialog otomatis setelah selesai")
        self.auto_close.setChecked(_SETTINGS.get("auto_close", True))
        layout.addWidget(self.auto_close)

        self.show_log = QCheckBox("Tampilkan log detail saat install/update/hapus")
        self.show_log.setChecked(_SETTINGS.get("show_log", True))
        layout.addWidget(self.show_log)

        layout.addStretch()

        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("Batal"); cancel.setObjectName("cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        save = QPushButton("Simpan"); save.setObjectName("primary")
        save.clicked.connect(self.on_save)
        btns.addWidget(save)
        layout.addLayout(btns)

    def on_save(self):
        new = {
            "theme": self.theme_combo.currentData(),
            "auto_close": self.auto_close.isChecked(),
            "show_log": self.show_log.isChecked(),
        }
        save_settings(new)
        self.accept()


# ============ INFO DIALOG ============

class AppInfoDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Info: " + app['name'])
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet("""
            QDialog { background-color:#1a1a1a; }
            QLabel { color:#ddd; font-size:13px; }
            QLabel#title { color:%s; font-size:20px; font-weight:bold; }
            QLabel#k { color:#888; font-size:12px; }
            QLabel#v { color:#eee; font-size:13px; }
            QPushButton { background-color:%s; color:white; border:none;
                border-radius:6px; padding:8px 22px; font-weight:bold; }
            QPushButton:hover { background-color:%s; }
        """ % (accent(), accent(), hover()))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        head = QHBoxLayout()
        il = QLabel(); il.setFixedSize(64, 64); il.setAlignment(Qt.AlignCenter)
        pm = get_icon_pixmap(app['id'], 56, app.get('icon_name'))
        if pm and not pm.isNull():
            il.setPixmap(pm)
        else:
            il.setText(str(app['name'])[0].upper())
            il.setStyleSheet("background-color:" + accent() + ";color:white;border-radius:10px;font-size:28px;font-weight:bold;")
        head.addWidget(il)
        t = QLabel(app['name']); t.setObjectName("title")
        head.addWidget(t); head.addStretch()
        layout.addLayout(head)

        desc = app.get('description', '') or '(tidak ada deskripsi)'
        d = QLabel(desc); d.setWordWrap(True); d.setStyleSheet("color:#bbb;font-size:12px;")
        layout.addWidget(d)

        rows = [
            ("Kategori", app.get('category', 'Lainnya')),
            ("Tipe", (app.get('type', 'deb') or 'deb').upper()),
            ("ID", app['id']),
            ("Status", "Terinstall di sistem" if is_installed_system(app['id']) else "Belum terinstall"),
        ]
        info = get_install_info(app['id'])
        if info:
            rows.append(("Sumber", "FireStore"))
            rows.append(("Diinstall pada", info.get('installed_at', '-')))
        else:
            rows.append(("Sumber", "Sistem (bukan via FireStore)"))

        for k, v in rows:
            r = QHBoxLayout()
            kl = QLabel(k); kl.setObjectName("k"); kl.setFixedWidth(120)
            vl = QLabel(str(v)); vl.setObjectName("v"); vl.setWordWrap(True)
            r.addWidget(kl); r.addWidget(vl, 1)
            layout.addLayout(r)

        layout.addStretch()
        bl = QHBoxLayout(); bl.addStretch()
        ok = QPushButton("Tutup"); ok.clicked.connect(self.accept)
        bl.addWidget(ok)
        layout.addLayout(bl)


# ============ SHARED ACTIONS ============

def run_action(parent, action, app, on_done=None):
    dlg = ProgressDialog(action, app, parent)
    dlg.exec()
    refresh_system_installed()
    if on_done:
        on_done(dlg.finished_ok)
    return dlg.finished_ok


def launch_app(app_id):
    proc = QProcess()
    proc.setProgram(sys.executable)
    proc.setArguments([str(BACKEND), 'launch', app_id])
    proc.startDetached()


# ============ APP WIDGET ============

class AppWidget(QWidget):
    def __init__(self, app, owner, parent=None):
        super().__init__(parent)
        self.app = app
        self.owner = owner
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(14)

        il = QLabel(); il.setFixedSize(44, 44); il.setAlignment(Qt.AlignCenter)
        pm = get_icon_pixmap(app['id'], 40, app.get('icon_name'))
        if pm and not pm.isNull():
            il.setPixmap(pm)
        else:
            il.setText(str(app.get('name', '?'))[0].upper())
            il.setStyleSheet("QLabel { background-color:#444; color:#FF6B00; border:1px solid #555; border-radius:8px; font-size:20px; font-weight:bold; }")
        layout.addWidget(il)

        info = QVBoxLayout(); info.setSpacing(2); info.setContentsMargins(0, 0, 0, 0)
        nm = QLabel(str(app.get('name', app.get('id', 'Unknown')))[:60])
        nm.setStyleSheet("color:" + accent() + ";font-size:14px;font-weight:bold;background:transparent;")
        info.addWidget(nm)
        ds = QLabel((app.get('description', '') or '')[:75])
        ds.setStyleSheet("color:#cccccc;font-size:11px;background:transparent;")
        info.addWidget(ds)
        ct = QLabel(str(app.get('category', 'Lainnya')))
        ct.setStyleSheet("color:#888888;font-size:10px;background:transparent;")
        info.addWidget(ct)
        layout.addLayout(info, 1)

        self.primary_btn = QPushButton()
        self.primary_btn.setFixedSize(96, 34)
        self.primary_btn.setCursor(Qt.PointingHandCursor)
        self.primary_btn.clicked.connect(self.on_primary)
        layout.addWidget(self.primary_btn)

        self.menu_btn = QPushButton("⋯")
        self.menu_btn.setFixedSize(34, 34)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setStyleSheet("""
            QPushButton { background-color:#3a3a3a; color:#ddd; border:none;
                border-radius:6px; font-size:16px; font-weight:bold; }
            QPushButton:hover { background-color:#4a4a4a; color:white; }
        """)
        self.menu_btn.clicked.connect(self.show_menu)
        layout.addWidget(self.menu_btn)

        self.refresh_state()

    def refresh_state(self):
        installed_sys = is_installed_system(self.app['id'])
        installed_fs = self.app['id'] in load_installed()
        if installed_sys:
            self.primary_btn.setText(t("open"))
            self.primary_btn.setStyleSheet("""
                QPushButton { background-color:%s; color:white; border:none;
                    border-radius:6px; font-weight:bold; font-size:12px; }
                QPushButton:hover { background-color:%s; }
            """ % (accent(), hover()))
            self.primary_btn.setEnabled(True)
        else:
            self.primary_btn.setText(t("install"))
            self.primary_btn.setStyleSheet("""
                QPushButton { background-color:%s; color:white; border:none;
                    border-radius:6px; font-weight:bold; font-size:12px; }
                QPushButton:hover { background-color:%s; }
            """ % (accent(), hover()))
            self.primary_btn.setEnabled(True)

    def on_primary(self):
        if is_installed_system(self.app['id']):
            launch_app(self.app['id'])
        else:
            self.owner.install_app_flow(self.app)

    def contextMenuEvent(self, event):
        self.show_menu()

    def show_menu(self):
        app = self.app
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color:#2a2a2a; color:#eee; border:1px solid #3a3a3a;
                border-radius:6px; padding:6px; }
            QMenu::item { padding:8px 24px 8px 14px; border-radius:4px; font-size:12px; }
            QMenu::item:selected { background-color:%s; color:white; }
            QMenu::separator { height:1px; background:#3a3a3a; margin:4px 8px; }
        """ % accent())

        installed_sys = is_installed_system(app['id'])
        installed_fs = app['id'] in load_installed()

        if installed_sys:
            a = QAction(t("open"), menu); a.triggered.connect(lambda: launch_app(app['id']))
            menu.addAction(a)
            a = QAction(t("update"), menu); a.triggered.connect(lambda: self.owner.update_app_flow(app))
            menu.addAction(a)
            menu.addSeparator()
        else:
            a = QAction(t("install"), menu); a.triggered.connect(lambda: self.owner.install_app_flow(app))
            menu.addAction(a)
            menu.addSeparator()

        if installed_fs:
            a = QAction(t("uninstall"), menu); a.triggered.connect(lambda: self.owner.uninstall_app_flow(app))
            menu.addAction(a)

        a = QAction(t("info"), menu); a.triggered.connect(lambda: AppInfoDialog(app, self).exec())
        menu.addAction(a)

        menu.exec(self.mapToGlobal(self.rect().bottomRight()))


# ============ FEATURED CARD ============

class FeaturedCard(QFrame):
    def __init__(self, app, owner, parent=None):
        super().__init__(parent)
        self.app = app
        self.owner = owner
        self.setObjectName("FeaturedCard")
        self.setFixedSize(150, 170)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setStyleSheet("""
            QFrame#FeaturedCard { background-color:#2a2a2a; border:2px solid #3a3a3a; border-radius:12px; }
            QFrame#FeaturedCard:hover { border:2px solid %s; background-color:#333333; }
        """ % accent())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        il = QLabel(); il.setFixedSize(64, 64); il.setAlignment(Qt.AlignCenter)
        il.setStyleSheet("background:transparent;border:none;")
        pm = get_icon_pixmap(app['id'], 56, app.get('icon_name'))
        if pm and not pm.isNull():
            il.setPixmap(pm)
        else:
            il.setText(str(app['name'])[0].upper())
            il.setStyleSheet("QLabel { background-color:" + accent() + ";color:white;border-radius:10px;font-size:28px;font-weight:bold; }")
        hl = QHBoxLayout(); hl.addStretch(); hl.addWidget(il); hl.addStretch()
        layout.addLayout(hl)

        nm = QLabel(str(app['name'])[:20])
        nm.setAlignment(Qt.AlignCenter)
        nm.setStyleSheet("color:" + accent() + ";font-size:12px;font-weight:bold;background:transparent;")
        nm.setWordWrap(True)
        layout.addWidget(nm)

        ct = QLabel(str(app.get('category', 'Lainnya')))
        ct.setAlignment(Qt.AlignCenter)
        ct.setStyleSheet("color:#888;font-size:10px;background:transparent;")
        layout.addWidget(ct)

        layout.addStretch()

        self.primary_btn = QPushButton()
        self.primary_btn.setFixedHeight(28)
        self.primary_btn.setCursor(Qt.PointingHandCursor)
        self.primary_btn.clicked.connect(self.on_primary)
        layout.addWidget(self.primary_btn)
        self.refresh_state()

    def refresh_state(self):
        if is_installed_system(self.app['id']):
            self.primary_btn.setText(t("open"))
            self.primary_btn.setStyleSheet("""
                QPushButton { background-color:%s; color:white; border:none;
                    border-radius:6px; font-weight:bold; font-size:11px; }
                QPushButton:hover { background-color:%s; }
            """ % (accent(), hover()))
        else:
            self.primary_btn.setText(t("install"))
            self.primary_btn.setStyleSheet("""
                QPushButton { background-color:%s; color:white; border:none;
                    border-radius:6px; font-weight:bold; font-size:11px; }
                QPushButton:hover { background-color:%s; }
            """ % (accent(), hover()))

    def on_primary(self):
        if is_installed_system(self.app['id']):
            launch_app(self.app['id'])
        else:
            self.owner.install_app_flow(self.app)

    def contextMenuEvent(self, event):
        self.owner.show_app_menu(self.app, self)


# ============ MAIN WINDOW ============

class FireStore(QMainWindow):
    def __init__(self):
        super().__init__()
        load_settings()
        self.setWindowTitle("FireStore v1.0")
        self.setGeometry(100, 100, 1100, 720)
        _logo = _find_logo_path()
        if _logo:
            self.setWindowIcon(QIcon(_logo))
        self.all_apps = []
        self.system_apps = []
        self.current_category = "Semua"
        self.current_search = ""
        self._build_ui()
        QTimer.singleShot(50, self.load_data)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.setStyleSheet("background-color:#1a1a1a;")
        main = QHBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # === SIDEBAR ===
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("QFrame { background-color:#222; border:none; border-right:1px solid #333; }")
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(12, 18, 12, 18)
        sb.setSpacing(6)

        logo_row = QHBoxLayout(); logo_row.setSpacing(10)
        logo_pix = None
        for lp in LOGO_CANDIDATES:
            if lp.exists():
                pm = QPixmap(str(lp))
                if not pm.isNull():
                    logo_pix = pm.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    break
        if logo_pix is not None:
            ll = QLabel(); ll.setPixmap(logo_pix); ll.setFixedSize(36, 36)
            ll.setStyleSheet("background:transparent;border:none;")
            logo_row.addWidget(ll)
        ttl = QLabel("FireStore")
        ttl.setStyleSheet("color:" + accent() + ";font-size:22px;font-weight:bold;background:transparent;")
        logo_row.addWidget(ttl); logo_row.addStretch()
        sb.addLayout(logo_row)
        sb.addSpacing(18)

        self.sidebar_buttons = []
        categories = ['Semua', 'FireWine', 'Internet', 'Multimedia', 'Office',
                      'Gaming', 'Development', 'System', 'Network', 'Security',
                      'Installed', 'Lainnya']
        for cat in categories:
            btn = QPushButton(cat)
            btn.setFixedHeight(38)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background-color:transparent; color:#ccc; border:none;
                    border-radius:8px; padding:8px 14px; text-align:left; font-size:13px; }
                QPushButton:hover { background-color:#2a2a2a; color:%s; }
                QPushButton:checked { background-color:%s; color:white; font-weight:bold; }
            """ % (accent(), accent()))
            btn.clicked.connect(lambda checked, c=cat: self.on_category_change(c))
            sb.addWidget(btn)
            self.sidebar_buttons.append(btn)
        for b in self.sidebar_buttons:
            b.setChecked(b.text() == self.current_category)

        sb.addStretch()

        settings_btn = QPushButton(t("settings"))
        settings_btn.setFixedHeight(34)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setStyleSheet("""
            QPushButton { background-color:#2a2a2a; color:#ccc; border:1px solid #3a3a3a;
                border-radius:8px; font-size:12px; font-weight:bold; }
            QPushButton:hover { background-color:#333; color:%s; border:1px solid %s; }
        """ % (accent(), accent()))
        settings_btn.clicked.connect(self.open_settings)
        sb.addWidget(settings_btn)

        ver = QLabel("v1.0")
        ver.setStyleSheet("color:#555;font-size:11px;")
        ver.setAlignment(Qt.AlignCenter)
        sb.addWidget(ver)
        main.addWidget(sidebar)

        # === CONTENT ===
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(12)

        hl = QHBoxLayout()
        self.page_title = QLabel(self.current_category + " Apps" if self.current_category != "Semua" else "Semua Apps")
        self.page_title.setStyleSheet("color:" + accent() + ";font-size:24px;font-weight:bold;")
        hl.addWidget(self.page_title); hl.addStretch()
        self.stats = QLabel("Memuat...")
        self.stats.setStyleSheet("color:#888;font-size:12px;")
        hl.addWidget(self.stats)
        cl.addLayout(hl)

        self.search = QLineEdit()
        self.search.setText(self.current_search)
        self.search.setPlaceholderText(t("search"))
        self.search.setStyleSheet("""
            QLineEdit { background-color:#2a2a2a; color:white; border:1px solid #3a3a3a;
                border-radius:8px; padding:10px 14px; font-size:13px; }
            QLineEdit:focus { border:1px solid %s; }
        """ % accent())
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.apply_search)
        self.search.textChanged.connect(lambda: self.search_timer.start(400))
        cl.addWidget(self.search)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color:transparent; border:none; outline:none; }
            QListWidget::item { background-color:#2a2a2a; border:1px solid #3a3a3a;
                border-radius:8px; margin:3px 0; padding:0; }
            QListWidget::item:hover { border:1px solid %s; background-color:#2f2f2f; }
            QScrollBar:vertical { background:#2a2a2a; width:14px; border-radius:7px; margin:0; }
            QScrollBar::handle:vertical { background:%s; border-radius:7px; min-height:40px; }
            QScrollBar::handle:vertical:hover { background:%s; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
        """ % (accent(), accent(), hover()))
        self.list_widget.setSpacing(2)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        cl.addWidget(self.list_widget)
        main.addWidget(content)

    def rebuild(self):
        self._build_ui()
        QTimer.singleShot(30, lambda: self.load_apps(self.current_category, self.current_search))

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.rebuild()

    def load_data(self):
        refresh_system_installed()
        data = load_cache()
        self.all_apps = data.get('apps', [])
        _build_icon_lookup(self.all_apps)
        self.system_apps = load_system_apps()
        self.stats.setText(t("available", len(self.all_apps)))
        QTimer.singleShot(50, lambda: self.load_apps(self.current_category, self.current_search))

    # === ACTION FLOWS ===

    def install_app_flow(self, app):
        run_action(self, 'install', app, on_done=lambda ok: self.after_change(ok))
        if is_installed_system(app['id']):
            launch_app(app['id'])

    def uninstall_app_flow(self, app):
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Konfirmasi Hapus")
        confirm.setText("Hapus " + app['name'] + "?")
        confirm.setInformativeText("App akan dihapus dari sistem.")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setDefaultButton(QMessageBox.No)
        confirm.setStyleSheet("""
            QMessageBox { background-color:#1a1a1a; color:#eee; }
            QLabel { color:#eee; font-size:13px; }
            QPushButton { background-color:#3a3a3a; color:#eee; border:none;
                border-radius:6px; padding:6px 18px; min-width:70px; }
            QPushButton:hover { background-color:%s; color:white; }
        """ % accent())
        if confirm.exec() != QMessageBox.Yes:
            return
        run_action(self, 'uninstall', app, on_done=lambda ok: self.after_change(ok))

    def update_app_flow(self, app):
        run_action(self, 'update', app, on_done=lambda ok: self.after_change(ok))

    def after_change(self, ok):
        refresh_system_installed()
        QTimer.singleShot(200, lambda: self.load_apps(self.current_category, self.current_search))

    def show_app_menu(self, app, widget):
        installed_sys = is_installed_system(app['id'])
        installed_fs = app['id'] in load_installed()
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color:#2a2a2a; color:#eee; border:1px solid #3a3a3a;
                border-radius:6px; padding:6px; }
            QMenu::item { padding:8px 24px 8px 14px; border-radius:4px; font-size:12px; }
            QMenu::item:selected { background-color:%s; color:white; }
            QMenu::separator { height:1px; background:#3a3a3a; margin:4px 8px; }
        """ % accent())
        if installed_sys:
            a = QAction(t("open"), menu); a.triggered.connect(lambda: launch_app(app['id'])); menu.addAction(a)
            a = QAction(t("update"), menu); a.triggered.connect(lambda: self.update_app_flow(app)); menu.addAction(a)
            menu.addSeparator()
        else:
            a = QAction(t("install"), menu); a.triggered.connect(lambda: self.install_app_flow(app)); menu.addAction(a)
            menu.addSeparator()
        if installed_fs:
            a = QAction(t("uninstall"), menu); a.triggered.connect(lambda: self.uninstall_app_flow(app)); menu.addAction(a)
        a = QAction(t("info"), menu); a.triggered.connect(lambda: AppInfoDialog(app, self).exec()); menu.addAction(a)
        menu.exec(widget.mapToGlobal(widget.rect().bottomRight()))

    # === LIST BUILD ===

    def load_apps(self, category="Semua", search=""):
        self.list_widget.clear()
        if not self.all_apps:
            self.stats.setText("0 app")
            return
        installed_fs = set(load_installed())
        sl = search.lower()
        filtered = []
        searching = bool(sl)
        seen_ids = set()
        for app in self.all_apps:
            if app['id'] in seen_ids:
                continue
            if category == "Installed":
                if app['id'] not in installed_fs:
                    continue
            elif category != "Semua":
                if category_for(app) != category:
                    continue
            if sl and sl not in app['name'].lower() and sl not in app.get('description', '').lower():
                continue
            filtered.append(app)
            seen_ids.add(app['id'])

        # Search tambahan: system command dari apt-cache
        if searching:
            for app in self.system_apps:
                if app['id'] in seen_ids:
                    continue
                if sl not in app['name'].lower() and sl not in (app.get('description') or '').lower():
                    continue
                filtered.append(app)
                seen_ids.add(app['id'])

        filtered.sort(key=lambda a: (a.get('name') or a['id']).lower())
        if searching:
            filtered = filtered[:300]
        else:
            filtered = filtered[:200]

        if category == "Semua" and not search:
            featured = []
            for fid in FEATURED_APPS:
                for a in self.all_apps:
                    if a['id'] == fid:
                        featured.append(a); break
            if featured:
                ti = QListWidgetItem(); ti.setSizeHint(QSize(0, 40))
                tw = QLabel(t("featured"))
                tw.setStyleSheet("color:" + accent() + ";font-size:17px;font-weight:bold;padding:10px 0;background:transparent;")
                self.list_widget.addItem(ti); self.list_widget.setItemWidget(ti, tw)

                fi = QListWidgetItem(); fi.setSizeHint(QSize(0, 220))
                fw = QWidget(); fw.setStyleSheet("background-color:#1a1a1a;border:none;")
                wl = QVBoxLayout(fw); wl.setContentsMargins(0, 0, 0, 0)
                fs = QScrollArea(); fs.setWidgetResizable(True)
                fs.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                fs.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                fs.setFixedHeight(200)
                fs.setStyleSheet("""
                    QScrollArea { border:none; background:transparent; }
                    QScrollBar:horizontal { background:#2a2a2a; height:8px; border-radius:4px; }
                    QScrollBar::handle:horizontal { background:%s; border-radius:4px; min-width:40px; }
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }
                """ % accent())
                inner = QWidget(); inner.setStyleSheet("background:transparent;")
                fl = QHBoxLayout(inner); fl.setContentsMargins(0, 10, 0, 10); fl.setSpacing(14)
                for a in featured[:15]:
                    fl.addWidget(FeaturedCard(a, self))
                fl.addStretch()
                fs.setWidget(inner); wl.addWidget(fs)
                self.list_widget.addItem(fi); self.list_widget.setItemWidget(fi, fw)

                ai = QListWidgetItem(); ai.setSizeHint(QSize(0, 40))
                aw = QLabel(t("all_apps"))
                aw.setStyleSheet("color:" + accent() + ";font-size:17px;font-weight:bold;padding:10px 0;background:transparent;")
                self.list_widget.addItem(ai); self.list_widget.setItemWidget(ai, aw)

        for app in filtered:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 64))
            w = AppWidget(app, self)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, w)
        if not filtered and not (category == "Semua" and not search):
            empty_item = QListWidgetItem()
            empty_item.setSizeHint(QSize(0, 100))
            empty_label = QLabel("Tidak ada aplikasi di kategori ini.")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color:#666;font-size:14px;padding:40px 0;background:transparent;")
            self.list_widget.addItem(empty_item)
            self.list_widget.setItemWidget(empty_item, empty_label)
        self.stats.setText(t("count", len(filtered)))

    def on_category_change(self, category):
        self.current_category = category
        self.page_title.setText((category + " Apps") if category != "Semua" else "Semua Apps")
        for b in self.sidebar_buttons:
            b.setChecked(b.text() == category)
        self.load_apps(category, self.current_search)

    def apply_search(self):
        self.current_search = self.search.text()
        self.load_apps(self.current_category, self.current_search)


def main():
    app = QApplication(sys.argv)
    QIcon.setThemeSearchPaths([
        "/usr/share/icons/Papirus",
        "/usr/share/icons/hicolor",
        "/usr/share/icons/Adwaita",
        "/usr/share/icons/breeze",
        "/usr/share/icons",
        str(Path.home() / ".local/share/icons"),
        str(Path.home() / ".icons"),
    ])
    for theme_name in ("Papirus", "Papirus-Dark", "hicolor", "Adwaita", "breeze"):
        QIcon.setThemeName(theme_name)
        if not QIcon.fromTheme("firefox").isNull():
            break
    window = FireStore()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
