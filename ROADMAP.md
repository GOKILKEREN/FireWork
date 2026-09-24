# FireWork OS - ROADMAP

> "Just A Normal Distro."

This is the roadmap for FireWork OS. I made this so I (and you) know
where this project is heading. Nothing fancy. Just clear.

---

## WHY I BUILT THIS DISTRO

Honestly, not because I wanted to "make a new distro" or "compete with
Ubuntu". I built this because I had a problem, and no distro actually
solved it. The problem:

1. My laptop is a potato - Lenovo IdeaPad S300 (2012), 1.77 GB RAM,
   14-year-old HDD. Modern distros (Mint, Ubuntu, Fedora) keep getting
   heavier. Updates slow it down. Boot takes a minute.

2. I need Windows apps - Some software only exists on Windows. I can't
   fully switch to Linux without them.

3. I need Android apps - I use Android apps daily. They don't exist on
   Linux.

4. Can't use them together - Other distros make you choose: either
   Linux native, OR Wine, OR Waydroid. Can't have all three at once
   easily.

5. Install is painful - For normal users, installing Linux is hell.
   Download ISO, flash USB, enter BIOS, partition, GRUB... already
   exhausted before even trying.

So I built FireWork OS. One OS, three worlds (Linux + Windows + Android),
on a potato laptop, easy install.

Nothing revolutionary. Nothing game-changing. Just a normal distro that
solves a normal problem, that normal people like me have.

---

## POSITIONING

FireWork isn't "better than Ubuntu" or "Mint killer". FireWork isn't
"the next big thing". FireWork is just a normal distro.

But "normal" here means:

- Normal for potato laptops (2010-2015)
- Normal for people who need Windows + Android + Linux at the same time
- Normal for users who are afraid to install Linux

So maybe not "normal" for everyone. But normal for us.

Tagline:
> Not "Linux is easier than Windows".
> But: "Linux you install like installing a normal Windows app.
> Next, next, done."

---

## TARGET HARDWARE

Main focus:
- Laptops from 2010-2015
- RAM 2 GB - 4 GB (4 GB optimal)
- HDD / small SSD
- Intel / AMD (NVIDIA partial support)
- Legacy BIOS / UEFI

Tested on:
- Lenovo IdeaPad S300 (2012) - Intel Sandy Bridge, 1.77 GB RAM
- Other hardware - need testers

---

## 3 SUBSYSTEMS

### 1. FireLinux (Native)
Debian Trixie + KDE Plasma 6, custom orange-black theme.
Status: Working

### 2. FireWine (Windows Apps)
Wine 11 (Morgwai repo, NTSYNC patch) + DXVK + VKD3D-Proton.
Double-click .exe, it runs.
Status: Working

### 3. FireWay (Android Apps)
Waydroid (x86_64, VANILLA) + Weston bridge.
Android Full UI + desktop shortcut.
Status: Working (sometimes hangs on boot, already masked)

Note: FireSwitch is NOT a subsystem. It's a utility (planned for V1.0 BETA).

---

## V0.9 - DONE (Baseline)

All of this was finished before I wrote this roadmap:

- FireStore v1.0 (1876 apps, PySide6)
- RAM Profile Engine (4 modes)
- Hardware Detect v2
- Hide apps utility
- Logo + Wallpaper + Branding
- GitHub repo + GPL v3 license
- YouTube showcase video
- Boot optimization (52s to 32s)
- WiFi auto-connect
- VA-API active (i915)
- Time sync (RTC weak fix)
- Disk health check

V0.9 = foundation. V1.0 BETA = polish + new features.

Just a normal baseline. Nothing special. But it works.

---

## V1.0 BETA - IN PROGRESS

Target: first public ISO release.

Progress:

| # | Item | Status |
|---|------|--------|
| 1 | FireStore polish | Partial |
| 2 | Update System (APT repo + GPG) | Not started |
| 3 | FireUpdate (own update manager) | Not started |
| 4 | FireWork Installer (cross-platform) | Not started |
| 5 | Final ISO | Not started |
| 6 | Bug fixes from beta testers | Waiting for testers |
| 7 | Boot Animation (Plymouth) | Logo works, animation skipped |
| 8 | SDDM Login Screen FireWork | Not started |
| 9 | Multi-user support | WiFi done |
| 10 | Hardware Adaptive Detection (new) | Script done, integration pending |

Details of V1.0 BETA:

### 1. FireStore Polish
- Fix small bugs
- Optimize performance
- Polish UI/UX until user says "GG"

### 2. Update System
- Own APT repo + GPG signing
- Hosting: GitHub Pages
- Client: /etc/apt/sources.list.d/firework.list

### 3. FireUpdate
- NOT Discover (Discover is heavy, has ads)
- Build own: check update, install, changelog, rollback
- Can be a FireStore module or separate app

### 4. FireWork Installer
- Cross-platform: Windows .exe + Linux .AppImage + macOS .dmg
- Auto-detect origin OS
- Set username + password from installer
- Mode: USB bootable / dual-boot / VM
- Auto-partition + auto-GRUB
- This is the part where FireWork stops being "just a normal distro"
  and starts being useful for normal users.

### 5. Final ISO
- Build ISO (~2.5 GB target)
- Remaster Debian + FireWork branding
- Include FireStore, FireWine, FireWay ready to use
- Upload to SourceForge / Internet Archive

### 6. Bug Fix from Testers
- Distribute to 5-10 testers
- Fix bugs from feedback
- Iterate until stable

### 7. Boot Animation
- Plymouth theme: FireWork logo + background
- Status: Logo works, spinner animation SKIPPED (hardware limit)
- Alternative: GRUB background image

### 8. SDDM Login Screen
- QML custom theme
- FireWork wallpaper + logo + orange login box
- Color #FF6B00

### 9. Multi-user Support
- WiFi system-wide (done)
- Per-user config
- Auto-setup for new users

### 10. Hardware Adaptive Detection (new)
- Script firework-gpu-detect.sh v1.2 (done)
- Auto-detect GPU (Intel/AMD/NVIDIA/VM)
- Auto-config KMS modules
- Integration: run in installer or first boot
- Why important: so FireWork works on all hardware, not just my laptop.
  Because "normal distro" means normal for everyone, not just me.

---

## V1.0 RELEASE - After BETA Stable

After 9-10 V1.0 BETA items done + bugs fixed from testers:
V1.0 RELEASE = done.

Focus:
- Final bug fix
- Polish until normal users can use without asking
- Complete documentation
- Website + landing page

Nothing fancy. Just a normal stable release.

---

## V1.5+ - LONG TERM ROADMAP

### V1.5 - Extra Features
- FireSwitch (two-way OS switch, like Wubi)
- FireWine-as-Proton (Steam uses FireWine engine)
- FireStore auto-update catalog
- Adaptive hardware detection for all segments

### V2.0 - Mature & Universal
- Support modern hardware (NVMe, WiFi 6E, new GPUs)
- ARM support (Raspberry Pi, etc)
- Active community + contributors
- DistroWatch listed
- Mirrors in various countries

### V3.0 - Future
- Maybe FireWork becomes a normal option for normal users
- Maybe there is a team helping
- Maybe there are sponsors
- What's certain: still free, still open source (GPL v3), still focused on users

Because in the end, FireWork is just a normal distro.
Normal distros don't disappear. They just keep going.

---

## PRINCIPLES

Things that won't change no matter what:

1. GPL v3, anti-Microsoft. Open source, always.
2. Don't attack other distros. Respect Ubuntu, Mint, etc.
3. Be honest. If it's a solo project, say it's a solo project.
4. Focus on FireWork's strengths, not bashing others.
5. Normal users = priority. If user has to open terminal, it's not finished yet.
6. Old hardware = main target. Not just "can run", but "runs smooth".
7. Stay humble. FireWork is just a normal distro. Not the best. Just normal.

---

## REALISTIC?

Honest: I'm a solo dev, age 11-14, this project is a hobby.

Realistic estimates:
- V1.0 BETA release: 1-3 months from now
- V1.0 RELEASE: 6-12 months (bug fix from testers)
- V1.5: 1-2 years
- V2.0: 2-3 years

But: I've already beaten 90% of people who just plan without executing.
I already have V0.9 that works. Just need to continue.

If anyone wants to help - welcome.
If anyone wants to test - welcome.
If anyone wants to criticize - welcome, but contribute, don't just talk.

---

## CREDIT & THANKS

- Debian - foundation
- KDE Plasma - desktop
- Wine Project - FireWine
- Waydroid - FireWay
- PySide6 - FireStore UI
- DeepSeek AI - coding help (I disclose this, honest)
- All testers who will help (coming soon)

---

## NOTES

This roadmap is alive - can change anytime based on reality.
If you have a good idea, open an issue on GitHub.
If you find a bug, report on GitHub Issues.

FireWork isn't a project just for me.
FireWork is for anyone with a potato laptop who wants to try Linux
without the hassle.

Just a normal distro, for normal people, with normal problems.

---

Last update: 24 September 2026
Next update: After V1.0 BETA item #1 done (FireStore polish)

Keep going.
