#!/usr/bin/env python3
"""FireWork OS - Hardware Driver Apply v2 (smart)"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DETECT_SCRIPT = SCRIPT_DIR / "hardware-detect.py"
HW_JSON = Path("/tmp/firework-hardware.json")


def run(cmd, capture=False, timeout=30):
    try:
        if capture:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return r.returncode, r.stdout, r.stderr
        return subprocess.run(cmd, timeout=timeout).returncode, "", ""
    except Exception as e:
        return 1, "", str(e)


def ensure_root():
    if os.geteuid() != 0:
        print("ERROR: butuh root. Pakai: sudo python3 " + sys.argv[0], file=sys.stderr)
        sys.exit(1)


def detect():
    print("Detecting hardware...")
    rc, out, err = run(["python3", str(DETECT_SCRIPT)], capture=True, timeout=60)
    print(out)
    if not HW_JSON.exists():
        print("ERROR: detect gagal", file=sys.stderr)
        sys.exit(1)
    return json.loads(HW_JSON.read_text())


def get_installed():
    installed = set()
    rc, out, _ = run(["dpkg-query", "-W", "-f=${Package} ${Status}\n"],
                     capture=True, timeout=15)
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[1:4] == ["install", "ok", "installed"]:
            installed.add(parts[0])
    return installed


def install_pkgs(pkgs, dry_run=False):
    if not pkgs:
        print("Gak ada paket yang perlu diinstall.")
        return True
    cmd = ["pkexec", "env", "DEBIAN_FRONTEND=noninteractive",
           "apt-get", "install", "-y", "--no-install-recommends"] + sorted(pkgs)
    print("Command:")
    print(" ", " ".join(cmd))
    print()
    if dry_run:
        print("[DRY-RUN] Gak dieksekusi.")
        return True
    rc, out, err = run(cmd, timeout=900)
    if rc != 0:
        print("GAGAL:", err[-800:])
        return False
    print("✅ Berhasil install.")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--include-optional", action="store_true",
                        help="Install paket optional (printer dll)")
    parser.add_argument("--skip-confirm", action="store_true",
                        help="Skip driver proprietary")
    args = parser.parse_args()

    ensure_root()
    hw = detect()
    rec = hw["recommendations"]
    installed = get_installed()

    # Filter yang belum keinstall
    need_safe = [p for p in rec["safe"] if p not in installed]
    need_optional = [p for p in rec["optional"] if p not in installed]
    need_confirm = [p for p in rec["needs_confirm"] if p not in installed]
    skip = rec["skip"]

    print()
    print("=" * 60)
    print("HARDWARE DRIVER PLAN")
    print("=" * 60)
    if need_safe:
        print(f"✅ Safe ({len(need_safe)}):")
        for p in need_safe:
            print(f"   + {p}")
    if need_optional:
        print(f"⚠ Optional ({len(need_optional)}) — printer, dll:")
        for p in need_optional:
            print(f"   + {p}")
    if need_confirm:
        print(f"🔒 Butuh konfirmasi ({len(need_confirm)}):")
        for p in need_confirm:
            print(f"   ? {p}")
    if skip:
        print(f"⏭ Skip ({len(skip)}): {', '.join(skip)}")
    if not (need_safe or need_optional or need_confirm):
        print("✅ Semua driver udah keinstall. Gak ada yang perlu diinstall.")
        return

    # Tanya optional
    if need_optional and not args.include_optional:
        print()
        ans = input(f"Install paket optional ({len(need_optional)} paket)? [y/N] ").strip().lower()
        if ans == "y":
            need_safe.extend(need_optional)
        else:
            print(f"   → Skip {len(need_optional)} paket optional")

    # Tanya proprietary
    if need_confirm and not args.skip_confirm:
        print()
        print("Driver proprietary (NVIDIA) — bisa gagal boot kalau salah versi.")
        ans = input("Install? [y/N] ").strip().lower()
        if ans == "y":
            need_safe.extend(need_confirm)
        else:
            print("   → Skip driver proprietary")

    if not need_safe:
        print("Gak ada yang diinstall. Selesai.")
        return

    print()
    print(f"Total: {len(need_safe)} paket")
    if not args.yes and not args.dry_run:
        ans = input("Lanjut apply? [y/N] ").strip().lower()
        if ans != "y":
            print("Dibatalkan.")
            return

    ok = install_pkgs(need_safe, args.dry_run)
    if ok and not args.dry_run:
        print()
        print("⚠ Beberapa driver (kernel modules) butuh REBOOT.")
        print("   Reboot sekarang? [y/N] ", end="")
        try:
            if input().strip().lower() == "y":
                run(["reboot"])
        except EOFError:
            pass


if __name__ == "__main__":
    main()
