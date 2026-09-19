#!/usr/bin/env python3
"""FireStore Backend v3 - install/uninstall/update/launch"""

import configparser
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

FIRESTORE_DIR = Path.home() / "FireStore"
CACHE_FILE = FIRESTORE_DIR / "metadata" / "apt-cache.json"
CATALOG_FILE = FIRESTORE_DIR / "metadata" / "desktop-catalog.json"
INSTALLED_FILE = FIRESTORE_DIR / "metadata" / "installed.json"
META_FILE = FIRESTORE_DIR / "metadata" / "firestore-installed.json"
APPS_DIR = FIRESTORE_DIR / "apps"

FIREWINE_APPS = [
    {"id": "notepadpp", "name": "Notepad++", "type": "exe", "file": "notepadpp.exe", "url": ""},
    {"id": "winrar", "name": "WinRAR", "type": "exe", "file": "winrar.exe", "url": ""},
    {"id": "aimp", "name": "AIMP", "type": "exe", "file": "aimp.exe", "url": ""},
    {"id": "foobar", "name": "foobar2000", "type": "exe", "file": "foobar.exe", "url": ""},
    {"id": "photoshop", "name": "Photoshop CS6", "type": "exe", "file": "photoshop.exe", "url": ""},
    {"id": "msoffice", "name": "MS Office 2010", "type": "exe", "file": "msoffice.exe", "url": ""},
]


def load_installed():
    if not INSTALLED_FILE.exists():
        return []
    with open(INSTALLED_FILE) as f:
        return json.load(f).get("installed", [])


def save_installed(items):
    INSTALLED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INSTALLED_FILE, 'w') as f:
        json.dump({"installed": sorted(set(items))}, f, indent=2)


def load_meta():
    if not META_FILE.exists():
        return {"apps": {}}
    try:
        with open(META_FILE) as f:
            return json.load(f)
    except Exception:
        return {"apps": {}}


def save_meta(meta):
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(META_FILE, 'w') as f:
        json.dump(meta, f, indent=2)


def add_meta(app_id, source="firestore"):
    meta = load_meta()
    meta.setdefault("apps", {})[app_id] = {
        "installed_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
    }
    save_meta(meta)


def remove_meta(app_id):
    meta = load_meta()
    if app_id in meta.get("apps", {}):
        del meta["apps"][app_id]
        save_meta(meta)


def is_installed_dpkg(pkg_id):
    try:
        r = subprocess.run(['dpkg-query', '-W', '-f=${Status}', pkg_id],
                           capture_output=True, text=True, timeout=3)
        return 'install ok installed' in r.stdout
    except Exception:
        return False


def find_app(app_id):
    # 1. FireWine
    for app in FIREWINE_APPS:
        if app['id'] == app_id:
            return app
    # 2. Desktop catalog (AppStream — 1876 app)
    if CATALOG_FILE.exists():
        try:
            with open(CATALOG_FILE) as f:
                catalog = json.load(f)
            for app in catalog:
                if app.get('id') == app_id:
                    return app
        except Exception:
            pass
    # 3. Fallback ke apt-cache (5000 paket sistem)
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                cache = json.load(f)
            for app in cache.get('apps', []):
                if app.get('id') == app_id:
                    return app
        except Exception:
            pass
    return None


def stream_apt(args, status_msgs):
    print("[STATUS]" + status_msgs['start'], flush=True)
    proc = subprocess.Popen(
        ['pkexec', 'env', 'DEBIAN_FRONTEND=noninteractive', 'apt-get'] + args,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    current = status_msgs['start']
    for raw in proc.stdout:
        line = raw.rstrip()
        if not line:
            continue
        low = line.lower()
        new_status = None
        if any(k in low for k in ('get:', 'butuh ', 'need to get', 'fetch')):
            new_status = status_msgs['download']
        elif any(k in low for k in ('unpacking', 'menyiapkan ')):
            new_status = status_msgs['unpack']
        elif any(k in low for k in ('setting up', 'sedang menata ')):
            new_status = status_msgs['setup']
        elif 'processing trigger' in low:
            new_status = status_msgs['finish']
        if new_status and new_status != current:
            current = new_status
            print("[STATUS]" + new_status, flush=True)
        print("[LOG]" + line, flush=True)
    proc.wait()
    return proc.returncode == 0


def install_app(app_id):
    app = find_app(app_id)
    if not app:
        print("[LOG]App '" + app_id + "' tidak ada di cache!", flush=True)
        print("[FAIL]", flush=True)
        return False

    app_type = app.get('type', 'deb')

    if app_type == 'deb':
        if is_installed_dpkg(app_id):
            installed = load_installed()
            if app_id not in installed:
                installed.append(app_id)
                save_installed(installed)
            add_meta(app_id)
            print("[STATUS]Sudah terinstall!", flush=True)
            print("[DONE]", flush=True)
            return True

        installed = load_installed()
        if app_id not in installed:
            installed.append(app_id)
            save_installed(installed)
        add_meta(app_id)

        ok = stream_apt(
            ['install', '-y', '--no-install-recommends', app_id],
            {
                'start':    'Menyiapkan instalasi...',
                'download': 'Mengunduh paket...',
                'unpack':   'Memasang paket...',
                'setup':    'Mengkonfigurasi...',
                'finish':   'Menyelesaikan...',
            }
        )
        if not ok:
            installed = load_installed()
            if app_id in installed:
                installed.remove(app_id)
                save_installed(installed)
            remove_meta(app_id)
            print("[STATUS]Instalasi gagal!", flush=True)
            print("[FAIL]", flush=True)
            return False
        print("[STATUS]Instalasi selesai!", flush=True)
        print("[DONE]", flush=True)
        return True

    elif app_type == 'exe':
        app_file = APPS_DIR / "exe" / app['file']
        if not app_file.exists() or app_file.stat().st_size == 0:
            print("[FAIL]File .exe tidak ada.", flush=True)
            return False
        r = subprocess.run(['wine', str(app_file)])
        return r.returncode == 0

    return False


def uninstall_app(app_id):
    ok = stream_apt(
        ['remove', '-y', app_id],
        {
            'start':    'Menyiapkan penghapusan...',
            'download': 'Mengunduh...',
            'unpack':   'Menghapus paket...',
            'setup':    'Membersihkan...',
            'finish':   'Menyelesaikan...',
        }
    )
    if ok:
        installed = load_installed()
        if app_id in installed:
            installed.remove(app_id)
            save_installed(installed)
        remove_meta(app_id)
        print("[STATUS]Berhasil dihapus!", flush=True)
        print("[DONE]", flush=True)
    else:
        print("[STATUS]Gagal menghapus!", flush=True)
        print("[FAIL]", flush=True)
    return ok


def update_app(app_id):
    ok = stream_apt(
        ['install', '--only-upgrade', '-y', app_id],
        {
            'start':    'Menyiapkan update...',
            'download': 'Mengunduh update...',
            'unpack':   'Memasang update...',
            'setup':    'Mengkonfigurasi...',
            'finish':   'Menyelesaikan...',
        }
    )
    print("[STATUS]" + ("Update selesai!" if ok else "Update gagal!"), flush=True)
    print("[DONE]" if ok else "[FAIL]", flush=True)
    return ok


def launch_app(app_id):
    candidates = (
        ["/usr/share/applications/" + app_id + ".desktop"] +
        glob.glob("/usr/share/applications/*" + app_id + "*.desktop") +
        ["/usr/local/share/applications/" + app_id + ".desktop"]
    )
    for path in candidates:
        if not os.path.exists(path):
            continue
        cp = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            cp.read(path)
        except Exception:
            continue
        if cp.has_section("Desktop Entry"):
            exec_cmd = cp["Desktop Entry"].get("Exec", "")
            exec_cmd = re.sub(r'%[a-zA-Z]', '', exec_cmd).strip()
            if exec_cmd:
                subprocess.Popen(exec_cmd, shell=True)
                print("[STATUS]Menjalankan " + app_id + "...", flush=True)
                print("[DONE]", flush=True)
                return True
    if shutil.which(app_id):
        subprocess.Popen([app_id])
        print("[STATUS]Menjalankan " + app_id + "...", flush=True)
        print("[DONE]", flush=True)
        return True
    print("[STATUS]Gagal menjalankan app.", flush=True)
    print("[FAIL]", flush=True)
    return False


def main():
    if len(sys.argv) < 3:
        print("Usage: firestore-backend.py <install|uninstall|update|launch> <id>")
        sys.exit(1)
    cmd, app_id = sys.argv[1], sys.argv[2]
    handlers = {
        'install':   install_app,
        'uninstall': uninstall_app,
        'update':    update_app,
        'launch':    launch_app,
    }
    fn = handlers.get(cmd)
    if not fn:
        print("Unknown command: " + cmd)
        sys.exit(2)
    ok = fn(app_id)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
