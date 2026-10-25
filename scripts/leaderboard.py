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
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Display order of the platforms (results directory label -> column title)
PLATFORMS: List[Tuple[str, str]] = [
    ("linux-x86_64", "Linux x64"),
    ("linux-arm64", "Linux ARM64"),
    ("macos-x86_64", "macOS x64"),
    ("macos-arm64", "macOS ARM64"),
    ("windows-x86_64", "Win x64 NTFS"),
    ("windows-x86_64-refs", "Win x64 ReFS"),
    ("windows-arm64", "Win ARM64 NTFS"),
]
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def geomean(values: List[float]) -> Optional[float]:
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
            parts = [cold_rel, warm_rel] + ([index_rel] if index_rel else [])
            out[r["id"]] = {
                "status": "ok",
                "cold_s": float(r["cold_time_ms"]) / 1000.0,
                "warm_s": float(r["warm_time_ms"]) / 1000.0,
                "cold_rel": cold_rel,
                "warm_rel": warm_rel,
                "index_rel": index_rel,
                "platform_score": geomean(parts),
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


def build(artifacts: Path, preset: str, sha: str) -> Tuple[str, Dict[str, Any]]:
    dirs = find_platform_dirs(artifacts)
    known = [label for label, _ in PLATFORMS]
    titles = dict(PLATFORMS)
    # Unlisted labels (a new runner) still show up, after the known ones; the RAM-disk pass is not a real disk
    extra = sorted(lbl for lbl in dirs if lbl not in known and not lbl.endswith("-ramdisk"))
    labels = [lbl for lbl in known if lbl in dirs] + extra
    missing = [titles[lbl] for lbl in known if lbl not in dirs]

    per_platform: Dict[str, Dict[str, Dict[str, Any]]] = {}
    baselines: Dict[str, Dict[str, Any]] = {}
    scanners: Dict[str, Dict[str, str]] = {}
    gt: Dict[str, Any] = {}
    for label in labels:
        data = json.loads((dirs[label] / "normalized_results.json").read_text(encoding="utf-8"))
        rows = data.get("results", [])
        gt = gt or data.get("ground_truth", {})
        baselines[label] = data.get("baseline", {})
        per_platform[label] = score_platform(rows)
        for r in rows:
            scanners.setdefault(r["id"], {"name": r.get("scanner", r["id"]), "version": str(r.get("version", "-"))})

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
        index = geomean([e["index_rel"] for e in ok if e.get("index_rel")])
        total = geomean([v for v in (cold, warm, index) if v])
        overall.append(
            {
                "id": sid,
                "scanner": meta["name"],
                "version": meta["version"],
                "overall": total,
                "cold": cold,
                "warm": warm,
                "index": index,
                "valid_platforms": len(ok),
                "entered_platforms": len(entries),
                "wins": sum(1 for e in ok if e.get("rank") == 1),
            }
        )
    overall.sort(key=lambda o: (-(o["overall"] or 0), -o["valid_platforms"]))
    for pos, o in enumerate(overall, start=1):
        o["rank"] = pos

    files, dirs_n = int(gt.get("total_files", 0)), int(gt.get("total_dirs", 0))
    head = f"# 🏆 Overall Leaderboard 总榜 ({preset})"
    lines = [head, ""]
    info = f"合成数据 `{files:,}` 个文件 + `{dirs_n:,}` 个目录，共 `{len(labels)}` 个平台"
    if sha:
        info += f"，commit `{sha[:7]}`"
    lines += [info + "。各平台的完整报告在本总榜下方。", ""]
    if missing:
        lines += [f"> [!WARNING]\n> 以下平台没有产出结果，未计入总榜：{'、'.join(missing)}", ""]

    lines += [
        "| 名次 | 扫描器 | **综合分** | 冷扫 | 热扫 | 均衡指数 | 有效平台 | 平台第一 |",
        "| :---: | :--- | ---: | ---: | ---: | ---: | :---: | :---: |",
    ]
    for o in overall:
        medal = MEDALS.get(o["rank"], str(o["rank"]))
        lines.append(
            f"| {medal} | **{o['scanner']}** | **{fmt_score(o['overall'])}** | {fmt_score(o['cold'])} "
            f"| {fmt_score(o['warm'])} | {fmt_score(o['index'])} | {o['valid_platforms']}/{o['entered_platforms']} "
            f"| {o['wins'] or '-'} |"
        )
    if unranked:
        names = "、".join(scanners[s]["name"] for s in unranked)
        lines += ["", f"未上榜（没有任何平台的有效成绩）：{names}"]

    # Per-platform matrix: rank and raw cold / warm seconds, or why there is no result
    status_text = {"cannot_run": "⛔ 无法运行", "disqualified": "❌ 违规", "invalid": "⚠️ 无效"}
    order = [o["id"] for o in overall] + unranked
    lines += [
        "",
        "### 各平台名次（冷扫 / 热扫 秒）",
        "",
        "| 扫描器 | " + " | ".join(titles.get(lbl, lbl) for lbl in labels) + " |",
        "| :--- | " + " | ".join(":---:" for _ in labels) + " |",
    ]
    for sid in order:
        cells = []
        for lbl in labels:
            e = per_platform[lbl].get(sid)
            if e is None:
                cells.append("—")
            elif e["status"] == "ok":
                rank = MEDALS.get(e["rank"], f"#{e['rank']}")
                cells.append(f"{rank} {fmt_s(e['cold_s'])} / {fmt_s(e['warm_s'])}")
            else:
                cells.append(status_text[e["status"]])
        lines.append(f"| **{scanners[sid]['name']}** | " + " | ".join(cells) + " |")

    # Platform overview: the hardware each column ran on and who won it
    lines += [
        "",
        "### 平台概况",
        "",
        "| 平台 | 逻辑核 | $S_{\\text{IOPS}}$ | $B_{\\text{cpu}}$ | 有效/参赛 | 冷扫最快 | 热扫最快 |",
        "| :--- | ---: | ---: | ---: | :---: | :--- | :--- |",
    ]
    for lbl in labels:
        b = baselines[lbl]
        plat = per_platform[lbl]
        ok_ids = [sid for sid, e in plat.items() if e["status"] == "ok"]
        tried = [sid for sid, e in plat.items() if e["status"] != "cannot_run"]

        def fastest(key: str) -> str:
            if not ok_ids:
                return "-"
            sid = min(ok_ids, key=lambda s: plat[s][key])
            return f"{scanners[sid]['name']} {fmt_s(plat[sid][key])} s"

        iops = float(b.get("b_rand_read_iops") or 0)
        cpu_ms = float(b.get("b_cpu_ms") or 0)
        lines.append(
            f"| {titles.get(lbl, lbl)} | {b.get('logical_cores', '-')} | {f'{iops:,.0f}' if iops else '-'} "
            f"| {f'{cpu_ms:.0f} ms' if cpu_ms else '-'} | {len(ok_ids)}/{len(tried)} "
            f"| {fastest('cold_s')} | {fastest('warm_s')} |"
        )

    notes = [
        "",
        "<sub>",
        "计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ "
        "该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。"
        "综合分 = 冷扫、热扫、均衡指数三项的几何平均。只计有效成绩：违规、无效、无法运行的平台不计入，"
        "但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。"
        "综合分只按扫描器跑过的平台计算，覆盖面看「有效平台」列。",
    ]
    if "windows-arm64" in labels:
        notes.append("Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。")
    notes.append("</sub>")
    lines += notes

    payload = {
        "preset": preset,
        "platforms": labels,
        "missing_platforms": missing,
        "overall": overall,
        "unranked": unranked,
        "per_platform": per_platform,
    }
    return "\n".join(lines) + "\n", payload


def assemble_summary(artifacts: Path, leaderboard_md: str) -> str:
    """The leaderboard first, then every platform's full report (and the NTFS/ReFS audit) in platform order."""
    dirs = find_platform_dirs(artifacts)
    known = [label for label, _ in PLATFORMS]
    order: List[str] = []
    for label in known + sorted(lbl for lbl in dirs if lbl not in known and not lbl.endswith("-ramdisk")):
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
    md, payload = build(artifacts, args.preset, args.sha)
    Path(args.out).write_text(md, encoding="utf-8")
    Path(args.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.summary_out:
        Path(args.summary_out).write_text(assemble_summary(artifacts, md), encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
