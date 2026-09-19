#!/usr/bin/env python3
"""FireWork: Hide apps dari menu KDE (FireWay + FireWine + Discover)"""

import configparser
import shutil
import subprocess
from pathlib import Path

HOME = Path.home()
SYSTEM_DIRS = [Path("/usr/share/applications"), Path("/usr/local/share/applications")]
USER_DIR = HOME / ".local/share/applications"
BACKUP_DIR = HOME / ".local/share/applications-hide-backup"
LOG_FILE = BACKUP_DIR / "LOG.txt"

# === HIDE LIST ===
HIDE = [
    # --- FireWay: semua waydroid ---
    "waydroid.app.install.desktop",
    "Waydroid.desktop",
    "waydroid.market.desktop",
    "waydroid.com.android.calculator2.desktop",
    "waydroid.com.android.contacts.desktop",
    "waydroid.com.android.deskclock.desktop",
    "waydroid.com.android.documentsui.desktop",
    "waydroid.com.android.gallery3d.desktop",
    "waydroid.com.android.settings.desktop",
    "waydroid.org.lineageos.aperture.desktop",
    "waydroid.org.lineageos.eleven.desktop",
    "waydroid.org.lineageos.etar.desktop",
    "waydroid.org.lineageos.jelly.desktop",
    "waydroid.org.lineageos.recorder.desktop",
    "waydroid.ru.zdevs.zarchiver.desktop",
    # --- FireWay: script internal ---
    "fireway-apk.desktop",
    # --- FireWine: semua Wine ---
    "wine.desktop",
    "winetricks.desktop",
    "firewine.desktop",
    "wine-exe.desktop",
    "wine-extension-chm.desktop",
    "wine-extension-crt.desktop",
    "wine-extension-hlp.desktop",
    "wine-extension-msp.desktop",
    "wine-extension-reg.desktop",
    "wine-extension-vbs.desktop",
    # --- Discover ---
    "org.kde.discover.desktop",
    "org.kde.discover.notifier.desktop",
    "org.kde.discover.urlhandler.desktop",
    "org.kde.discover.apt.urlhandler.desktop",
]

# === JANGAN DISENTUH ===
KEEP = {
    "android.desktop",     # shortcut Full UI Android
    "konsole.desktop",     # terminal
    "firestore.desktop",   # app store kita
}


def find_desktop(name):
    for d in SYSTEM_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


def make_override(src_path, name):
    USER_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = USER_DIR / name
    backup = BACKUP_DIR / name

    if not backup.exists():
        shutil.copy2(src_path, backup)

    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    try:
        cp.read(src_path, encoding='utf-8')
    except Exception as e:
        return False, f"parse error: {e}"

    if not cp.has_section("Desktop Entry"):
        return False, "no Desktop Entry section"

    # NoDisplay=true aja (JANGAN Hidden=true, biar MIME association aman)
    cp["Desktop Entry"]["NoDisplay"] = "true"
    cp["Desktop Entry"]["X-FireWork-Override"] = "hidden"

    with open(dest, 'w', encoding='utf-8') as f:
        cp.write(f, space_around_delimiters=False)

    with open(LOG_FILE, 'a') as f:
        f.write(f"{name}\t{src_path}\n")
    return True, str(dest)


def main():
    print("=== FireWork: Hide Apps ===")
    print(f"Override dir: {USER_DIR}")
    print(f"Backup dir:   {BACKUP_DIR}")
    print()

    ok = skip = fail = 0
    hidden_names = []
    for name in HIDE:
        if name in KEEP:
            print(f"  [KEEP] {name}")
            skip += 1
            continue
        src = find_desktop(name)
        if not src:
            print(f"  [SKIP] {name} (gak ada di sistem)")
            skip += 1
            continue
        success, msg = make_override(src, name)
        if success:
            print(f"  [OK]   {name}")
            hidden_names.append(name)
            ok += 1
        else:
            print(f"  [FAIL] {name} - {msg}")
            fail += 1

    print()
    print(f"Hasil: {ok} disembunyiin | {skip} skip | {fail} gagal")

    print()
    print("Refresh menu KDE...")
    for tool in ("kbuildsycoca6", "kbuildsycoca5"):
        try:
            r = subprocess.run([tool, "--noincremental"], capture_output=True, timeout=30)
            if r.returncode == 0:
                print(f"  [OK] {tool}")
                break
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"  [!] {tool}: {e}")

    print()
    print("=== SELESAI! Cek menu KDE ===")
    print()
    print("Yang TETAP muncul:")
    print("  - Android (shortcut Full UI)")
    print("  - FireStore")
    print("  - Konsole")
    print()
    print("Untuk balikin semua: python3 ~/restore-apps.py")


if __name__ == '__main__':
    main()
