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
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


def _median(values: List[Optional[float]]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return statistics.median(vals) if vals else None


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

    overall: List[Dict[str, Any]] = []
    unranked: List[str] = []
    for sid, meta in scanners.items():
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

    return {
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
        "overall": overall,
        "unranked": unranked,
        "per_platform": per_platform,
    }


# --- Markdown rendering (shared with scripts/readme_board.py) ---


def render_overall_table(p: Dict[str, Any]) -> List[str]:
    lines = [
        "| 名次 | 扫描器 | **综合分** | 冷扫 | 热扫 | 均衡指数 | 峰值内存 | 大小误差 | 核验 | 有效平台 | 平台第一 |",
        "| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: | :---: |",
    ]
    for o in p["overall"]:
        medal = MEDALS.get(o["rank"], str(o["rank"]))
        rss = f"{o['rss_mb']:,.0f} MB" if o.get("rss_mb") else "-"
        acc = f"{o['abs_acc_pct']:.2f}%" if o.get("abs_acc_pct") is not None else "未核验"
        lines.append(
            f"| {medal} | **{o['scanner']}** | **{fmt_score(o['overall'])}** | {fmt_score(o['cold'])} "
            f"| {fmt_score(o['warm'])} | {fmt_score(o['index'])} | {rss} | {acc} | {verification_label(o.get('verification'))} "
            f"| {o['valid_platforms']}/{o['entered_platforms']} | {o['wins'] or '-'} |"
        )
    if p["unranked"]:
        names = "、".join(p["scanners"][s]["name"] for s in p["unranked"])
        lines += ["", f"未上榜（没有任何平台的有效成绩）：{names}"]
    return lines


def render_kings(p: Dict[str, Any]) -> List[str]:
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
    for title, key, low, fmt in (
        ("冷扫", "cold", False, lambda v: f"{v:.1f}"),
        ("热扫", "warm", False, lambda v: f"{v:.1f}"),
        ("均衡", "index", False, lambda v: f"{v:.1f}"),
        ("最省内存", "rss_mb", True, lambda v: f"{v:,.0f} MB"),
        ("最准", "abs_acc_pct", True, lambda v: f"误差 {v:.2f}%"),
    ):
        o = best(key, low)
        if o is not None:
            parts.append(f"**{title}** {o['scanner']}（{fmt(o[key])}）")
    return ["单项第一：" + " · ".join(parts)]


def render_matrix(p: Dict[str, Any]) -> List[str]:
    labels = p["platforms"]
    titles = {lbl: p["platform_info"][lbl]["title"] for lbl in labels}
    order = [o["id"] for o in p["overall"]] + p["unranked"]
    lines = [
        "| 扫描器 | " + " | ".join(titles[lbl] for lbl in labels) + " |",
        "| :--- | " + " | ".join(":---:" for _ in labels) + " |",
    ]
    for sid in order:
        cells = []
        for lbl in labels:
            e = p["per_platform"][lbl].get(sid)
            if e is None:
                cells.append("—")
            elif e["status"] == "ok":
                rank = MEDALS.get(e["rank"], f"#{e['rank']}")
                cells.append(f"{rank} {fmt_s(e['cold_s'])} / {fmt_s(e['warm_s'])}")
            else:
                cells.append(STATUS_TEXT.get(e["status"], e["status"]))
        lines.append(f"| **{p['scanners'][sid]['name']}** | " + " | ".join(cells) + " |")
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


def render_notes(p: Dict[str, Any]) -> List[str]:
    notes = [
        "<sub>",
        "计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ "
        "该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。"
        "综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。"
        "只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。"
        "名次表按该平台三项相对分的几何平均排名。",
        "缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看「有效平台」列。",
    ]
    if "windows-arm64" in p["platforms"]:
        notes.append("Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。")
    notes.append("</sub>")
    return notes


def render_run_summary(p: Dict[str, Any], title_preset: str) -> str:
    lines = [f"# 🏆 Overall Leaderboard 总榜 ({title_preset})", ""] + small_preset_notice(p["preset"])
    info = f"合成数据 `{p['files']:,}` 个文件 + `{p['dirs']:,}` 个目录，共 `{len(p['platforms'])}` 个平台"
    if p.get("sha"):
        info += f"，commit `{p['sha'][:7]}`"
    lines += [info + "。各平台的完整报告在本总榜下方。", ""]
    if p["missing_platforms"]:
        names = "、".join(platform_title(lbl) for lbl in p["missing_platforms"])
        lines += [f"> [!WARNING]\n> 以下平台没有产出结果，未计入总榜：{names}", ""]
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
