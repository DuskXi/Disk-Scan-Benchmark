#!/usr/bin/env python3
"""
Unified Cross-Platform Disk Scanner Benchmark Runner & Installer
Reads scanner definitions & pinned versions from scripts/wrappers/scanners_registry.json,
executes Cold Cache (with disk-mgr purge-cache) and Warm Cache (3x average) runs,
collects Peak RSS (MB) and Scanned Size / File Count, and outputs raw_results.json.
"""

import argparse
import csv
import ctypes
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def windows_native_machine() -> Optional[str]:
    """Native CPU of a Windows host, which an x64 Python emulated on Windows on ARM would report as AMD64."""
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        process_machine = ctypes.c_ushort(0)
        native_machine = ctypes.c_ushort(0)
        ok = kernel32.IsWow64Process2(
            ctypes.c_void_p(kernel32.GetCurrentProcess()), ctypes.byref(process_machine), ctypes.byref(native_machine)
        )
    except (AttributeError, OSError):
        return None
    if not ok:
        return None
    return {0xAA64: "arm64", 0x8664: "amd64"}.get(native_machine.value)


def detect_os_arch() -> Tuple[str, str]:
    sys_name = platform.system().lower()
    if sys_name.startswith("linux"):
        os_key = "linux"
    elif sys_name.startswith("darwin"):
        os_key = "macos"
    elif sys_name.startswith("win"):
        os_key = "windows"
    else:
        os_key = sys_name

    machine = platform.machine().lower()
    if os_key == "windows":
        machine = windows_native_machine() or machine
    if machine in ("x86_64", "amd64"):
        arch_key = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch_key = "aarch64"
    else:
        arch_key = machine

    return os_key, arch_key


def parse_human_size_to_bytes(text: str, scanner_id: str = "") -> int:
    """
    Extracts byte size from CLI output of gdu, dua, or dust.
    - gdu -n: outputs one line per top-level entry (e.g. '  10.0 GiB /zone_sparse_media'), so we sum all entry lines.
    - dust -d 1: outputs a root summary on the last line using 'Ti', 'Gi', 'Mi', 'Ki', 'B'.
    - dua: outputs a '... total' summary on the last line.
    """
    ansi_re = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
    clean = ansi_re.sub("", text).replace("\r", "\n")
    lines = [ln.strip() for ln in clean.splitlines() if ln.strip()]
    if not lines:
        return 0

    pattern = re.compile(
        r"([0-9]+(?:\.[0-9]+)?)\s*(TiB|GiB|MiB|KiB|Ti|Gi|Mi|Ki|TB|GB|MB|KB|T|G|M|K|B)\b",
        re.IGNORECASE,
    )
    multipliers = {
        "b": 1,
        "k": 1024,
        "kb": 1000,
        "ki": 1024,
        "kib": 1024,
        "m": 1024**2,
        "mb": 1000**2,
        "mi": 1024**2,
        "mib": 1024**2,
        "g": 1024**3,
        "gb": 1000**3,
        "gi": 1024**3,
        "gib": 1024**3,
        "t": 1024**4,
        "tb": 1000**4,
        "ti": 1024**4,
        "tib": 1024**4,
    }

    if scanner_id == "gdu":
        gdu_line_re = re.compile(
            r"([0-9]+(?:\.[0-9]+)?)\s*(TiB|GiB|MiB|KiB|TB|GB|MB|KB|B)\s+/",
            re.IGNORECASE,
        )
        total_b = 0
        for line in lines:
            m = gdu_line_re.search(line)
            if m:
                val = float(m.group(1))
                unit = m.group(2).lower()
                total_b += int(val * multipliers.get(unit, 1))
        if total_b > 0:
            return total_b

    for line in reversed(lines):
        m = pattern.search(line)
        if m:
            val = float(m.group(1))
            unit = m.group(2).lower()
            return int(val * multipliers.get(unit, 1))
    return 0


def parse_spaceknife_scan_ms(text: str) -> Optional[float]:
    """
    Extracts the scan duration SpaceKnife reports about itself ("Time 85 ms" / "用时 85 毫秒"). It excludes process
    start-up, so comparing it with the wall-clock time shows how much fixed overhead a small preset contains.
    """
    clean = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text).replace("\r", "\n")
    m = re.search(
        r"(?:Time|Duration|Elapsed|用时)\s+([0-9][0-9,]*(?:\.[0-9]+)?)\s*(ms|milliseconds?|毫秒|secs?|seconds?|秒|s)\b",
        clean,
        re.IGNORECASE,
    )
    if not m:
        return None
    value = float(m.group(1).replace(",", ""))
    unit = m.group(2).lower()
    return value if unit in ("ms", "毫秒") or unit.startswith("milli") else value * 1000.0


def parse_squirreldisk_json(text: str) -> Tuple[int, int, Dict[str, Dict[str, Any]]]:
    """
    Parses `squirreldisk scan <path> --json`: the root node's `size` (bytes on disk; on Windows the logical size
    rounded up to 4 KiB clusters, files <= 700 B counted as resident) and `files`, plus its children as zone samples.
    """
    start = text.find("{")
    if start < 0:
        return 0, 0, {}
    try:
        root = json.loads(text[start:])
    except json.JSONDecodeError:
        return 0, 0, {}
    zones: Dict[str, Dict[str, Any]] = {}
    for child in root.get("children") or []:
        name = str(child.get("name", "")).rstrip("/\\")
        if child.get("kind") in ("dir", "mount") and name:
            zones[name] = {"allocated_bytes": int(child.get("size", 0)), "files": int(child.get("files", 0))}
    return int(root.get("size", 0)), int(root.get("files", 0)), zones


def spaceknife_mft_fallback(text: str) -> Optional[str]:
    """
    For `scan --mft`: None when SpaceKnife read the volume's $MFT ("Method MFT quick scan" / "方式 MFT 快速扫描"),
    else why it fell back to a full scan. Anchored on the method line: the note under a full scan also mentions the
    MFT quick scan.
    """
    clean = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text).replace("\r", "\n")
    if re.search(r"(?:Method|方式)\s+MFT\s*(?:quick scan|快速扫描)", clean):
        return None
    m = re.search(r"Method full scan \((.*?)\)|方式\s*硬扫描（(.*?)）", clean, re.DOTALL)
    if m:
        return " ".join((m.group(1) or m.group(2) or "").split()) or "no reason given"
    return "no scan method line in the output"


def parse_spaceknife_subtree(text: str, name: str, os_key: str) -> Tuple[int, int]:
    """
    Size on disk and file count of one first-level row of the `scan` summary table ("▸ bench  512.3 GB  98.1% ███ 1,000,006").
    An MFT scan has to be pointed at the volume root, so the benchmark subtree is read from its row.
    """
    clean = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text).replace("\r", "\n")
    base = 1000 if os_key == "macos" else 1024
    units = {"b": 1, "kb": base, "mb": base**2, "gb": base**3, "tb": base**4, "pb": base**5}
    units.update({"kib": 1024, "mib": 1024**2, "gib": 1024**3, "tib": 1024**4, "pib": 1024**5})
    row_re = re.compile(
        rf"^[\s│▸▾]*{re.escape(name)}\s+([0-9]+(?:\.[0-9]+)?)\s*(PiB|TiB|GiB|MiB|KiB|PB|TB|GB|MB|KB|B)\s+"
        r"[0-9.]+%(.*)$",
        re.IGNORECASE | re.MULTILINE,
    )
    m = row_re.search(clean)
    if not m:
        return 0, 0
    # the file count is the last column; a table wider than the console crops it ("200,0…"): count unknown then
    files = re.search(r"([0-9][0-9,]*)$", m.group(3).strip())
    return int(float(m.group(1)) * units.get(m.group(2).lower(), 1)), (
        int(files.group(1).replace(",", "")) if files else 0
    )


def parse_spaceknife_output(text: str, effective_metric: str, os_key: str) -> Tuple[int, int]:
    """
    Parses `spaceknife-backend scan <path> --no-snapshot` summary panel output.
    Extracts:
      - `Size on disk <val> <unit>` (or `占用 <val> <unit>`) -> allocated bytes
      - `Logical size <val> <unit>` (or `逻辑大小 <val> <unit>`) -> apparent bytes
      - `files <N>` (or `文件 <N>`) -> scanned file count
    Note: SpaceKnife uses binary 1024 multiples for KB/MB/GB/TB on Windows and Linux, and 1000 on macOS.
    """
    ansi_re = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
    clean = ansi_re.sub("", text).replace("\r", "\n")

    base = 1000 if os_key == "macos" else 1024
    unit_map = {
        "b": 1,
        "kb": base,
        "kib": 1024,
        "mb": base**2,
        "mib": 1024**2,
        "gb": base**3,
        "gib": 1024**3,
        "tb": base**4,
        "tib": 1024**4,
        "pb": base**5,
        "pib": 1024**5,
    }

    alloc_re = re.compile(
        r"(?:Size on disk|占用)\s+([0-9]+(?:\.[0-9]+)?)\s*(PiB|TiB|GiB|MiB|KiB|PB|TB|GB|MB|KB|B)\b",
        re.IGNORECASE,
    )
    logical_re = re.compile(
        r"(?:Logical size|逻辑大小)\s+([0-9]+(?:\.[0-9]+)?)\s*(PiB|TiB|GiB|MiB|KiB|PB|TB|GB|MB|KB|B)\b",
        re.IGNORECASE,
    )
    files_re = re.compile(r"(?:files|文件)\s+([0-9,]+)", re.IGNORECASE)

    alloc_bytes = 0
    logical_bytes = 0
    scanned_files = 0

    m_alloc = alloc_re.search(clean)
    if m_alloc:
        alloc_bytes = int(float(m_alloc.group(1)) * unit_map.get(m_alloc.group(2).lower(), 1))

    m_logical = logical_re.search(clean)
    if m_logical:
        logical_bytes = int(float(m_logical.group(1)) * unit_map.get(m_logical.group(2).lower(), 1))

    m_files = files_re.search(clean)
    if m_files:
        try:
            scanned_files = int(m_files.group(1).replace(",", ""))
        except ValueError:
            scanned_files = 0

    chosen_bytes = logical_bytes if effective_metric == "apparent" else alloc_bytes
    if chosen_bytes == 0:
        chosen_bytes = alloc_bytes or logical_bytes
    return chosen_bytes, scanned_files


def find_subtree_row(rows: List[List[str]], scan_path: str) -> Optional[List[str]]:
    """Returns the CSV row whose path equals scan_path (case-insensitive, trailing separators ignored)."""
    target = str(Path(scan_path).resolve()).rstrip("\\/").lower()
    for row in rows:
        if row and row[0].strip().rstrip("\\/").lower() == target:
            return row
    return None


def effective_size_metric(scanner: Dict[str, Any], os_key: str) -> str:
    """'apparent' where a scanner can only report logical sizes on this OS ("apparent_on"), else its size_metric."""
    if os_key in scanner.get("apparent_on", []):
        return "apparent"
    return str(scanner.get("size_metric", "allocated"))


def command_template_for(scanner: Dict[str, Any], os_key: str) -> List[str]:
    """The scanner's command line, with an optional per-OS override ("command_template_by_os")."""
    return list(scanner.get("command_template_by_os", {}).get(os_key, scanner["command_template"]))


def reference_bytes(gt_data: Dict[str, Any], scanner: Dict[str, Any], metric: str, os_key: str) -> int:
    """Ground-truth size a scanner is compared against, honoring how the scanner accounts for allocation."""
    if metric == "apparent":
        return int(gt_data.get("apparent_size_bytes", 0))
    if os_key in scanner.get("excludes_dir_blocks", []):
        files_only = int(gt_data.get("allocated_files_only_bytes", 0))
        if files_only > 0:
            return files_only
    return int(gt_data.get("allocated_size_bytes", 0))


def parse_wiztree_csv(
    csv_path: Path, scan_path: str = "", subtree_totals: bool = False
) -> Tuple[int, int, int, Dict[str, Dict[str, Any]]]:
    """
    Parses WizTree CSV export to return (apparent_bytes, allocated_bytes, scanned_files, sampled_zones).
    WizTree CSV header:
      Line 0: Generated by WizTree ...
      Line 1: File Name,Size,Allocated,Modified,Attributes,Files,Folders,...
      Line 2: "X:\bench\",<Size>,<Allocated>,<Modified>,<Attributes>,<Files>,<Folders>,...
    """
    if not csv_path.exists():
        return 0, 0, 0, {}

    with open(csv_path, "r", encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.reader(f))

    if len(rows) < 2:
        return 0, 0, 0, {}

    # Skip banner if present (Line 0 may start with 'Generated by' or '生成由')
    header_idx = 0
    if len(rows) > 1 and (
        "wiztree" in rows[0][0].lower() or "大小" in rows[1] or "size" in [c.lower() for c in rows[1]]
    ):
        header_idx = 1

    root_idx = header_idx + 1
    if root_idx >= len(rows):
        return 0, 0, 0, {}

    apparent = 0
    allocated = 0
    files = 0
    root_row = rows[root_idx]
    if subtree_totals and scan_path:
        # Volume-root scan (MFT mode): report totals of the benchmark subtree, not of the whole volume
        root_row = find_subtree_row(rows[root_idx:], scan_path) or root_row
    try:
        apparent = int(root_row[1].strip())
        allocated = int(root_row[2].strip())
        files = int(root_row[5].strip())
    except (IndexError, ValueError):
        pass

    norm_scan_path = str(Path(scan_path).resolve()).rstrip("\\/") if scan_path else ""
    sampled_zones: Dict[str, Dict[str, Any]] = {}

    for row in rows[root_idx + 1 :]:
        if not row:
            continue
        p = row[0].strip().rstrip("\\/")
        if norm_scan_path:
            try:
                rel = os.path.relpath(p, norm_scan_path)
                parts = rel.replace("\\", "/").split("/")
                if len(parts) == 1 and parts[0] != ".":
                    zone_name = parts[0]
                    z_app = int(row[1].strip()) if len(row) > 1 and row[1].strip().isdigit() else 0
                    z_alloc = int(row[2].strip()) if len(row) > 2 and row[2].strip().isdigit() else 0
                    z_files = int(row[5].strip()) if len(row) > 5 and row[5].strip().isdigit() else 0
                    sampled_zones[zone_name] = {
                        "apparent_bytes": z_app,
                        "allocated_bytes": z_alloc,
                        "files": z_files,
                    }
            except Exception:
                pass

    return apparent, allocated, files, sampled_zones


def parse_windirstat_csv(
    csv_path: Path, scan_path: str = "", subtree_totals: bool = False
) -> Tuple[int, int, int, Dict[str, Dict[str, Any]]]:
    """
    Parses WinDirStat CSV export (/SaveTo <OutputFile>) to return:
    (apparent_bytes, allocated_bytes, scanned_files, sampled_zones).
    WinDirStat CSV header:
      Line 0: "Name","Files","Folders","Logical Size","Physical Size","Attributes",...
      Line 1: "<scan_path>",<Files>,<Folders>,<Logical Size>,<Physical Size>,...
    """
    if not csv_path.exists():
        return 0, 0, 0, {}

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))

    if len(rows) < 2:
        return 0, 0, 0, {}

    root_row = rows[1]
    if subtree_totals and scan_path:
        root_row = find_subtree_row(rows[1:], scan_path) or root_row
    logical_bytes = 0
    physical_bytes = 0
    total_files = 0
    try:
        total_files = int(root_row[1].strip())
        logical_bytes = int(root_row[3].strip())
        physical_bytes = int(root_row[4].strip())
    except (IndexError, ValueError):
        pass

    norm_scan_path = str(Path(scan_path).resolve()).rstrip("\\/") if scan_path else ""
    sampled_zones: Dict[str, Dict[str, Any]] = {}

    for row in rows[2:]:
        if not row:
            continue
        p = row[0].strip().rstrip("\\/")
        if norm_scan_path:
            try:
                rel = os.path.relpath(p, norm_scan_path)
                parts = rel.replace("\\", "/").split("/")
                if len(parts) == 1 and parts[0] != ".":
                    zone_name = parts[0]
                    z_files = int(row[1].strip()) if len(row) > 1 and row[1].strip().isdigit() else 0
                    z_app = int(row[3].strip()) if len(row) > 3 and row[3].strip().isdigit() else 0
                    z_alloc = int(row[4].strip()) if len(row) > 4 and row[4].strip().isdigit() else 0
                    sampled_zones[zone_name] = {
                        "apparent_bytes": z_app,
                        "allocated_bytes": z_alloc,
                        "files": z_files,
                    }
            except Exception:
                pass

    return logical_bytes, physical_bytes, total_files, sampled_zones


def _zone_of(path_text: str) -> Optional[str]:
    name = re.split(r"[\\/]", path_text.strip().rstrip("\\/"))[-1]
    return name if name.startswith("zone_") else None


def parse_du_lines(text: str, scan_path: str, unit: int) -> Tuple[int, Dict[str, Dict[str, Any]]]:
    """
    GNU `du -B1 -d 1` (unit 1) or BSD `du -k -d 1` (unit 1024): "<size>\t<path>" per line, the scanned root last.
    Returns (root bytes, top-level zones).
    """
    root = os.path.normpath(scan_path)
    total = 0
    zones: Dict[str, Dict[str, Any]] = {}
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)\s+(.+?)\s*$", line)
        if not m:
            continue
        size, path_text = int(m.group(1)) * unit, m.group(2)
        if os.path.normpath(path_text) == root:
            total = size
        elif (zone := _zone_of(path_text)) is not None:
            zones[zone] = {"allocated_bytes": size}
    if total == 0:
        sizes = [int(m.group(1)) * unit for m in re.finditer(r"(?m)^\s*(\d+)\s+", text)]
        total = sizes[-1] if sizes else 0
    return total, zones


def parse_sysinternals_du_csv(text: str, scan_path: str, metric: str) -> Tuple[int, int, Dict[str, Dict[str, Any]]]:
    """
    Sysinternals `du -c -l 1`: CSV with Path,CurrentFileCount,CurrentFileSize,FileCount,DirectoryCount,DirectorySize,
    DirectorySizeOnDisk. The root row (or, failing a path match, the largest row) is the total.
    Returns (bytes, files, zones).
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    start = next((i for i, ln in enumerate(lines) if "DirectorySize" in ln and "Path" in ln), None)
    if start is None:
        return 0, 0, {}
    rows = list(csv.DictReader(lines[start:]))
    size_col = "DirectorySize" if metric == "apparent" else "DirectorySizeOnDisk"
    root = os.path.normcase(os.path.normpath(scan_path))
    best: Optional[Dict[str, str]] = None
    zones: Dict[str, Dict[str, Any]] = {}

    def num(row: Dict[str, str], key: str) -> int:
        try:
            return int(str(row.get(key) or "0").replace(",", "").strip())
        except ValueError:
            return 0

    for row in rows:
        path_text = str(row.get("Path") or "").strip().strip('"')
        if os.path.normcase(os.path.normpath(path_text)) == root:
            best = row
        elif (zone := _zone_of(path_text)) is not None:
            zones[zone] = {("apparent_bytes" if metric == "apparent" else "allocated_bytes"): num(row, size_col)}
    if best is None and rows:
        best = max(rows, key=lambda r: num(r, size_col))
    if best is None:
        return 0, 0, zones
    return num(best, size_col), num(best, "FileCount"), zones


def parse_pdu_json(text: str, metric: str) -> Tuple[int, Dict[str, Dict[str, Any]]]:
    """pdu --json-output: {"tree": {"name", "size", "children": [...]}}; children are the top-level entries."""
    start = text.find("{")
    if start < 0:
        return 0, {}
    try:
        data = json.loads(text[start:])
    except json.JSONDecodeError:
        return 0, {}
    tree = data.get("tree", data)
    key = "apparent_bytes" if metric == "apparent" else "allocated_bytes"
    zones = {}
    for child in tree.get("children", []) or []:
        if (zone := _zone_of(str(child.get("name", "")))) is not None:
            zones[zone] = {key: int(child.get("size", 0))}
    return int(tree.get("size", 0)), zones


def parse_bare_integer(text: str) -> int:
    """diskus prints only the byte count when stdout is not a terminal."""
    nums = re.findall(r"(?m)^\s*(\d+)\s*$", text)
    return int(nums[-1]) if nums else 0


def parse_erdtree(text: str, scan_path: str) -> Tuple[int, int, Dict[str, Dict[str, Any]]]:
    """
    erdtree `-y iflat -L 1` without --human: "<n> <unit>   <name>" per entry with the root first, then a
    "<d> directories, <f> files" summary. Returns (root bytes, files, zones).
    """
    units = {
        "B": 1,
        "KB": 1000,
        "MB": 1000**2,
        "GB": 1000**3,
        "TB": 1000**4,
        "KIB": 1024,
        "MIB": 1024**2,
        "GIB": 1024**3,
        "TIB": 1024**4,
    }
    ansi = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
    root_name = os.path.basename(os.path.normpath(scan_path))
    entries: List[Tuple[int, str]] = []
    files = 0
    for raw in text.splitlines():
        line = ansi.sub("", raw)
        m = re.match(r"^\s*([\d.]+)\s*([KMGT]?i?B)\s+(.+?)\s*$", line, re.IGNORECASE)
        if m:
            size = int(float(m.group(1)) * units.get(m.group(2).upper(), 1))
            entries.append((size, m.group(3)))
            continue
        s = re.search(r"([\d,]+)\s+files?", line)
        if s and "director" in line:
            files = int(s.group(1).replace(",", ""))
    if not entries:
        return 0, files, {}
    root = next((size for size, name in entries if os.path.basename(name.rstrip("\\/")) == root_name), None)
    total = root if root is not None else max(size for size, _ in entries)
    zones = {z: {"allocated_bytes": size} for size, name in entries if (z := _zone_of(name)) is not None}
    return total, files, zones


def parse_ncdu_export(path: Path, metric: str) -> Tuple[int, int, Dict[str, Dict[str, Any]]]:
    """
    ncdu's JSON export: [1, 2, {meta}, [{root}, {file}, [{dir}, ...], ...]]. Walked object by object, so a tree of
    millions of entries never becomes millions of Python dicts at once. Hard links (hlnkc) count once per inode.
    Returns (bytes, files, zones).
    """
    if not path.exists():
        return 0, 0, {}
    text = path.read_text(encoding="utf-8", errors="replace")
    dec = json.JSONDecoder()
    key = "asize" if metric == "apparent" else "dsize"
    zkey = "apparent_bytes" if metric == "apparent" else "allocated_bytes"
    i, n = 0, len(text)
    depth = 0  # 1 = the export's outer array, 2 = the scanned root's list, 3 = a top-level folder's list
    first_in_list = False
    zone_stack: List[Optional[str]] = []
    seen: set = set()
    total = files = 0
    zones: Dict[str, Dict[str, Any]] = {}
    while i < n:
        c = text[i]
        if c == "[":
            depth += 1
            first_in_list = True
            i += 1
        elif c == "]":
            depth -= 1
            if zone_stack:
                zone_stack.pop()
            i += 1
        elif c == "{":
            obj, i = dec.raw_decode(text, i)
            if depth < 1 or "name" not in obj:
                first_in_list = False
                continue  # the metadata object
            size = int(obj.get(key, 0) or 0)
            if obj.get("hlnkc"):
                ident = (obj.get("dev"), obj.get("ino"))
                size = 0 if ident in seen else size
                seen.add(ident)
            if first_in_list:  # a directory's own entry
                name = str(obj["name"])
                zone_stack.append(name if depth == 3 and name.startswith("zone_") else None)
            else:
                files += 1
                if depth == 2 and str(obj["name"]).startswith("zone_"):
                    zones.setdefault(str(obj["name"]), {zkey: 0, "files": 0})
            total += size
            zone = next((z for z in zone_stack if z), None)
            if zone:
                entry = zones.setdefault(zone, {zkey: 0, "files": 0})
                entry[zkey] += size
                entry["files"] += 0 if first_in_list else 1
            first_in_list = False
        else:
            i += 1
    return total, files, zones


def parse_cli_structure_samples(stdout_text: str, scanner_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts top-level zone breakdown from CLI output.
    """
    ansi_re = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
    clean = ansi_re.sub("", stdout_text).replace("\r", "\n")

    multipliers = {
        "b": 1,
        "k": 1024,
        "kb": 1000,
        "ki": 1024,
        "kib": 1024,
        "m": 1024**2,
        "mb": 1000**2,
        "mi": 1024**2,
        "mib": 1024**2,
        "g": 1024**3,
        "gb": 1000**3,
        "gi": 1024**3,
        "gib": 1024**3,
        "t": 1024**4,
        "tb": 1000**4,
        "ti": 1024**4,
        "tib": 1024**4,
    }

    def _to_bytes(v_str: str, u_str: str) -> int:
        try:
            return int(float(v_str) * multipliers.get(u_str.lower(), 1))
        except ValueError:
            return 0

    sampled_zones: Dict[str, Dict[str, Any]] = {}
    if scanner_id == "gdu":
        for m in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]+)\s+/(zone_[a-zA-Z0-9_]+|[a-zA-Z0-9_-]+)", clean):
            z_name = m.group(3)
            sampled_zones[z_name] = {"apparent_bytes": _to_bytes(m.group(1), m.group(2))}
    elif scanner_id == "dua":
        for m in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]+)\s+(zone_[a-zA-Z0-9_]+|[a-zA-Z0-9_-]+)", clean):
            z_name = m.group(3)
            if z_name != "total":
                sampled_zones[z_name] = {"apparent_bytes": _to_bytes(m.group(1), m.group(2))}
    elif scanner_id == "dust":
        for m in re.finditer(
            r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]+)\s+[┌├─│\s]+(zone_[a-zA-Z0-9_]+|[a-zA-Z0-9_-]+)", clean
        ):
            z_name = m.group(3)
            sampled_zones[z_name] = {"apparent_bytes": _to_bytes(m.group(1), m.group(2))}
    elif scanner_id == "spaceknife":
        for z in ("zone_sparse_media", "zone_deep", "zone_flat_cache", "zone_edge"):
            if z in clean:
                sampled_zones[z] = {"detected": True}

    return sampled_zones


def query_windows_peak_rss_mb(process_handle: int) -> float:
    """
    Queries PROCESS_MEMORY_COUNTERS.PeakWorkingSetSize on Windows via ctypes.
    """

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    pmc = PROCESS_MEMORY_COUNTERS()
    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    res = ctypes.windll.psapi.GetProcessMemoryInfo(
        ctypes.c_void_p(process_handle),
        ctypes.byref(pmc),
        pmc.cb,
    )
    if res != 0:
        return round(pmc.PeakWorkingSetSize / (1024.0 * 1024.0), 2)
    return 0.0


def children_cpu_seconds() -> float:
    """User + system CPU seconds of all waited-for child processes so far (Unix; 0 on Windows)."""
    try:
        import resource

        r = resource.getrusage(resource.RUSAGE_CHILDREN)  # type: ignore[attr-defined]
        return float(r.ru_utime + r.ru_stime)
    except Exception:
        return 0.0


def children_written_bytes() -> Optional[int]:
    """
    Linux: bytes all waited-for children sent to the storage layer so far (ru_oublock counts 512-byte units there).
    Pipes and tmpfs never reach the storage layer, so the captured output is not in it (tmpfs: see shmem_kib).
    """
    try:
        import resource

        return int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_oublock) * 512  # type: ignore[attr-defined]
    except Exception:
        return None


def shmem_kib() -> Optional[int]:
    """Linux: RAM held by tmpfs files (/dev/shm, a tmpfs /tmp) and shared anonymous memory, system-wide."""
    try:
        with open("/proc/meminfo", encoding="ascii") as f:
            for line in f:
                if line.startswith("Shmem:"):
                    return int(line.split()[1])
    except Exception:
        return None
    return None


class MacRusage:
    """
    macOS proc_pid_rusage (RUSAGE_INFO_V4) of a process and its descendants: phys_footprint (the memory Activity
    Monitor shows: resident plus compressed and purgeable memory, which the resident size leaves out) and the bytes
    written to files (logical writes, so a temporary file counts even if it is deleted before reaching the disk).
    """

    def __init__(self) -> None:
        self.lib = ctypes.CDLL("/usr/lib/libproc.dylib")  # type: ignore[attr-defined]
        self.lib.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
        self.lib.proc_listchildpids.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        self.written: Dict[int, int] = {}  # pid -> last seen bytes written
        self.peak_footprint = 0

    def _info(self, pid: int) -> Optional[Tuple[int, int, int, int]]:
        # rusage_info_v4: a 16-byte uuid, then 64-bit fields; phys_footprint is the 8th, diskio_byteswritten the 18th,
        # logical_writes the 28th and lifetime_max_phys_footprint the 29th
        buf = (ctypes.c_uint64 * 48)()
        if self.lib.proc_pid_rusage(pid, 4, buf) != 0:
            return None
        f = list(buf)[2:]
        return f[7], f[17], f[27], f[28]

    def _tree(self, pid: int) -> List[int]:
        out, todo = [], [pid]
        while todo:
            p = todo.pop()
            out.append(p)
            arr = (ctypes.c_int * 512)()
            n = self.lib.proc_listchildpids(p, arr, ctypes.sizeof(arr))
            todo.extend(arr[i] for i in range(max(0, min(n, 512))) if arr[i] > 0)
        return out

    def sample(self, pid: int) -> None:
        total = 0
        for p in self._tree(pid):
            info = self._info(p)
            if info is None:
                continue
            footprint, disk_written, logical_written, lifetime_max = info
            total += footprint
            self.written[p] = max(disk_written, logical_written)
            if p == pid:
                self.peak_footprint = max(self.peak_footprint, lifetime_max)
        self.peak_footprint = max(self.peak_footprint, total)


class WindowsJob:
    """
    A job object the scanner process is put in right after it starts, so the CPU time of everything it spawns
    afterwards (helpers, worker processes) is counted too.
    """

    class _Accounting(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_int64),
            ("TotalKernelTime", ctypes.c_int64),
            ("ThisPeriodTotalUserTime", ctypes.c_int64),
            ("ThisPeriodTotalKernelTime", ctypes.c_int64),
            ("TotalPageFaultCount", ctypes.c_uint32),
            ("TotalProcesses", ctypes.c_uint32),
            ("ActiveProcesses", ctypes.c_uint32),
            ("TotalTerminatedProcesses", ctypes.c_uint32),
        ]

    def __init__(self, process_handle: int) -> None:
        self.k32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        self.k32.CreateJobObjectW.restype = ctypes.c_void_p
        self.k32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self.k32.QueryInformationJobObject.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        self.k32.CloseHandle.argtypes = [ctypes.c_void_p]
        self.job = self.k32.CreateJobObjectW(None, None)
        self.ok = bool(self.job) and bool(self.k32.AssignProcessToJobObject(self.job, process_handle))

    class _IoAccounting(ctypes.Structure):
        # JOBOBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION: the basic accounting, then IO_COUNTERS
        _fields_ = [
            ("Basic", ctypes.c_byte * 48),
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    def cpu_seconds(self) -> Optional[float]:
        if not self.ok:
            return None
        info = self._Accounting()
        if not self.k32.QueryInformationJobObject(self.job, 1, ctypes.byref(info), ctypes.sizeof(info), None):
            return None
        return (info.TotalUserTime + info.TotalKernelTime) / 1e7

    def write_bytes(self) -> Optional[int]:
        """Bytes every process of the job wrote (files, and also pipes: the caller subtracts its captured output)."""
        if not self.ok:
            return None
        info = self._IoAccounting()
        if not self.k32.QueryInformationJobObject(self.job, 8, ctypes.byref(info), ctypes.sizeof(info), None):
            return None
        return int(info.WriteTransferCount)

    def close(self) -> None:
        if self.job:
            self.k32.CloseHandle(self.job)
            self.job = None


def device_io_counters(path: str, os_key: str) -> Optional[Tuple[int, int]]:
    """
    Cumulative (read requests completed, bytes written) of the device holding `path`: the reads feed the I/O term of
    the balanced index and the scan-efficiency score, the bytes written show how much a scan writes to the disk.
    Windows: the volume's IOCTL_DISK_PERFORMANCE counters; Linux: /sys/dev/block/<major>:<minor>/stat (the loop
    device of the benchmark image); macOS: the sums of "Operations (Read)" and "Bytes (Write)" of all block storage
    drivers (the whole machine: the benchmark tree lives on the system volume there).
    """
    try:
        if os_key == "windows":
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
            k32.CreateFileW.restype = ctypes.c_void_p
            k32.CreateFileW.argtypes = [
                ctypes.c_wchar_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_void_p,
            ]
            k32.DeviceIoControl.argtypes = [
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.c_void_p,
            ]
            k32.CloseHandle.argtypes = [ctypes.c_void_p]
            drive = Path(path).resolve().drive  # "X:"
            handle = k32.CreateFileW(f"\\\\.\\{drive}", 0, 3, None, 3, 0, None)
            if not handle or handle == ctypes.c_void_p(-1).value:
                return None
            try:
                buf = ctypes.create_string_buffer(128)
                returned = ctypes.c_uint32(0)
                # IOCTL_DISK_PERFORMANCE -> DISK_PERFORMANCE: BytesRead, BytesWritten, ReadTime, WriteTime, IdleTime
                # (LARGE_INTEGERs), then DWORD ReadCount
                if not k32.DeviceIoControl(handle, 0x70020, None, 0, buf, 128, ctypes.byref(returned), None):
                    return None
                return int.from_bytes(buf.raw[40:44], "little"), int.from_bytes(buf.raw[8:16], "little")
            finally:
                k32.CloseHandle(handle)
        if os_key == "linux":
            st_dev = os.stat(path).st_dev
            major, minor = getattr(os, "major"), getattr(os, "minor")  # Unix only
            stat_path = Path(f"/sys/dev/block/{major(st_dev)}:{minor(st_dev)}/stat")
            if not stat_path.exists():
                # Btrfs and ZFS report an anonymous device number: use the loop device of the benchmark image, as
                # recorded by linux_loop.sh (image|mount path|ramdisk|loop device|fs)
                state = Path("/tmp/disk_scanner_bench_linux.state").read_text().strip().split("|")
                if len(state) < 4 or not state[3] or not Path(path).resolve().is_relative_to(Path(state[1]).resolve()):
                    return None
                stat_path = Path(f"/sys/class/block/{Path(state[3]).name}/stat")
            fields = stat_path.read_text().split()
            return int(fields[0]), int(fields[6]) * 512  # reads completed, sectors written
        if os_key == "macos":
            out = subprocess.run(
                ["ioreg", "-c", "IOBlockStorageDriver", "-r", "-w", "0"], capture_output=True, text=True
            ).stdout
            counts = [int(m) for m in re.findall(r'"Operations \(Read\)"=(\d+)', out)]
            written = [int(m) for m in re.findall(r'"Bytes \(Write\)"=(\d+)', out)]
            return (sum(counts), sum(written)) if counts else None
    except Exception:
        return None
    return None


def flush_volume(path: str, os_key: str) -> None:
    """Writes the volume's pending metadata (e.g. access-time updates) out, so the device write counter sees them."""
    time.sleep(1.0)  # updates made when the scanner closed its handles
    try:
        if os_key == "windows":
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
            k32.CreateFileW.restype = ctypes.c_void_p
            k32.CreateFileW.argtypes = [
                ctypes.c_wchar_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_void_p,
            ]
            k32.FlushFileBuffers.argtypes = [ctypes.c_void_p]
            k32.CloseHandle.argtypes = [ctypes.c_void_p]
            drive = Path(path).resolve().drive  # "X:"
            # GENERIC_READ | GENERIC_WRITE on the volume (administrator): FlushFileBuffers then flushes the whole volume
            handle = k32.CreateFileW(f"\\\\.\\{drive}", 0xC0000000, 3, None, 3, 0, None)
            if handle and handle != ctypes.c_void_p(-1).value:
                try:
                    k32.FlushFileBuffers(handle)
                finally:
                    k32.CloseHandle(handle)
        else:
            getattr(os, "sync")()  # Unix only
    except Exception as exc:
        print(f"  [warn] could not flush the volume: {exc}")
    time.sleep(1.0)


def reset_access_times(root: str, os_key: str) -> int:
    """
    Sets the access time of every file and directory under root two days back (modification times kept), so the next
    scan meets stale access times everywhere: every daily-use policy (Linux relatime: older than a day; Windows: more
    than an hour off) then updates whatever the scan touches, and no scanner inherits fresh times from the one before.
    """
    # list everything first: listing a folder updates its access time, so no folder may be listed after its time is set
    targets: List[Tuple[str, int]] = []
    stack = [root]
    try:
        targets.append((root, os.stat(root).st_mtime_ns))
    except OSError:
        pass
    while stack:
        try:
            with os.scandir(stack.pop()) as it:
                entries = list(it)
        except OSError:
            continue
        for e in entries:
            try:
                if e.is_symlink():
                    continue
                targets.append((e.path, e.stat(follow_symlinks=False).st_mtime_ns))
                if e.is_dir(follow_symlinks=False):
                    stack.append(e.path)
            except OSError:
                continue
    old_ns = time.time_ns() - 2 * 86400 * 10**9
    count = 0
    # contents before their folder (a folder is listed before what it holds): on NTFS setting a file's times updates
    # its folder's index, which counts as an access to the folder
    for path, mtime_ns in reversed(targets):
        try:
            os.utime(path, ns=(old_ns, mtime_ns))
            count += 1
        except OSError:
            continue
    return count


def reset_access_times_fast(scan_path: str, os_key: str, repo_root: Path) -> None:
    """Stale access times before a cold scan: fs-mirage --reset-atime (parallel), else reset_access_times."""
    exe = repo_root / "target" / "release" / ("fs-mirage.exe" if os_key == "windows" else "fs-mirage")
    t0 = time.perf_counter()
    if exe.exists():
        try:
            out = subprocess.run(
                [str(exe), "--root", scan_path, "--reset-atime"], capture_output=True, text=True, timeout=3600
            )
            if out.returncode == 0:
                print(f"  [atime] {out.stdout.strip()}")
                return
            print(f"  [warn] fs-mirage --reset-atime failed ({out.returncode}): {out.stderr.strip()[:200]}")
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"  [warn] fs-mirage --reset-atime failed: {exc}")
    n = reset_access_times(scan_path, os_key)
    print(f"  [atime] access times of {n:,} entries set two days back in {time.perf_counter() - t0:.1f} s (Python)")


def probe_access_time_updates(
    scan_path: str, os_key: str, repo_root: Path, skip_purge: bool, purge_mode: str
) -> Optional[bool]:
    """
    Whether this volume updates access times now (the daily-use setting the caller mounted it with, or the platform's
    default): a folder and a file inside the tree (removed again before any scan) get stale access times, the caches
    are dropped, both are read, and their access times must have moved. Where the volume keeps no access times the
    reset and flush before each scan are skipped.
    """
    # inside the tree: on Linux the tree is the volume's mount point, and its parent another volume
    probe = Path(scan_path).resolve() / "_atime_probe"
    try:
        probe.mkdir(exist_ok=True)
        f = probe / "probe.bin"
        f.write_bytes(b"x" * 65536)
        old = time.time_ns() - 2 * 86400 * 10**9
        for p in (probe, f):
            os.utime(p, ns=(old, os.stat(p).st_mtime_ns))
        flush_volume(scan_path, os_key)
        invoke_purge_cache(os_key, scan_path, repo_root, skip_purge, purge_mode)
        os.listdir(probe)
        f.read_bytes()
        flush_volume(scan_path, os_key)
        newest = max(os.stat(probe).st_atime_ns, os.stat(f).st_atime_ns)
        return newest > old + 3600 * 10**9
    except OSError as exc:
        print(f"  [warn] access-time probe failed: {exc}")
        return None
    finally:
        shutil.rmtree(probe, ignore_errors=True)


def save_scanner_output(out_dir: Path, scanner_id: str, text: str, keep: int = 200_000) -> None:
    """
    The scanner's own output of the cold run, next to raw_results.json (scanner_output/<id>.txt), so a result that
    could not be parsed or failed verification can be checked against what the tool really printed.
    """
    if len(text) > 2 * keep:
        text = text[:keep] + f"\n... [{len(text) - 2 * keep:,} characters left out] ...\n" + text[-keep:]
    try:
        target = out_dir / "scanner_output"
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{scanner_id}.txt").write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"  [warn] could not save the output of {scanner_id}: {exc}")


def run_monitored_cli(
    cmd: List[str],
    os_key: str,
    timeout_sec: int = 900,
    extra_env: Optional[Dict[str, str]] = None,
    io_out: Optional[Dict[str, Any]] = None,
) -> Tuple[float, float, str, Optional[float]]:
    """
    Executes a CLI command and returns (elapsed_ms, peak_rss_mb, stdout_text, cpu_seconds).
    cpu_seconds is the user + kernel CPU time of the process and everything it started (None if unknown).
    Drains stdout concurrently on a background thread so OS pipe buffers (e.g. 64KB on macOS)
    can never fill up and deadlock while polling process memory.

    io_out, if given, receives what the scanner kept outside its own resident memory:
      written_bytes   bytes its process tree wrote to files (Windows: minus its captured output; Linux: sent to the
                      storage layer; macOS: logical writes), e.g. a disk cache that keeps its memory low
      shmem_peak_mb   Linux: the largest rise of tmpfs / shared memory during the run (files in /dev/shm or a tmpfs
                      /tmp are RAM the resident size does not show)
      footprint_mb    macOS: peak phys_footprint of the process tree (resident plus compressed memory)
    """
    cpu0 = children_cpu_seconds()
    written0 = children_written_bytes() if os_key == "linux" else None
    shmem0 = shmem_kib() if os_key == "linux" else None
    t0 = time.perf_counter()
    child_env = os.environ.copy()
    child_env["SPACEKNIFE_LANGUAGE"] = "en"
    child_env.update(extra_env or {})
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=child_env,
    )
    job: Optional[WindowsJob] = None
    if os_key == "windows":
        try:
            job = WindowsJob(int(proc._handle))  # type: ignore[attr-defined]
        except Exception:
            job = None
    mac: Optional[MacRusage] = None
    if os_key == "macos":
        try:
            mac = MacRusage()
        except Exception:
            mac = None

    peak_rss_mb = 0.0
    shmem_peak_kib = 0
    if os_key == "windows":
        try:
            stdout_text, _ = proc.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_text, _ = proc.communicate()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        try:
            peak_rss_mb = query_windows_peak_rss_mb(int(proc._handle))  # type: ignore[attr-defined]
        except Exception:
            peak_rss_mb = 0.0
    else:
        stdout_chunks: List[str] = []

        def _drain_stdout() -> None:
            if proc.stdout is not None:
                try:
                    stdout_chunks.append(proc.stdout.read())
                except Exception:
                    pass

        reader_thread = threading.Thread(target=_drain_stdout, daemon=True)
        reader_thread.start()

        # Poll while stdout is concurrently drained: Linux /proc/<pid>/status VmHWM and the system's Shmem,
        # macOS the process tree's footprint and writes
        pid = proc.pid
        proc_status_path = Path(f"/proc/{pid}/status")
        while proc.poll() is None:
            if (time.perf_counter() - t0) > timeout_sec:
                proc.kill()
                break
            if os_key == "linux" and proc_status_path.exists():
                try:
                    content = proc_status_path.read_text(encoding="utf-8", errors="ignore")
                    for line in content.splitlines():
                        if line.startswith(("VmHWM:", "VmRSS:")):
                            kb = int(line.split()[1])
                            mb = kb / 1024.0
                            if mb > peak_rss_mb:
                                peak_rss_mb = mb
                except Exception:
                    pass
            if shmem0 is not None:
                now_kib = shmem_kib()
                if now_kib is not None:
                    shmem_peak_kib = max(shmem_peak_kib, now_kib - shmem0)
            if mac is not None:
                try:
                    mac.sample(pid)
                except Exception:
                    mac = None
            time.sleep(0.015)

        proc.wait()
        reader_thread.join(timeout=5.0)
        stdout_text = "".join(stdout_chunks)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if peak_rss_mb == 0.0:
            try:
                import resource

                rusage = resource.getrusage(resource.RUSAGE_CHILDREN)  # type: ignore[attr-defined]
                # ru_maxrss is in bytes on macOS and in KiB on Linux
                divisor = 1024.0 * 1024.0 if os_key == "macos" else 1024.0
                peak_rss_mb = round(rusage.ru_maxrss / divisor, 2)
            except Exception:
                pass

    cpu_seconds: Optional[float]
    written: Optional[int] = None
    if job is not None:
        cpu_seconds = job.cpu_seconds()
        total = job.write_bytes()
        if total is not None:
            # the job's writes include its output into our pipe
            written = max(0, total - len((stdout_text or "").encode("utf-8", errors="replace")))
        job.close()
    else:
        cpu_seconds = children_cpu_seconds() - cpu0 if os_key != "windows" else None
        if os_key == "linux":
            written1 = children_written_bytes()
            written = written1 - written0 if written0 is not None and written1 is not None else None
        elif mac is not None:
            written = sum(mac.written.values())
    if io_out is not None:
        io_out["written_bytes"] = written
        io_out["shmem_peak_mb"] = round(shmem_peak_kib / 1024.0, 2) if shmem0 is not None else None
        io_out["footprint_mb"] = round(mac.peak_footprint / (1024.0 * 1024.0), 2) if mac is not None else None
    return round(elapsed_ms, 2), round(peak_rss_mb, 2), stdout_text, cpu_seconds


def _windows_purge_standby() -> bool:
    """
    Evicts the file cache the way RAMMap's "Empty System Working Set" + "Empty Standby List" do: trims the system file
    cache working set (where NTFS keeps the $MFT and directory index pages it is using), flushes modified pages and
    purges the standby list. Needs an elevated token; prints the step that failed.
    """
    try:
        from ctypes import wintypes

        advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)  # type: ignore[attr-defined]
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        ntdll = ctypes.WinDLL("ntdll")  # type: ignore[attr-defined]

        class LUID(ctypes.Structure):
            _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

        class TOKEN_PRIVILEGES(ctypes.Structure):
            _fields_ = [("PrivilegeCount", wintypes.DWORD), ("Luid", LUID), ("Attributes", wintypes.DWORD)]

        # Without explicit types ctypes passes handles and sizes as 32-bit ints: the -1 pseudo-handle of the current
        # process and the (SIZE_T)-1 cache limits would arrive truncated on 64-bit Windows.
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.SetSystemFileCacheSize.argtypes = [ctypes.c_size_t, ctypes.c_size_t, wintypes.DWORD]
        kernel32.SetSystemFileCacheSize.restype = wintypes.BOOL
        advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
        advapi32.OpenProcessToken.restype = wintypes.BOOL
        advapi32.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(LUID)]
        advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL
        advapi32.AdjustTokenPrivileges.argtypes = [
            wintypes.HANDLE,
            wintypes.BOOL,
            ctypes.POINTER(TOKEN_PRIVILEGES),
            wintypes.DWORD,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL
        ntdll.NtSetSystemInformation.argtypes = [ctypes.c_int, ctypes.c_void_p, wintypes.ULONG]
        ntdll.NtSetSystemInformation.restype = wintypes.LONG

        def fail(step: str, code: int) -> bool:
            print(f"[purge] {step} failed ({code:#x})", file=sys.stderr, flush=True)
            return False

        token = wintypes.HANDLE()
        # TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY
        if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x20 | 0x8, ctypes.byref(token)):
            return fail("OpenProcessToken", ctypes.get_last_error())  # type: ignore[attr-defined]
        try:
            # SeIncreaseQuotaPrivilege: SetSystemFileCacheSize; SeProfileSingleProcessPrivilege: the memory lists
            for privilege in ("SeIncreaseQuotaPrivilege", "SeProfileSingleProcessPrivilege"):
                luid = LUID()
                if not advapi32.LookupPrivilegeValueW(None, privilege, ctypes.byref(luid)):
                    return fail(f"LookupPrivilegeValue {privilege}", ctypes.get_last_error())  # type: ignore
                tp = TOKEN_PRIVILEGES(1, luid, 0x2)  # SE_PRIVILEGE_ENABLED
                advapi32.AdjustTokenPrivileges(token, False, ctypes.byref(tp), 0, None, None)
                err = ctypes.get_last_error()  # type: ignore[attr-defined]
                if err != 0:  # ERROR_NOT_ALL_ASSIGNED (0x514): not elevated
                    return fail(f"enable {privilege}", err)
        finally:
            kernel32.CloseHandle(token)

        # (SIZE_T)-1 for both limits empties the system file cache working set: its pages go to the standby list
        unlimited = ctypes.c_size_t(-1).value
        if not kernel32.SetSystemFileCacheSize(unlimited, unlimited, 0):
            return fail("SetSystemFileCacheSize (empty the system working set)", ctypes.get_last_error())  # type: ignore
        for command, name in ((3, "MemoryFlushModifiedList"), (4, "MemoryPurgeStandbyList")):
            cmd = ctypes.c_int(command)
            status = ntdll.NtSetSystemInformation(80, ctypes.byref(cmd), ctypes.sizeof(cmd))  # SystemMemoryListInfo
            if status != 0:
                return fail(name, status & 0xFFFFFFFF)
        return True
    except (AttributeError, OSError) as exc:
        print(f"[purge] {exc}", file=sys.stderr, flush=True)
        return False


def purge_system_cache(os_key: str) -> bool:
    """OS-wide file cache purge for scans of real drives, which cannot be remounted. False without privileges."""
    if os_key == "windows":
        return _windows_purge_standby()
    subprocess.run(["sync"], check=False)
    if os_key == "linux":
        if hasattr(os, "geteuid") and os.geteuid() == 0:  # type: ignore[attr-defined]
            try:
                Path("/proc/sys/vm/drop_caches").write_text("3\n")
                return True
            except OSError:
                return False
        cmd = ["sudo", "-n", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"]
    elif os_key == "macos":
        cmd = ["purge"] if hasattr(os, "geteuid") and os.geteuid() == 0 else ["sudo", "-n", "purge"]  # type: ignore
    else:
        return False
    return subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def invoke_purge_cache(os_key: str, mount_path: str, repo_root: Path, skip_purge: bool, mode: str = "vdisk") -> bool:
    """Makes the next scan cold; returns whether that worked. vdisk remounts the benchmark volume (CI)."""
    if skip_purge or mode == "none":
        return False
    if mode == "system":
        return purge_system_cache(os_key)
    disk_mgr_dir = repo_root / "scripts" / "disk-mgr"
    if os_key == "linux":
        script = disk_mgr_dir / "linux_loop.sh"
        subprocess.run(["bash", str(script), "purge-cache", mount_path], check=True)
    elif os_key == "macos":
        script = disk_mgr_dir / "macos_dmg.sh"
        subprocess.run(["bash", str(script), "purge-cache", mount_path], check=True)
    elif os_key == "windows":
        script = disk_mgr_dir / "windows_vhd.ps1"
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "purge-cache", mount_path],
            check=True,
        )
    return True


def freeze_volume(os_key: str, mount_path: str, repo_root: Path, skip_purge: bool, mode: str = "vdisk") -> bool:
    """
    Windows CI: the benchmark volume (its access times just set back) is kept as it is, and every purge-cache from now
    on mounts a fresh copy of it (windows_vhd.ps1 freeze). Each cold scan then meets the same old access times without
    setting them back first, which took minutes per scanner there. Returns whether the volume is frozen; if not (no
    room for a copy), it is mounted as before.
    """
    if os_key != "windows" or skip_purge or mode != "vdisk":
        return False
    script = repo_root / "scripts" / "disk-mgr" / "windows_vhd.ps1"
    out = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "freeze", mount_path]
    )
    return out.returncode == 0


def extract_zip_keep_modes(archive: Path, dest: Path) -> None:
    """
    zipfile.extractall drops Unix permission bits, so a macOS / Linux portable bundle came out with no executable
    files besides the one binary chmod-ed afterwards. Restores the mode stored in each entry (symlinks stay files).
    """
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(dest)
        if os.name == "nt":
            return
        for info in zf.infolist():
            mode = (info.external_attr >> 16) & 0o777
            if mode and not info.is_dir():
                target = dest / info.filename
                if target.is_file():
                    target.chmod(mode)


def install_runtime_packages(scanner: Dict[str, Any], os_key: str) -> None:
    """
    Shared libraries a prebuilt binary links against but a CI image may lack ("runtime_packages": {"linux": [...]}).
    Each name is tried on its own: Ubuntu 24.04 renamed some (libasound2 -> libasound2t64).
    """
    if os_key != "linux":
        return
    for pkg in scanner.get("runtime_packages", {}).get(os_key, []):
        subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", pkg], check=False)


def resolve_installed_scanner(scanner: Dict[str, Any], os_key: str, arch_key: str, bin_dir: Path) -> Optional[str]:
    """Where an already installed scanner lives, matching every place install_pinned_scanner can put it."""
    scanner_id = scanner["id"]
    exe = ".exe" if os_key == "windows" else ""
    bundle = bin_dir / f"{scanner_id}_portable"
    if bundle.exists():
        target = (scanner["name"] + exe).lower()
        for root, _, files in os.walk(bundle):
            for fn in files:
                if fn.lower() == target:
                    return str(Path(root) / fn)
    spec = str(scanner.get("install", {}).get(f"{os_key}_{arch_key}", ""))
    if spec.startswith("system:"):
        return shutil.which(spec.split(":", 1)[1])
    if spec.startswith("cargo:"):
        built = bin_dir / f"cargo-{scanner_id}" / "bin" / (spec.split(":", 2)[2] + exe)
        if built.exists():
            return str(built)
    names = [scanner_id if os_key != "windows" else scanner["name"], scanner.get("bin_name", ""), scanner_id]
    for name in [n for n in names if n]:
        local = bin_dir / (name + exe)
        if local.exists():
            return str(local)
    return shutil.which(scanner["name"] + exe) or shutil.which(scanner_id + exe)


def install_pinned_scanner(scanner: Dict[str, Any], os_key: str, arch_key: str, bin_dir: Path) -> Optional[str]:
    """
    Resolves an existing binary or downloads the pinned version from scanners_registry.json into bin_dir.
    """
    scanner_id = scanner["id"]
    exe_suffix = ".exe" if os_key == "windows" else ""
    candidates = [
        scanner["name"] + exe_suffix,
        scanner_id + exe_suffix,
    ]
    if scanner.get("bin_name"):
        candidates.append(scanner["bin_name"] + exe_suffix)
    if scanner_id == "gdu":
        candidates.extend(
            [
                "gdu_linux_amd64",
                "gdu_linux_arm64",
                "gdu_darwin_amd64",
                "gdu_darwin_arm64",
                "gdu_windows_amd64.exe",
                "gdu_windows_arm64.exe",
            ]
        )

    # Check portable bundle directories first for bundled tools (WizTree, TreeSize, SpaceKnife)
    portable_bundle_dir = bin_dir / f"{scanner_id}_portable"
    if portable_bundle_dir.exists():
        target_exe_name = (scanner["name"] + exe_suffix).lower()
        for root, _, files in os.walk(portable_bundle_dir):
            for fn in files:
                if fn.lower() == target_exe_name:
                    return str(Path(root) / fn)

    for cand in candidates:
        local_cand = bin_dir / cand
        if local_cand.exists():
            return str(local_cand)
        which_cand = shutil.which(cand)
        if which_cand:
            return which_cand

    install_map = scanner.get("install", {})
    target_key = f"{os_key}_{arch_key}"
    spec = install_map.get(target_key)
    if not spec:
        return None

    if spec.startswith("system:"):
        # A tool the OS image already ships (GNU du on Ubuntu, BSD du on macOS)
        return shutil.which(spec.split(":", 1)[1])

    if spec.startswith("cargo:"):
        # Format: cargo:<crate>@<version>:<binary>; for targets without a prebuilt release asset
        crate_ver, bin_name = spec.split(":", 2)[1:]
        crate, version = crate_ver.split("@", 1)
        cargo_root = bin_dir / f"cargo-{scanner_id}"
        built = cargo_root / "bin" / (bin_name + exe_suffix)
        if built.exists():
            return str(built)
        print(f"[installer] cargo install {crate} {version} (--bin {bin_name}) into {cargo_root}...")
        subprocess.run(
            ["cargo", "install", crate, "--version", version, "--locked", "--bin", bin_name, "--root", str(cargo_root)],
            check=False,
        )
        return str(built) if built.exists() else None

    bin_dir.mkdir(parents=True, exist_ok=True)
    print(f"[installer] Installing pinned {scanner['name']} v{scanner['version']} for {target_key} from {spec}...")

    if spec.startswith("gh-artifact:"):
        # Format: gh-artifact:<owner/repo>:<run_id>:<artifact_name>
        _, repo_slug, run_id, artifact_name = spec.split(":", 3)
        portable_bundle_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmpd:
            tmp_dir = Path(tmpd)
            gh_res = subprocess.run(
                ["gh", "run", "download", run_id, "-R", repo_slug, "-n", artifact_name, "-D", str(tmp_dir)],
                check=False,
            )
            if gh_res.returncode != 0:
                nightly_url = f"https://nightly.link/{repo_slug}/actions/runs/{run_id}/{artifact_name}.zip"
                print(f"[installer] gh run download returned {gh_res.returncode}; downloading via {nightly_url}...")
                outer_zip = tmp_dir / f"{artifact_name}.zip"
                req = urllib.request.Request(nightly_url, headers={"User-Agent": "disk-scanner-bench/0.1"})
                with urllib.request.urlopen(req, timeout=180) as resp, open(outer_zip, "wb") as out_f:
                    shutil.copyfileobj(resp, out_f)
                with zipfile.ZipFile(outer_zip, "r") as zf:
                    zf.extractall(tmp_dir)
                outer_zip.unlink(missing_ok=True)

            # Extract nested *-portable.zip or *-portable.tar.gz inside the downloaded artifact
            for item in tmp_dir.rglob("*"):
                if not item.is_file():
                    continue
                if item.name.endswith((".tar.gz", ".tgz")):
                    with tarfile.open(item, "r:gz") as tf:
                        tf.extractall(portable_bundle_dir)
                elif item.name.endswith(".zip"):
                    extract_zip_keep_modes(item, portable_bundle_dir)

        target_exe_name = (scanner["name"] + exe_suffix).lower()
        for root, _, files in os.walk(portable_bundle_dir):
            for fn in files:
                if fn.lower() == target_exe_name:
                    resolved = Path(root) / fn
                    if os_key != "windows":
                        resolved.chmod(resolved.stat().st_mode | stat.S_IEXEC)
                    return str(resolved)
        return None

    if spec.startswith("brew:"):
        pkg = spec.split(":", 1)[1]
        subprocess.run(["brew", "install", pkg], check=False)
        return shutil.which(scanner_id)

    if spec.startswith("apt:"):
        pkg = spec.split(":", 1)[1]
        subprocess.run(["sudo", "apt-get", "update", "-qq"], check=False)
        subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", pkg], check=False)
        return shutil.which(scanner_id)

    if spec.startswith("choco:"):
        parts = spec.split(":")
        pkg = parts[1]
        ver = parts[2] if len(parts) > 2 else None
        cmd = ["choco", "install", pkg, "-y", "--no-progress"]
        if ver:
            cmd.extend(["--version", ver])
        subprocess.run(cmd, check=False)
        found = shutil.which(scanner["name"]) or shutil.which(scanner_id)
        if found:
            return found
        choco_path = (
            Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "chocolatey" / "bin" / f"{scanner['name']}.exe"
        )
        if choco_path.exists():
            return str(choco_path)
        return None

    # Direct URL download (.tar.gz / .tgz / .zip)
    with tempfile.TemporaryDirectory() as tmpd:
        tmp_dir = Path(tmpd)
        archive_name = spec.split("/")[-1]
        archive_path = tmp_dir / archive_name
        req = urllib.request.Request(spec, headers={"User-Agent": "disk-scanner-bench/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp, open(archive_path, "wb") as out_f:
                shutil.copyfileobj(resp, out_f)
        except Exception as dl_err:
            if os_key == "linux" and scanner_id == "ncdu":
                print(f"[installer] Direct download failed ({dl_err}); falling back to apt-get install ncdu...")
                subprocess.run(["sudo", "apt-get", "update", "-qq"], check=False)
                subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", "ncdu"], check=False)
                return shutil.which("ncdu")
            raise

        if not archive_name.endswith((".tar.gz", ".tgz", ".zip")):
            # A release asset that is the executable itself (e.g. squirreldisk-x86_64-unknown-linux-gnu)
            raw_target = bin_dir / (
                scanner.get("bin_name", scanner["name"]) + exe_suffix if os_key == "windows" else scanner_id
            )
            shutil.copy2(archive_path, raw_target)
            if os_key != "windows":
                raw_target.chmod(raw_target.stat().st_mode | stat.S_IEXEC)
            install_runtime_packages(scanner, os_key)
            return str(raw_target)

        extract_dir = (
            (bin_dir / f"{scanner_id}_portable") if scanner_id in ("treesize", "wiztree") else (tmp_dir / "extracted")
        )
        extract_dir.mkdir(parents=True, exist_ok=True)
        if archive_name.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(extract_dir)
        elif archive_name.endswith(".zip"):
            extract_zip_keep_modes(archive_path, extract_dir)

        if scanner_id == "treesize":
            for root, _, files in os.walk(extract_dir):
                for fn in files:
                    if fn.lower() == "treesizefree.exe":
                        return str(Path(root) / fn)

        if scanner_id == "wiztree":
            # Keep WizTree64.exe alongside WizTree.exe in its portable directory so its integrity check passes,
            # and explicitly disable MFT folder scanning and admin elevation in WizTree3.ini.
            ini_path = extract_dir / "WizTree3.ini"
            ini_path.write_text(
                "[frmWizTreeMain]\r\n"
                "actWindowsContextMenu_Checked=FALSE\r\n"
                "actRunAsAdmin_Checked=FALSE\r\n"
                "cbScanMFTifPossible_Checked=FALSE\r\n"
                "DefaultLanguageCode=en\r\n",
                encoding="ascii",
            )
            wt64 = extract_dir / "WizTree64.exe"
            if wt64.exists():
                return str(wt64)

        target_bin = bin_dir / (
            scanner.get("bin_name", scanner["name"]) + exe_suffix if os_key == "windows" else scanner_id
        )
        matched_files: List[Path] = []
        exact_target_lower = (scanner["name"] + exe_suffix).lower()
        cand_lower_set = {c.lower() for c in candidates}
        for root, _, files in os.walk(extract_dir):
            for fn in files:
                fn_lower = fn.lower()
                if os_key == "windows" and not fn_lower.endswith(".exe"):
                    continue
                if fn_lower.endswith(
                    (
                        ".txt",
                        ".md",
                        ".1",
                        ".csv",
                        ".dll",
                        ".pdb",
                        ".xml",
                        ".ini",
                        ".chm",
                        ".pdf",
                        ".html",
                        ".sig",
                        ".asc",
                    )
                ):
                    continue
                if fn_lower in cand_lower_set or fn_lower.startswith(scanner_id.lower()):
                    matched_files.append(Path(root) / fn)

        wanted = scanner.get("exe_by_arch", {}).get(arch_key)
        if wanted:
            # One archive with a build per architecture (Sysinternals: du64.exe / du64a.exe)
            for root, _, files in os.walk(extract_dir):
                for fn in files:
                    if fn.lower() == wanted.lower():
                        shutil.copy2(Path(root) / fn, target_bin)
                        return str(target_bin)

        if matched_files:
            # Prefer exact match on scanner['name'] (e.g. WizTree64.exe over 32-bit WizTree.exe), then architecture subfolder
            preferred_arch_token = "x64" if arch_key == "x86_64" else "arm64"
            matched_files.sort(
                key=lambda mf: (
                    0 if mf.name.lower() == exact_target_lower else 1,
                    0 if mf.name.lower() in cand_lower_set else 1,
                    0 if preferred_arch_token in [p.lower() for p in mf.parts] else 1,
                )
            )
            chosen = matched_files[0]

            shutil.copy2(chosen, target_bin)
            if os_key != "windows":
                target_bin.chmod(target_bin.stat().st_mode | stat.S_IEXEC)

            if scanner_id == "spacesniffer":
                cfg_path = bin_dir / "SpaceSnifferConfig.xml"
                if not cfg_path.exists():
                    cfg_path.write_text("", encoding="utf-8")
            elif scanner_id == "windirstat" and os_key == "windows":
                subprocess.run(
                    [
                        "reg",
                        "add",
                        r"HKCU\Software\WinDirStat",
                        "/v",
                        "UseBackupRestore",
                        "/t",
                        "REG_DWORD",
                        "/d",
                        "0",
                        "/f",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )

            return str(target_bin)

    return None


def write_wiztree_ini(bin_path: str, mft: bool) -> None:
    """Rewrites WizTree3.ini next to the executable; a cached portable dir may come from the other mode."""
    flag = "TRUE" if mft else "FALSE"
    ini_path = Path(bin_path).parent / "WizTree3.ini"
    ini_path.write_text(
        "[frmWizTreeMain]\r\n"
        "actWindowsContextMenu_Checked=FALSE\r\n"
        f"actRunAsAdmin_Checked={flag}\r\n"
        f"cbScanMFTifPossible_Checked={flag}\r\n"
        "DefaultLanguageCode=en\r\n",
        encoding="ascii",
    )


def configure_windows_gui_scanner(scanner_id: str, os_key: str, bin_path: str = "", mft: bool = False) -> None:
    """
    Applies per-user settings that force Windows scanners onto standard Win32 directory traversal
    (no MFT / Backup-privilege fast paths) and disable extra work unrelated to size scanning.
    With mft=True the same settings enable the scanner's raw $MFT fast path instead.
    Must run before every benchmark (not only at install time) because cached binaries skip the installer.
    """
    if os_key != "windows":
        return
    if scanner_id == "sysinternals-du":
        # -accepteula is passed too; the registry flag also covers the prewarm launch
        subprocess.run(
            ["reg", "add", r"HKCU\Software\Sysinternals\Du", "/v", "EulaAccepted", "/t", "REG_DWORD", "/d", "1", "/f"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    if scanner_id == "wiztree" and bin_path:
        write_wiztree_ini(bin_path, mft)
    if scanner_id == "windirstat":
        # WinDirStat 2.x stores options under HKCU\Software\WinDirStat\WinDirStat\<Section>
        reg_values = [
            (r"HKCU\Software\WinDirStat\WinDirStat\Options", "UseFastScanEngine", int(mft)),  # MFT engine when elevated
            (r"HKCU\Software\WinDirStat\WinDirStat\Options", "UseBackupRestore", int(mft)),  # SeBackupPrivilege
            (r"HKCU\Software\WinDirStat\WinDirStat\Options", "AutoElevate", 0),
            (r"HKCU\Software\WinDirStat\WinDirStat\Options", "ShowElevationPrompt", 0),
            (r"HKCU\Software\WinDirStat\WinDirStat\Options", "PacmanAnimation", 0),
            (r"HKCU\Software\WinDirStat\WinDirStat\DupeView", "ScanForDuplicates", 0),  # no content hashing
        ]
        for key, name, val in reg_values:
            subprocess.run(
                ["reg", "add", key, "/v", name, "/t", "REG_DWORD", "/d", str(val), "/f"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )


def prewarm_scanner_binary(scanner: Dict[str, Any], bin_path: str, os_key: str) -> None:
    """
    Launches the scanner once, untimed, BEFORE invoke_purge_cache and the Cold Cache run, so the timed cold run is the
    process's second start. The first start pays for things a desktop user pays once: the antivirus scan of the
    executable and its DLLs, SmartScreen, runtime extraction and page-in. The prewarm runs the real scan command on a
    tiny directory, so the same code paths and libraries load, without touching the benchmark volume.
    """
    with tempfile.TemporaryDirectory() as dummy_dir:
        (Path(dummy_dir) / "warmup.txt").write_bytes(b"warmup")
        export_file = str(Path(dummy_dir) / "warmup.csv")
        cmd = [
            tok.replace("{bin}", bin_path).replace("{path}", dummy_dir).replace("{export_file}", export_file)
            for tok in command_template_for(scanner, os_key)
        ]
        try:
            if scanner["runner_type"] == "cli":
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=False)
            else:
                # GUI scanners never exit on their own; the image scan happens while the process is created
                p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2.0)
                p.terminate()
                try:
                    p.wait(timeout=5)
                except Exception:
                    p.kill()
        except Exception as exc:
            print(f"[runner] prewarm of {scanner['name']} failed: {exc}", file=sys.stderr)


def windows_defender_state(scan_path: str) -> Optional[Dict[str, Any]]:
    """Defender real-time protection state during the scans, and whether the benchmark path is excluded from it."""
    script = (
        "$s = Get-MpComputerStatus; $p = Get-MpPreference; "
        "@{ realtime = [bool]$s.RealTimeProtectionEnabled; tamper = [bool]$s.IsTamperProtected; "
        "exclusions = @($p.ExclusionPath) } | ConvertTo-Json -Compress"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=60, check=False
        ).stdout
        data = json.loads(out)
    except Exception:
        return None
    target = os.path.normcase(os.path.abspath(scan_path))
    excluded = False
    for raw in data.get("exclusions") or []:
        if not raw:
            continue
        excl = os.path.normcase(os.path.abspath(str(raw)))
        if target == excl or target.startswith(excl.rstrip("\\/") + os.sep):
            excluded = True
    return {"realtime": bool(data.get("realtime")), "tamper": bool(data.get("tamper")), "bench_excluded": excluded}


def main() -> int:
    # Windows runners default stdout to cp1252, which cannot encode the status emoji in log lines
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="Run disk space scanner benchmarks across CLI and GUI tools")
    parser.add_argument("--path", default=".", help="Root path of the benchmark volume to scan")
    parser.add_argument("--ground-truth", default="ground_truth.json", help="Path to ground_truth.json")
    parser.add_argument("--out", default="raw_results.json", help="Output path for raw_results.json")
    parser.add_argument("--registry", default=None, help="Path to scanners_registry.json")
    parser.add_argument("--bin-dir", default="./bin", help="Directory to store/find downloaded scanner binaries")
    parser.add_argument(
        "--install-missing", action="store_true", help="Automatically install missing scanners using pinned URLs"
    )
    parser.add_argument(
        "--install-only",
        action="store_true",
        help="Only download/install pinned scanners for current platform and exit",
    )
    parser.add_argument(
        "--skip-purge", action="store_true", help="Skip OS disk-mgr purge-cache (for local folder runs)"
    )
    parser.add_argument(
        "--purge-mode",
        choices=["vdisk", "system", "none"],
        default="vdisk",
        help="How to make cold scans cold: remount the benchmark volume (CI), purge the OS file cache (real drives)",
    )
    parser.add_argument("--timeout", type=int, default=0, help="Seconds allowed per scan (default: scaled to the tree)")
    parser.add_argument(
        "--warm-runs", type=int, default=3, help="Number of consecutive Warm Cache runs to average (default: 3)"
    )
    parser.add_argument("--scanners", default=None, help="Optional comma-separated filter of scanner IDs to run")
    parser.add_argument(
        "--reset-atime",
        action="store_true",
        help="Timed scans with the daily-use access-time setting on (the caller mounts the volume that way): if the "
        "volume updates access times, every access time under --path is set two days back before each scanner's cold "
        "scan (fs-mirage --reset-atime), so each one meets the same stale times, and the volume is flushed after "
        "each run before its write counter is read, so the cold scan's writes are its access-time updates",
    )
    parser.add_argument(
        "--mft-mode",
        action="store_true",
        help="Windows/NTFS only: run just the scanners that support raw $MFT scanning, scanning the volume root",
    )
    parser.add_argument("--with-gui-render", action="store_true", help="Do not minimize Windows GUI scanner windows")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    registry_path = (
        Path(args.registry) if args.registry else (repo_root / "scripts" / "wrappers" / "scanners_registry.json")
    )
    with open(registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    os_key, arch_key = detect_os_arch()
    bin_dir = Path(args.bin_dir).resolve()

    if args.install_only:
        for scanner in registry_data.get("scanners", []):
            if not scanner.get("enabled", True) or scanner.get("unavailable"):
                continue
            if os_key not in scanner.get("platforms", []) or arch_key not in scanner.get("architectures", []):
                continue
            try:
                installed = install_pinned_scanner(scanner, os_key, arch_key, bin_dir)
                print(f"[provision] {scanner['name']} v{scanner['version']} -> {installed}")
            except Exception as exc:
                print(f"[provision] Warning: failed to install {scanner['name']}: {exc}", file=sys.stderr)
        return 0

    gt_data: Dict[str, Any] = {}
    gt_path = Path(args.ground_truth)
    if gt_path.exists():
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

    scan_path = str(Path(args.path).resolve())
    volume_root = Path(scan_path).anchor  # MFT scanners must be pointed at the whole volume, e.g. X:\
    if args.mft_mode and os_key != "windows":
        print("[runner] --mft-mode is only supported on Windows/NTFS", file=sys.stderr)
        return 2

    allowed_ids = [s.strip() for s in args.scanners.split(",") if s.strip()] if args.scanners else None

    results: List[Dict[str, Any]] = []
    gui_monitor_ps1 = repo_root / "scripts" / "wrappers" / "win_gui_monitor.ps1"

    atime_active: Optional[bool] = None
    fresh_disks = False  # each purge mounts a fresh copy of a volume whose access times are old
    if args.reset_atime:
        atime_active = probe_access_time_updates(scan_path, os_key, repo_root, args.skip_purge, args.purge_mode)
        if atime_active and os_key == "windows":
            reset_access_times_fast(scan_path, os_key, repo_root)
            fresh_disks = freeze_volume(os_key, scan_path, repo_root, args.skip_purge, args.purge_mode)
        print(
            f"[runner] Access times: this volume {'updates' if atime_active else 'does not update'} them"
            + ("; each cold scan starts from access times two days old" if atime_active else "")
            + (" (set back once, then a fresh copy of the volume per scanner)" if fresh_disks else "")
        )

    for scanner in registry_data.get("scanners", []):
        if not scanner.get("enabled", True):
            continue
        if os_key not in scanner.get("platforms", []):
            continue
        if arch_key not in scanner.get("architectures", []):
            print(f"[runner] Skipping {scanner['name']} (no native {os_key} {arch_key} build)")
            continue
        if allowed_ids and scanner["id"] not in allowed_ids:
            continue
        if args.mft_mode and not scanner.get("mft"):
            print(f"[runner] Skipping {scanner['name']} (no raw $MFT scanning support)")
            continue
        if scanner.get("unavailable"):
            # Listed as unable to run instead of being timed: its runs measured nothing (e.g. a license dialog)
            print(f"[runner] {scanner['name']} cannot run here: {scanner['unavailable']}")
            results.append(
                {
                    "id": scanner["id"],
                    "scanner": scanner["name"],
                    "version": scanner["version"],
                    "runner_type": scanner["runner_type"],
                    "size_metric": scanner.get("size_metric", "allocated"),
                    "cold_time_ms": 0.0,
                    "warm_time_ms": 0.0,
                    "warm_runs_ms": [],
                    "tool_reported_scan_ms": None,
                    "peak_rss_mb": 0.0,
                    "scanned_files": 0,
                    "scanned_bytes": 0,
                    "reference_bytes": 0,
                    "accuracy_diff_pct": 0.0,
                    "mode": "mft" if args.mft_mode else "api",
                    "valid": False,
                    "invalid_reason": f"⛔ CANNOT RUN: {scanner['unavailable']}",
                    "structure_samples": {},
                }
            )
            continue

        scanner_id = scanner["id"]
        bin_path = resolve_installed_scanner(scanner, os_key, arch_key, bin_dir)
        if not bin_path and args.install_missing:
            try:
                bin_path = install_pinned_scanner(scanner, os_key, arch_key, bin_dir)
            except Exception as exc:
                print(f"[runner] Warning: failed to install {scanner['name']}: {exc}", file=sys.stderr)

        if not bin_path:
            print(f"[runner] Skipping {scanner['name']} (binary not found and not installed)")
            continue

        print(f"\n=== Benchmarking {scanner['name']} v{scanner['version']} ({scanner['runner_type']}) ===")
        export_file = Path(tempfile.gettempdir()) / f"bench_export_{scanner_id}.csv"

        cmd_template = scanner["mft"]["command_template"] if args.mft_mode else command_template_for(scanner, os_key)

        def export_size() -> int:
            """Size of the export the benchmark asked for (CSV of the GUI tools): not the scanner's own writing."""
            try:
                return export_file.stat().st_size if export_file.exists() else 0
            except OSError:
                return 0

        def build_cmd() -> List[str]:
            return [
                tok.replace("{bin}", bin_path)
                .replace("{path}", scan_path)
                .replace("{volume}", volume_root)
                .replace("{export_file}", str(export_file))
                for tok in cmd_template
            ]

        def execute_once() -> Tuple[float, float, int, int, Dict[str, Dict[str, Any]]]:
            if export_file.exists():
                export_file.unlink()
            # device reads and bytes written during this run (outside the timed window): the balanced resource index,
            # the scan-efficiency score and the disk-write column
            io0 = device_io_counters(scan_path, os_key)
            try:
                return execute_scan()
            finally:
                if atime_active:
                    # access-time updates are written lazily: flush them into this run's window
                    flush_volume(scan_path, os_key)
                io1 = device_io_counters(scan_path, os_key)
                if io0 is not None and io1 is not None:
                    run_reads.append(io1[0] - io0[0])
                    run_written.append(io1[1] - io0[1])
                else:
                    run_reads.append(None)
                    run_written.append(None)

        def execute_scan() -> Tuple[float, float, int, int, Dict[str, Dict[str, Any]]]:
            if scanner["runner_type"] == "win_gui":
                cmd_tokens = build_cmd()
                gui_exe = cmd_tokens[0]
                gui_args = " ".join(f'"{t}"' if " " in t else t for t in cmd_tokens[1:])
                ps_cmd = [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(gui_monitor_ps1),
                    "-ExePath",
                    gui_exe,
                    "-ScanArgs",
                    gui_args,
                ]
                # win_gui_monitor.ps1 gives up after 90 s by default, which is far too short for millions of files
                # twice as long with access-time updates on (ReFS cold scans take up to 14x as long then)
                gui_timeout = max(90, int(gt_data.get("total_files", 0)) // (2000 if atime_active else 4000) + 90)
                ps_cmd.extend(["-TimeoutSec", str(gui_timeout)])
                if args.with_gui_render:
                    ps_cmd.append("-WithGuiRender")
                if args.mft_mode:
                    ps_cmd.append("-Elevated")

                out = subprocess.check_output(ps_cmd, text=True, encoding="utf-8", errors="replace")
                lines = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("{")]
                payload = json.loads(lines[-1]) if lines else {}
                elapsed = float(payload.get("elapsed_ms", 0.0))
                rss = float(payload.get("peak_rss_mb", 0.0))
                run_cpu.append(float(payload["cpu_ms"]) / 1000.0 if payload.get("cpu_ms") is not None else None)
                # MFT scans read raw volume data instead of enumerating directories, so count read ops there
                ops_key = "read_ops_total" if args.mft_mode else "other_ops_total"
                gui_io_samples.append(
                    (int(payload.get(ops_key, 0) or 0), bool(payload.get("launched_non_admin", False)))
                )
                gui_written = payload.get("write_bytes_total")
                run_proc_written.append(None if gui_written is None else max(0, int(gui_written) - export_size()))
                run_shmem.append(None)
                run_footprint.append(None)
                # GUI tools export no totals: size and file count stay unreported (0), never the ground truth
                return elapsed, rss, 0, 0, {}

            cmd_tokens = build_cmd()
            # Large presets (millions of files) need far more than the 15 minute default per scan run
            # 1 ms per file, 2 ms with access-time updates on: a ReFS cold scan then takes up to 0.9 ms per file
            cli_timeout = args.timeout or max(
                900, int(gt_data.get("total_files", 0)) // (500 if atime_active else 1000)
            )
            io_out: Dict[str, Any] = {}
            elapsed, rss, stdout_text, cpu_s = run_monitored_cli(
                cmd_tokens, os_key, cli_timeout, {k: str(v) for k, v in scanner.get("env", {}).items()}, io_out
            )
            run_cpu.append(cpu_s)
            proc_written = io_out.get("written_bytes")
            run_proc_written.append(None if proc_written is None else max(0, int(proc_written) - export_size()))
            run_shmem.append(io_out.get("shmem_peak_mb"))
            run_footprint.append(io_out.get("footprint_mb"))
            run_outputs.append(stdout_text)
            parser_kind = scanner.get("output_parser", "human_last_line")
            effective_metric = effective_size_metric(scanner, os_key)
            scanned_f = 0  # 0 = the tool reports no file count
            scanned_b = 0  # 0 = no size could be read from its output
            sampled_zones: Dict[str, Dict[str, Any]] = {}

            if parser_kind == "windirstat_csv":
                app_b, alloc_b, csv_files, sampled_zones = parse_windirstat_csv(export_file, scan_path, args.mft_mode)
                scanned_b = app_b if effective_metric == "apparent" else alloc_b
                if csv_files > 0:
                    scanned_f = csv_files
            elif parser_kind == "wiztree_csv":
                apparent_b, allocated_b, csv_files, sampled_zones = parse_wiztree_csv(
                    export_file, scan_path, args.mft_mode
                )
                scanned_b = apparent_b if effective_metric == "apparent" else allocated_b
                if csv_files > 0:
                    scanned_f = csv_files
            elif parser_kind == "ncdu_null":
                pass  # timed with -o /dev/null; the untimed verification export below supplies the numbers
            elif parser_kind in ("du_bytes", "du_kib"):
                scanned_b, sampled_zones = parse_du_lines(
                    stdout_text, scan_path, 1 if parser_kind == "du_bytes" else 1024
                )
            elif parser_kind == "sysinternals_du_csv":
                scanned_b, du_files, sampled_zones = parse_sysinternals_du_csv(stdout_text, scan_path, effective_metric)
                if du_files > 0:
                    scanned_f = du_files
            elif parser_kind == "pdu_json":
                scanned_b, sampled_zones = parse_pdu_json(stdout_text, effective_metric)
            elif parser_kind == "bare_integer":
                scanned_b = parse_bare_integer(stdout_text)
            elif parser_kind == "erdtree":
                scanned_b, erd_files, sampled_zones = parse_erdtree(stdout_text, scan_path)
                if erd_files > 0:
                    scanned_f = erd_files
            elif parser_kind == "squirreldisk_json":
                scanned_b, sq_files, sampled_zones = parse_squirreldisk_json(stdout_text)
                if sq_files > 0:
                    scanned_f = sq_files
            elif parser_kind == "spaceknife_cli":
                scanned_b, sk_files = parse_spaceknife_output(stdout_text, effective_metric, os_key)
                sk_scan_ms = parse_spaceknife_scan_ms(stdout_text)
                if sk_scan_ms is not None:
                    tool_scan_ms_samples.append(sk_scan_ms)
                if args.mft_mode:
                    # scanned the volume root: take the benchmark subtree's row, and check the $MFT was really read
                    sk_mft_fallbacks.append(spaceknife_mft_fallback(stdout_text))
                    sub_b, sub_f = parse_spaceknife_subtree(stdout_text, Path(scan_path).name, os_key)
                    if sub_b > 0:
                        scanned_b, sk_files = sub_b, sub_f
                sampled_zones = parse_cli_structure_samples(stdout_text, "spaceknife")
                for zone in list(sampled_zones):
                    # each zone's row of the summary table carries its size on disk and file count
                    zone_b, zone_f = parse_spaceknife_subtree(stdout_text, zone, os_key)
                    if zone_b > 0:
                        sampled_zones[zone] = {"allocated_bytes": zone_b, "files": zone_f}
                if sk_files > 0:
                    scanned_f = sk_files
            else:
                scanned_b = parse_human_size_to_bytes(stdout_text, scanner_id)
                sampled_zones = parse_cli_structure_samples(stdout_text, scanner_id)
            return elapsed, rss, scanned_b, scanned_f, sampled_zones

        # 0. Pre-warm binary executable (eliminates Windows Defender / DLL cold-start noise without touching scan_path)
        gui_io_samples: List[Tuple[int, bool]] = []
        tool_scan_ms_samples: List[float] = []
        run_outputs: List[str] = []  # each CLI run's stdout + stderr, cold first
        sk_mft_fallbacks: List[Optional[str]] = []
        run_cpu: List[Optional[float]] = []  # per run, cold first: CPU seconds of the scanner's process tree
        run_reads: List[Optional[int]] = []  # per run, cold first: read requests completed by the device
        run_written: List[Optional[int]] = []  # per run, cold first: bytes the device wrote
        # per run, cold first: what the scanner kept outside its resident memory (see run_monitored_cli)
        run_proc_written: List[Optional[int]] = []  # bytes its processes wrote to files, the requested export excluded
        run_shmem: List[Optional[float]] = []  # Linux: MB of tmpfs / shared memory it added
        run_footprint: List[Optional[float]] = []  # macOS: peak phys_footprint MB
        configure_windows_gui_scanner(scanner_id, os_key, bin_path, args.mft_mode)
        prewarm_scanner_binary(scanner, bin_path, os_key)

        # 1. Cold Cache Run
        if atime_active and not fresh_disks:
            reset_access_times_fast(scan_path, os_key, repo_root)
        cold_purged = invoke_purge_cache(os_key, scan_path, repo_root, args.skip_purge, args.purge_mode)
        cold_ms, cold_rss, scanned_bytes, scanned_files, last_zones = execute_once()
        accumulated_zones = dict(last_zones)
        print(f"  [Cold Cache] {cold_ms:.2f} ms | Peak RSS: {cold_rss:.2f} MB | Scanned: {scanned_bytes} B")

        # 2. Warm Cache Runs (3x consecutive without purging cache)
        warm_times: List[float] = []
        rss_runs: List[float] = [cold_rss]
        peak_rss = cold_rss
        for w_idx in range(max(1, args.warm_runs)):
            w_ms, w_rss, w_bytes, w_files, w_zones = execute_once()
            warm_times.append(w_ms)
            rss_runs.append(w_rss)
            if w_zones and not accumulated_zones:
                accumulated_zones = dict(w_zones)
            if w_rss > peak_rss:
                peak_rss = w_rss
            if scanned_bytes == 0 and w_bytes > 0:
                scanned_bytes = w_bytes
            print(f"  [Warm #{w_idx + 1}]   {w_ms:.2f} ms | Peak RSS: {w_rss:.2f} MB")

        warm_avg_ms = round(sum(warm_times) / len(warm_times), 2)

        # memory the resident size does not show: tmpfs / shared memory it filled (Linux) and its compressed memory
        # (macOS phys_footprint); the GUI monitor and Windows report the working set as before
        def effective_mb(i: int) -> float:
            sh = run_shmem[i] if i < len(run_shmem) else None
            fp = run_footprint[i] if i < len(run_footprint) else None
            return max(rss_runs[i] + (sh or 0.0), fp or 0.0)

        peak_mem = max(effective_mb(i) for i in range(len(rss_runs)))
        if peak_mem > peak_rss * 1.05 + 1:
            print(f"  [Memory] {peak_mem:.2f} MB with tmpfs / compressed memory (resident peak {peak_rss:.2f} MB)")

        # Untimed verification pass for tools whose timed command prints nothing to check (ncdu -o /dev/null)
        if scanner.get("verify_command_template") and not args.mft_mode:
            vcmd = [
                tok.replace("{bin}", bin_path).replace("{path}", scan_path).replace("{export_file}", str(export_file))
                for tok in scanner["verify_command_template"]
            ]
            try:
                subprocess.run(vcmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200, check=False)
                if scanner.get("verify_parser") == "ncdu_json":
                    v_bytes, v_files, v_zones = parse_ncdu_export(export_file, effective_size_metric(scanner, os_key))
                    scanned_bytes, scanned_files, accumulated_zones = v_bytes, v_files, v_zones
                    print(f"  [Verify] {v_bytes:,} B, {v_files:,} files, zones {sorted(v_zones)}")
            except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
                print(f"  [Verify] failed: {exc}")
            finally:
                if export_file.exists():
                    export_file.unlink()

        # Accuracy Diff % against ground_truth.json
        size_metric = effective_size_metric(scanner, os_key)
        ref_bytes = reference_bytes(gt_data, scanner, size_metric, os_key)
        accuracy_diff_pct: Optional[float] = (
            round(((scanned_bytes - ref_bytes) / ref_bytes) * 100.0, 2) if ref_bytes > 0 and scanned_bytes > 0 else None
        )
        expected_files = int(gt_data.get("total_files", 0))

        # Comprehensive Sanity, Anti-Cheat, and Directory Sampling Audits
        valid = True
        invalid_reason = ""

        # 1. Reporting more than the tree holds (links followed, entries counted twice, files outside the tree) is a
        #    warning only: it costs the scanner work instead of saving it. Reporting less is what invalidates (step 3).
        warnings: List[str] = []
        if ref_bytes > 0 and scanned_bytes > 3.0 * ref_bytes and scanned_bytes > 20 * (1024**3):
            warnings.append(
                f"⚠️ WARNING: reported size {scanned_bytes:,} is more than 3x the tree's {ref_bytes:,} "
                "(counted outside the tree or followed links)"
            )
        if expected_files > 0 and scanned_files > expected_files + 3000 + int(gt_data.get("scan_slack_files", 0)):
            warnings.append(
                f"⚠️ WARNING: reported {scanned_files:,} files, more than the tree's {expected_files:,} "
                "(links followed or entries counted twice)"
            )
        for w in warnings:
            print(f"  {w}")

        # 1b. SpaceKnife's --mft falls back to a full scan (with the reason) when it cannot read the $MFT; that run would
        # be timed as an MFT scan otherwise
        fallbacks = [r for r in sk_mft_fallbacks if r]
        if valid and fallbacks:
            valid = False
            invalid_reason = f"❌ INVALID: no MFT scan, SpaceKnife fell back to a full scan ({fallbacks[0]})"

        # 2. GUI Traversal Sanity Check
        if valid and scanner["runner_type"] == "win_gui" and gui_io_samples:
            min_ops = min(s[0] for s in gui_io_samples)
            if args.mft_mode:
                # Raw $MFT scan: no per-directory enumeration, but the volume must actually have been read
                ops_label, expected_min_ops = "ReadOps", 1
            else:
                ops_label, expected_min_ops = "OtherOps", int(gt_data.get("total_dirs", 0))
            if expected_min_ops > 0 and min_ops < expected_min_ops:
                valid = False
                invalid_reason = (
                    f"❌ INVALID: Insufficient traversal detected ({ops_label}={min_ops:,} < {expected_min_ops:,}; "
                    "scanner blocked by dialog or did not scan the volume)"
                )
            if not args.mft_mode and not all(s[1] for s in gui_io_samples):
                invalid_reason = (
                    invalid_reason + "; " if invalid_reason else ""
                ) + "non-admin launch fell back to elevated token"
                valid = False
            print(f"  [Sanity] min {ops_label}={min_ops:,} | valid={valid} {invalid_reason}")

        # 3. Completeness: the same checks for every scanner, on what it reports itself (never the ground truth).
        #    Sizes may legitimately run high (directory blocks, hard-link and resident-file accounting differ), so only
        #    a shortfall counts: a skipped subtree shows up as a missing or much smaller total, zone or file count.
        is_gui = scanner["runner_type"] == "win_gui"
        zone_refs = gt_data.get("zones", {}) or {}
        zone_key = "apparent_bytes" if size_metric == "apparent" else "allocated_bytes"
        ref_zone_key = "apparent_size_bytes" if size_metric == "apparent" else "allocated_size_bytes"
        if size_metric != "apparent" and os_key in scanner.get("excludes_dir_blocks", []):
            # same accounting as the total (reference_bytes): the zone without its folders' own blocks
            ref_zone_key = "allocated_files_only_bytes"
        checked: List[str] = []
        if valid and not is_gui:
            if scanned_bytes <= 0:
                valid = False
                invalid_reason = "❌ INVALID: no total size could be read from the scanner's output"
            else:
                checked.append("size")
                if ref_bytes > 0 and scanned_bytes < 0.75 * ref_bytes:
                    valid = False
                    invalid_reason = (
                        f"❌ INVALID: Incomplete traversal (reported size {scanned_bytes:,} < 75% of {ref_bytes:,})"
                    )
        if valid and scanned_files > 0:
            checked.append("files")
            if expected_files > 0 and scanned_files < 0.9 * expected_files:
                valid = False
                invalid_reason = (
                    f"❌ INVALID: Incomplete traversal (scanned files {scanned_files:,} < 90% of tree total "
                    f"{expected_files:,})"
                )
        if valid and accumulated_zones and zone_refs:
            checked.append("zones")
            for zone, ref in zone_refs.items():
                sample = accumulated_zones.get(zone)
                if sample is None:
                    valid = False
                    invalid_reason = (
                        f"❌ INVALID: Incomplete traversal (top-level folder {zone} missing from the output)"
                    )
                    break
                # 0 is a reported size (on APFS a folder of files that were never written allocates nothing): only a
                # missing number counts as unreported, so no `or` chain here
                got = next(
                    (sample[k] for k in (zone_key, "allocated_bytes", "apparent_bytes") if sample.get(k) is not None),
                    None,
                )
                # manifests from before the files-only zone field fall back to the full allocation
                want_raw = ref.get(ref_zone_key)
                want = int(want_raw if want_raw is not None else ref.get("allocated_size_bytes", 0) or 0)
                if got is None:
                    # the folder's name shows up (e.g. in a largest-files list) but no size is reported for it
                    valid = False
                    invalid_reason = f"❌ INVALID: Incomplete traversal (no size reported for top-level folder {zone})"
                    break
                if want > 0 and float(got) < 0.75 * want:
                    valid = False
                    invalid_reason = (
                        f"❌ INVALID: Incomplete traversal ({zone} reported {int(got):,} < 75% of {want:,})"
                    )
                    break
        verification = "+".join(checked) if checked else ("io-only" if is_gui else "none")
        if run_outputs:
            saved = run_outputs[0]
            if len(run_outputs) > 1 and all(len(o) <= 20_000 for o in run_outputs):
                # short outputs: every run, so a result that differs between runs shows which one
                labels = ["cold"] + [f"warm #{i}" for i in range(1, len(run_outputs))]
                saved = "\n".join(f"===== {lbl} =====\n{out}" for lbl, out in zip(labels, run_outputs))
            save_scanner_output(Path(args.out).parent, scanner_id, saved)

        results.append(
            {
                "id": scanner_id,
                "scanner": scanner["name"],
                "version": scanner["version"],
                "runner_type": scanner["runner_type"],
                "size_metric": size_metric,
                "cold_time_ms": round(cold_ms, 2),
                "warm_time_ms": warm_avg_ms,
                "warm_runs_ms": warm_times,
                "tool_reported_scan_ms": (
                    round(sorted(tool_scan_ms_samples)[len(tool_scan_ms_samples) // 2], 1)
                    if tool_scan_ms_samples
                    else None
                ),
                "peak_rss_mb": round(peak_rss, 2),
                "scanned_files": scanned_files if scanned_files > 0 else None,
                "scanned_bytes": scanned_bytes if scanned_bytes > 0 else None,
                "verification": verification,
                "warnings": warnings,
                "reference_bytes": ref_bytes,
                "accuracy_diff_pct": accuracy_diff_pct,
                "mode": "mft" if args.mft_mode else "api",
                "cold_purged": cold_purged,
                "cpu_seconds_runs": [None if c is None else round(c, 3) for c in run_cpu],
                "device_reads_runs": run_reads,
                "device_written_bytes_runs": run_written,
                "peak_mem_mb": round(peak_mem, 2),
                "proc_written_bytes_runs": run_proc_written,
                "shmem_peak_mb_runs": run_shmem,
                "footprint_mb_runs": run_footprint,
                "valid": valid,
                "invalid_reason": invalid_reason,
                "structure_samples": accumulated_zones,
            }
        )

    if os_key == "windows" and results:
        defender = windows_defender_state(scan_path)
        print(f"[runner] Windows Defender during the scans: {defender}")
        for entry in results:
            entry["defender"] = defender
    if args.reset_atime:
        for entry in results:
            entry["atime_mode"] = "daily"  # timed with access-time updates on: the cold run's writes are those updates
            entry["atime_updates_active"] = atime_active
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[runner] Saved {len(results)} scanner result(s) to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
