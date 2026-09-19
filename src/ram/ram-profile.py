#!/usr/bin/env python3
"""
FireWork OS - RAM Profile Engine
Deteksi RAM, pilih mode, output JSON perubahan yang perlu di-apply.
Dipakai oleh installer V1.0 + bisa dijalankan manual.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROFILES_FILE = SCRIPT_DIR / "ram-profiles.json"
OUTPUT_FILE = Path.home() / ".cache" / "firework" / "ram-profile.json"


def load_profiles():
    if not PROFILES_FILE.exists():
        print(f"ERROR: {PROFILES_FILE} tidak ada!", file=sys.stderr)
        sys.exit(1)
    with open(PROFILES_FILE) as f:
        return json.load(f)


def get_ram_total_gb():
    """Baca /proc/meminfo, return RAM total dalam GB (float)."""
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                kb = int(line.split()[1])
                return round(kb / 1024 / 1024, 2)
    return 0.0


def get_ram_available_gb():
    """RAM available saat ini."""
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                kb = int(line.split()[1])
                return round(kb / 1024 / 1024, 2)
    return 0.0


def zram_for_ram(ram_gb):
    """Aturan ZRAM FireWork:
       < 2 GB  -> 3 GB
       2-4 GB  -> 2 GB
       >= 4 GB -> OFF
    """
    if ram_gb < 2.0:
        return {"enabled": True, "size_gb": 3, "algorithm": "lz4"}
    elif ram_gb < 4.0:
        return {"enabled": True, "size_gb": 2, "algorithm": "lz4"}
    else:
        return {"enabled": False, "size_gb": 0, "algorithm": "lz4"}


def detect_mode(ram_gb, profiles):
    t = profiles["thresholds"]
    if ram_gb <= t["survival_max_gb"]:
        return "survival"
    elif ram_gb <= t["balanced_max_gb"]:
        return "balanced"
    elif ram_gb <= t["comfort_max_gb"]:
        return "comfort"
    else:
        return "performance"


def _read_file(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None


def _get_zram_info():
    zram_dirs = sorted(Path("/sys/block").glob("zram*"))
    if not zram_dirs:
        return {"active": False, "count": 0}
    total_bytes = 0
    algos = set()
    for d in zram_dirs:
        ds = _read_file(d / "disksize")
        if ds and ds.isdigit():
            total_bytes += int(ds)
        ca = _read_file(d / "comp_algorithm")
        if ca:
            for token in ca.split():
                if token.startswith("[") and token.endswith("]"):
                    algos.add(token[1:-1])
    total_gb = round(total_bytes / 1024 / 1024 / 1024, 2) if total_bytes else 0
    return {
        "active": True,
        "count": len(zram_dirs),
        "total_gb": total_gb,
        "size_str": f"{total_gb} GB" if total_gb else "?",
        "algorithms": sorted(algos),
    }


def _get_swap_info():
    text = _read_file("/proc/swaps")
    if not text:
        return []
    lines = text.splitlines()[1:]
    swaps = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 4:
            swaps.append({
                "device": parts[0],
                "type": parts[1],
                "size_kb": int(parts[2]),
                "used_kb": int(parts[3]),
            })
    return swaps


def get_current_state():
    state = {}
    zi = _get_zram_info()
    state["zram_active"] = zi["active"]
    state["zram_size"] = zi.get("size_str", "?")
    state["zram_algo"] = ", ".join(zi.get("algorithms", [])) or "?"
    state["zram_count"] = zi.get("count", 0)
    swaps = _get_swap_info()
    state["swap_devices"] = [s["device"] for s in swaps]
    # Swappiness
    try:
        with open("/proc/sys/vm/swappiness") as f:
            state["swappiness"] = int(f.read().strip())
    except Exception:
        state["swappiness"] = None
    # VFS cache pressure
    try:
        with open("/proc/sys/vm/vfs_cache_pressure") as f:
            state["vfs_cache_pressure"] = int(f.read().strip())
    except Exception:
        state["vfs_cache_pressure"] = None
    # Baloo
    try:
        r = subprocess.run(["balooctl6", "status"], capture_output=True, text=True, timeout=3)
        state["baloo_status"] = "enabled" if "enabled" in r.stdout.lower() else "disabled"
    except Exception:
        try:
            r = subprocess.run(["balooctl", "status"], capture_output=True, text=True, timeout=3)
            state["baloo_status"] = "enabled" if "enabled" in r.stdout.lower() else "disabled"
        except Exception:
            state["baloo_status"] = "unknown"
    return state


def build_output(mode, ram_gb, profiles, include_current=True):
    p = dict(profiles["profiles"][mode])  # copy biar gak mutate
    # Override ZRAM pakai aturan khusus FireWork
    p["zram"] = zram_for_ram(ram_gb)
    out = {
        "ram_total_gb": ram_gb,
        "ram_available_gb": get_ram_available_gb(),
        "mode": mode,
        "profile": p,
        "timestamp": subprocess.run(["date", "-Iseconds"], capture_output=True, text=True).stdout.strip(),
    }
    if include_current:
        out["current_state"] = get_current_state()
    return out


def print_pretty(out):
    p = out["profile"]
    print(f"=== FireWork RAM Profile ===")
    print(f"RAM Total    : {out['ram_total_gb']} GB")
    print(f"RAM Available: {out['ram_available_gb']} GB")
    print(f"Mode         : {out['mode'].upper()} - {p['name']}")
    print(f"Description  : {p['description']}")
    print()
    print("Rekomendasi konfigurasi:")
    z = p["zram"]
    print(f"  ZRAM        : {'ON' if z['enabled'] else 'OFF'} ({z['size_gb']} GB, {z['algorithm']})")
    print(f"  Swappiness  : {p['swappiness']}")
    print(f"  VFS Pressure: {p['vfs_cache_pressure']}")
    print(f"  Compositor  : {p['kde_compositor']}")
    print(f"  Animasi     : {p['kde_animations']}")
    print(f"  Baloo       : {'ON' if p['baloo_indexer'] else 'OFF'}")
    print(f"  Autostart   : {p['autostart_level']}")
    if p["disabled_services"]:
        print(f"  Services off: {', '.join(p['disabled_services'])}")
    print()
    cur = out.get("current_state", {})
    if cur:
        print("State saat ini:")
        print(f"  ZRAM        : {cur.get('zram_size', '?')} ({cur.get('zram_algo', '?')}) - {cur.get('zram_active', '?')}")
        print(f"  Swappiness  : {cur.get('swappiness', '?')}")
        print(f"  VFS Pressure: {cur.get('vfs_cache_pressure', '?')}")
        print(f"  Baloo       : {cur.get('baloo_status', '?')}")
        swaps = cur.get('swap_devices', [])
        if swaps:
            print(f"  Swap devices: {', '.join(swaps)}")


def main():
    parser = argparse.ArgumentParser(description="FireWork RAM Profile Engine")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview aja, gak apply apa-apa (default)")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON aja (buat installer)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply perubahan (butuh root, HATI-HATI!)")
    parser.add_argument("--force-mode", choices=["survival", "balanced", "comfort", "performance"],
                        help="Override deteksi otomatis")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE),
                        help="File output JSON")
    args = parser.parse_args()

    profiles = load_profiles()
    ram_gb = get_ram_total_gb()
    mode = args.force_mode or detect_mode(ram_gb, profiles)

    out = build_output(mode, ram_gb, profiles, include_current=True)

    # Simpan JSON
    out_path = Path(args.output)
    try:
        if out_path.exists():
            out_path.unlink()
    except Exception:
        pass
    try:
        with open(args.output, "w") as f:
            json.dump(out, f, indent=2)
    except PermissionError:
        # Fallback: tulis ke /tmp dengan nama unik kalau gak bisa
        import tempfile
        alt = Path(tempfile.gettempdir()) / f"firework-ram-profile-{__import__('os').getuid()}.json"
        with open(alt, "w") as f:
            json.dump(out, f, indent=2)
        print(f"WARN: gak bisa tulis ke {args.output}, pakai {alt}", file=sys.stderr)
        args.output = str(alt)

    if args.json:
        print(json.dumps(out, indent=2))
        return

    print_pretty(out)
    print()
    print(f"JSON output: {args.output}")
    print()

    if args.apply:
        if os.geteuid() != 0:
            print("ERROR: --apply butuh root (sudo)!", file=sys.stderr)
            sys.exit(1)
        print("⚠ --apply belum diimplementasi di V0.9")
        print("  Akan diimplementasi di installer V1.0")
    else:
        print("Mode: DRY-RUN (gak ada yang diubah)")
        print("Untuk apply, tunggu installer V1.0")


if __name__ == "__main__":
    main()
