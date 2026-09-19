#!/usr/bin/env python3
"""Sync system packages + installed.json"""

import json
import subprocess
from pathlib import Path

FIRESTORE_DIR = Path.home() / "FireStore"
CACHE_FILE = FIRESTORE_DIR / "metadata" / "apt-cache.json"
INSTALLED_FILE = FIRESTORE_DIR / "metadata" / "installed.json"
SYSTEM_PKG_FILE = FIRESTORE_DIR / "metadata" / "system-packages.json"


def get_installed_packages():
    """Dapetin semua package yang udah keinstall di sistem"""
    result = subprocess.run(
        ['dpkg-query', '-W', '-f=${Package}\n'],
        capture_output=True, text=True
    )
    installed = set()
    for line in result.stdout.split('\n'):
        pkg = line.strip()
        if pkg:
            installed.add(pkg)
    return installed


def load_cache():
    if not CACHE_FILE.exists():
        return []
    with open(CACHE_FILE) as f:
        return json.load(f).get('apps', [])


def load_installed_json():
    """Load installed.json — app yang diinstall via FireStore"""
    if not INSTALLED_FILE.exists():
        return []
    with open(INSTALLED_FILE) as f:
        return json.load(f).get('installed', [])


def save_installed_json(installed):
    INSTALLED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INSTALLED_FILE, 'w') as f:
        json.dump({"installed": installed}, f, indent=2)
    # Chown balik ke user
    try:
        import pwd
        user = pwd.getpwnam('putera')
        import os
        os.chown(INSTALLED_FILE, user.pw_uid, user.pw_gid)
    except:
        pass


def save_system_packages(packages):
    """Simpen daftar package system"""
    SYSTEM_PKG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SYSTEM_PKG_FILE, 'w') as f:
        json.dump({"packages": sorted(list(packages))}, f, indent=2)


def main():
    print("🔍 Sync system packages...")
    
    # 1. Ambil package terinstall di system
    system_installed = get_installed_packages()
    print(f"📦 Total package system: {len(system_installed)}")
    
    # 2. Ambil cache
    cache_apps = load_cache()
    print(f"📦 Cache FireStore: {len(cache_apps)} app")
    
    # 3. Simpen system packages (buat cek "installed" di tab lain)
    save_system_packages(system_installed)
    print(f"✅ system-packages.json: {len(system_installed)} package")
    
    # 4. Update installed.json — TAMBAHIN app yang diinstall via apt (tapi gak di FireStore)
    # HAPUS baris ini kalau mau installed.json cuma app FireStore
    # installed_json = load_installed_json()
    # print(f"📦 installed.json (FireStore): {len(installed_json)} app")
    
    print("✅ Selesai!")


if __name__ == '__main__':
    main()
