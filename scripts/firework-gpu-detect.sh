#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# FireWork OS — GPU Auto Detection & KMS Setup
# Version: 1.2 (dry-run support)
# Usage: sudo ./firework-gpu-detect.sh [--dry-run]
# ═══════════════════════════════════════════════════════════════

set -e

# ─── Parse args ───
DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run|-n) DRY_RUN=1 ;;
        --help|-h)
            echo "Usage: sudo $0 [--dry-run]"
            echo "  --dry-run, -n  : Test detection tanpa modif system"
            exit 0
            ;;
    esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

LOG_DIR=/var/log/firework
LOG_FILE=$LOG_DIR/gpu-detect.log
MODULES_FILE=/etc/initramfs-tools/modules
FRAMEBUFFER_FILE=/etc/initramfs-tools/conf.d/splash
BACKUP_DIR=/var/backups/firework/gpu-detect

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Harus root! Pake: sudo $0${NC}"
    exit 1
fi

mkdir -p "$LOG_DIR" "$BACKUP_DIR"

log() { echo -e "$*" | tee -a "$LOG_FILE"; }

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔥 FireWork OS — GPU Auto Detection v1.2${NC}"
if [ "$DRY_RUN" -eq 1 ]; then
    echo -e "${CYAN}   🧪 DRY-RUN MODE — No system changes${NC}"
fi
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

log "[$(date '+%Y-%m-%d %H:%M:%S')] Starting GPU detection (dry-run=$DRY_RUN)..."

# ─── Detect Virtualization ───
detect_virt() {
    if command -v systemd-detect-virt &>/dev/null; then
        systemd-detect-virt 2>/dev/null | head -1 | tr -d '[:space:]'
    else
        if grep -qi "hypervisor" /proc/cpuinfo 2>/dev/null; then
            echo "unknown-vm"
        else
            echo "none"
        fi
    fi
}

VIRT=$(detect_virt)
[ -z "$VIRT" ] && VIRT="none"
log "  Virtualization: ${YELLOW}${VIRT}${NC}"

# ─── Detect GPU ───
detect_gpu() {
    local gpu_info
    gpu_info=$(lspci 2>/dev/null | grep -iE "vga|3d|display" | head -1)
    [ -z "$gpu_info" ] && echo "unknown" && return

    if echo "$gpu_info" | grep -qi "intel"; then
        echo "intel"
    elif echo "$gpu_info" | grep -qiE "amd|radeon|ati"; then
        echo "amd"
    elif echo "$gpu_info" | grep -qi "nvidia"; then
        echo "nvidia"
    else
        echo "unknown"
    fi
}

GPU_VENDOR=$(detect_gpu)
GPU_INFO=$(lspci 2>/dev/null | grep -iE "vga|3d|display" | head -1)
log "  GPU vendor: ${YELLOW}${GPU_VENDOR}${NC}"
log "  GPU info: $GPU_INFO"

# ─── Modules ───
MODULES=""
GPU_LABEL=""

if [ "$VIRT" != "none" ] && [ "$VIRT" != "unknown-vm" ]; then
    case "$VIRT" in
        vmware)              MODULES="vmwgfx drm drm_kms_helper";           GPU_LABEL="VMware (VM)" ;;
        oracle|virtualbox)   MODULES="vboxvideo drm drm_kms_helper";        GPU_LABEL="VirtualBox (VM)" ;;
        qemu|kvm)            MODULES="virtio_gpu qxl drm drm_kms_helper";   GPU_LABEL="QEMU/KVM (VM)" ;;
        microsoft)           MODULES="hyperv_drm drm drm_kms_helper";       GPU_LABEL="Hyper-V (VM)" ;;
        *)                   MODULES="";                                    GPU_LABEL="Unknown VM" ;;
    esac
else
    case "$GPU_VENDOR" in
        intel)   MODULES="i915 drm drm_kms_helper";                  GPU_LABEL="Intel (i915)" ;;
        amd)     MODULES="amdgpu radeon drm drm_kms_helper";         GPU_LABEL="AMD (amdgpu/radeon)" ;;
        nvidia)  MODULES="nouveau drm drm_kms_helper";               GPU_LABEL="NVIDIA (nouveau)" ;;
        *)       MODULES="";                                         GPU_LABEL="Unknown GPU" ;;
    esac
fi

log "  Label: ${GREEN}${GPU_LABEL}${NC}"

# ─── Dry-run exit ───
if [ "$DRY_RUN" -eq 1 ]; then
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}🧪 DRY-RUN RESULT${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo "  Virtualization : $VIRT"
    echo "  GPU vendor     : $GPU_VENDOR"
    echo "  GPU label      : $GPU_LABEL"
    if [ -z "$MODULES" ]; then
        echo "  Modules        : (fallback → MODULES=most)"
    else
        echo "  Modules        : $MODULES"
    fi
    echo ""
    echo "  ✅ Detection works. Run tanpa --dry-run untuk apply."
    echo ""
    exit 0
fi

# ═══════════════════════════════════════════════════════════════
# REAL RUN (no dry-run)
# ═══════════════════════════════════════════════════════════════

TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# ─── Fallback ───
if [ -z "$MODULES" ]; then
    log "${YELLOW}⚠️  GPU tidak dikenali — MODULES=most (fallback)${NC}"

    cp /etc/initramfs-tools/initramfs.conf "$BACKUP_DIR/initramfs.conf.bak.$TIMESTAMP" 2>/dev/null || true
    sed -i 's/^MODULES=.*/MODULES=most/' /etc/initramfs-tools/initramfs.conf
    log "  Set MODULES=most"

    mkdir -p /etc/initramfs-tools/conf.d
    echo "FRAMEBUFFER=y" > "$FRAMEBUFFER_FILE"

    log "  Rebuilding initramfs..."
    update-initramfs -u 2>&1 | tee -a "$LOG_FILE"

    log ""
    log "${GREEN}✅ Fallback mode applied (MODULES=most)${NC}"
    exit 0
fi

# ─── Backup ───
[ -f "$MODULES_FILE" ] && cp "$MODULES_FILE" "$BACKUP_DIR/modules.bak.$TIMESTAMP"
[ -f "$FRAMEBUFFER_FILE" ] && cp "$FRAMEBUFFER_FILE" "$BACKUP_DIR/splash.bak.$TIMESTAMP"

# ─── Write modules ───
{
    echo "# ═══════════════════════════════════════════════════════════════"
    echo "# FireWork OS — Auto-generated by firework-gpu-detect.sh"
    echo "# Generated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# GPU: $GPU_LABEL"
    echo "# ═══════════════════════════════════════════════════════════════"
    for m in $MODULES; do
        echo "$m"
    done
} > "$MODULES_FILE"

log "  Modules written: $MODULES"

mkdir -p /etc/initramfs-tools/conf.d
echo "FRAMEBUFFER=y" > "$FRAMEBUFFER_FILE"
log "  FRAMEBUFFER=y written"

# ─── Rebuild ───
log ""
log "  Rebuilding initramfs..."
if update-initramfs -u 2>&1 | tee -a "$LOG_FILE"; then
    log "${GREEN}✅ Initramfs rebuilt${NC}"
else
    log "${RED}❌ Failed — restore backup${NC}"
    [ -f "$BACKUP_DIR/modules.bak.$TIMESTAMP" ] && cp "$BACKUP_DIR/modules.bak.$TIMESTAMP" "$MODULES_FILE"
    update-initramfs -u
    exit 1
fi

# ─── Verify ───
log ""
log "${BLUE}═══ Verification ═══${NC}"

KERNEL=$(uname -r)
for mod in $MODULES; do
    [ "$mod" = "drm" ] && continue
    [ "$mod" = "drm_kms_helper" ] && continue
    if lsinitramfs /boot/initrd.img-$KERNEL 2>/dev/null | grep -q "$mod"; then
        log "  ✅ $mod ada di initramfs"
    else
        log "  ${YELLOW}⚠️  $mod gak kedetect (mungkin built-in)${NC}"
    fi
done

log ""
log "${GREEN}═══════════════════════════════════════════════════════${NC}"
log "${GREEN}✅ SELESAI!${NC}"
log "${GREEN}═══════════════════════════════════════════════════════${NC}"
log "   GPU     : $GPU_LABEL"
log "   Modules : $MODULES"
log "   Log     : $LOG_FILE"
log ""
log "   Reboot: ${YELLOW}sudo reboot${NC}"
log ""

exit 0
