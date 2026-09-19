#!/usr/bin/env python3
"""Build pkg_id -> icon_file mapping"""

import configparser
import json
import shutil
from pathlib import Path

HOME = Path.home()
FIRESTORE = HOME / "FireStore"
ICONS_OUT = FIRESTORE / "metadata" / "icons"
CACHE_FILE = FIRESTORE / "metadata" / "apt-cache.json"
MAP_FILE = FIRESTORE / "metadata" / "icon-map.json"
DPKG_INFO = Path("/var/lib/dpkg/info")

THEMES = [
    Path("/usr/share/icons/Papirus"),
    Path("/usr/share/icons/Papirus-Dark"),
    Path("/usr/share/icons/hicolor"),
    Path("/usr/share/icons/Adwaita"),
    Path("/usr/share/icons/breeze"),
    Path("/usr/share/icons"),
    HOME / ".local/share/icons",
    HOME / ".icons",
]
SIZES = ["128x128", "96x96", "64x64", "48x48", "256x256", "scalable"]


def find_icon(name):
    if not name:
        return None
    if name.endswith(('.png', '.svg', '.xpm')):
        name = name.rsplit('.', 1)[0]
    if name.startswith('/'):
        p = Path(name)
        return p if p.exists() else None
    for theme in THEMES:
        if not theme.exists():
            continue
        for size in SIZES:
            for sub in ('apps', ''):
                base = theme / size / sub if sub else theme / size
                for ext in ('.png', '.svg', '.xpm'):
                    p = base / (name + ext)
                    if p.exists():
                        return p
    return None


def desktop_icon(path):
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        cp.read(path, encoding='utf-8')
    except Exception:
        return None
    if not cp.has_section("Desktop Entry"):
        return None
    if cp["Desktop Entry"].get("Type") != "Application":
        return None
    return cp["Desktop Entry"].get("Icon", "")


def main():
    print("Scan /var/lib/dpkg/info/*.list ...")
    pkg_desktops = {}
    for lf in DPKG_INFO.glob("*.list"):
        pkg = lf.stem
        if ':' in pkg:
            pkg = pkg.split(':', 1)[0]
        try:
            text = lf.read_text(errors='ignore')
        except Exception:
            continue
        for line in text.splitlines():
            if (line.startswith('/usr/share/applications/')
                    or line.startswith('/usr/local/share/applications/')) \
                    and line.endswith('.desktop'):
                pkg_desktops.setdefault(pkg, []).append(line)
    print("Paket punya desktop:", len(pkg_desktops))

    if not CACHE_FILE.exists():
        print("Cache tidak ada!")
        return
    with open(CACHE_FILE) as f:
        cache = json.load(f)
    pkg_ids = [a['id'] for a in cache.get('apps', []) if a.get('type', 'deb') == 'deb']
    print("Total pkg di cache:", len(pkg_ids))

    mapping = {}
    copied = 0
    missing = []

    for pkg_id in pkg_ids:
        # 1. langsung icons/{pkg_id}.png ?
        for ext in ('.png', '.svg', '.xpm'):
            p = ICONS_OUT / (pkg_id + ext)
            if p.exists():
                mapping[pkg_id] = p.name
                break
        if pkg_id in mapping:
            continue

        desktops = pkg_desktops.get(pkg_id, [])
        if not desktops:
            missing.append(pkg_id)
            continue

        # 2. desktop stem ada di icons/ ?
        found = False
        for dpath in desktops:
            stem = Path(dpath).stem
            for ext in ('.png', '.svg', '.xpm'):
                p = ICONS_OUT / (stem + ext)
                if p.exists():
                    mapping[pkg_id] = p.name
                    found = True
                    break
            if found:
                break
        if found:
            continue

        # 3. resolve Icon= dari desktop
        for dpath in desktops:
            icon_name = desktop_icon(dpath)
            src = find_icon(icon_name)
            if not src:
                continue
            dest = ICONS_OUT / (pkg_id + src.suffix)
            try:
                if not dest.exists():
                    shutil.copy2(src, dest)
                    copied += 1
                mapping[pkg_id] = dest.name
                found = True
                break
            except Exception:
                continue
        if not found:
            missing.append(pkg_id)

    with open(MAP_FILE, 'w') as f:
        json.dump(mapping, f, indent=2, sort_keys=True)

    print()
    print("Mapping tersimpan:", MAP_FILE)
    print("Total mapping:", len(mapping))
    print("Copy baru dari theme:", copied)
    print("Missing (beneran gak punya icon):", len(missing))
    print("Contoh missing:", ", ".join(missing[:15]))


if __name__ == '__main__':
    main()
