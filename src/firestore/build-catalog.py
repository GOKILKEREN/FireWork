#!/usr/bin/env python3
"""Build desktop catalog dari AppStream DEP-11 YAML"""

import gzip
import json
import sys
from collections import Counter
from pathlib import Path

HOME = Path.home()
FIRESTORE = HOME / "FireStore"
OUT = FIRESTORE / "metadata" / "desktop-catalog.json"
YAML_DIR = Path("/var/lib/swcatalog/yaml")

# Priority order penting: subkategori spesifik harus dicek dulu
CATEGORY_MAP = {
    # Internet (subkategori Network)
    'WebBrowser': 'Internet', 'Email': 'Internet', 'InstantMessaging': 'Internet',
    'IRCClient': 'Internet', 'Feed': 'Internet', 'FileTransfer': 'Internet',
    'P2P': 'Internet', 'News': 'Internet', 'Chat': 'Internet',
    'VideoConference': 'Internet',
    # Network
    'Network': 'Network', 'RemoteAccess': 'Network', 'VPN': 'Network',
    'HamRadio': 'Network', 'Dialup': 'Network', 'Telephony': 'Network',
    # Multimedia
    'AudioVideo': 'Multimedia', 'Audio': 'Multimedia', 'Video': 'Multimedia',
    'Player': 'Multimedia', 'Recorder': 'Multimedia', 'TV': 'Multimedia',
    'Graphics': 'Multimedia',
    # Lainnya
    'Development': 'Development', 'Education': 'Education', 'Game': 'Gaming',
    'Office': 'Office', 'Science': 'Education', 'Settings': 'System',
    'System': 'System', 'Utility': 'Lainnya', 'Security': 'Security',
}

# Subkategori yang harus dicek DULU sebelum kategori utama
PRIORITY_CATS = [
    'WebBrowser', 'Email', 'InstantMessaging', 'IRCClient', 'Feed',
    'FileTransfer', 'P2P', 'News', 'Chat', 'VideoConference',
]


def open_maybe_gz(path):
    if path.suffix == '.gz' or path.name.endswith('.yml.gz'):
        return gzip.open(path, 'rt', encoding='utf-8')
    return open(path, encoding='utf-8')


def parse_dep11(path):
    """DEP-11: multi-document YAML. Setiap dokumen = 1 komponen."""
    try:
        import yaml
    except ImportError:
        print("[!] PyYAML tidak ada. Install: sudo apt install python3-yaml")
        sys.exit(1)
    apps = {}
    total = 0
    with open_maybe_gz(path) as f:
        try:
            for doc in yaml.safe_load_all(f):
                if not isinstance(doc, dict):
                    continue
                # Skip header dokument (File: DEP-11)
                if 'File' in doc and 'Type' not in doc:
                    continue
                if doc.get('Type') not in ('desktop-application', 'desktop'):
                    continue
                total += 1
                app_id = doc.get('ID', '')
                if not app_id:
                    continue
                pkg = None
                pkgs = doc.get('Package')
                if isinstance(pkgs, list) and pkgs:
                    pkg = pkgs[0]
                elif isinstance(pkgs, str):
                    pkg = pkgs
                if not pkg:
                    pkg = app_id.split('.')[0].lower()
                name = doc.get('Name', {})
                if isinstance(name, dict):
                    name = name.get('C') or name.get('en') or next(iter(name.values()), pkg)
                elif not isinstance(name, str):
                    name = pkg
                summary = doc.get('Summary', {})
                if isinstance(summary, dict):
                    summary = summary.get('C') or summary.get('en') or next(iter(summary.values()), '')
                elif not isinstance(summary, str):
                    summary = ''
                # Icon
                icon = doc.get('Icon', {})
                icon_name = None
                if isinstance(icon, dict):
                    icon_name = icon.get('stock') or icon.get('cached')
                elif isinstance(icon, list):
                    for entry in icon:
                        if isinstance(entry, dict):
                            icon_name = entry.get('stock') or entry.get('cached')
                        elif isinstance(entry, str):
                            icon_name = entry
                        if icon_name:
                            break
                elif isinstance(icon, str):
                    icon_name = icon
                if isinstance(icon_name, str) and icon_name.endswith(('.png', '.svg', '.xpm')):
                    icon_name = icon_name.rsplit('.', 1)[0]
                if not isinstance(icon_name, str):
                    icon_name = None
                # Kategori
                category = 'Lainnya'
                cats = doc.get('Categories') or []
                if isinstance(cats, list):
                    # Pass 1: prioritas subkategori Internet
                    for c in cats:
                        if c in PRIORITY_CATS:
                            category = CATEGORY_MAP[c]
                            break
                    # Pass 2: kalau belum ke-set, cek kategori utama
                    if category == 'Lainnya':
                        for c in cats:
                            if c in CATEGORY_MAP:
                                category = CATEGORY_MAP[c]
                                break
                apps[pkg] = {
                    "id": pkg,
                    "appstream_id": app_id,
                    "name": str(name)[:80],
                    "description": str(summary)[:200],
                    "category": category,
                    "icon_name": icon_name or pkg,
                    "type": "deb",
                }
        except yaml.YAMLError as e:
            print(f"  [!] YAML error di {path.name}: {str(e)[:120]}")
    return apps, total


def main():
    print("=== FireStore Catalog Builder ===")
    print()
    if not YAML_DIR.exists():
        print(f"GAGAL: {YAML_DIR} tidak ada")
        sys.exit(1)

    yaml_files = sorted(YAML_DIR.glob("*.yml*"))
    print(f"Ditemukan {len(yaml_files)} file YAML:")
    for y in yaml_files:
        print(f"  {y.name}")
    print()

    all_apps = {}
    for yf in yaml_files:
        apps, total = parse_dep11(yf)
        print(f"  {yf.name}: {total} komponen -> {len(apps)} unique app")
        for k, v in apps.items():
            if k not in all_apps:
                all_apps[k] = v

    if not all_apps:
        print("\nGAGAL: tidak ada app yang berhasil diparsing")
        sys.exit(1)

    apps_list = sorted(all_apps.values(), key=lambda a: a['name'].lower())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(apps_list, f, indent=2, ensure_ascii=False)

    print()
    print(f"[OK] Total: {len(apps_list)} app")
    print(f"[OK] Output: {OUT}")
    cats = Counter(a['category'] for a in apps_list)
    print("\nKategori:")
    for c, n in cats.most_common():
        print(f"  {c}: {n}")
    print("\nSample 12:")
    for a in apps_list[:12]:
        print(f"  {a['id']:<28} {a['name'][:35]:<37} {a['category']}")


if __name__ == '__main__':
    main()
