#!/usr/bin/env python3
"""
Overall cross-platform leaderboard for one benchmark run.

Reads every platform's normalized_results.json (as written by report_gen.py) from the downloaded artifacts and
ranks the scanners on all platforms at once. Hardware differs between runners, so raw times are never compared
across platforms: inside each platform a scanner gets a relative score (the platform's best divided by its own,
x100), and the cross-platform score is the geometric mean of those relative scores over the platforms where its
result was valid.

  cold  = best cold time / cold time x 100            (per platform)
  warm  = best warm time / warm time x 100            (per platform)
  index = geomean(cold, warm balanced index / best)   (per platform, x100)
  overall = geomean(cold, warm, index), each first averaged (geometric mean) over the platforms

The JSON payload holds everything the Markdown needs, so scripts/readme_board.py can render the same tables into
README.md later from the stored payload alone.
"""

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from report_gen import small_preset_notice, verification_label

PAYLOAD_SCHEMA = 2
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
# Platforms every standard run is expected to produce; a missing one is called out above the tables
CORE_PLATFORMS = [
    "linux-x86_64",
    "linux-arm64",
    "macos-x86_64",
    "macos-arm64",
    "windows-x86_64",
    "windows-x86_64-refs",
    "windows-arm64",
]
OS_NAMES = {"linux": "Linux", "macos": "macOS", "windows": "Win"}
OS_ORDER = {"linux": 0, "macos": 1, "windows": 2}
DEFAULT_FS = {"linux": "ext4", "macos": "apfs", "windows": "ntfs"}
FS_NAMES = {
    "ext4": "ext4",
    "btrfs": "Btrfs",
    "xfs": "XFS",
    "zfs": "ZFS",
    "apfs": "APFS",
    "ntfs": "NTFS",
    "refs": "ReFS",
    "mft": "NTFS · MFT",
    "ramdisk": "RAM",
}
FS_ORDER = ["ext4", "apfs", "ntfs", "btrfs", "xfs", "zfs", "refs", "mft", "ramdisk"]
STATUS_TEXT = {"cannot_run": "⛔ 无法运行", "disqualified": "❌ 违规", "invalid": "⚠️ 无效"}


def parse_label(label: str) -> Tuple[str, str, str]:
    """'windows-x86_64-refs' -> ('windows', 'x86_64', 'refs'); the filesystem defaults per OS."""
    parts = label.split("-")
    os_key = parts[0]
    arch = parts[1] if len(parts) > 1 else ""
    fs = parts[2] if len(parts) > 2 else DEFAULT_FS.get(os_key, "")
    return os_key, arch, fs


def platform_title(label: str) -> str:
    os_key, arch, fs = parse_label(label)
    arch_name = {"x86_64": "x64", "arm64": "ARM64", "aarch64": "ARM64"}.get(arch, arch)
    return f"{OS_NAMES.get(os_key, os_key)} {arch_name} ({FS_NAMES.get(fs, fs)})".strip()


def platform_sort_key(label: str) -> Tuple[int, int, int, str]:
    os_key, arch, fs = parse_label(label)
    fs_rank = FS_ORDER.index(fs) if fs in FS_ORDER else len(FS_ORDER)
    return OS_ORDER.get(os_key, 9), fs_rank, 0 if arch == "x86_64" else 1, label


def geomean(values: List[Optional[float]]) -> Optional[float]:
    vals = [v for v in values if v and v > 0]
    if not vals:
        return None
    return math.exp(sum(math.log(v) for v in vals) / len(vals))


def find_platform_dirs(artifacts: Path) -> Dict[str, Path]:
    """label -> directory holding normalized_results.json; the Windows "final" artifact (with the ReFS audit) wins."""
    found: Dict[str, Path] = {}
    for norm in sorted(artifacts.rglob("normalized_results.json")):
        label = norm.parent.name
        if label in found and "-final-" not in str(norm.parent.parent.name):
            continue
        found[label] = norm.parent
    return found


def status_of(row: Dict[str, Any]) -> str:
    """'ok', 'cannot_run', 'disqualified' or 'invalid'."""
    if row.get("valid", True) is not False:
        cold, warm = float(row.get("cold_time_ms") or 0), float(row.get("warm_time_ms") or 0)
        return "ok" if cold > 0 and warm > 0 else "invalid"
    reason = str(row.get("invalid_reason", ""))
    if "CANNOT RUN" in reason:
        return "cannot_run"
    if "DISQUALIFIED" in reason:
        return "disqualified"
    return "invalid"


def balanced_score(row: Dict[str, Any], key: str) -> Optional[float]:
    data = row.get(key) or {}
    score = data.get("score") if isinstance(data, dict) else None
    return float(score) if score else None


def score_platform(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Per-scanner relative scores inside one platform, keyed by scanner id."""
    ok = [r for r in rows if status_of(r) == "ok"]
    out: Dict[str, Dict[str, Any]] = {}
    if ok:
        best_cold = min(float(r["cold_time_ms"]) for r in ok)
        best_warm = min(float(r["warm_time_ms"]) for r in ok)
        bal_cold = [s for s in (balanced_score(r, "balanced_cold") for r in ok) if s]
        bal_warm = [s for s in (balanced_score(r, "balanced_warm") for r in ok) if s]
        best_bal_cold = max(bal_cold) if bal_cold else None
        best_bal_warm = max(bal_warm) if bal_warm else None
        for r in ok:
            cold_rel = best_cold / float(r["cold_time_ms"]) * 100.0
            warm_rel = best_warm / float(r["warm_time_ms"]) * 100.0
            bc, bw = balanced_score(r, "balanced_cold"), balanced_score(r, "balanced_warm")
            index_rel = None
            if bc and bw and best_bal_cold and best_bal_warm:
                index_rel = math.sqrt((bc / best_bal_cold) * (bw / best_bal_warm)) * 100.0
            out[r["id"]] = {
                "status": "ok",
                "cold_s": float(r["cold_time_ms"]) / 1000.0,
                "warm_s": float(r["warm_time_ms"]) / 1000.0,
                "cold_rel": cold_rel,
                "warm_rel": warm_rel,
                "index_rel": index_rel,
                "platform_score": geomean([cold_rel, warm_rel, index_rel]),
                "rss_mb": float(r["peak_rss_mb"]) if r.get("peak_rss_mb") else None,
                "verification": r.get("verification"),
                "warnings": list(r.get("warnings") or []),  # reported more than the tree holds: counted anyway
                # GUI scanners report no size of their own (the monitor fills in the ground truth), so no accuracy
                "acc_pct": (
                    float(r["accuracy_diff_pct"])
                    if r.get("accuracy_diff_pct") is not None and r.get("runner_type") != "win_gui"
                    else None
                ),
            }
        ranked = sorted(out.values(), key=lambda v: -(v["platform_score"] or 0))
        for pos, v in enumerate(ranked, start=1):
            v["rank"] = pos
    for r in rows:
        if r["id"] not in out:
            out[r["id"]] = {"status": status_of(r), "reason": str(r.get("invalid_reason", ""))}
    return out


def fmt_s(seconds: float) -> str:
    if seconds < 10:
        return f"{seconds:.2f}"
    if seconds < 100:
        return f"{seconds:.1f}"
    return f"{seconds:,.0f}"


def fmt_score(value: Optional[float]) -> str:
    return "-" if value is None else f"{value:.1f}"


def best_flags(values: Sequence[Optional[float]], fmt: Callable[[float], str], low: bool = False) -> List[bool]:
    """Which entries show the column's best value (highest, or lowest with low=True); ties as shown all count."""
    present = [v for v in values if v is not None]
    if not present:
        return [False] * len(values)
    best = fmt(min(present) if low else max(present))
    return [v is not None and fmt(v) == best for v in values]


def mark_best(text: str, on: bool) -> str:
    """The best value of a column: bold on a highlighted background (bold alone barely shows in GitHub tables)."""
    return f"<mark>**{text}**</mark>" if on else text


def _median(values: List[Optional[float]]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return statistics.median(vals) if vals else None


def display_names() -> Dict[str, str]:
    """Scanner id -> the name shown on boards ("display_name" in the registry, else "name")."""
    registry = Path(__file__).resolve().parent / "wrappers" / "scanners_registry.json"
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {s["id"]: s.get("display_name", s["name"]) for s in data.get("scanners", [])}


def apply_display_names(payload: Dict[str, Any], names: Dict[str, str]) -> Dict[str, Any]:
    """Renames scanners in a payload in place (stored payloads from older runs carry the executable names)."""
    for sid, meta in payload.get("scanners", {}).items():
        meta["name"] = names.get(sid, meta["name"])
    for o in payload.get("overall", []):
        o["scanner"] = names.get(o["id"], o["scanner"])
    return payload


def build_payload(artifacts: Path, preset: str, sha: str) -> Dict[str, Any]:
    dirs = find_platform_dirs(artifacts)
    # The RAM-disk pass is not a real disk and stays out of the ranking
    labels = sorted((lbl for lbl in dirs if not lbl.endswith("-ramdisk")), key=platform_sort_key)
    only_mft = bool(labels) and all(parse_label(lbl)[2] == "mft" for lbl in labels)
    missing = [] if only_mft else [lbl for lbl in CORE_PLATFORMS if lbl not in dirs]

    per_platform: Dict[str, Dict[str, Dict[str, Any]]] = {}
    platform_info: Dict[str, Dict[str, Any]] = {}
    scanners: Dict[str, Dict[str, str]] = {}
    gt: Dict[str, Any] = {}
    for label in labels:
        data = json.loads((dirs[label] / "normalized_results.json").read_text(encoding="utf-8"))
        rows = data.get("results", [])
        gt = gt or data.get("ground_truth", {})
        plat = score_platform(rows)
        per_platform[label] = plat
        for r in rows:
            scanners.setdefault(r["id"], {"name": r.get("scanner", r["id"]), "version": str(r.get("version", "-"))})
        b = data.get("baseline", {})
        ok_ids = [sid for sid, e in plat.items() if e["status"] == "ok"]
        platform_info[label] = {
            "title": platform_title(label),
            "cores": b.get("logical_cores"),
            "iops": float(b.get("b_rand_read_iops") or 0) or None,
            "cpu_ms": float(b.get("b_cpu_ms") or 0) or None,
            "ok": len(ok_ids),
            "tried": len([sid for sid, e in plat.items() if e["status"] != "cannot_run"]),
            "fastest_cold": min(ok_ids, key=lambda s: plat[s]["cold_s"]) if ok_ids else None,
            "fastest_warm": min(ok_ids, key=lambda s: plat[s]["warm_s"]) if ok_ids else None,
        }

    payload = {
        "schema": PAYLOAD_SCHEMA,
        "preset": str(gt.get("preset") or preset),
        "sha": sha,
        "files": int(gt.get("total_files", 0)),
        "dirs": int(gt.get("total_dirs", 0)),
        "aged_timeline": gt.get("aged_timeline"),
        "platforms": labels,
        "platform_info": platform_info,
        "missing_platforms": missing,
        "scanners": scanners,
        "per_platform": per_platform,
    }
    aggregate_overall(payload)
    return apply_display_names(payload, display_names())


def merge_platforms(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    """
    A copy of `base` with the platforms of `extra` (a payload built from other artifacts of the same preset, e.g. the
    separate WinBtrfs run) added and the overall ranking recomputed. Per-platform scores are relative inside their own
    platform, so the platforms already in `base` keep their entries unchanged.
    """
    merged = json.loads(json.dumps(base))
    for label in extra.get("platforms", []):
        merged["per_platform"][label] = extra["per_platform"][label]
        merged["platform_info"][label] = extra["platform_info"][label]
    for sid, meta in extra.get("scanners", {}).items():
        merged["scanners"].setdefault(sid, meta)
    merged["platforms"] = sorted(set(merged["platforms"]) | set(extra.get("platforms", [])), key=platform_sort_key)
    aggregate_overall(merged)
    return merged


def aggregate_overall(payload: Dict[str, Any]) -> None:
    """Fills payload['overall'] and payload['unranked'] from its per-platform entries (geometric means across them)."""
    labels: List[str] = payload["platforms"]
    per_platform: Dict[str, Dict[str, Dict[str, Any]]] = payload["per_platform"]
    overall: List[Dict[str, Any]] = []
    unranked: List[str] = []
    for sid, meta in payload["scanners"].items():
        entries = [per_platform[lbl][sid] for lbl in labels if sid in per_platform[lbl]]
        ok = [e for e in entries if e["status"] == "ok"]
        if not ok:
            unranked.append(sid)
            continue
        cold = geomean([e["cold_rel"] for e in ok])
        warm = geomean([e["warm_rel"] for e in ok])
        index = geomean([e["index_rel"] for e in ok])
        accs = [abs(e["acc_pct"]) for e in ok if e.get("acc_pct") is not None]
        levels = [e.get("verification") for e in ok if e.get("verification")]
        overall.append(
            {
                "id": sid,
                "scanner": meta["name"],
                "version": meta["version"],
                "overall": geomean([cold, warm, index]),
                "cold": cold,
                "warm": warm,
                "index": index,
                "rss_mb": _median([e.get("rss_mb") for e in ok]),
                "abs_acc_pct": statistics.median(accs) if accs else None,
                "verification": max(set(levels), key=levels.count) if levels else None,
                "valid_platforms": len(ok),
                "entered_platforms": len(entries),
                "wins": sum(1 for e in ok if e.get("rank") == 1),
            }
        )
    overall.sort(key=lambda o: (-(o["overall"] or 0), -o["valid_platforms"]))
    for pos, o in enumerate(overall, start=1):
        o["rank"] = pos
    payload["overall"] = overall
    payload["unranked"] = unranked


# --- Markdown rendering (shared with scripts/readme_board.py) ---
#
# bi=False: Chinese, for the run summary. bi=True: Chinese and English on one page (README), with tables kept from
# wrapping inside cells (non-breaking spaces and hyphens) and short two-line headers.

NB = "&nbsp;"
VERIFY_CODES = {"size": "S", "files": "F", "zones": "Z", "io-only": "IO", "none": "—"}


CJK = "⺀-鿿豈-﫿＀-￯"
CJK_PAIR = re.compile(f"(?<=[{CJK}])(?=[{CJK}])")


def nobreak(text: str) -> str:
    """
    No line break inside a short cell ("dua-cli", "very-lite", "名次"): non-breaking hyphens and spaces, and a word
    joiner (U+2060) between Chinese characters, which a browser may otherwise split one per line in a squeezed column.
    """
    return CJK_PAIR.sub("⁠", str(text).replace("-", "‑").replace(" ", NB))


def head(zh: str, en: str, bi: bool) -> str:
    return f"{nobreak(zh)}<br>{nobreak(en)}" if bi else zh


def verify_code(value: Optional[str]) -> str:
    if not value:
        return "—"
    return "·".join(VERIFY_CODES.get(part, part) for part in value.split("+"))


def seconds_geomean(p: Dict[str, Any], sid: str, key: str) -> str:
    """'12.3&nbsp;s': geometric mean of a scanner's cold_s or warm_s over the platforms where its result is valid."""
    secs = [e[key] for lbl in p["platforms"] if (e := p["per_platform"][lbl].get(sid)) and e.get("status") == "ok"]
    value = geomean(secs)
    return f"{fmt_s(value)}{NB}s" if value else "—"


def render_overall_table(p: Dict[str, Any], bi: bool = False) -> List[str]:
    # bi (README): short headers spelled out in the notes, "#" for the rank and no platform-wins column (the
    # per-platform tables show the medals), so the table fits GitHub's README width without wrapping or scrolling
    cols = [
        ("名次", "Rank", ":---:"),
        ("扫描器", "Scanner", ":---"),
        ("**综合分**", "**Score**", "---:"),
        ("冷扫", "Cold", "---:"),
        ("热扫", "Warm", "---:"),
        ("均衡" if bi else "均衡指数", "Balanced", "---:"),
        ("内存" if bi else "峰值内存", "RAM", "---:"),
        ("误差" if bi else "大小误差", "Error", "---:"),
        ("核验", "Check", ":---:"),
        ("平台" if bi else "有效平台", "Platforms", ":---:"),
    ]
    if not bi:
        cols.append(("平台第一", "Wins", ":---:"))
    heads = ["#" if bi and zh == "名次" else head(zh, en, bi) for zh, en, _ in cols]
    lines = [
        "| " + " | ".join(heads) + " |",
        "| " + " | ".join(align for _, _, align in cols) + " |",
    ]
    rows = p["overall"]
    # the best value of each column in bold (highest score; least RAM; smallest size error)
    best = {key: best_flags([o.get(key) for o in rows], fmt_score) for key in ("overall", "cold", "warm", "index")}
    best["rss_mb"] = best_flags([o.get("rss_mb") or None for o in rows], lambda v: f"{v:,.0f}", low=True)
    best["abs_acc_pct"] = best_flags([o.get("abs_acc_pct") for o in rows], lambda v: f"{v:.2f}", low=True)
    for i, o in enumerate(rows):
        medal = MEDALS.get(o["rank"], str(o["rank"]))
        sep = NB if bi else " "
        rss = mark_best(f"{o['rss_mb']:,.0f}{sep}MB", best["rss_mb"][i]) if o.get("rss_mb") else "-"
        unverified = "n/a" if bi else "未核验"
        acc = (
            mark_best(f"{o['abs_acc_pct']:.2f}%", best["abs_acc_pct"][i])
            if o.get("abs_acc_pct") is not None
            else unverified
        )
        verified = verify_code(o.get("verification")) if bi else verification_label(o.get("verification"))
        name = nobreak(o["scanner"]) if bi else o["scanner"]
        wins = "" if bi else f" {o['wins'] or '-'} |"
        score, index = mark_best(fmt_score(o["overall"]), best["overall"][i]), mark_best(
            fmt_score(o["index"]), best["index"][i]
        )
        cold, warm = mark_best(fmt_score(o["cold"]), best["cold"][i]), mark_best(fmt_score(o["warm"]), best["warm"][i])
        if bi:
            # the seconds behind the relative scores, in small print: geometric mean over its valid platforms
            cold += f"<br><sub>{seconds_geomean(p, o['id'], 'cold_s')}</sub>"
            warm += f"<br><sub>{seconds_geomean(p, o['id'], 'warm_s')}</sub>"
        lines.append(
            f"| {medal} | **{name}** | {score} | {cold} | {warm} | {index} | {rss} | {acc} | {verified} "
            f"| {o['valid_platforms']}/{o['entered_platforms']} |{wins}"
        )
    if p["unranked"]:
        names = "、".join(p["scanners"][s]["name"] for s in p["unranked"])
        lines += [
            "",
            f"未上榜（没有任何平台的有效成绩）{' · Unranked (no valid result anywhere)' if bi else ''}：{names}",
        ]
    return lines


def render_kings(p: Dict[str, Any], bi: bool = False) -> List[str]:
    """One line naming the best scanner of each category."""
    rows = p["overall"]
    if not rows:
        return []

    def best(key: str, low: bool = False) -> Optional[Dict[str, Any]]:
        cands = [o for o in rows if o.get(key) is not None]
        if not cands:
            return None
        return min(cands, key=lambda o: o[key]) if low else max(cands, key=lambda o: o[key])

    parts = []
    for zh, en, key, low, fmt in (
        ("冷扫", "Cold", "cold", False, lambda v: f"{v:.1f}"),
        ("热扫", "Warm", "warm", False, lambda v: f"{v:.1f}"),
        ("均衡", "Balanced", "index", False, lambda v: f"{v:.1f}"),
        ("最省内存", "Least RAM", "rss_mb", True, lambda v: f"{v:,.0f} MB"),
        ("最准", "Most accurate", "abs_acc_pct", True, lambda v: f"±{v:.2f}%"),
    ):
        o = best(key, low)
        if o is not None:
            title = f"{zh} {en}" if bi else zh
            parts.append(f"**{title}** {o['scanner']} ({fmt(o[key])})")
    return [("单项第一 · Category winners：" if bi else "单项第一：") + " · ".join(parts)]


OS_GROUP_NAMES = {"linux": "Linux", "macos": "macOS", "windows": "Windows"}
ARCH_NAMES = {"x86_64": "x64", "arm64": "ARM64", "aarch64": "ARM64"}
MAX_GROUP_COLUMNS = 5


def matrix_groups(labels: List[str]) -> List[Tuple[str, List[str]]]:
    """Platforms split into narrow tables: one per OS, and one per OS and architecture when an OS has many columns."""
    by_os: Dict[str, List[str]] = {}
    for lbl in labels:
        by_os.setdefault(parse_label(lbl)[0], []).append(lbl)
    groups: List[Tuple[str, List[str]]] = []
    for os_key, lbls in by_os.items():
        name = OS_GROUP_NAMES.get(os_key, os_key)
        if len(lbls) <= MAX_GROUP_COLUMNS:
            groups.append((name, lbls))
            continue
        by_arch: Dict[str, List[str]] = {}
        for lbl in lbls:
            by_arch.setdefault(parse_label(lbl)[1], []).append(lbl)
        for arch, arch_lbls in by_arch.items():
            groups.append((f"{name} {ARCH_NAMES.get(arch, arch)}", arch_lbls))
    return groups


def render_matrix(p: Dict[str, Any], bi: bool = False) -> List[str]:
    if not bi:
        titles = {lbl: p["platform_info"][lbl]["title"] for lbl in p["platforms"]}
        return matrix_table(p, p["platforms"], titles, False)
    # README: one narrow table per OS (per OS and architecture for Linux's many filesystems), headers "x64 / ext4"
    lines: List[str] = []
    for group, labels in matrix_groups(p["platforms"]):
        titles = {}
        for lbl in labels:
            _, arch, fs = parse_label(lbl)
            titles[lbl] = f"{ARCH_NAMES.get(arch, arch)}<br>{nobreak(FS_NAMES.get(fs, fs))}"
        if lines:
            lines.append("")
        lines += [f"**{nobreak(group)}**", ""] + matrix_table(p, labels, titles, True)
    return lines


def matrix_table(p: Dict[str, Any], labels: List[str], titles: Dict[str, str], bi: bool) -> List[str]:
    order = [o["id"] for o in p["overall"]] + p["unranked"]
    if bi:
        # a scanner with no entry on any of these platforms gets no row in this table
        order = [sid for sid in order if any(p["per_platform"][lbl].get(sid) for lbl in labels)]
    lines = [
        f"| {head('扫描器', 'Scanner', bi)} | " + " | ".join(titles[lbl] for lbl in labels) + " |",
        "| :--- | " + " | ".join(":---:" for _ in labels) + " |",
    ]
    status_bi = {"cannot_run": "⛔", "disqualified": "❌", "invalid": "⚠️"}
    # per platform column: the fastest cold and the fastest warm time in bold (they can belong to different scanners)
    fastest: Dict[str, Dict[str, str]] = {}
    for lbl in labels:
        ok = [e for sid in order if (e := p["per_platform"][lbl].get(sid)) and e["status"] == "ok"]
        fastest[lbl] = {k: fmt_s(min(e[k] for e in ok)) for k in ("cold_s", "warm_s")} if ok else {}
    for sid in order:
        cells = []
        for lbl in labels:
            e = p["per_platform"][lbl].get(sid)
            if e is None:
                cells.append("—")
            elif e["status"] == "ok":
                rank = MEDALS.get(e["rank"], f"#{e['rank']}") + ("❕" if e.get("warnings") else "")
                cold_t, warm_t = fmt_s(e["cold_s"]), fmt_s(e["warm_s"])
                cold_t = mark_best(cold_t, cold_t == fastest[lbl].get("cold_s"))
                warm_t = mark_best(warm_t, warm_t == fastest[lbl].get("warm_s"))
                if bi:
                    cells.append(f"{rank}<br>{cold_t}{NB}/{NB}{warm_t}")
                else:
                    cells.append(f"{rank} {cold_t} / {warm_t}")
            else:
                cells.append(status_bi.get(e["status"], "?") if bi else STATUS_TEXT.get(e["status"], e["status"]))
        name = nobreak(p["scanners"][sid]["name"]) if bi else p["scanners"][sid]["name"]
        lines.append(f"| **{name}** | " + " | ".join(cells) + " |")
    return lines


def render_platforms(p: Dict[str, Any]) -> List[str]:
    lines = [
        "| 平台 | 逻辑核 | $S_{\\text{IOPS}}$ | $B_{\\text{cpu}}$ | 有效/参赛 | 冷扫最快 | 热扫最快 |",
        "| :--- | ---: | ---: | ---: | :---: | :--- | :--- |",
    ]
    for lbl in p["platforms"]:
        info = p["platform_info"][lbl]
        plat = p["per_platform"][lbl]

        def fastest(sid: Optional[str], key: str) -> str:
            if not sid:
                return "-"
            return f"{p['scanners'][sid]['name']} {fmt_s(plat[sid][key])} s"

        iops = f"{info['iops']:,.0f}" if info.get("iops") else "-"
        cpu = f"{info['cpu_ms']:.0f} ms" if info.get("cpu_ms") else "-"
        lines.append(
            f"| {info['title']} | {info.get('cores') or '-'} | {iops} | {cpu} | {info['ok']}/{info['tried']} "
            f"| {fastest(info.get('fastest_cold'), 'cold_s')} | {fastest(info.get('fastest_warm'), 'warm_s')} |"
        )
    return lines


NOTES_EN = [
    "Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time "
    "/ the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of "
    "cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels "
    "out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians "
    "over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable "
    "platforms are left out but marked in the per-platform table, and — means not supported or no native build.",
    "Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is "
    "the same as filling every missing platform with its own average. Running on more platforms therefore does not "
    "make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a "
    "tool with few platforms was only compared where it runs, which the Platforms column shows.",
]


def render_notes(p: Dict[str, Any], bi: bool = False) -> List[str]:
    notes: List[str] = []
    if bi:
        notes += [
            "冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，"
            "用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its "
            "valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only "
            "and the ranks follow the relative scores. "
            "<mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· "
            "<mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform "
            "tables the platform's fastest cold and warm time). "
            "表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not "
            "verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · "
            "核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · "
            "IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。",
            "各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. "
            "⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · "
            "❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。",
        ]
    notes += [
        "少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；"
        "报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。",
    ]
    if bi:
        notes.append(
            "Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly "
            "below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries "
            "counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down."
        )
    notes += [
        "计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ "
        "该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。"
        "综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。"
        "只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。"
        "名次表按该平台三项相对分的几何平均排名。",
        "缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。",
    ]
    if bi:
        notes += NOTES_EN
    if "windows-arm64" in p["platforms"]:
        notes.append("Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。")
        if bi:
            notes.append("Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.")
    # one <sub> block; blank-line-like breaks keep the paragraphs apart (an HTML block would run them together)
    return ["<sub>" + "<br><br>".join(notes) + "</sub>"]


def render_run_summary(p: Dict[str, Any], title_preset: str) -> str:
    lines = [f"# 🏆 Overall Leaderboard 总榜 ({title_preset})", ""] + small_preset_notice(p["preset"])
    info = f"合成数据 `{p['files']:,}` 个文件 + `{p['dirs']:,}` 个目录，共 `{len(p['platforms'])}` 个平台"
    if p.get("sha"):
        info += f"，commit `{p['sha'][:7]}`"
    lines += [info + "。各平台的完整报告在本总榜下方。", ""]
    if p["missing_platforms"]:
        names = "、".join(platform_title(lbl) for lbl in p["missing_platforms"])
        warning = [f"> [!WARNING]\n> 以下平台没有产出结果，未计入总榜：{names}。"]
        if "windows-x86_64-refs" in p["missing_platforms"] and "windows-x86_64" in p["platforms"]:
            warning.append(
                "> 没有 ReFS 成绩，Win x64 NTFS 的成绩没有经过 NTFS/ReFS 交叉核查（MFT 逃逸），只能当作未核查的参考。"
            )
        warning.append("> 缺少核心平台的运行只出现在这份运行总结里，不会发布到 README 榜单。")
        lines += ["\n".join(warning), ""]
    lines += render_overall_table(p) + [""] + render_kings(p)
    lines += ["", "### 各平台名次（冷扫 / 热扫 秒）", ""] + render_matrix(p)
    lines += ["", "### 平台概况", ""] + render_platforms(p)
    lines += [""] + render_notes(p)
    return "\n".join(lines) + "\n"


def assemble_summary(artifacts: Path, leaderboard_md: str) -> str:
    """The leaderboard first, then every platform's full report (and the NTFS/ReFS audit) in platform order."""
    dirs = find_platform_dirs(artifacts)
    order: List[str] = []
    for label in sorted((lbl for lbl in dirs if not lbl.endswith("-ramdisk")), key=platform_sort_key):
        order += [label, f"{label}-ramdisk"]
    parts = [leaderboard_md.rstrip()]
    for label in order:
        report = dirs[label] / "benchmark_report.md" if label in dirs else None
        if report is None or not report.exists():
            continue
        parts.append(report.read_text(encoding="utf-8").rstrip())
        if label == "windows-x86_64-refs":
            audit = dirs.get("windows-x86_64", Path("-")) / "refs_audit.md"
            if audit.exists():
                parts.append(audit.read_text(encoding="utf-8").rstrip())
    return "\n\n---\n\n".join(parts) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="Build the cross-platform overall leaderboard of one run")
    parser.add_argument("--artifacts", required=True, help="Directory the run's result artifacts were downloaded to")
    parser.add_argument("--preset", default="", help="Preset name shown in the title")
    parser.add_argument("--sha", default="", help="Commit the run tested")
    parser.add_argument("--out", default="leaderboard.md", help="Markdown output path")
    parser.add_argument("--json-out", default="leaderboard.json", help="JSON output path")
    parser.add_argument(
        "--summary-out", default="", help="Also write the leaderboard followed by every platform report"
    )
    args = parser.parse_args()

    artifacts = Path(args.artifacts)
    if not any(artifacts.rglob("normalized_results.json")):
        print(f"[leaderboard] no normalized_results.json under {artifacts}", file=sys.stderr)
        return 1
    payload = build_payload(artifacts, args.preset, args.sha)
    md = render_run_summary(payload, args.preset or payload["preset"])
    Path(args.out).write_text(md, encoding="utf-8")
    Path(args.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.summary_out:
        Path(args.summary_out).write_text(assemble_summary(artifacts, md), encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
