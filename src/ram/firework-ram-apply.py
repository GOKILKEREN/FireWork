#!/usr/bin/env python3
"""
FireWork OS - RAM Profile Apply
Apply konfigurasi RAM profile dengan backup + rollback.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROFILE_SCRIPT = SCRIPT_DIR / "ram-profile.py"
BACKUP_DIR = Path("/tmp/firework-ram-backup")
SYSCTL_FILE = Path("/etc/sysctl.d/99-firework.conf")
STATE_FILE = Path("/var/lib/firework/ram-state.json")


def run(cmd, check=False, capture=False):
    try:
        if capture:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return r.returncode, r.stdout, r.stderr
        r = subprocess.run(cmd, timeout=30)
        return r.returncode, "", ""
    except Exception as e:
        return 1, "", str(e)


def ensure_root():
    if os.geteuid() != 0:
        print("ERROR: Script ini butuh root.", file=sys.stderr)
        print("Jalankan: sudo python3 " + sys.argv[0], file=sys.stderr)
        sys.exit(1)


def load_profile_json():
    """Panggil ram-profile.py --json, ambil output."""
    # Panggil dengan output ke /tmp unik biar gak konflik ownership
    import tempfile
    tmp_out = Path(tempfile.gettempdir()) / f"firework-ram-{os.getuid()}-{os.getpid()}.json"
    try:
        tmp_out.unlink()
    except Exception:
        pass
    rc, out, err = run(
        ["python3", str(PROFILE_SCRIPT), "--json", "--output", str(tmp_out)],
        capture=True
    )
    if rc != 0:
        print("ERROR: Gagal baca profile:", err, file=sys.stderr)
        sys.exit(1)
    return json.loads(out)


def backup_file(path):
    """Backup file sebelum diubah."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if Path(path).exists():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = BACKUP_DIR / f"{Path(path).name}.{ts}"
        shutil.copy2(path, dest)
        return str(dest)
    return None


def phase1_sysctl(profile, dry_run=False):
    """Phase 1: sysctl (swappiness, vfs_cache_pressure). AMAN."""
    print("=== Phase 1: sysctl (SAFE) ===")
    p = profile["profile"]
    lines = [
        "# FireWork OS - RAM Profile",
        f"# Generated: {datetime.now().isoformat()}",
        f"# Mode: {profile['mode']}",
        f"vm.swappiness = {p['swappiness']}",
        f"vm.vfs_cache_pressure = {p['vfs_cache_pressure']}",
    ]
    content = "\n".join(lines) + "\n"

    print(f"File: {SYSCTL_FILE}")
    print(content)

    if dry_run:
        print("[DRY-RUN] Gak ditulis.\n")
        return True

    # Backup
    if SYSCTL_FILE.exists():
        bk = backup_file(SYSCTL_FILE)
        print(f"Backup: {bk}")

    SYSCTL_FILE.parent.mkdir(parents=True, exist_ok=True)
    SYSCTL_FILE.write_text(content)

    # Apply langsung
    rc, _, err = run(["sysctl", "--system"], capture=True)
    if rc != 0:
        print(f"WARNING sysctl --system: {err}")

    rc, out, _ = run(["sysctl", "vm.swappiness", "vm.vfs_cache_pressure"], capture=True)
    print(out.strip())
    print("✅ Phase 1 selesai\n")
    return True


def phase2_services(profile, dry_run=False):
    """Phase 2: services + baloo. MEDIUM."""
    print("=== Phase 2: services + baloo (MEDIUM) ===")
    p = profile["profile"]

    # Baloo
    if not p["baloo_indexer"]:
        print("Baloo: disable")
        if not dry_run:
            user = os.environ.get("SUDO_USER", "putera")
            # balooctl harus jalan sebagai user
            run(["sudo", "-u", user, "balooctl6", "disable"], capture=True)
            run(["sudo", "-u", user, "balooctl6", "suspend"], capture=True)
    else:
        print("Baloo: enable")
        if not dry_run:
            user = os.environ.get("SUDO_USER", "putera")
            run(["sudo", "-u", user, "balooctl6", "enable"], capture=True)

    # Disabled services
    for svc in p.get("disabled_services", []):
        print(f"Service: disable {svc}")
        if not dry_run:
            run(["systemctl", "disable", "--now", svc], capture=True)

    print("✅ Phase 2 selesai\n")
    return True


def phase3_kde(profile, dry_run=False):
    """Phase 3: KDE config (compositor, animasi). RISKY - butuh logout."""
    print("=== Phase 3: KDE config (RISKY - butuh logout untuk efek penuh) ===")
    p = profile["profile"]
    user = os.environ.get("SUDO_USER")
    if not user:
        print("SKIP: butuh SUDO_USER (jalanin via sudo, bukan root langsung)")
        return False

    home = Path(f"/home/{user}")
    kwinrc = home / ".config" / "kwinrc"
    kdeglobals = home / ".config" / "kdeglobals"

    # Compositor (kwinrc)
    comp = p.get("kde_compositor", "opengl")
    print(f"Compositor: {comp}")
    if comp == "off":
        # Matiin compositor
        run(["sudo", "-u", user, "kwriteconfig6", "--file", "kwinrc",
             "--group", "Compositing", "--key", "Enabled", "false"], capture=True)
    else:
        run(["sudo", "-u", user, "kwriteconfig6", "--file", "kwinrc",
             "--group", "Compositing", "--key", "Enabled", "true"], capture=True)
        run(["sudo", "-u", user, "kwriteconfig6", "--file", "kwinrc",
             "--group", "Compositing", "--key", "Backend", comp], capture=True)

    # Animasi (kdeglobals)
    anim = p.get("kde_animations", "full")
    print(f"Animasi: {anim}")
    if anim == "off":
        run(["sudo", "-u", user, "kwriteconfig6", "--file", "kdeglobals",
             "--group", "KDE", "--key", "AnimationDurationFactor", "0"], capture=True)
    elif anim == "medium":
        run(["sudo", "-u", user, "kwriteconfig6", "--file", "kdeglobals",
             "--group", "KDE", "--key", "AnimationDurationFactor", "0.5"], capture=True)
    else:
        run(["sudo", "-u", user, "kwriteconfig6", "--file", "kdeglobals",
             "--group", "KDE", "--key", "AnimationDurationFactor", "1"], capture=True)

    print("✅ Phase 3 selesai (relogin biar efek penuh)\n")
    return True


def save_state(profile):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "applied_at": datetime.now().isoformat(),
        "mode": profile["mode"],
        "ram_total_gb": profile["ram_total_gb"],
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview aja")
    parser.add_argument("--phase", choices=["1", "2", "3", "all"], default="1",
                        help="Phase mana yang di-apply (default: 1)")
    parser.add_argument("--yes", action="store_true",
                        help="Skip konfirmasi")
    args = parser.parse_args()

    ensure_root()
    profile = load_profile_json()

    print("=" * 50)
    print(f"FireWork RAM Profile Apply")
    print(f"Mode        : {profile['mode']}")
    print(f"RAM Total   : {profile['ram_total_gb']} GB")
    print(f"Phase       : {args.phase}")
    print(f"Dry-run     : {args.dry_run}")
    print("=" * 50)
    print()

    if not args.yes and not args.dry_run:
        ans = input("Lanjut apply? [y/N] ").strip().lower()
        if ans != "y":
            print("Dibatalkan.")
            return

    phases = [args.phase] if args.phase != "all" else ["1", "2", "3"]
    for ph in phases:
        if ph == "1":
            phase1_sysctl(profile, args.dry_run)
        elif ph == "2":
            phase2_services(profile, args.dry_run)
        elif ph == "3":
            phase3_kde(profile, args.dry_run)

    if not args.dry_run:
        save_state(profile)
        print(f"State disimpan: {STATE_FILE}")
        print()
        print(f"Backup tersimpan di: {BACKUP_DIR}")
        print("Kalau mau rollback, tinggal restore file dari backup.")

    print("🔥 DONE")


if __name__ == "__main__":
    main()
