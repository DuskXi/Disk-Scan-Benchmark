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
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from disclosure import notice  # noqa: E402
from disclosure import ANCHOR  # noqa: E402
from scoring import (  # noqa: E402
    KIND_LABEL,
    SCORING_NOTE,
    SCORING_NOTE_EN,
    author_note,
    drive_line,
    drive_table,
    drives_summary,
    ranking,
    ranking_table,
    usage,
)
from submission_schema import validate  # noqa: E402

SUBMISSIONS = REPO / "community" / "submissions"
REGISTRY = REPO / "scripts" / "wrappers" / "scanners_registry.json"
README = REPO / "README.md"
COMMUNITY_README = REPO / "community" / "README.md"
START, END = "<!-- COMMUNITY:START -->", "<!-- COMMUNITY:END -->"
# the short entry near the top of the README (render_entry), so the real-drive board is easy to find
ENTRY_START, ENTRY_END = "<!-- COMMUNITY-ENTRY:START -->", "<!-- COMMUNITY-ENTRY:END -->"


def scanner_names() -> Dict[str, str]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {s["id"]: s.get("display_name", s["name"]) for s in data["scanners"]}


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


# --- community board (README) and the full page (community/README.md) ---


def load_submissions() -> List[Tuple[str, Dict[str, Any]]]:
    if not SUBMISSIONS.exists():
        return []
    return [(p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in sorted(SUBMISSIONS.glob("*.json"))]


def all_drives(subs: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[Dict[str, Any], int]]:
    """Every submitted drive with the logical core count of its machine (the balanced score needs it)."""
    return [(v, int(sub["machine"]["logical_cores"])) for _, sub in subs for v in sub["volumes"]]


def board(subs: List[Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Per scanner: each score averaged geometrically over the drives it ran on, then combined (scoring.py)."""
    return ranking(all_drives(subs))


def submission_link(stem: str, repo: str) -> str:
    issue = stem.replace("issue-", "")
    return f"[#{issue}](https://github.com/{repo}/issues/{issue})" if stem.startswith("issue-") else stem


def author_share(subs: List[Tuple[str, Dict[str, Any]]]) -> Optional[Tuple[str, str]]:
    """(Chinese, English): how much of the board comes from this benchmark's author's own machine, from which drives."""
    own = [sub for _, sub in subs if sub.get("by_author")]
    if not own:
        return None
    vols = [v for sub in own for v in sub["volumes"]]
    n = len(subs)
    if len(own) == n:
        zh = "目前收录的成绩全部" if n > 1 else "目前收录的这份成绩"
        en = {1: "The only submission so far comes", 2: "Both submissions so far come"}.get(
            n, f"All {n} submissions so far come"
        )
    else:
        zh, en = f"{n} 份提交里有 {len(own)} 份", f"{len(own)} of {n} submissions come"
    return (
        f"{zh}来自本基准作者自己的电脑：{drives_summary(vols)}，都是日常在用的盘。",
        f"{en} from this benchmark's author's own machine: {drives_summary(vols, True)}, all of them in daily use.",
    )


def author_lines(subs: List[Tuple[str, Dict[str, Any]]]) -> List[str]:
    share = author_share(subs)
    return [f"> ⚖️ {share[0]}<br>", f"> ⚖️ {share[1]}", ""] if share else []


def render_board(subs: List[Tuple[str, Dict[str, Any]]], repo: str) -> List[str]:
    """The README's entry: the overall ranking of all real drives, with the full data one link away."""
    # an explicit anchor: the heading's own one depends on how GitHub slugs its emoji
    lines = [START, "", '<a id="real-drives"></a>', "", "## 🖥️ 社区真实盘成绩 · Community results on real drives", ""]
    if not subs:
        lines += [
            "_还没有社区提交。_ 用 [本地基准套件](docs/LOCAL_SUITE.md) 在自己的硬盘上跑一遍，再提交成绩，就会出现在这里。",
            "",
            "_No submissions yet._ Run the [local suite](docs/LOCAL_SUITE.md) on your own drives and submit the result to "
            "see it here.",
            "",
            END,
        ]
        return lines
    n_vols = sum(len(s["volumes"]) for _, s in subs)
    lines += notice(REGISTRY)  # this benchmark's author also writes some of the scanners it ranks
    lines += author_lines(subs)
    lines += [
        f"来自 {len(subs)} 份提交、{n_vols} 块真实硬盘。每块盘内先算相对分，再在所有盘上取几何平均；"
        "<mark>**高亮**</mark> 为该列最高分。**每份提交、每块盘的全部数据**见 "
        "[community/README.md](community/README.md)，提交方法见 [docs/LOCAL_SUITE.md](docs/LOCAL_SUITE.md)。",
        "",
        f"From {len(subs)} submissions on {n_vols} real drives. Each drive is scored on its own, then the scores are "
        "averaged geometrically over all drives; <mark>**highlighted**</mark> = best in its column. **Every submission "
        "and every drive in full**: [community/README.md](community/README.md); how to submit: "
        "[docs/LOCAL_SUITE.md](docs/LOCAL_SUITE.md).",
        "",
    ]
    lines += ranking_table(board(subs), scanner_names(), bi=True)
    lines += ["", f"<sub>{SCORING_NOTE}<br><br>{SCORING_NOTE_EN}</sub>", "", END]
    return lines


def render_details(subs: List[Tuple[str, Dict[str, Any]]], repo: str) -> str:
    """Every accepted submission, newest first, each drive with every scanner's scores and measured numbers."""
    names = scanner_names()
    lines = [
        "# 社区真实盘成绩 · Community results on real drives",
        "",
        "由 `scripts/local_suite/community.py render` 生成，请勿手改。[返回 README](../README.md) · "
        "[怎样提交](../docs/LOCAL_SUITE.md)",
        "",
        "大家用[本地基准套件](../docs/LOCAL_SUITE.md)在自己的硬盘上跑出的成绩，经维护者核对后收录在这里。"
        "提交里只有数字、扫描器版本、系统版本、CPU 和硬盘型号、文件系统与盘的类型，没有路径、文件夹名、文件名、盘符、卷标、"
        "计算机名或用户名：套件只复制白名单里的字段并在提交前自查，收录前工作流再按同一份白名单校验。",
        "",
        "Results from the [local suite](../docs/LOCAL_SUITE.md) on contributors' own drives, accepted after a "
        "maintainer's check. A submission holds numbers, versions, the OS version, CPU and drive models, filesystem and "
        "drive type, and nothing else: no paths, folder or file names, drive letters, volume labels, computer or user "
        "names.",
        "",
    ]
    if not subs:
        return "\n".join(lines + ["_还没有社区提交 · No submissions yet._", ""]) + "\n"
    lines += notice(REGISTRY, "../README.md") + author_lines(subs)
    drives = all_drives(subs)
    lines += [f"## 综合排名 · Overall（{len(subs)} 份提交、{len(drives)} 块盘）", ""]
    lines += ranking_table(board(subs), names) + ["", f"<sub>{SCORING_NOTE}<br><br>{SCORING_NOTE_EN}</sub>", ""]

    # one row per drive, linking to its submission below
    lines += [
        "## 所有盘 · All drives",
        "",
        "| 提交 | CPU | 用途 | 文件系统 | 类型 | 型号 | 随机读 IOPS | 项数 | 本盘第一 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | ---: | ---: | :--- |",
    ]
    for stem, sub in reversed(subs):
        for i, v in enumerate(sub["volumes"], start=1):
            top = ranking([(v, int(sub["machine"]["logical_cores"]))])[0]
            iops = f"{v['rand_read_iops']:,}" if v.get("rand_read_iops") else "-"
            lines.append(
                f"| {submission_link(stem, repo)} 盘 {i} | {sub['machine']['cpu']} | {usage(v) or '-'} | {v['fs']} | "
                f"{KIND_LABEL.get(v['kind'], v['kind'])} | {v['disk_model']} | {iops} | {v['items_k']:,}k | "
                f"{names.get(top['id'], top['id'])} |"
            )
    lines.append("")

    for stem, sub in reversed(subs):
        m = sub["machine"]
        cores = int(m["logical_cores"])
        lines += [
            f"## {submission_link(stem, repo)} · {m['cpu']} · {m.get('physical_cores') or '?'} 核 / {cores} 线程 · "
            f"{m['ram_gb']} GB · {m['os_version']}",
            "",
            f"提交日期 {sub['date']}，套件版本 `{sub['suite']}`，{len(sub['volumes'])} 块盘。",
            "",
        ]
        lines += author_note(sub, "../README.md" + ANCHOR)
        if len(sub["volumes"]) > 1:
            lines += ["**这份提交的综合**", ""]
            lines += ranking_table(ranking([(v, cores) for v in sub["volumes"]]), names) + [""]
        for i, v in enumerate(sub["volumes"], start=1):
            lines += [drive_line(i, v), ""] + drive_table(v, cores, names) + [""]
    return "\n".join(lines) + "\n"


def render_entry(subs: List[Tuple[str, Dict[str, Any]]]) -> List[str]:
    """The entry near the top of the README: how much real-drive data there is, whose it is, where to read it all
    (no ranking here: the board below shows it next to the conflict-of-interest notice)."""
    lines = [ENTRY_START, ""]
    if not subs:
        lines += [
            "> 🖥️ **真实盘成绩 · Real drives**：还没有社区提交，欢迎用[本地套件](docs/LOCAL_SUITE.md)在自己的硬盘上跑一遍。<br>",
            "> No real-drive submissions yet: run the [local suite](docs/LOCAL_SUITE.md) on your own drives.",
        ]
    else:
        n_vols = sum(len(s["volumes"]) for _, s in subs)
        share = author_share(subs) or ("", "")
        lines += [
            f"> 🖥️ **真实盘成绩 · Real drives**：除了 CI 上的合成数据，这里还有在真实硬盘上跑出的成绩，"
            f"已收录 {len(subs)} 份提交、{n_vols} 块盘。{share[0]}"
            "[看榜单](#real-drives) · [每块盘的全部数据](community/README.md) · [提交你的成绩](docs/LOCAL_SUITE.md)<br>",
            f"> Besides the synthetic CI data: results on real drives, {len(subs)} submissions on {n_vols} drives so far. "
            f"{share[1]} [Board](#real-drives) · [every drive in full](community/README.md) · "
            "[submit yours](docs/LOCAL_SUITE.md)",
        ]
    return lines + ["", ENTRY_END]


def replace_between(text: str, start: str, end: str, block: List[str]) -> str:
    if start not in text or end not in text:
        return text
    before, rest = text.split(start, 1)
    return before + "\n".join(block) + rest.split(end, 1)[1]


def render(repo: str) -> None:
    subs = load_submissions()
    text = README.read_text(encoding="utf-8")
    text = replace_between(text, START, END, render_board(subs, repo))
    text = replace_between(text, ENTRY_START, ENTRY_END, render_entry(subs))
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
