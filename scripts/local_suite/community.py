#!/usr/bin/env python3
"""
Community submissions: check an issue or PR, accept it into community/submissions/, render the community board.

  community.py check-issue --event $GITHUB_EVENT_PATH --comment-out comment.md   # exit 0 = valid
  community.py accept --event $GITHUB_EVENT_PATH                                  # store + re-render
  community.py check-files community/submissions/x.json ...                     # PR check
  community.py render                                                             # README + community/README.md

The issue body is only ever parsed as JSON here; nothing from it reaches a shell.
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))

from submission_schema import validate  # noqa: E402

SUBMISSIONS = REPO / "community" / "submissions"
REGISTRY = REPO / "scripts" / "wrappers" / "scanners_registry.json"
README = REPO / "README.md"
COMMUNITY_README = REPO / "community" / "README.md"
START, END = "<!-- COMMUNITY:START -->", "<!-- COMMUNITY:END -->"
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def scanner_names() -> Dict[str, str]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {s["id"]: s["name"] for s in data["scanners"]}


def extract_json(body: str) -> Optional[Any]:
    """The submission is the first ```json block of the issue body (the issue form renders its field that way)."""
    for block in re.findall(r"```(?:json)?\s*\n(.*?)\n```", body or "", flags=re.S):
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            continue
    return None


def check(sub: Any) -> Tuple[List[str], List[str]]:
    return validate(sub, set(scanner_names()))


def comment_for(errors: List[str], warnings: List[str]) -> str:
    if errors:
        lines = [
            "### ❌ 提交没有通过校验",
            "",
            "请用最新版的本地套件重新生成，或按下面的提示修改后编辑这个 issue：",
            "",
        ]
        lines += [f"- {e}" for e in errors]
    else:
        lines = [
            "### ✅ 提交格式正确",
            "",
            "数据里只有允许的字段，没有发现路径或个人信息。维护者核对后会打上 `accepted` 标签，成绩随后进入 README 的社区榜单。",
        ]
    if warnings:
        lines += ["", "**需要注意：**", ""] + [f"- {w}" for w in warnings]
    return "\n".join(lines) + "\n"


def load_event(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# --- community board ---


def geomean(values: List[float]) -> Optional[float]:
    vals = [v for v in values if v and v > 0]
    return math.exp(sum(math.log(v) for v in vals) / len(vals)) if vals else None


def load_submissions() -> List[Tuple[str, Dict[str, Any]]]:
    if not SUBMISSIONS.exists():
        return []
    return [(p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in sorted(SUBMISSIONS.glob("*.json"))]


def board(subs: List[Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Per scanner: geometric mean over all submitted volumes of its score relative to the volume's best."""
    per: Dict[str, Dict[str, List[float]]] = {}
    for _, sub in subs:
        for vol in sub["volumes"]:
            res = vol["results"]
            best_warm = min(r["warm_ms"] for r in res)
            best_cold = min(r["cold_ms"] for r in res) if vol["cold_purged"] else None
            for r in res:
                entry = per.setdefault(r["scanner"], {"cold": [], "warm": [], "vols": []})
                entry["warm"].append(best_warm / r["warm_ms"] * 100)
                if best_cold:
                    entry["cold"].append(best_cold / r["cold_ms"] * 100)
                entry["vols"].append(1)
    rows: List[Dict[str, Any]] = []
    for sid, e in per.items():
        cold, warm = geomean(e["cold"]), geomean(e["warm"])
        rows.append(
            {
                "id": sid,
                "cold": cold,
                "warm": warm,
                "score": geomean([v for v in (cold, warm) if v]),
                "volumes": len(e["vols"]),
            }
        )
    rows.sort(key=lambda r: -float(r["score"] or 0))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def render_board(subs: List[Tuple[str, Dict[str, Any]]], repo: str) -> List[str]:
    names = scanner_names()
    lines = [START, "", "## 🖥️ 社区真实盘成绩", ""]
    if not subs:
        lines += [
            "_还没有社区提交。_ 用 [本地基准套件](docs/LOCAL_SUITE.md) 在自己的硬盘上跑一遍，再提交成绩，就会出现在这里。",
            "",
            END,
        ]
        return lines
    n_vols = sum(len(s["volumes"]) for _, s in subs)
    lines += [
        f"来自 {len(subs)} 份提交、{n_vols} 块真实硬盘。每块盘内先算相对分（该盘最快 ÷ 自己 × 100），再在所有盘上取几何平均；"
        "没能清缓存的盘只计热扫。提交方法见 [docs/LOCAL_SUITE.md](docs/LOCAL_SUITE.md)，每块盘的明细见 "
        "[community/README.md](community/README.md)。",
        "",
        "| 名次 | 扫描器 | **综合分** | 冷扫 | 热扫 | 测过的盘 |",
        "| :---: | :--- | ---: | ---: | ---: | ---: |",
    ]
    for r in board(subs):
        fmt = lambda v: "-" if v is None else f"{v:.1f}"  # noqa: E731
        lines.append(
            f"| {MEDALS.get(r['rank'], str(r['rank']))} | **{names.get(r['id'], r['id'])}** | **{fmt(r['score'])}** "
            f"| {fmt(r['cold'])} | {fmt(r['warm'])} | {r['volumes']} |"
        )
    lines += ["", END]
    return lines


def render_details(subs: List[Tuple[str, Dict[str, Any]]], repo: str) -> str:
    names = scanner_names()
    lines = ["# 社区真实盘成绩明细", "", "由 `scripts/local_suite/community.py render` 生成，请勿手改。", ""]
    for stem, sub in reversed(subs):
        m = sub["machine"]
        issue = stem.replace("issue-", "")
        link = f"[#{issue}](https://github.com/{repo}/issues/{issue})" if stem.startswith("issue-") else stem
        lines += [
            f"## {link} · {m['cpu']} · {m['logical_cores']} 线程 · {m['ram_gb']} GB · {m['os']} {m['os_version']}",
            "",
            f"提交日期 {sub['date']}，套件版本 `{sub['suite']}`。",
            "",
        ]
        for i, v in enumerate(sub["volumes"], start=1):
            note = "" if v["cold_purged"] else "（未能清缓存：冷扫实为热扫）"
            lines += [
                f"**盘 {i}**：{v['fs']} · {v['media']} · {v['bus']} · {v['disk_model']} · "
                f"{v['used_gb']}/{v['size_gb']} GB · 约 {v['items_k']}k 项{note}",
                "",
                "| 扫描器 | 版本 | 冷扫 (s) | 热扫 (s) | 峰值内存 (MB) | 报告大小 (GB) |",
                "| :--- | :--- | ---: | ---: | ---: | ---: |",
            ]
            for r in sorted(v["results"], key=lambda r: r["cold_ms"]):
                lines.append(
                    f"| {names.get(r['scanner'], r['scanner'])} | `{r['version']}` | {r['cold_ms'] / 1000:.2f} "
                    f"| {r['warm_ms'] / 1000:.2f} | {r['peak_rss_mb']:.0f} | {r['size_gb']} |"
                )
            lines.append("")
    return "\n".join(lines) + "\n"


def render(repo: str) -> None:
    subs = load_submissions()
    text = README.read_text(encoding="utf-8")
    block = "\n".join(render_board(subs, repo))
    if START in text and END in text:
        before, rest = text.split(START, 1)
        text = before + block + rest.split(END, 1)[1]
        README.write_text(text, encoding="utf-8", newline="\n")
    COMMUNITY_README.parent.mkdir(parents=True, exist_ok=True)
    COMMUNITY_README.write_text(render_details(subs, repo), encoding="utf-8", newline="\n")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser(description="Community submission checks and board")
    ap.add_argument("command", choices=["check-issue", "accept", "check-files", "render"])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--event", default="")
    ap.add_argument("--comment-out", default="")
    ap.add_argument("--repo", default="DuskXi/Disk-Scan-Benchmark")
    args = ap.parse_args()

    if args.command == "render":
        render(args.repo)
        return 0

    if args.command == "check-files":
        failed = False
        for f in args.files:
            try:
                sub = json.loads(Path(f).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"{f}: not readable JSON ({exc})")
                failed = True
                continue
            errors, warnings = check(sub)
            print(f"{f}: {'OK' if not errors else 'REJECTED'}")
            for line in errors + warnings:
                print(f"  - {line}")
            failed = failed or bool(errors)
        return 1 if failed else 0

    event = load_event(args.event)
    issue = event["issue"]
    sub = extract_json(issue.get("body") or "")
    errors, warnings = (["没有在 issue 里找到 JSON 代码块"], []) if sub is None else check(sub)
    if args.comment_out:
        Path(args.comment_out).write_text(comment_for(errors, warnings), encoding="utf-8")
    if args.command == "check-issue":
        print("valid" if not errors else "invalid")
        return 1 if errors else 0

    # accept
    if errors:
        print("not accepted: " + "; ".join(errors))
        return 1
    SUBMISSIONS.mkdir(parents=True, exist_ok=True)
    out = SUBMISSIONS / f"issue-{int(issue['number'])}.json"
    out.write_text(json.dumps(sub, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    render(args.repo)
    print(f"stored {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
