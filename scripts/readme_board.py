#!/usr/bin/env python3
"""
README leaderboard publisher.

Each benchmark run publishes only its own preset: `--ingest` stores that run's leaderboard payload (written by
scripts/leaderboard.py) as leaderboard/data/<kind>-<preset>.json. The README section between the LEADERBOARD
markers and the shields.io endpoint badges under leaderboard/badges/ are then regenerated from every stored preset,
so presets can be run one at a time and the board keeps the latest result of each.

  kind = standard   the cross-platform benchmark (benchmark.yml)
  kind = mft        the NTFS raw-$MFT benchmark (benchmark-mft.yml)

Run without --ingest to only re-render (e.g. after editing this script).
"""

import argparse
import datetime as dt
import json
import math
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

from leaderboard import (
    MEDALS,
    fmt_s,
    fmt_score,
    render_kings,
    render_matrix,
    render_notes,
    render_overall_table,
)

PRESETS = ["very-lite", "lite", "low", "mid", "high", "very-high"]
SMALL = {"very-lite", "lite"}  # reference only: start-up cost dominates the wall clock
PRESET_SIZE = {
    "very-lite": "10 万文件",
    "lite": "40 万文件",
    "low": "100 万文件",
    "mid": "300 万文件",
    "high": "500 万文件",
    "very-high": "900 万文件",
}
START, END = "<!-- LEADERBOARD:START -->", "<!-- LEADERBOARD:END -->"
RANK_COLORS = {1: "e3b341", 2: "a8b3bd", 3: "c47f3d"}


def geomean(values: List[float]) -> Optional[float]:
    vals = [v for v in values if v and v > 0]
    return math.exp(sum(math.log(v) for v in vals) / len(vals)) if vals else None


def load_data(data_dir: Path, kind: str) -> Dict[str, Dict[str, Any]]:
    """preset -> stored record ({'meta', 'payload'}) for one kind, in preset order."""
    found = {}
    for preset in PRESETS:
        path = data_dir / f"{kind}-{preset}.json"
        if path.exists():
            found[preset] = json.loads(path.read_text(encoding="utf-8"))
    return found


def static_badge(label: str, message: str, color: str) -> str:
    def esc(s: str) -> str:
        return urllib.parse.quote(s.replace("-", "--").replace("_", "__"), safe="")

    return f"https://img.shields.io/badge/{esc(label)}-{esc(message)}-{color}"


def endpoint_badge(repo: str, branch: str, file_name: str) -> str:
    raw = f"https://raw.githubusercontent.com/{repo}/{branch}/leaderboard/badges/{file_name}"
    return "https://img.shields.io/endpoint?url=" + urllib.parse.quote(raw, safe="")


def badge_json(label: str, rank: int, score: Optional[float]) -> Dict[str, Any]:
    msg = f"#{rank}" + (f" · {score:.1f}" if score is not None else "")
    return {"schemaVersion": 1, "label": label, "message": msg, "color": RANK_COLORS.get(rank, "4c8eda")}


def cross_size(standard: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One row per scanner: its overall score in each preset and the combined score of the presets >= low."""
    rows: Dict[str, Dict[str, Any]] = {}
    for preset, rec in standard.items():
        for o in rec["payload"]["overall"]:
            row = rows.setdefault(o["id"], {"id": o["id"], "name": o["scanner"], "presets": {}})
            row["presets"][preset] = {"rank": o["rank"], "score": o["overall"]}
    for row in rows.values():
        big = [v["score"] for p, v in row["presets"].items() if p not in SMALL]
        small = [v["score"] for p, v in row["presets"].items() if p in SMALL]
        row["combined"] = geomean(big) if big else geomean(small)
        row["combined_from_small_only"] = not big
    ordered = sorted(rows.values(), key=lambda r: (r["combined_from_small_only"], -(r["combined"] or 0)))
    for pos, row in enumerate(ordered, start=1):
        row["rank"] = pos
    return ordered


def render_section(
    standard: Dict[str, Dict[str, Any]], mft: Dict[str, Dict[str, Any]], repo: str, branch: str
) -> List[str]:
    lines = [START, "", "## 🏆 排行榜 Leaderboard", ""]
    dates = [rec["meta"].get("date", "") for rec in list(standard.values()) + list(mft.values())]
    last = max(dates) if dates else "—"
    scanners = {o["id"] for rec in standard.values() for o in rec["payload"]["overall"]}
    platforms = {lbl for rec in standard.values() for lbl in rec["payload"]["platforms"]}
    header = [
        ("最近更新", last or "—", "4c8eda"),
        ("已测体量", f"{len(standard)}/{len(PRESETS)}", "2ea44f" if len(standard) == len(PRESETS) else "dbab09"),
        ("扫描器", str(len(scanners)), "6f42c1"),
        ("平台", str(len(platforms)), "0969da"),
        ("MFT 专栏", f"{len(mft)} 个体量", "8250df"),
    ]
    lines.append(" ".join(f"![{lbl}]({static_badge(lbl, msg, col)})" for lbl, msg, col in header))
    lines += [
        "",
        "> 每个体量单独运行、单独更新：哪个体量跑完就刷新哪一列，其余保持上次的结果。"
        "`very-lite` / `lite` 体量过小，计时以进程启动等固定开销为主，只作参考，不计入跨体量综合分。"
        "评分方法与数据生成原理见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。",
        "",
    ]
    if not standard:
        lines += ["_还没有已发布的运行结果。_", "", END]
        return lines

    # Cross-size board
    present = [p for p in PRESETS if p in standard]
    head = (
        ["名次", "扫描器", "**综合分**（low 及以上）"] + [f"{p}{'*' if p in SMALL else ''}" for p in present] + ["徽章"]
    )
    lines += [
        "### 跨体量总榜",
        "",
        "| " + " | ".join(head) + " |",
        "| " + " | ".join([":---:", ":---", "---:"] + [":---:" for _ in present] + [":---:"]) + " |",
    ]
    for row in cross_size(standard):
        medal = MEDALS.get(row["rank"], str(row["rank"]))
        combined = fmt_score(row["combined"]) + (" *" if row["combined_from_small_only"] else "")
        cells = []
        for p in present:
            v = row["presets"].get(p)
            cells.append(f"{MEDALS.get(v['rank'], '#' + str(v['rank']))} {fmt_score(v['score'])}" if v else "—")
        badge = f"![{row['name']}]({endpoint_badge(repo, branch, row['id'] + '.json')})"
        lines.append(f"| {medal} | **{row['name']}** | **{combined}** | " + " | ".join(cells) + f" | {badge} |")
    lines += [
        "",
        "<sub>* 仅供参考的小体量；综合分带 * 的扫描器只有小体量成绩。综合分 = 各体量综合分的几何平均。缺平台、缺体量都不扣分也不加分：只用它实际跑过的平台和体量计算，等于把缺的部分按它自己的平均分补上，平台多的工具不会因此更容易刷分，平台少的工具也不会因此被扣分。</sub>",
        "",
    ]

    # Per-preset details, the largest reliable preset open
    open_preset = next((p for p in reversed(present) if p not in SMALL), present[-1])
    lines += ["### 各体量详情", ""]
    for p in reversed(present):
        rec = standard[p]
        meta, payload = rec["meta"], rec["payload"]
        run = f"<a href=\"{meta['run_url']}\">run {meta.get('run_id', '')}</a>" if meta.get("run_url") else ""
        sha = f" · commit <code>{meta['sha'][:7]}</code>" if meta.get("sha") else ""
        note = " · 仅供参考" if p in SMALL else ""
        lines += [
            f"<details{' open' if p == open_preset else ''}>",
            f"<summary><b>{p}</b> · {PRESET_SIZE.get(p, '')} · {meta.get('date', '')} · {run}{sha}{note}</summary>",
            "",
        ]
        lines += render_overall_table(payload) + [""] + render_kings(payload)
        lines += ["", "**各平台名次（冷扫 / 热扫 秒）**", ""] + render_matrix(payload)
        lines += [""] + render_notes(payload) + ["", "</details>", ""]

    # NTFS raw-MFT column
    lines += ["### NTFS MFT 专栏", ""]
    if not mft:
        lines += ["_还没有已发布的 MFT 运行结果（工作流 `benchmark-mft.yml`）。_", ""]
    else:
        lines += [
            "直接读取 NTFS `$MFT` 的扫描模式单独比较（冷热两次耗时应接近，因为每次都要读完整个 MFT）。"
            "这里的成绩不和上面的普通遍历混排。",
            "",
        ]
        mft_present = [p for p in PRESETS if p in mft]
        ids: Dict[str, str] = {}
        for rec in mft.values():
            for o in rec["payload"]["overall"]:
                ids.setdefault(o["id"], o["scanner"])
        lines += [
            "| 扫描器 | " + " | ".join(mft_present) + " | 徽章 |",
            "| :--- | " + " | ".join(":---:" for _ in mft_present) + " | :---: |",
        ]
        for sid, name in ids.items():
            cells = []
            for p in mft_present:
                payload = mft[p]["payload"]
                o = next((x for x in payload["overall"] if x["id"] == sid), None)
                mft_plats: List[Dict[str, Any]] = list(payload["per_platform"].values())
                plat = mft_plats[0].get(sid) if mft_plats else None
                if o and plat and plat.get("status") == "ok":
                    medal = MEDALS.get(o["rank"], f"#{o['rank']}")
                    cells.append(f"{medal} {fmt_s(plat['cold_s'])} / {fmt_s(plat['warm_s'])} s")
                else:
                    cells.append("—")
            badge_file = f"{sid}-mft-{mft_present[-1]}.json"
            lines.append(
                f"| **{name}** | "
                + " | ".join(cells)
                + f" | ![{name} MFT]({endpoint_badge(repo, branch, badge_file)}) |"
            )
        lines += ["", "<sub>单元格：名次 冷扫 / 热扫 秒。</sub>", ""]

    # Badge snippets for other READMEs
    board_url = f"https://github.com/{repo}#-排行榜-leaderboard"
    lines += [
        "### 在你的 README 里显示成绩",
        "",
        "徽章由 CI 在每次发布时更新，内容是该扫描器的最新名次和综合分。把下面一行贴进任何 Markdown：",
        "",
        "```markdown",
    ]
    for row in cross_size(standard):
        lines.append(f"[![{row['name']}]({endpoint_badge(repo, branch, row['id'] + '.json')})]({board_url})")
    lines += [
        "```",
        "",
        "只看某个体量：把文件名换成 `<扫描器>-<体量>.json`（例如 `gdu-low.json`）；MFT 专栏用 "
        "`<扫描器>-mft-<体量>.json`。也可以用 `python scripts/readme_board.py --snippet <扫描器> [--preset low]` 生成。",
        "",
        END,
    ]
    return lines


def write_badges(standard: Dict[str, Dict[str, Any]], mft: Dict[str, Dict[str, Any]], badge_dir: Path) -> None:
    badge_dir.mkdir(parents=True, exist_ok=True)
    for row in cross_size(standard):
        payload = badge_json(f"{row['name']} · disk-scan-bench", row["rank"], row["combined"])
        (badge_dir / f"{row['id']}.json").write_text(json.dumps(payload), encoding="utf-8")
    for kind, data in (("", standard), ("mft-", mft)):
        for preset, rec in data.items():
            for o in rec["payload"]["overall"]:
                label = f"{o['scanner']} · {'MFT ' if kind else ''}{preset}"
                out = badge_dir / f"{o['id']}-{kind}{preset}.json"
                out.write_text(json.dumps(badge_json(label, o["rank"], o["overall"])), encoding="utf-8")


def update_readme(readme: Path, section: List[str]) -> None:
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    block = "\n".join(section)
    if START in text and END in text:
        before, rest = text.split(START, 1)
        after = rest.split(END, 1)[1]
        text = before + block + after
    else:
        # First publish: put the board right after the title paragraph
        parts = text.split("\n\n", 2)
        text = "\n\n".join(parts[:2] + [block] + parts[2:]) if len(parts) >= 2 else text + "\n\n" + block + "\n"
    readme.write_text(text, encoding="utf-8", newline="\n")


SCANNERS_START, SCANNERS_END = "<!-- SCANNERS:START -->", "<!-- SCANNERS:END -->"
OS_LABELS = {"linux": "Linux", "macos": "macOS", "windows": "Windows"}


def render_scanners(registry: Path) -> List[str]:
    """The participant table, straight from scanners_registry.json."""
    data = json.loads(registry.read_text(encoding="utf-8"))
    lines = [
        SCANNERS_START,
        "",
        "| 扫描器 | 锁定版本 | 平台 | 架构 | 大小口径 | 说明 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for s in data["scanners"]:
        if not s.get("enabled", True):
            continue
        oses = ", ".join(OS_LABELS.get(o, o) for o in s.get("platforms", []))
        arches = ", ".join(f"`{a}`" for a in s.get("architectures", []))
        metric = s.get("size_metric", "allocated")
        if s.get("apparent_on"):
            metric += "（" + "、".join(OS_LABELS.get(o, o) for o in s["apparent_on"]) + " 上为 apparent）"
        mode = "图形界面" if s.get("runner_type") == "win_gui" else "命令行"
        if s.get("mft"):
            mode += "，参加 MFT 专栏"
        note = s.get("notes", "")
        lines.append(
            f"| **{s['name']}** | `{s['version']}` | {oses} | {arches} | {metric} | {mode}{'；' + note if note else ''} |"
        )
    off = [s["name"] for s in data["scanners"] if not s.get("enabled", True)]
    if off:
        lines += ["", f"<sub>未参加：{'、'.join(off)}（原因见注册表）。</sub>"]
    lines += ["", SCANNERS_END]
    return lines


def replace_block(readme: Path, start: str, end: str, block: List[str]) -> None:
    """Swap the text between two markers; leaves the file alone when the markers are missing."""
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if start not in text or end not in text:
        return
    before, rest = text.split(start, 1)
    readme.write_text(before + "\n".join(block) + rest.split(end, 1)[1], encoding="utf-8", newline="\n")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description="Publish leaderboard payloads into README.md and badge files")
    ap.add_argument("--ingest", default="", help="leaderboard.json of the run to publish")
    ap.add_argument("--kind", choices=["standard", "mft"], default="standard")
    ap.add_argument("--preset", default="", help="Preset of the ingested run (defaults to the payload's)")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--sha", default="")
    ap.add_argument("--data-dir", default="leaderboard/data")
    ap.add_argument("--badge-dir", default="leaderboard/badges")
    ap.add_argument("--readme", default="README.md")
    ap.add_argument("--repo", default="DuskXi/Disk-Scan-Benchmark", help="owner/name used in badge URLs")
    ap.add_argument("--branch", default="main", help="Branch the badge JSON is served from")
    ap.add_argument("--snippet", default="", help="Print the Markdown badge for this scanner id and exit")
    ap.add_argument("--allow-partial", action="store_true", help="Publish even if some core platforms are missing")
    ap.add_argument("--registry", default="scripts/wrappers/scanners_registry.json", help="Source of the scanner list")
    args = ap.parse_args()

    if args.snippet:
        name = f"{args.snippet}-{args.preset}.json" if args.preset else f"{args.snippet}.json"
        url = endpoint_badge(args.repo, args.branch, name)
        print(f"[![{args.snippet}]({url})](https://github.com/{args.repo}#-排行榜-leaderboard)")
        return 0

    data_dir = Path(args.data_dir)
    if args.ingest:
        payload = json.loads(Path(args.ingest).read_text(encoding="utf-8"))
        preset = args.preset or payload.get("preset", "")
        if preset not in PRESETS:
            print(f"[readme_board] preset {preset!r} is not a standard preset; nothing published", file=sys.stderr)
            return 1
        if payload.get("missing_platforms") and not args.allow_partial:
            # A run with failed platforms would replace this preset's complete result with a partial one
            print(
                f"[readme_board] not publishing: platforms without results {payload['missing_platforms']}",
                file=sys.stderr,
            )
            return 0
        data_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "meta": {
                "kind": args.kind,
                "preset": preset,
                "run_id": args.run_id,
                "run_url": args.run_url,
                "sha": args.sha or payload.get("sha", ""),
                "date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
            },
            "payload": payload,
        }
        out = data_dir / f"{args.kind}-{preset}.json"
        out.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print(f"[readme_board] stored {out}")

    standard, mft = load_data(data_dir, "standard"), load_data(data_dir, "mft")
    update_readme(Path(args.readme), render_section(standard, mft, args.repo, args.branch))
    registry = Path(args.registry)
    if registry.exists():
        replace_block(Path(args.readme), SCANNERS_START, SCANNERS_END, render_scanners(registry))
    write_badges(standard, mft, Path(args.badge_dir))
    print(f"[readme_board] README and badges rendered from {len(standard)} standard and {len(mft)} MFT preset(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
