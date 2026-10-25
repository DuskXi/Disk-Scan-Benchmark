"""
Hardware and OS facts for a local-suite submission: exact OS version, CPU cores, and per drive its type
(NVMe SSD / SATA SSD / SATA HDD / ...) and link (PCIe generation and lanes, SATA or SAS speed).

Only models, versions and numbers are read. No serial number, volume label, path or name is ever queried for the
submission; anything that comes back as text goes through clean_text before it is kept.
"""

import json
import os
import platform
import plistlib
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from submission_schema import TEXT_RE

GEN_BY_GTS = {2.5: "1.0", 5.0: "2.0", 8.0: "3.0", 16.0: "4.0", 32.0: "5.0", 64.0: "6.0"}
# Windows DEVPKEY_PciDevice_CurrentLinkSpeed values
GEN_BY_WIN_CODE = {1: "1.0", 2: "2.0", 3: "3.0", 4: "4.0", 5: "5.0", 6: "6.0"}


def clean_text(value: str, fallback: str = "unknown", limit: int = 64) -> str:
    """Only characters a submission may contain, so a model or version string can never carry a path or address."""
    text = re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ()._+,#-]", " ", value or "")).strip()[:limit]
    return text if text and (limit > 64 or TEXT_RE.match(text)) else fallback


def run(cmd: List[str], env: Optional[Dict[str, str]] = None) -> str:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=False, env={**os.environ, **(env or {})}, timeout=60
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def powershell_json(script: str, env: Optional[Dict[str, str]] = None) -> Any:
    out = run(["powershell", "-NoProfile", "-Command", script], env)
    try:
        return json.loads(out) if out.strip() else None
    except json.JSONDecodeError:
        return None


# --- OS version ---


def os_detail(os_key: str) -> str:
    """'Windows 11 25H2 (build 26300.1234)', 'Ubuntu 24.04.1 LTS, kernel 6.8.0-45-generic', 'macOS 15.1 (24B83)'."""
    if os_key == "windows":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as k:

                def val(name: str) -> str:
                    try:
                        return str(winreg.QueryValueEx(k, name)[0])
                    except OSError:
                        return ""

                build, ubr, display = val("CurrentBuild"), val("UBR"), val("DisplayVersion") or val("ReleaseId")
                product, kind = val("ProductName"), val("InstallationType")
            if kind.lower() == "server":
                name = re.sub(r"\s+(Datacenter|Standard|Essentials).*$", "", product) or "Windows Server"
            else:
                # ProductName still says "Windows 10" on Windows 11; the build number tells them apart
                name = "Windows 11" if build.isdigit() and int(build) >= 22000 else "Windows 10"
            return clean_text(f"{name} {display} (build {build}.{ubr})", limit=96)
        except OSError:
            return clean_text(f"Windows {platform.version()}", limit=96)
    if os_key == "linux":
        pretty = ""
        try:
            m = re.search(r'^PRETTY_NAME="?([^"\n]+)"?', Path("/etc/os-release").read_text(), re.M)
            pretty = m.group(1) if m else ""
        except OSError:
            pass
        return clean_text(f"{pretty or 'Linux'}, kernel {platform.release()}", limit=96)
    if os_key == "macos":
        ver, build = run(["sw_vers", "-productVersion"]).strip(), run(["sw_vers", "-buildVersion"]).strip()
        return clean_text(f"macOS {ver} ({build})", limit=96)
    return clean_text(platform.platform(), limit=96)


# --- CPU ---


def physical_cores(os_key: str) -> Optional[int]:
    try:
        if os_key == "windows":
            n = powershell_json(
                "(Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum | ConvertTo-Json"
            )
            return int(n) if n else None
        if os_key == "linux":
            pairs = set()
            phys = core = None
            for line in Path("/proc/cpuinfo").read_text().splitlines():
                if line.startswith("physical id"):
                    phys = line.split(":", 1)[1].strip()
                elif line.startswith("core id"):
                    core = line.split(":", 1)[1].strip()
                elif not line.strip() and core is not None:
                    pairs.add((phys, core))
                    phys = core = None
            return len(pairs) or None
        if os_key == "macos":
            out = run(["sysctl", "-n", "hw.physicalcpu"]).strip()
            return int(out) if out.isdigit() else None
    except (OSError, ValueError, TypeError):
        pass
    return None


# --- drive type and link ---


def disk_kind(bus: str, media: str) -> str:
    if bus == "nvme":
        return "nvme_ssd"
    if bus in ("sata", "sas", "usb"):
        return f"{bus}_{media}" if media in ("ssd", "hdd") else bus
    if bus == "virtual":
        return "virtual"
    return "unknown" if bus == "unknown" else "other"


def pcie_link(gts: Optional[float], width: Optional[int]) -> str:
    gen = GEN_BY_GTS.get(gts or 0.0)
    if not gen:
        return "PCIe"
    return f"PCIe {gen} x{width}" if width else f"PCIe {gen}"


def _windows_disk(target: str) -> Dict[str, Any]:
    # The target path goes to PowerShell through an environment variable, never into the command text
    d = powershell_json(
        "$v = Get-Volume -FilePath $env:DSB_TARGET; $d = $v | Get-Partition | Get-Disk; "
        "$p = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq [string]$d.Number }; "
        "$id = ($d.Path -replace '^\\\\\\\\\\?\\\\', '' -replace '#\\{.*$', '') -replace '#', '\\'; "
        "$parent = (Get-PnpDeviceProperty -InstanceId $id -KeyName DEVPKEY_Device_Parent "
        "-ErrorAction SilentlyContinue).Data; "
        "$speed = $null; $width = $null; "
        "if ($parent) { "
        "$speed = (Get-PnpDeviceProperty -InstanceId $parent -KeyName DEVPKEY_PciDevice_CurrentLinkSpeed "
        "-ErrorAction SilentlyContinue).Data; "
        "$width = (Get-PnpDeviceProperty -InstanceId $parent -KeyName DEVPKEY_PciDevice_CurrentLinkWidth "
        "-ErrorAction SilentlyContinue).Data }; "
        "@{ fs = $v.FileSystemType; bus = [string]$d.BusType; model = $d.Model; media = [string]$p.MediaType; "
        "speed = $speed; width = $width } | ConvertTo-Json -Compress",
        {"DSB_TARGET": target},
    )
    if not isinstance(d, dict):
        return {}
    bus = str(d.get("bus") or "").lower()
    bus = {"spaces": "virtual", "file backed virtual": "virtual", "ata": "sata", "raid": "other"}.get(bus, bus)
    media = str(d.get("media") or "").lower()
    media = media if media in ("ssd", "hdd") else ("ssd" if bus == "nvme" else "unknown")
    if bus == "nvme":
        code, width = d.get("speed"), d.get("width")
        gen = GEN_BY_WIN_CODE.get(int(code)) if isinstance(code, int) else None
        link = (f"PCIe {gen} x{width}" if width else f"PCIe {gen}") if gen else "PCIe"
    elif bus in ("sata", "sas", "usb"):
        link = bus.upper()  # Windows does not expose the negotiated SATA/SAS speed without vendor tools
    else:
        link = "unknown"
    return {
        "fs": str(d.get("fs") or "").lower(),
        "bus": bus,
        "media": media,
        "disk_model": clean_text(str(d.get("model") or "")),
        "link": link,
    }


def _linux_disk(target: str) -> Dict[str, Any]:
    fs_line = run(["findmnt", "-no", "FSTYPE,SOURCE", "--target", target]).split()
    fstype, source = (fs_line + ["", ""])[:2]
    try:
        tree = json.loads(run(["lsblk", "-sJno", "NAME,TYPE,MODEL,ROTA,TRAN", source]) or "{}")
    except json.JSONDecodeError:
        tree = {}
    disks: List[Dict[str, Any]] = []

    def walk(nodes: List[Dict[str, Any]]) -> None:
        for n in nodes:
            if n.get("type") == "disk":
                disks.append(n)
            walk(n.get("children") or [])

    walk(tree.get("blockdevices", []))
    info: Dict[str, Any] = {
        "fs": fstype.lower(),
        "bus": "unknown",
        "media": "unknown",
        "disk_model": "unknown",
        "link": "unknown",
    }
    if not disks:
        return info
    disk = disks[0]
    name = str(disk.get("name", ""))
    info["disk_model"] = clean_text(str(disk.get("model") or ""))
    info["media"] = "hdd" if disk.get("rota") in (True, "1", 1) else "ssd"
    tran = str(disk.get("tran") or "").lower()
    info["bus"] = "nvme" if name.startswith("nvme") else (tran or "unknown")
    sys_dev = Path("/sys/block") / name / "device"
    try:
        if info["bus"] == "nvme":
            pci = (sys_dev / "device").resolve()
            speed = (pci / "current_link_speed").read_text().split()[0]
            width = (pci / "current_link_width").read_text().strip()
            info["link"] = pcie_link(float(speed), int(width) if width.isdigit() else None)
        elif info["bus"] == "sata":
            m = re.search(r"/ata(\d+)/", str(sys_dev.resolve()))
            spd = Path(f"/sys/class/ata_link/link{m.group(1)}/sata_spd").read_text().strip() if m else ""
            num = re.match(r"([\d.]+)", spd)
            info["link"] = f"SATA {float(num.group(1)):g} Gb/s" if num else "SATA"
        elif info["bus"] == "sas":
            rates = [p.read_text().strip() for p in Path("/sys/class/sas_phy").glob("*/negotiated_linkrate")]
            num = re.match(r"([\d.]+)", rates[0]) if rates else None
            info["link"] = f"SAS {float(num.group(1)):g} Gb/s" if num else "SAS"
        elif info["bus"] == "usb":
            info["link"] = "USB"
    except (OSError, ValueError, AttributeError):
        info["link"] = {"nvme": "PCIe", "sata": "SATA", "sas": "SAS", "usb": "USB"}.get(info["bus"], "unknown")
    return info


def _macos_disk(target: str) -> Dict[str, Any]:
    out = subprocess.run(["diskutil", "info", "-plist", target], capture_output=True).stdout
    d = plistlib.loads(out) if out else {}
    proto = str(d.get("BusProtocol", "")).lower()
    bus = {"pci-express": "nvme", "apple fabric": "nvme", "sata": "sata", "usb": "usb"}.get(proto, "other")
    media = "ssd" if d.get("SolidState") else ("hdd" if "SolidState" in d else "unknown")
    link = "unknown"
    if bus == "nvme":
        link = "PCIe"
        try:
            nvme = json.loads(run(["system_profiler", "SPNVMeDataType", "-json"]) or "{}")
            for ctrl in nvme.get("SPNVMeDataType", []):
                speed = re.match(r"([\d.]+)", str(ctrl.get("spnvme_linkspeed", "")))
                width = re.search(r"(\d+)", str(ctrl.get("spnvme_linkwidth", "")))
                if speed:
                    link = pcie_link(float(speed.group(1)), int(width.group(1)) if width else None)
                    break
        except (json.JSONDecodeError, ValueError):
            pass
    elif bus == "sata":
        link = "SATA"
    elif bus == "usb":
        link = "USB"
    return {
        "fs": str(d.get("FilesystemType", "")).lower(),
        "bus": bus,
        "media": media,
        "disk_model": clean_text(str(d.get("MediaName", ""))),
        "link": link,
    }


def disk_info(os_key: str, target: str) -> Dict[str, Any]:
    try:
        if os_key == "windows":
            info = _windows_disk(target)
        elif os_key == "linux":
            info = _linux_disk(target)
        elif os_key == "macos":
            info = _macos_disk(target)
        else:
            info = {}
    except (OSError, ValueError):
        info = {}
    info.setdefault("fs", "other")
    info.setdefault("bus", "unknown")
    info.setdefault("media", "unknown")
    info.setdefault("disk_model", "unknown")
    info.setdefault("link", "unknown")
    info["kind"] = disk_kind(info["bus"], info["media"])
    return info
