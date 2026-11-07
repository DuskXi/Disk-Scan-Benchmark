"""
Scores for real-drive results, for the local suite's own summary and the community board. The rules are the CI boards'
(scripts/leaderboard.py), as far as a submission carries the numbers:

  cold     = the drive's fastest cold scan / own x 100            (only on drives whose file cache was purged)
  warm     = the drive's fastest warm scan / own x 100
  balanced = the drive's best balanced time / own x 100, with the balanced time of the cold scan
             B = T_wall^w x (T_cpu + T_io)^(1-w), T_cpu = CPU seconds / logical cores, T_io = device reads / the drive's
             random-read IOPS (scripts/report_gen.py balanced_index; a submission records the cold scan's CPU time and
             reads only, so the warm half of the CI index is left out)
  score    = geometric mean of cold, warm and balanced

Raw times are only compared on the same drive. Across drives each part is first averaged geometrically over the drives
where the scanner has it, then the parts are combined: every drive counts once, whatever its size or speed, and a
scanner is neither marked down nor up for the drives it did not run on.
"""

import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from report_gen import BALANCE_WEIGHT  # noqa: E402

PARTS = ("cold", "warm", "balanced")


def geomean(values: Iterable[Optional[float]]) -> Optional[float]:
    vals = [v for v in values if v is not None and v > 0]
    return math.exp(sum(math.log(v) for v in vals) / len(vals)) if vals else None


def balanced_time(r: Dict[str, Any], cores: int, iops: Optional[float]) -> Optional[float]:
    """B of one cold scan (seconds; lower is better), None without its CPU time."""
    wall = float(r["cold_ms"]) / 1000
    cpu = r.get("cpu_s")
    if cpu is None or wall <= 0 or cores <= 0:
        return None
    t_io = float(r["reads"]) / iops if iops and r.get("reads") is not None else 0.0
    used = float(cpu) / cores + t_io
    return wall**BALANCE_WEIGHT * used ** (1 - BALANCE_WEIGHT) if used > 0 else None


def drive_scores(vol: Dict[str, Any], cores: int) -> Dict[str, Dict[str, Optional[float]]]:
    """Scanner id -> its cold, warm, balanced and score on one drive."""
    res = vol["results"]
    purged = bool(vol.get("cold_purged"))
    best_cold = min(float(r["cold_ms"]) for r in res)
    best_warm = min(float(r["warm_ms"]) for r in res)
    bal = {r["scanner"]: balanced_time(r, cores, vol.get("rand_read_iops")) for r in res} if purged else {}
    known = [b for b in bal.values() if b]
    best_bal = min(known) if known else None
    out: Dict[str, Dict[str, Optional[float]]] = {}
    for r in res:
        b = bal.get(r["scanner"])
        parts: Dict[str, Optional[float]] = {
            "cold": best_cold / float(r["cold_ms"]) * 100 if purged else None,
            "warm": best_warm / float(r["warm_ms"]) * 100,
            "balanced": best_bal / b * 100 if b and best_bal else None,
        }
        out[r["scanner"]] = {**parts, "score": geomean(parts.values())}
    return out


def rank(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows.sort(key=lambda r: -float(r["score"] or 0))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def ranking(drives: List[Tuple[Dict[str, Any], int]]) -> List[Dict[str, Any]]:
    """Across (drive, logical cores) pairs: per scanner each part averaged over its drives, then the score."""
    per: Dict[str, Dict[str, List[Optional[float]]]] = {}
    for vol, cores in drives:
        for sid, s in drive_scores(vol, cores).items():
            entry = per.setdefault(sid, {p: [] for p in PARTS})
            for p in PARTS:
                entry[p].append(s[p])
    rows: List[Dict[str, Any]] = []
    for sid, e in per.items():
        parts = {p: geomean(e[p]) for p in PARTS}
        rows.append({"id": sid, **parts, "score": geomean(parts.values()), "drives": len(e["warm"])})
    return rank(rows)


def fmt(v: Optional[float]) -> str:
    return "-" if v is None else f"{v:.1f}"


# --- Markdown tables (the suite's summary, community/README.md and the README board) ---

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
SCORE_HEADS = ["综合分", "冷扫分", "热扫分", "均衡分"]
SCORE_HEADS_EN = ["Score", "Cold", "Warm", "Balanced"]
SCORE_KEYS = ["score", "cold", "warm", "balanced"]
KIND_LABEL = {
    "nvme_ssd": "NVMe SSD",
    "sata_ssd": "SATA SSD",
    "sata_hdd": "SATA HDD",
    "sas_ssd": "SAS SSD",
    "sas_hdd": "SAS HDD",
    "usb_ssd": "USB SSD",
    "usb_hdd": "USB HDD",
    "virtual": "虚拟盘",
}


def drive_line(i: int, v: Dict[str, Any]) -> str:
    """One drive's hardware: what a submission records about it, nothing that names the machine or its folders."""
    cold_note = "" if v["cold_purged"] else "（未能清缓存：冷扫实为热扫）"
    iops = f"{v['rand_read_iops']:,} IOPS" if v.get("rand_read_iops") else "IOPS 未测"
    return (
        f"**盘 {i}**：{v['fs']} · {KIND_LABEL.get(v['kind'], v['kind'])} · {v['link']} · {v['disk_model']} · "
        f"{iops} · {v['used_gb']}/{v['size_gb']} GB · 约 {v['items_k']}k 项{cold_note}"
    )


def marked(rows: List[Dict[str, Any]], key: str) -> List[str]:
    """The column's cells, its best value (as shown; ties all count) highlighted."""
    best = max((fmt(r[key]) for r in rows if r[key] is not None), key=float, default="")
    return [
        f"<mark>**{fmt(r[key])}**</mark>" if r[key] is not None and fmt(r[key]) == best else fmt(r[key]) for r in rows
    ]


def ranking_table(rows: List[Dict[str, Any]], names: Dict[str, str], bi: bool = False) -> List[str]:
    """Rank, scanner, the four scores and how many drives it ran on (bi: Chinese and English headers)."""
    cols = [marked(rows, k) for k in SCORE_KEYS]
    heads = ["名次", "扫描器"] + SCORE_HEADS + ["盘数"]
    if bi:
        heads = [f"{zh}<br>{en}" for zh, en in zip(heads, ["Rank", "Scanner"] + SCORE_HEADS_EN + ["Drives"])]
    lines = [
        "| " + " | ".join(heads) + " |",
        "| :---: | :--- | " + " | ".join("---:" for _ in SCORE_HEADS) + " | ---: |",
    ]
    for i, r in enumerate(rows):
        cells = " | ".join(c[i] for c in cols)
        lines.append(
            f"| {MEDALS.get(r['rank'], str(r['rank']))} | **{names.get(r['id'], r['id'])}** | {cells} | {r['drives']} |"
        )
    return lines


def drive_table(vol: Dict[str, Any], cores: int, names: Dict[str, str]) -> List[str]:
    """One drive: every scanner's scores and measured numbers, best score first."""
    scores = drive_scores(vol, cores)
    rows = rank([{"id": r["scanner"], **scores[r["scanner"]], "r": r} for r in vol["results"]])
    cols = [marked(rows, k) for k in SCORE_KEYS]
    lines = [
        "| 名次 | 扫描器 | 版本 | "
        + " | ".join(SCORE_HEADS)
        + " | 冷扫 (s) | 热扫 (s) | 峰值内存 (MB) | 冷扫 CPU (s) | 冷扫读盘次数 | 报告大小 (GB) |",
        "| :---: | :--- | :--- | "
        + " | ".join("---:" for _ in SCORE_HEADS)
        + " | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for i, row in enumerate(rows):
        r = row["r"]
        cpu = f"{r['cpu_s']:.0f}" if r.get("cpu_s") is not None else "-"
        reads = f"{r['reads']:,}" if r.get("reads") is not None else "-"
        version = str(r["version"]).split(" (")[0]  # long build notes stay in the data
        lines.append(
            f"| {MEDALS.get(row['rank'], str(row['rank']))} | {names.get(r['scanner'], r['scanner'])} | `{version}` | "
            + " | ".join(c[i] for c in cols)
            + f" | {r['cold_ms'] / 1000:.2f} | {r['warm_ms'] / 1000:.2f} | {r['peak_rss_mb']:.0f} | {cpu} | {reads} "
            f"| {r['size_gb']} |"
        )
    return lines


SCORING_NOTE = (
    "分数在每块盘内计算：冷扫分、热扫分 = 这块盘上最快的用时 ÷ 自己的用时 × 100；均衡分同时看冷扫的墙钟时间和占用的 CPU、"
    "读盘资源（与 CI 榜单的均衡指数同一公式，只用冷扫这一次），= 这块盘上最好的均衡时间 ÷ 自己的 × 100；综合分 = 三者的"
    "几何平均。多块盘时每项先在各盘之间取几何平均，再算综合分；不同盘的原始用时从不直接比较。没能清缓存的盘只算热扫分。"
)
SCORING_NOTE_EN = (
    "Scores are computed per drive: cold and warm = the drive's fastest time / own x 100; balanced weighs the cold "
    "scan's wall time with the CPU and disk reads it used (the CI boards' balanced index, from the cold scan only) = the "
    "drive's best balanced time / own x 100; score = geometric mean of the three. Over several drives each part is first "
    "averaged geometrically across them, then combined; raw times are never compared across drives. Drives whose cache "
    "could not be purged count for the warm score only."
)
