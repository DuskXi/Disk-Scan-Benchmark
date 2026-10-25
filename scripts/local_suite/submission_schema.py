"""
Schema of a community submission (a benchmark of real drives on the submitter's own machine) and its validator.

A submission carries numbers, scanner ids from the registry, and a few short hardware strings. It never carries
paths, drive letters, volume labels, host or user names, or serial numbers: the builder only copies whitelisted
fields, and the validator rejects anything outside the schema, so a mistake on either side cannot leak more.
"""

import re
from typing import Any, Dict, List, Set, Tuple

SCHEMA = "dsb-local-1"
OS_VALUES = {"windows", "linux", "macos"}
ARCH_VALUES = {"x86_64", "aarch64"}
FS_VALUES = {
    "ntfs",
    "refs",
    "exfat",
    "fat32",
    "ext4",
    "ext3",
    "btrfs",
    "xfs",
    "zfs",
    "f2fs",
    "bcachefs",
    "apfs",
    "hfs+",
    "other",
}
MEDIA_VALUES = {"ssd", "hdd", "unknown"}
BUS_VALUES = {"nvme", "sata", "sas", "usb", "scsi", "virtual", "other", "unknown"}
# Hardware names: letters, digits, spaces and a little punctuation; no path separators, colons or @
TEXT_RE = re.compile(r"^[A-Za-z0-9 ()._+,#-]{1,64}$")
VERSION_RE = re.compile(r"^[A-Za-z0-9 ()._+,-]{1,64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

TOP_KEYS = {"schema", "suite", "date", "machine", "volumes"}
MACHINE_KEYS = {"os", "os_version", "arch", "cpu", "logical_cores", "ram_gb"}
VOLUME_KEYS = {"fs", "media", "bus", "disk_model", "size_gb", "used_gb", "items_k", "cold_purged", "results"}
RESULT_KEYS = {
    "scanner",
    "version",
    "cold_ms",
    "warm_ms",
    "warm_runs_ms",
    "peak_rss_mb",
    "cpu_s",
    "reads",
    "size_gb",
    "files_k",
}


def _num(v: Any, lo: float, hi: float) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and lo <= v <= hi


def validate(sub: Any, scanner_ids: Set[str]) -> Tuple[List[str], List[str]]:
    """Returns (errors, warnings). Any error rejects the submission."""
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(sub, dict):
        return ["the submission is not a JSON object"], []

    def keys(obj: Dict[str, Any], allowed: Set[str], where: str) -> None:
        extra = set(obj) - allowed
        if extra:
            errors.append(f"{where}: fields not allowed in a submission: {', '.join(sorted(extra))}")

    keys(sub, TOP_KEYS, "submission")
    if sub.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA!r}")
    if not isinstance(sub.get("suite"), str) or not VERSION_RE.match(sub.get("suite", "")):
        errors.append("suite: missing or not a plain version string")
    if not isinstance(sub.get("date"), str) or not DATE_RE.match(sub.get("date", "")):
        errors.append("date must be YYYY-MM-DD")

    m = sub.get("machine")
    if not isinstance(m, dict):
        errors.append("machine: missing")
    else:
        keys(m, MACHINE_KEYS, "machine")
        if m.get("os") not in OS_VALUES:
            errors.append(f"machine.os must be one of {sorted(OS_VALUES)}")
        if m.get("arch") not in ARCH_VALUES:
            errors.append(f"machine.arch must be one of {sorted(ARCH_VALUES)}")
        for key, rx in (("os_version", VERSION_RE), ("cpu", TEXT_RE)):
            if not isinstance(m.get(key), str) or not rx.match(m.get(key, "")):
                errors.append(f"machine.{key}: missing or contains characters that are not allowed")
        if not _num(m.get("logical_cores"), 1, 1024):
            errors.append("machine.logical_cores out of range")
        if not _num(m.get("ram_gb"), 1, 65536):
            errors.append("machine.ram_gb out of range")

    vols = sub.get("volumes")
    if not isinstance(vols, list) or not 1 <= len(vols) <= 16:
        errors.append("volumes: need 1 to 16 entries")
        vols = []
    for i, v in enumerate(vols):
        where = f"volumes[{i}]"
        if not isinstance(v, dict):
            errors.append(f"{where}: not an object")
            continue
        keys(v, VOLUME_KEYS, where)
        if v.get("fs") not in FS_VALUES:
            errors.append(f"{where}.fs must be one of {sorted(FS_VALUES)}")
        if v.get("media") not in MEDIA_VALUES:
            errors.append(f"{where}.media must be one of {sorted(MEDIA_VALUES)}")
        if v.get("bus") not in BUS_VALUES:
            errors.append(f"{where}.bus must be one of {sorted(BUS_VALUES)}")
        if not isinstance(v.get("disk_model"), str) or not TEXT_RE.match(v.get("disk_model", "")):
            errors.append(f"{where}.disk_model: missing or contains characters that are not allowed")
        for key, hi in (("size_gb", 10**6), ("used_gb", 10**6), ("items_k", 10**7)):
            if not _num(v.get(key), 0, hi):
                errors.append(f"{where}.{key} out of range")
        if not isinstance(v.get("cold_purged"), bool):
            errors.append(f"{where}.cold_purged must be true or false")
        results = v.get("results")
        if not isinstance(results, list) or not results:
            errors.append(f"{where}.results: need at least one scanner result")
            continue
        files = []
        for j, r in enumerate(results):
            rw = f"{where}.results[{j}]"
            if not isinstance(r, dict):
                errors.append(f"{rw}: not an object")
                continue
            keys(r, RESULT_KEYS, rw)
            if r.get("scanner") not in scanner_ids:
                errors.append(f"{rw}.scanner {r.get('scanner')!r} is not in the scanner registry")
            if not isinstance(r.get("version"), str) or not VERSION_RE.match(r.get("version", "")):
                errors.append(f"{rw}.version: not a plain version string")
            if not _num(r.get("cold_ms"), 1, 86_400_000) or not _num(r.get("warm_ms"), 1, 86_400_000):
                errors.append(f"{rw}: cold_ms / warm_ms out of range")
            runs = r.get("warm_runs_ms")
            if not isinstance(runs, list) or not 1 <= len(runs) <= 20 or not all(_num(x, 1, 86_400_000) for x in runs):
                errors.append(f"{rw}.warm_runs_ms: 1 to 20 positive numbers")
            for key, hi in (
                ("peak_rss_mb", 10**6),
                ("cpu_s", 10**7),
                ("reads", 10**12),
                ("size_gb", 10**6),
                ("files_k", 10**7),
            ):
                if r.get(key) is not None and not _num(r.get(key), 0, hi):
                    errors.append(f"{rw}.{key} out of range")
            if _num(r.get("files_k"), 0.001, 10**7):  # 0 = the tool reports no file count
                files.append(float(r["files_k"]))
            if _num(r.get("cold_ms"), 1, 1e9) and _num(r.get("warm_ms"), 1, 1e9) and r["cold_ms"] < 0.5 * r["warm_ms"]:
                warnings.append(f"{rw}: cold scan faster than half the warm scan; the cache was probably not purged")
        if len(files) >= 3:
            med = sorted(files)[len(files) // 2]
            for j, r in enumerate(results):
                f = r.get("files_k") if isinstance(r, dict) else None
                if med > 0 and isinstance(f, (int, float)) and f > 0 and abs(float(f) - med) / med > 0.10:
                    warnings.append(
                        f"{where}.results[{j}] ({r.get('scanner')}): file count {f}k differs from the "
                        f"other scanners' median {med}k by more than 10%"
                    )
        if v.get("cold_purged") is False:
            warnings.append(f"{where}: the file cache could not be purged, so cold times are really warm times")
    return errors, warnings
