# FireWork OS

**Just A Normal Distro.**

FireWork is an open source Linux distro. It is just a normal
distro, like any other distro, but there is a catch.

---

## 1. What Is FireWork?

FireWork is a Linux distro based on Debian, with KDE Plasma
as the desktop. Because it uses KDE, you can customize your
desktop however you want.

But that is not all. FireWork has two subsystems that let
you run software from other operating systems, without
dual-booting.

And do not worry about drivers. FireWork detects your
hardware and picks the right driver automatically.

---

## 2. FireWine (Subsystem #1) - Recommended

FireWine is a Windows apps and games support layer.

- Built on Wine 11.0.
- Uses NTSYNC, which makes games run faster and more stable.
- DXVK and VKD3D-Proton included for gaming.
- You double-click a .exe, it runs. No terminal needed.

In a future update, FireWine will get a new patch to support
more MP3 playback and more games on FireWine.

Status: Working.

---

## 3. Android (Subsystem #2) - Not Recommended

FireWay is an Android subsystem. It gives you a full Android
UI, so you can play or open Android apps.

But there are limits:

- It only supports x86 and x86_64 APKs.
- ARM-only apps will not run.
- Boot time is slow.
- The full Android UI is heavy.

Because of these limits, I do not recommend using FireWay
as a daily driver. Use it only when you need one specific
Android app.

Status: Working, but often hangs on boot.

---

## 4. FireStore

FireStore is the app store that comes with FireWork.

- 1,876 desktop apps from AppStream DEP-11 YAML.
- Search across the catalog and apt-cache.
- Categories: All, FireWine, Internet, Network, Multimedia,
  Office, Gaming, Development, System, Security, Education,
  Installed, Other.
- Featured apps carousel.
- Progress dialog with live log.
- Right-click menu: Open, Install, Update, Remove, Info.
- Five themes: orange, blue, green, purple, red.
- Auto language: Indonesian / English.

Written in Python with PySide6 and a backend script that
wraps apt.

Status: v0.9 done. v1.0 polish in progress.

---

## 5. How To Install FireWork

There will be two ways to install FireWork.

### Method 1: USB Bootable

Write the FireWork ISO to a USB drive, boot from it, and
install like a normal Linux distro.

### Method 2: FireWork Installer

A standalone installer that runs from Windows, Linux, or
macOS. It detects your current OS, sets up a username and
password, and installs FireWork next to your existing system.

Both methods are planned for V1.0. Not available yet.

---

## 6. FireSwitch

FireSwitch is a two-way OS switcher.

- In FireWork, there is a "Back to [OS]" shortcut on the
  desktop.
- In the other OS, there is a "Back to FireWork" shortcut.
- One click reboots into the other OS.

FireSwitch is not a subsystem. It is a utility.

Status: Planned for V1.0 BETA.

---

## Closing

FireWork is a solo project. It is not finished. It is not
trying to beat any other distro.

It is just a normal distro that tries to run well on old
hardware.

If you want to help, open an issue.
If you want to test it, build it from source.
If you want to tell me it is bad, that is fine too.

---

## Links

- GitHub: https://github.com/GOKILKEREN/FireWork
- License: GPL v3
