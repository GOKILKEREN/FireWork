#!/usr/bin/env python3
"""FireWork OS - Hardware Detector v2 (smart)"""

import json
import re
import subprocess
from pathlib import Path

OUTPUT = Path("/tmp/firework-hardware.json")


def run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except Exception:
        return ""


def detect_cpu():
    info = {"vendor": None, "model": None, "cores": 0, "arch": None, "generation": None}
    text = Path("/proc/cpuinfo").read_text()
    m = re.search(r"vendor_id\s*:\s*(\S+)", text)
    if m:
        info["vendor"] = m.group(1)
    m = re.search(r"model name\s*:\s*(.+)", text)
    if m:
        info["model"] = m.group(1).strip()
    info["cores"] = text.count("processor\t:")
    info["arch"] = run(["uname", "-m"]).strip()
    # Deteksi generasi Intel (buat VA-API driver)
    if info["vendor"] == "GenuineIntel":
        if "Celeron" in (info["model"] or "") or "Pentium" in (info["model"] or ""):
            info["generation"] = "low-end"
    return info


def detect_gpu():
    out = run(["lspci", "-nn"])
    gpus = []
    for line in out.splitlines():
        if any(k in line for k in ("VGA", "3D", "Display")):
            gpus.append(line.strip())
    vendors = set()
    for g in gpus:
        if "Intel" in g:
            vendors.add("intel")
        elif "NVIDIA" in g:
            vendors.add("nvidia")
        elif "AMD" in g or "ATI" in g:
            vendors.add("amd")
    # Cek VA-API sekarang
    vainfo_out = run(["vainfo"]) if run(["which", "vainfo"]).strip() else ""
    vaapi_working = "VAProfile" in vainfo_out
    return {
        "devices": gpus,
        "vendors": sorted(vendors),
        "vaapi_working": vaapi_working,
        "vaapi_info": vainfo_out[:300] if vainfo_out else "vainfo not installed",
    }


def detect_wifi():
    out = run(["lspci", "-nn"]) + "\n" + run(["lsusb"])
    wifis = []
    vendors = set()
    for line in out.splitlines():
        if any(k in line for k in ("Network controller", "Wireless", "WiFi", "WLAN")):
            wifis.append(line.strip())
            if "Intel" in line:
                vendors.add("intel")
            elif "Realtek" in line:
                vendors.add("realtek")
            elif "Broadcom" in line:
                vendors.add("broadcom")
            elif "Atheros" in line or "Qualcomm" in line:
                vendors.add("atheros")
            elif "MediaTek" in line or "Ralink" in line:
                vendors.add("mediatek")
    # Cek interface
    interfaces = []
    ip_out = run(["ip", "-br", "link"])
    for line in ip_out.splitlines():
        if line.startswith(("wlan", "wlp", "wlx")):
            parts = line.split()
            interfaces.append({"name": parts[0], "state": parts[1] if len(parts) > 1 else "?"})
    # Cek firmware error di dmesg
    dmesg_err = ""
    dmesg_out = run(["dmesg"])
    for line in dmesg_out.splitlines():
        if "firmware" in line.lower() and ("fail" in line.lower() or "error" in line.lower() or "missing" in line.lower()):
            dmesg_err += line + "\n"
    # rfkill
    rfkill_out = run(["rfkill", "list"])
    rfkill_blocked = "blocked: yes" in rfkill_out.lower()
    return {
        "devices": wifis,
        "vendors": sorted(vendors),
        "interfaces": interfaces,
        "firmware_errors": dmesg_err[:500],
        "rfkill_blocked": rfkill_blocked,
    }


def detect_bluetooth():
    out = run(["lsusb"]) + run(["hciconfig"]) + run(["bluetoothctl", "list"])
    bt = [l for l in out.splitlines() if "Bluetooth" in l or "bluetooth" in l]
    return {"devices": bt, "present": bool(bt)}


def detect_audio():
    # Cek PCI/USB audio
    pci_out = run(["lspci", "-nn"])
    usb_out = run(["lsusb"])
    audio = [l.strip() for l in pci_out.splitlines() if "Audio" in l or "Multimedia" in l]
    # Cek server (pipewire vs pulseaudio)
    pactl = run(["pactl", "info"])
    server = "unknown"
    if "PipeWire" in pactl:
        server = "pipewire"
    elif "PulseAudio" in pactl:
        server = "pulseaudio"
    else:
        # Cek manual
        if run(["pgrep", "-x", "pipewire"]).strip():
            server = "pipewire"
        elif run(["pgrep", "-x", "pulseaudio"]).strip():
            server = "pulseaudio"
    # Cek SOF firmware (Sound Open Firmware untuk Intel modern)
    cpu_model = run(["grep", "-m1", "model name", "/proc/cpuinfo"])
    needs_sof = "Intel" in cpu_model
    return {
        "devices": audio,
        "server": server,
        "needs_sof": needs_sof,
    }


def detect_printer():
    # USB printers
    usb_out = run(["lsusb"])
    usb_printers = [l for l in usb_out.splitlines()
                    if any(k in l for k in ("Printer", "HP", "Canon", "Epson", "Brother", "Lexmark"))]
    # Network printers (via avahi/cups)
    lpinfo = run(["lpinfo", "-v"]) if run(["which", "lpinfo"]).strip() else ""
    network_printers = [l for l in lpinfo.splitlines() if "ipp" in l.lower() or "dnssd" in l.lower()]
    # CUPS status
    cups_running = bool(run(["systemctl", "is-active", "cups"]).strip() == "active")
    return {
        "usb_printers": usb_printers,
        "network_printers": network_printers,
        "cups_running": cups_running,
        "has_printer": bool(usb_printers or network_printers),
    }


def detect_touchpad():
    out = run(["grep", "-i", "-E", "touchpad|synaptics|elan|alps", "/proc/bus/input/devices"])
    return {"found": bool(out.strip())}


def detect_storage():
    out = run(["lsblk", "-d", "-o", "NAME,SIZE,TYPE,MODEL,ROTA"])
    return {"devices": out.strip().splitlines()}


def build_recommendations(hw):
    """Smart filter: cuma paket yang BENERAN dibutuhin."""
    rec = {"safe": [], "optional": [], "skip": [], "needs_confirm": []}

    # === MICROCODE (safe) ===
    if hw["cpu"]["vendor"] == "GenuineIntel":
        rec["safe"].append("intel-microcode")
    elif hw["cpu"]["vendor"] == "AuthenticAMD":
        rec["safe"].append("amd64-microcode")

    # === WIFI (cuma vendor yang ada) ===
    for v in hw["wifi"]["vendors"]:
        pkg = f"firmware-{v}" if v != "mediatek" else "firmware-mediatek"
        if v == "intel":
            pkg = "firmware-iwlwifi"
        rec["safe"].append(pkg)

    # === GPU / VA-API ===
    if "intel" in hw["gpu"]["vendors"]:
        if not hw["gpu"]["vaapi_working"]:
            rec["safe"].extend(["intel-media-va-driver", "i965-va-driver", "mesa-va-drivers"])
    if "amd" in hw["gpu"]["vendors"]:
        rec["safe"].extend(["mesa-va-drivers", "firmware-amd-graphics"])
    if "nvidia" in hw["gpu"]["vendors"]:
        rec["needs_confirm"].append("nvidia-driver")

    # === AUDIO ===
    if hw["audio"]["server"] == "pipewire":
        # Jangan install pulseaudio!
        rec["skip"].append("pulseaudio")
        rec["safe"].append("pipewire-audio")
    if hw["audio"]["needs_sof"]:
        rec["safe"].append("firmware-sof-signed")
    rec["safe"].append("alsa-utils")

    # === BLUETOOTH ===
    if hw["bluetooth"]["present"]:
        rec["safe"].append("bluez")

    # === PRINTER (cuma kalau ada printer beneran) ===
    if hw["printer"]["has_printer"]:
        rec["optional"].extend(["cups", "cups-filters", "printer-driver-all"])
    else:
        rec["skip"].extend(["cups", "cups-filters", "printer-driver-all"])

    # Hapus duplikat
    for k in rec:
        rec[k] = sorted(set(rec[k]))

    return rec


def main():
    print("=== FireWork Hardware Detector v2 ===")
    print()

    hw = {
        "cpu": detect_cpu(),
        "gpu": detect_gpu(),
        "wifi": detect_wifi(),
        "bluetooth": detect_bluetooth(),
        "audio": detect_audio(),
        "printer": detect_printer(),
        "touchpad": detect_touchpad(),
        "storage": detect_storage(),
    }
    hw["recommendations"] = build_recommendations(hw)

    OUTPUT.write_text(json.dumps(hw, indent=2))

    # === Pretty print ===
    print(f"CPU   : {hw['cpu']['model']} ({hw['cpu']['cores']} cores)")
    print(f"GPU   : {', '.join(hw['gpu']['vendors']) or 'unknown'}")
    print(f"        VA-API: {'✅ aktif' if hw['gpu']['vaapi_working'] else '❌ belum'}")
    print(f"WiFi  : {', '.join(hw['wifi']['vendors']) or 'tidak terdeteksi'}")
    if hw['wifi']['interfaces']:
        for i in hw['wifi']['interfaces']:
            print(f"        {i['name']}: {i['state']}")
    if hw['wifi']['firmware_errors']:
        print(f"        ⚠ firmware error di dmesg!")
    if hw['wifi']['rfkill_blocked']:
        print(f"        ⚠ rfkill BLOCKED")
    print(f"BT    : {'✅ ada' if hw['bluetooth']['present'] else '❌ tidak ada'}")
    print(f"Audio : {hw['audio']['server']}")
    print(f"Printer: {'✅ ada' if hw['printer']['has_printer'] else '❌ tidak ada'}")
    print()

    rec = hw["recommendations"]
    print(f"=== Rekomendasi Paket ===")
    print(f"✅ Safe ({len(rec['safe'])}): {', '.join(rec['safe']) or '-'}")
    print(f"⚠ Optional ({len(rec['optional'])}): {', '.join(rec['optional']) or '-'}")
    print(f"🔒 Butuh konfirmasi ({len(rec['needs_confirm'])}): {', '.join(rec['needs_confirm']) or '-'}")
    print(f"⏭ Skip ({len(rec['skip'])}): {', '.join(rec['skip']) or '-'}")
    print()
    print(f"JSON: {OUTPUT}")


if __name__ == "__main__":
    main()
