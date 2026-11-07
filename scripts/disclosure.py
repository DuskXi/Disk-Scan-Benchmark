#!/usr/bin/env python3
"""
Conflict-of-interest notice: this benchmark's author also writes one of the scanners it ranks (SpaceKnife).

The scanners concerned carry "author_project": true in scanners_registry.json. README.md says so in a short note under
the title and explains it under "利益声明 · Conflict of interest" (hand-written, below the boards so the scores stay at
the top); every generated README section that ranks scanners opens with notice(), and the scanner table marks them with
table_note().
"""

import json
from pathlib import Path
from typing import List

REGISTRY = Path(__file__).resolve().parent / "wrappers" / "scanners_registry.json"
ANCHOR = "#利益声明--conflict-of-interest"  # the README heading "## 利益声明 · Conflict of interest"


def author_projects(registry: Path = REGISTRY) -> List[str]:
    """Names shown on the boards of the scanners that belong to a project of this benchmark's author."""
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return [s.get("display_name", s["name"]) for s in data.get("scanners", []) if s.get("author_project")]


def notice(registry: Path = REGISTRY, readme: str = "") -> List[str]:
    """A quoted Chinese and English line for the top of a ranking (nothing when no scanner is marked); one paragraph,
    so it takes little room above the scores."""
    names = author_projects(registry)
    if not names:
        return []
    link = readme + ANCHOR  # readme: the path to README.md from a page elsewhere, e.g. "../README.md"
    zh = "、".join(names[:-1]) + " 和 " + names[-1] if len(names) > 1 else names[0]
    en = ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]
    many = len(names) > 1
    return [
        f"> ⚖️ **利益声明**：{zh} 属于本基准作者的项目，作者从{'它们' if many else '它'}的排名中直接受益，"
        f"详见[利益声明]({link})。<br>",
        f"> ⚖️ **Conflict of interest**: {en} {'belong' if many else 'belongs'} to a project of this benchmark's author, "
        f"who benefits directly from how {'they rank' if many else 'it ranks'}; see [Conflict of interest]({link}).",
        "",
    ]


def table_note() -> str:
    """The note for such a scanner in the README scanner table."""
    return (
        f"⚖️ 本基准作者的项目，见[利益声明]({ANCHOR})<br>"
        f"⚖️ A project of this benchmark's author, see [Conflict of interest]({ANCHOR})"
    )
