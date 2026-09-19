#!/usr/bin/env python3
"""Index paket yang punya .desktop file = app desktop beneran"""

import configparser
import json
import subprocess
from pathlib import Path

HOME = Path.home()
APPS_DIRS = [
    Path("/usr/share/applications"),
    Path("/usr/local/share/applications"),
    HOME / ".local/share/applications",
]
OUT = HOME / "FireStore" / "metadata" / "desktop-apps.json"


def resolve_pkg(dfile):
    try:
        r = subprocess.run(['dpkg-query', '-S', str(dfile)],
                           capture_output=True, text=True, timeout=2)
        if r.returncode == 0 and ':' in r.stdout:
            pkg = r.stdout.split(':', 1)[0].strip()
            return pkg.split(':', 1)[0]
    except Exception:
        pass
    return None


def parse(dfile):
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        cp.read(dfile, encoding='utf-8')
    except Exception:
        return None
    if not cp.has_section("Desktop Entry"):
        return None
    s = cp["Desktop Entry"]
    if s.get("Type") != "Application":
        return None
    if s.get("NoDisplay", "false").lower() == "true":
        return None
    if s.get("Hidden", "false").lower() == "true":
        return None
    return {
        "name": s.get("Name", dfile.stem),
        "icon": s.get("Icon", ""),
        "categories": s.get("Categories", ""),
    }


def main():
    seen = {}
    total = 0
    for d in APPS_DIRS:
        if not d.exists():
            continue
        for f in d.glob("*.desktop"):
            total += 1
            info = parse(f)
            if not info:
                continue
            pkg = resolve_pkg(f) or f.stem
            if pkg not in seen:
                seen[pkg] = info

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(seen, f, indent=2, sort_keys=True)

    print("Scan:", total, "desktop files")
    print("Paket terdaftar sebagai app desktop:", len(seen))
    print("Output:", OUT)


if __name__ == '__main__':
    main()
