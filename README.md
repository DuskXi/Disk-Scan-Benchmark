# disk-scanner-bench

**跨平台硬盘空间扫描工具基准测试 · Cross-platform benchmark for disk-space scanners**

> [!IMPORTANT]
> 本基准的作者也是参赛工具 SpaceKnife 的作者，SpaceKnife 排名靠前作者直接受益，见[利益声明](#利益声明--conflict-of-interest)。<br>
> This benchmark's author also wrote SpaceKnife, one of the scanners it ranks, and benefits when it ranks well: see [Conflict of interest](#利益声明--conflict-of-interest).

[🏆 排行榜 Leaderboard](#-排行榜--leaderboard) · [🖥️ 真实盘成绩 Real drives](#real-drives) · [🪟 访问时间关闭对照 Access times off](#atime-off) · [⚖️ 利益声明 Conflict of interest](#利益声明--conflict-of-interest) · [📐 方法说明 Methodology](docs/METHODOLOGY.md) · [🧪 本地套件 Local suite](docs/LOCAL_SUITE.md) · [➕ 新增扫描器 Add a scanner](#新增扫描器--adding-a-scanner)

在 GitHub Actions 的免费 Runner 上（Linux、macOS、Windows，x86_64 与 ARM64，多种文件系统），用确定性生成的合成文件树（最多 900 万个文件，逻辑上几 TB、物理上只占几 GB）给主流磁盘空间扫描工具做冷扫和热扫计时，核对每个工具自己报告的结果是否完整，再按平台归一化，排出跨平台、跨体量的总榜。合成数据会模拟用了多年的磁盘布局；生成算法只按"像不像真实的盘"取舍，不看任何扫描器的表现。

On free GitHub Actions runners (Linux, macOS and Windows, x86_64 and ARM64, several filesystems), mainstream disk-space scanners are timed on cold and warm scans of a deterministic synthetic tree (up to 9 million files, terabytes in logical size but only a few GB on disk). Each scanner's own output is checked for completeness, scores are normalized within each platform, and the results form one board across platforms and sizes. The test data imitates a drive that has been in use for years; generator choices are judged only by how closely they match real drives, never by how any scanner performs.

<!-- COMMUNITY-ENTRY:START -->

> 🖥️ **真实盘成绩 · Real drives**：除了 CI 上的合成数据，这里还有在真实硬盘上跑出的成绩，已收录 2 份提交、3 块盘。目前收录的成绩全部来自本基准作者自己的电脑：1 块 NTFS 系统盘（已使用约 1 年）、2 块 ReFS 数据盘（已使用约 3–4 年），都是日常在用的盘。[看榜单](#real-drives) · [每块盘的全部数据](community/README.md) · [提交你的成绩](docs/LOCAL_SUITE.md)<br>
> Besides the synthetic CI data: results on real drives, 2 submissions on 3 drives so far. Both submissions so far come from this benchmark's author's own machine: 1 NTFS system drive in use for about 1 year, 2 ReFS data drives in use for about 3–4 years, all of them in daily use. [Board](#real-drives) · [every drive in full](community/README.md) · [submit yours](docs/LOCAL_SUITE.md)

<!-- COMMUNITY-ENTRY:END -->

<!-- LEADERBOARD:START -->

## 🏆 排行榜 · Leaderboard

![updated](https://img.shields.io/badge/updated-2026--11--11-4c8eda) ![presets](https://img.shields.io/badge/presets-5%2F7-dbab09) ![scanners](https://img.shields.io/badge/scanners-16-6f42c1) ![platforms](https://img.shields.io/badge/platforms-14-0969da) ![MFT presets](https://img.shields.io/badge/MFT%20presets-7-8250df)

> ⚖️ **利益声明**：SpaceKnife (0.3.4) 和 SpaceKnife 属于本基准作者的项目，作者从它们的排名中直接受益，详见[利益声明](#利益声明--conflict-of-interest)。<br>
> ⚖️ **Conflict of interest**: SpaceKnife (0.3.4) and SpaceKnife belong to a project of this benchmark's author, who benefits directly from how they rank; see [Conflict of interest](#利益声明--conflict-of-interest).

> **参考**：SpaceKnife (0.3.4) 是 SpaceKnife 的旧版本，只作对照。它的分数照常计算，但不占名次、奖牌、高亮和单项第一，后面的扫描器顺延；奖牌只给当前版本。<br>**参考** (reference): SpaceKnife (0.3.4) is the earlier release of SpaceKnife, kept for comparison. Its scores are computed as usual, but it takes no rank, medal, highlight or category win, and the scanners after it move up; the medals go to the current release only.

> 每个体量单独运行、单独更新：哪个体量跑完就刷新哪一列，其余保持上次的结果。`very-lite` / `lite` 体量过小，计时以进程启动等固定开销为主，只作参考，不计入跨体量综合分。评分方法与数据生成原理见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。
>
> Each size runs and updates on its own: a finished run refreshes its column and the others keep their last result. `very-lite` and `lite` are so small that process start-up dominates the wall clock, so they are for reference only and stay out of the overall score. Scoring and test-data design: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

### 各项前四名 · Top 4 of each category

| 名⁠次<br>Rank | 综⁠合<br>Overall | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 内⁠存⁠峰⁠值\*<br>Peak&nbsp;RAM\* | 扫⁠描⁠效⁠率\*<br>I/O&nbsp;efficiency\* | 写⁠盘⁠量\*<br>Disk&nbsp;writes\* |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife**<br><sub>96.7</sub> | **SpaceKnife**<br><sub>97.2</sub> | **SpaceKnife**<br><sub>96.0</sub> | **ncdu**<br><sub>3.6&nbsp;MB</sub> | **WizTree**<br><sub>99.7</sub> | **SpaceKnife**<br><sub>0.0%&nbsp;·&nbsp;0.2&nbsp;MB</sub> |
| 🥈 | **gdu**<br><sub>57.9</sub> | **BSD&nbsp;du**<br><sub>52.4</sub> | **gdu**<br><sub>66.3</sub> | **GNU&nbsp;du**<br><sub>15&nbsp;MB</sub> | **GNU&nbsp;du**<br><sub>99.3</sub> | **SpaceSniffer**<br><sub>84%&nbsp;·&nbsp;2,053.1&nbsp;MB</sub> |
| 🥉 | **SquirrelDisk**<br><sub>54.0</sub> | **gdu**<br><sub>45.8</sub> | **SquirrelDisk**<br><sub>57.1</sub> | **dua‑cli**<br><sub>22&nbsp;MB</sub> | **SpaceKnife**<br><sub>97.9</sub> | **WinDirStat**<br><sub>84%&nbsp;·&nbsp;631.6&nbsp;MB</sub> |
| 4 | **BSD&nbsp;du**<br><sub>47.9</sub> | **SquirrelDisk**<br><sub>45.2</sub> | **diskus**<br><sub>40.0</sub> | **diskus**<br><sub>41&nbsp;MB</sub> | **ncdu**<br><sub>95.9</sub> | **SquirrelDisk**<br><sub>88%&nbsp;·&nbsp;786.2&nbsp;MB</sub> |

<sub>**\* 只作参考，不计入综合分**（综合 = 冷扫、热扫、均衡指数）· † 只有小体量成绩 · 各列按 `low` 及以上体量合并<br>**内存峰值**：各平台、各体量的中位数，含放进 tmpfs 的数据（Linux）和被压缩的内存（macOS）<br>**扫描效率**：1 ÷ (IOPS × 扫描时间) = 1 ÷ 冷扫读盘次数，平台内最少 ÷ 自己 × 100<br>**写盘量**：扫描器自己写的文件（如磁盘缓存）+ 冷扫时更新访问时间写的盘（[按日常设置开着](#怎么算分--how-scoring-works)）。百分比 = 自己 ÷ 同平台典型扫描器，排名按它（NTFS 每项写的是 ext4 的近 4 倍，平台内比才公平）；MB 是每百万项实测值。macOS 的写入计数是整台机器的，不参与<br><br>**\* For reference, not in the overall score** (overall = cold, warm, balanced index) · † small sizes only · each column combines the sizes from `low` up<br>**Peak RAM**: median over platforms and sizes, including data parked in tmpfs (Linux) and compressed memory (macOS)<br>**I/O efficiency**: 1 / (IOPS x scan time) = 1 / cold-scan disk reads, platform's fewest / own x 100<br>**Disk writes**: files the scanner writes itself (e.g. a disk cache) + what the cold scan writes for access-time updates ([on, as in daily use](#怎么算分--how-scoring-works)). The percentage is own / the platform's typical scanner and sets the rank (NTFS writes nearly 4x what ext4 does per item, so platforms are compared within themselves); MB is measured per million items. macOS stays out: its write counter covers the whole machine.</sub>

### 跨体量总榜 · Overall across sizes

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | very‑lite\* | lite\* | low | mid | high |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**96.7**</mark> | 🥇&nbsp;<mark>**86.6**</mark> | 🥇&nbsp;<mark>**96.9**</mark> | 🥇&nbsp;<mark>**96.8**</mark> | 🥇&nbsp;<mark>**96.5**</mark> | — |
| 参考 | **SpaceKnife&nbsp;(0.3.4)** | 94.2 | 参考&nbsp;55.5 | 参考&nbsp;84.2 | 参考&nbsp;92.2 | 参考&nbsp;90.9 | 参考&nbsp;99.8 |
| 🥈 | **gdu** | 57.9 | #4&nbsp;56.8 | 🥉&nbsp;58.1 | 🥉&nbsp;54.8 | 🥈&nbsp;60.2 | 🥇&nbsp;<mark>**58.9**</mark> |
| 🥉 | **SquirrelDisk** | 54.0 | 🥉&nbsp;67.2 | 🥈&nbsp;66.1 | 🥈&nbsp;63.4 | 🥉&nbsp;52.5 | #4&nbsp;47.4 |
| 4 | **BSD&nbsp;du** | 47.9 | 🥈&nbsp;76.2 | #4&nbsp;49.1 | #4&nbsp;40.0 | #4&nbsp;52.4 | 🥈&nbsp;52.5 |
| 5 | **diskus** | 43.7 | #5&nbsp;49.7 | #7&nbsp;37.1 | #7&nbsp;37.1 | #5&nbsp;46.0 | 🥉&nbsp;48.7 |
| 6 | **dua‑cli** | 42.5 | #7&nbsp;43.7 | #5&nbsp;40.7 | #5&nbsp;39.7 | #6&nbsp;45.1 | #5&nbsp;42.8 |
| 7 | **pdu** | 39.8 | #6&nbsp;45.3 | #8&nbsp;35.2 | #8&nbsp;34.1 | #7&nbsp;43.1 | #6&nbsp;42.7 |
| 8 | **GNU&nbsp;du** | 37.5 | #9&nbsp;38.9 | #6&nbsp;38.4 | #6&nbsp;37.7 | #9&nbsp;39.2 | #8&nbsp;35.7 |
| 9 | **ncdu** | 36.8 | #8&nbsp;39.6 | #10&nbsp;33.1 | #9&nbsp;33.3 | #8&nbsp;40.3 | #7&nbsp;37.3 |
| 10 | **dust** | 27.1 | #11&nbsp;31.4 | #12&nbsp;24.0 | #12&nbsp;24.2 | #10&nbsp;30.1 | #11&nbsp;27.2 |
| 11 | **WinDirStat** | 26.4 | #10&nbsp;38.3 | #9&nbsp;33.7 | #10&nbsp;29.4 | #12&nbsp;22.3 | #10&nbsp;27.9 |
| 12 | **WizTree** | 24.5 | #13&nbsp;24.2 | #11&nbsp;31.6 | #11&nbsp;27.4 | #13&nbsp;17.8 | #9&nbsp;30.2 |
| 13 | **erdtree** | 22.8 | #12&nbsp;27.6 | #13&nbsp;22.6 | #13&nbsp;23.4 | #11&nbsp;23.8 | #12&nbsp;21.4 |
| 14 | **SpaceSniffer** | 15.1 | #14&nbsp;16.6 | #14&nbsp;17.6 | #14&nbsp;15.2 | #14&nbsp;11.8 | #13&nbsp;19.2 |
| 15 | **Sysinternals&nbsp;du** | 6.2 | — | — | #15&nbsp;6.1 | — | #14&nbsp;6.3 |

<sub><mark>**高亮**</mark> = 该列最高分 · <mark>**highlighted**</mark> = best in its column.<br><br>综合分 = `low` 及以上各体量综合分的几何平均；\* 为仅供参考的小体量（综合分带 \* 的扫描器只有小体量成绩）。缺平台、缺体量都不扣分也不加分：只用它实际跑过的平台和体量计算，等于把缺的部分按它自己的平均分补上，平台多的工具不会因此更容易刷分，平台少的工具也不会因此被扣分。<br><br>Score = geometric mean of the per-size scores from `low` up; \* marks the reference-only small sizes (a score with \* comes from small sizes only). Missing platforms and sizes neither cost nor earn points: only what a scanner actually ran counts, the same as filling the gaps with its own average, so more platforms do not make a high score easier and fewer do not mark a tool down.</sub>

> 🪟 Windows 关掉访问时间更新之后会怎样，见下方的[访问时间关闭对照榜](#atime-off)：只作对照，不是正式排名。<br>What turning Windows last-access updates off changes: see the [access-times-off comparison](#atime-off) below, for comparison only, not a ranking.

### 冷扫综合榜 · Cold scans across sizes

> CI Runner 的盘是 IOPS 受限的云盘，冷扫比的是在这种盘上谁读得省，和本地 NVMe 上的冷扫排名可能不同，见[CI 冷扫测的是什么](#ci-冷扫测的是什么--what-the-ci-cold-scans-measure)。<br>The CI runners' disks are IOPS-capped cloud disks: cold scans here measure who reads most economically on such a disk, and may rank differently on a local NVMe drive; see [What the CI cold scans measure](#ci-冷扫测的是什么--what-the-ci-cold-scans-measure).

| # | 扫⁠描⁠器<br>Scanner | **冷⁠扫⁠分**<br>**Cold** | very‑lite\* | lite\* | low | mid | high |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**97.2**</mark> | 🥇&nbsp;<mark>**74.9**</mark> | 🥇&nbsp;<mark>**94.7**</mark> | 🥇&nbsp;<mark>**97.0**</mark> | 🥇&nbsp;<mark>**97.4**</mark> | — |
| 参考 | **SpaceKnife&nbsp;(0.3.4)** | 95.1 | 参考&nbsp;62.8 | 参考&nbsp;91.4 | 参考&nbsp;95.2 | 参考&nbsp;90.3 | 参考&nbsp;100.0 |
| 🥈 | **BSD&nbsp;du** | 52.4 | 🥉&nbsp;64.6 | #4&nbsp;48.5 | #8&nbsp;33.2 | 🥈&nbsp;62.4 | 🥇&nbsp;<mark>**69.4**</mark> |
| 🥉 | **gdu** | 45.8 | #8&nbsp;41.8 | #5&nbsp;43.9 | 🥉&nbsp;43.7 | #4&nbsp;48.0 | 🥉&nbsp;45.7 |
| 4 | **SquirrelDisk** | 45.2 | #5&nbsp;52.4 | 🥈&nbsp;55.7 | 🥈&nbsp;52.1 | #6&nbsp;41.6 | #5&nbsp;42.7 |
| 5 | **diskus** | 45.1 | #4&nbsp;54.4 | #7&nbsp;42.5 | #5&nbsp;40.7 | 🥉&nbsp;48.6 | 🥈&nbsp;46.2 |
| 6 | **dua‑cli** | 42.4 | #6&nbsp;49.7 | #6&nbsp;43.6 | #6&nbsp;38.9 | #5&nbsp;44.2 | #4&nbsp;44.4 |
| 7 | **pdu** | 38.2 | #7&nbsp;43.7 | #8&nbsp;37.9 | #7&nbsp;34.0 | #7&nbsp;41.6 | #6&nbsp;39.5 |
| 8 | **dust** | 34.3 | #9&nbsp;41.1 | #9&nbsp;32.8 | #9&nbsp;29.2 | #8&nbsp;37.4 | #7&nbsp;36.9 |
| 9 | **erdtree** | 29.4 | #10&nbsp;32.8 | #10&nbsp;28.7 | #10&nbsp;27.8 | #9&nbsp;31.5 | #9&nbsp;29.2 |
| 10 | **WinDirStat** | 29.3 | 🥈&nbsp;68.8 | 🥉&nbsp;49.1 | #4&nbsp;43.1 | #12&nbsp;22.4 | #10&nbsp;26.1 |
| 11 | **ncdu** | 25.4 | #12&nbsp;26.3 | #14&nbsp;21.9 | #14&nbsp;20.6 | #10&nbsp;26.9 | #8&nbsp;29.7 |
| 12 | **GNU&nbsp;du** | 25.0 | #13&nbsp;23.8 | #13&nbsp;25.3 | #12&nbsp;24.2 | #11&nbsp;25.4 | #11&nbsp;25.3 |
| 13 | **SpaceSniffer** | 17.7 | #11&nbsp;28.3 | #11&nbsp;26.3 | #13&nbsp;22.0 | #13&nbsp;13.6 | #12&nbsp;18.7 |
| 14 | **WizTree** | 15.6 | #14&nbsp;21.5 | #12&nbsp;25.6 | #11&nbsp;24.4 | #14&nbsp;9.9 | #13&nbsp;15.7 |
| 15 | **Sysinternals&nbsp;du** | 9.4 | — | — | #15&nbsp;11.6 | — | #14&nbsp;7.6 |

<sub>只看冷扫：每个体量取冷扫相对分（该平台最快 ÷ 自己 × 100，跨平台几何平均），再对 `low` 及以上取几何平均；格子里是该体量冷扫的名次和分数，<mark>**高亮**</mark> = 该列最高分。<br><br>The cold-scan score alone: each size's cold-scan relative score (platform fastest / own x 100, geometric mean across platforms), then the geometric mean from `low` up; each cell is the cold-scan rank and score in that size, <mark>**highlighted**</mark> = best in its column.</sub>

### 热扫综合榜 · Warm scans across sizes

| # | 扫⁠描⁠器<br>Scanner | **热⁠扫⁠分**<br>**Warm** | very‑lite\* | lite\* | low | mid | high |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**96.0**</mark> | 🥇&nbsp;<mark>**95.6**</mark> | 🥇&nbsp;<mark>**98.2**</mark> | 🥇&nbsp;<mark>**96.9**</mark> | 🥇&nbsp;<mark>**95.2**</mark> | — |
| 参考 | **SpaceKnife&nbsp;(0.3.4)** | 92.2 | 参考&nbsp;42.3 | 参考&nbsp;73.9 | 参考&nbsp;87.6 | 参考&nbsp;90.2 | 参考&nbsp;99.3 |
| 🥈 | **gdu** | 66.3 | #4&nbsp;70.1 | 🥉&nbsp;67.3 | 🥉&nbsp;60.8 | 🥈&nbsp;70.5 | 🥇&nbsp;<mark>**67.9**</mark> |
| 🥉 | **SquirrelDisk** | 57.1 | 🥈&nbsp;76.2 | 🥈&nbsp;70.5 | 🥈&nbsp;68.7 | 🥉&nbsp;59.2 | #4&nbsp;45.8 |
| 4 | **diskus** | 40.0 | #5&nbsp;44.2 | #9&nbsp;29.8 | #8&nbsp;30.8 | #4&nbsp;42.2 | 🥉&nbsp;49.3 |
| 5 | **dua‑cli** | 37.8 | #9&nbsp;35.3 | #6&nbsp;34.1 | #5&nbsp;35.4 | #5&nbsp;41.8 | #6&nbsp;36.5 |
| 6 | **pdu** | 36.0 | #6&nbsp;42.9 | #10&nbsp;28.3 | #9&nbsp;29.0 | #6&nbsp;40.1 | #5&nbsp;40.3 |
| 7 | **GNU&nbsp;du** | 36.0 | #7&nbsp;40.3 | #4&nbsp;37.1 | #4&nbsp;37.2 | #8&nbsp;39.1 | #7&nbsp;32.0 |
| 8 | **WizTree** | 34.7 | #10&nbsp;22.1 | #7&nbsp;33.9 | #10&nbsp;26.5 | #10&nbsp;26.4 | 🥈&nbsp;59.9 |
| 9 | **ncdu** | 34.0 | #8&nbsp;39.5 | #8&nbsp;31.2 | #6&nbsp;33.2 | #7&nbsp;39.3 | #8&nbsp;30.1 |
| 10 | **BSD&nbsp;du** | 30.2 | 🥉&nbsp;72.5 | #5&nbsp;34.7 | #7&nbsp;32.8 | #9&nbsp;31.2 | #9&nbsp;27.0 |
| 11 | **WinDirStat** | 20.2 | #13&nbsp;19.8 | #11&nbsp;20.8 | #11&nbsp;18.0 | #12&nbsp;18.0 | #10&nbsp;25.3 |
| 12 | **dust** | 18.2 | #11&nbsp;21.7 | #13&nbsp;14.9 | #13&nbsp;16.6 | #11&nbsp;21.4 | #11&nbsp;16.8 |
| 13 | **erdtree** | 15.7 | #12&nbsp;21.4 | #12&nbsp;15.7 | #12&nbsp;16.8 | #13&nbsp;16.8 | #12&nbsp;13.7 |
| 14 | **SpaceSniffer** | 8.3 | #14&nbsp;6.1 | #14&nbsp;8.1 | #14&nbsp;7.2 | #14&nbsp;6.5 | #13&nbsp;12.2 |
| 15 | **Sysinternals&nbsp;du** | 2.7 | — | — | #15&nbsp;2.4 | — | #14&nbsp;3.0 |

<sub>只看热扫：每个体量取热扫相对分（该平台最快 ÷ 自己 × 100，跨平台几何平均），再对 `low` 及以上取几何平均；格子里是该体量热扫的名次和分数，<mark>**高亮**</mark> = 该列最高分。<br><br>The warm-scan score alone: each size's warm-scan relative score (platform fastest / own x 100, geometric mean across platforms), then the geometric mean from `low` up; each cell is the warm-scan rank and score in that size, <mark>**highlighted**</mark> = best in its column.</sub>

### 各体量详情 · Results per size

<details open>
<summary><b>high</b> · 500 万文件 · 5M files · 2026-10-30 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40974157411">run 40974157411</a> · <code>1813c5c</code></summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 参考 | **SpaceKnife&nbsp;(0.3.4)** | 99.8 | 100.0<br><sub>53.8&nbsp;s</sub> | 99.3<br><sub>7.07&nbsp;s</sub> | 100.0 | 923&nbsp;MB | 0.55% | S·F·Z | 9/11 |
| 🥇 | **gdu** | <mark>**58.9**</mark> | 45.7<br><sub>199&nbsp;s</sub> | <mark>**67.9**</mark><br><sub>21.0&nbsp;s</sub> | 65.9 | 118&nbsp;MB | 0.56% | S·Z | 11/11 |
| 🥈 | **BSD&nbsp;du** | 52.5 | <mark>**69.4**</mark><br><sub>1,384&nbsp;s</sub> | 27.0<br><sub>1,279&nbsp;s</sub> | <mark>**77.3**</mark> | 1,141&nbsp;MB | 918.47% | S·Z | 2/2 |
| 🥉 | **diskus** | 48.7 | 46.2<br><sub>197&nbsp;s</sub> | 49.3<br><sub>28.9&nbsp;s</sub> | 50.8 | 46&nbsp;MB | <mark>**0.00%**</mark> | S | 11/11 |
| 4 | **SquirrelDisk** | 47.4 | 42.7<br><sub>304&nbsp;s</sub> | 45.8<br><sub>55.0&nbsp;s</sub> | 54.5 | 148&nbsp;MB | 1.09% | S·F·Z | 7/7 |
| 5 | **dua‑cli** | 42.8 | 44.4<br><sub>204&nbsp;s</sub> | 36.5<br><sub>39.1&nbsp;s</sub> | 48.3 | 41&nbsp;MB | 0.09% | S·Z | 11/11 |
| 6 | **pdu** | 42.7 | 39.5<br><sub>230&nbsp;s</sub> | 40.3<br><sub>35.4&nbsp;s</sub> | 49.0 | 241&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 11/11 |
| 7 | **ncdu** | 37.3 | 29.7<br><sub>282&nbsp;s</sub> | 30.1<br><sub>48.1&nbsp;s</sub> | 58.3 | <mark>**5&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 8/8 |
| 8 | **GNU&nbsp;du** | 35.7 | 25.3<br><sub>147&nbsp;s</sub> | 32.0<br><sub>15.7&nbsp;s</sub> | 56.4 | 19&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 6/6 |
| 9 | **WizTree** | 30.2 | 15.7<br><sub>641&nbsp;s</sub> | 59.9<br><sub>25.5&nbsp;s</sub> | 29.4 | 2,390&nbsp;MB | 0.79% | S·F·Z | 2/2 |
| 10 | **WinDirStat** | 27.9 | 26.1<br><sub>433&nbsp;s</sub> | 25.3<br><sub>54.1&nbsp;s</sub> | 33.1 | 1,024&nbsp;MB | 0.79% | S·F·Z | 3/3 |
| 11 | **dust** | 27.2 | 36.9<br><sub>246&nbsp;s</sub> | 16.8<br><sub>84.7&nbsp;s</sub> | 32.4 | 1,916&nbsp;MB | 0.68% | S·Z | 11/11 |
| 12 | **erdtree** | 21.4 | 29.2<br><sub>163&nbsp;s</sub> | 13.7<br><sub>48.5&nbsp;s</sub> | 24.4 | 4,284&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 8/10 |
| 13 | **SpaceSniffer** | 19.2 | 18.7<br><sub>537&nbsp;s</sub> | 12.2<br><sub>125&nbsp;s</sub> | 30.9 | 2,628&nbsp;MB | n/a | IO | 2/2 |
| 14 | **Sysinternals&nbsp;du** | 6.3 | 7.6<br><sub>1,493&nbsp;s</sub> | 3.0<br><sub>458&nbsp;s</sub> | 11.1 | 253&nbsp;MB | 1.00% | S·F·Z | 3/3 |

单项第一 · Category winners：**冷扫 Cold** BSD du (69.4) · **热扫 Warm** gdu (67.9) · **均衡 Balanced** BSD du (77.3) · **最省内存 Least RAM** ncdu (5 MB) · **扫描效率 I/O efficiency** BSD du (100.0) · **最准 Most accurate** diskus (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>59.8&nbsp;/&nbsp;5.16 | 参考<br>29.5&nbsp;/&nbsp;7.54 | 参考<br>37.3&nbsp;/&nbsp;5.97 |
| **gdu** | 🥈<br>71.0&nbsp;/&nbsp;7.90 | 🥈<br>54.1&nbsp;/&nbsp;13.4 | 🥈<br>46.6&nbsp;/&nbsp;10.5 |
| **diskus** | 🥉<br><mark>**70.8**</mark>&nbsp;/&nbsp;11.5 | 🥉<br>49.6&nbsp;/&nbsp;18.1 | 🥉<br><mark>**44.8**</mark>&nbsp;/&nbsp;14.2 |
| **SquirrelDisk** | 🥇<br>71.2&nbsp;/&nbsp;<mark>**5.84**</mark> | 🥇<br><mark>**43.8**</mark>&nbsp;/&nbsp;<mark>**8.27**</mark> | 🥇<br>47.9&nbsp;/&nbsp;<mark>**7.02**</mark> |
| **dua‑cli** | #7<br>84.0&nbsp;/&nbsp;22.1 | #5<br>73.8&nbsp;/&nbsp;25.2 | #5<br>58.0&nbsp;/&nbsp;20.7 |
| **pdu** | #4<br>81.6&nbsp;/&nbsp;15.4 | #4<br>62.5&nbsp;/&nbsp;21.9 | #4<br>54.3&nbsp;/&nbsp;13.4 |
| **ncdu** | #5<br>189&nbsp;/&nbsp;12.4 | #8<br>136&nbsp;/&nbsp;28.1 | #6<br>150&nbsp;/&nbsp;16.8 |
| **GNU&nbsp;du** | #6<br>195&nbsp;/&nbsp;12.2 | #6<br>136&nbsp;/&nbsp;22.8 | #7<br>149&nbsp;/&nbsp;17.3 |
| **dust** | #8<br>85.0&nbsp;/&nbsp;26.9 | #7<br>78.6&nbsp;/&nbsp;30.4 | #8<br>61.7&nbsp;/&nbsp;28.8 |
| **erdtree** | #9<br>95.5&nbsp;/&nbsp;30.5 | #9<br>104&nbsp;/&nbsp;26.2 | #9<br>95.1&nbsp;/&nbsp;26.6 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>55.7&nbsp;/&nbsp;4.14 | 参考<br>20.0&nbsp;/&nbsp;4.55 | 参考<br>35.5&nbsp;/&nbsp;3.70 |
| **gdu** | 🥉<br><mark>**68.2**</mark>&nbsp;/&nbsp;6.87 | 🥈<br>37.0&nbsp;/&nbsp;8.70 | 🥉<br>41.6&nbsp;/&nbsp;6.48 |
| **diskus** | 🥇<br>69.2&nbsp;/&nbsp;<mark>**4.61**</mark> | 🥇<br><mark>**26.0**</mark>&nbsp;/&nbsp;<mark>**4.90**</mark> | 🥇<br><mark>**38.3**</mark>&nbsp;/&nbsp;<mark>**4.13**</mark> |
| **dua‑cli** | #6<br>74.7&nbsp;/&nbsp;24.9 | #4<br>52.0&nbsp;/&nbsp;24.6 | #6<br>46.1&nbsp;/&nbsp;23.1 |
| **pdu** | 🥈<br>70.5&nbsp;/&nbsp;5.97 | 🥉<br>47.6&nbsp;/&nbsp;7.58 | 🥈<br>42.6&nbsp;/&nbsp;5.56 |
| **ncdu** | #4<br>194&nbsp;/&nbsp;13.2 | #7<br>101&nbsp;/&nbsp;20.1 | #4<br>123&nbsp;/&nbsp;11.4 |
| **GNU&nbsp;du** | #5<br>202&nbsp;/&nbsp;13.7 | #6<br>104&nbsp;/&nbsp;19.4 | #5<br>121&nbsp;/&nbsp;11.9 |
| **dust** | #7<br>79.5&nbsp;/&nbsp;28.3 | #5<br>53.1&nbsp;/&nbsp;25.9 | #7<br>49.1&nbsp;/&nbsp;25.9 |
| **erdtree** | #8<br>99.8&nbsp;/&nbsp;34.9 | #8<br>93.6&nbsp;/&nbsp;28.0 | #8<br>66.9&nbsp;/&nbsp;30.5 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife&nbsp;(0.3.4)** | ⚠️ | ⚠️ |
| **gdu** | 🥉<br>1,585&nbsp;/&nbsp;<mark>**403**</mark> | 🥉<br>1,689&nbsp;/&nbsp;<mark>**296**</mark> |
| **BSD&nbsp;du** | #7<br>1,055&nbsp;/&nbsp;1,019 | #6<br>1,816&nbsp;/&nbsp;1,605 |
| **diskus** | 🥈<br>1,335&nbsp;/&nbsp;432 | 🥈<br>1,351&nbsp;/&nbsp;340 |
| **SquirrelDisk** | #5<br>1,001&nbsp;/&nbsp;661 | #7<br>2,142&nbsp;/&nbsp;1,197 |
| **dua‑cli** | 🥇<br><mark>**924**</mark>&nbsp;/&nbsp;437 | 🥇<br><mark>**999**</mark>&nbsp;/&nbsp;317 |
| **pdu** | #4<br>1,270&nbsp;/&nbsp;545 | #5<br>1,840&nbsp;/&nbsp;666 |
| **ncdu** | #8<br>1,722&nbsp;/&nbsp;1,006 | #8<br>2,507&nbsp;/&nbsp;1,609 |
| **dust** | #6<br>1,134&nbsp;/&nbsp;697 | #4<br>1,761&nbsp;/&nbsp;607 |
| **erdtree** | ⚠️ | ⚠️ |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>ReFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>70.0&nbsp;/&nbsp;8.22 | 参考<br>144&nbsp;/&nbsp;11.0 | 参考<br>144&nbsp;/&nbsp;30.1 |
| **gdu** | 🥇<br>123&nbsp;/&nbsp;<mark>**10.7**</mark> | 🥇<br><mark>**903**</mark>&nbsp;/&nbsp;<mark>**16.1**</mark> | 🥉<br>3,437&nbsp;/&nbsp;39.6 |
| **diskus** | #6<br>211&nbsp;/&nbsp;67.6 | #4<br>1,315&nbsp;/&nbsp;126 | #6<br>3,121&nbsp;/&nbsp;34.4 |
| **SquirrelDisk** | #4<br>177&nbsp;/&nbsp;20.1 | — | #10<br>4,206&nbsp;/&nbsp;282 |
| **dua‑cli** | 🥈<br>119&nbsp;/&nbsp;14.0 | 🥈<br>1,036&nbsp;/&nbsp;23.8 | #4<br>3,543&nbsp;/&nbsp;43.0 |
| **pdu** | #7<br>219&nbsp;/&nbsp;67.6 | #5<br>1,361&nbsp;/&nbsp;138 | 🥈<br>3,448&nbsp;/&nbsp;28.4 |
| **WizTree** | 🥉<br>126&nbsp;/&nbsp;22.9 | — | #7<br>3,257&nbsp;/&nbsp;<mark>**28.3**</mark> |
| **WinDirStat** | #5<br><mark>**110**</mark>&nbsp;/&nbsp;34.7 | 🥉<br>1,423&nbsp;/&nbsp;64.6 | 🥇<br><mark>**520**</mark>&nbsp;/&nbsp;70.5 |
| **dust** | #8<br>230&nbsp;/&nbsp;84.4 | #7<br>1,444&nbsp;/&nbsp;706 | #8<br>3,570&nbsp;/&nbsp;142 |
| **erdtree** | #11<br>343&nbsp;/&nbsp;211 | — | #9<br>2,496&nbsp;/&nbsp;229 |
| **SpaceSniffer** | #9<br>294&nbsp;/&nbsp;93.0 | — | #5<br>978&nbsp;/&nbsp;167 |
| **Sysinternals&nbsp;du** | #10<br>471&nbsp;/&nbsp;206 | #6<br>1,738&nbsp;/&nbsp;450 | #11<br>4,061&nbsp;/&nbsp;1,031 |

<sub>**参考**：SpaceKnife (0.3.4) 是 spaceknife-rust 的旧版本，只作对照。它的分数照常计算，但不占名次、奖牌、高亮和单项第一，后面的扫描器顺延；奖牌只给当前版本。<br><br>**参考** (reference): SpaceKnife (0.3.4) is the earlier release of spaceknife-rust, kept for comparison. Its scores are computed as usual, but it takes no rank, medal, highlight or category win, and the scanners after it move up; the medals go to the current release only.<br><br>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>mid</b> · 300 万文件 · 3M files · 2026-11-10 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42861012833">run 42861012833</a> · <code>d36278b</code></summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**96.5**</mark> | <mark>**97.4**</mark><br><sub>29.0&nbsp;s</sub> | <mark>**95.2**</mark><br><sub>5.20&nbsp;s</sub> | <mark>**97.1**</mark> | 608&nbsp;MB | 0.04% | S·F·Z | 11/13 |
| 参考 | **SpaceKnife&nbsp;(0.3.4)** | 90.9 | 90.3<br><sub>31.3&nbsp;s</sub> | 90.2<br><sub>5.49&nbsp;s</sub> | 92.2 | 598&nbsp;MB | 0.04% | S·F·Z | 11/13 |
| 🥈 | **gdu** | 60.2 | 48.0<br><sub>87.4&nbsp;s</sub> | 70.5<br><sub>12.5&nbsp;s</sub> | 64.3 | 83&nbsp;MB | 0.17% | S·Z | 13/13 |
| 🥉 | **SquirrelDisk** | 52.5 | 41.6<br><sub>132&nbsp;s</sub> | 59.2<br><sub>22.8&nbsp;s</sub> | 58.7 | 78&nbsp;MB | 1.15% | S·F·Z | 8/8 |
| 4 | **BSD&nbsp;du** | 52.4 | 62.4<br><sub>592&nbsp;s</sub> | 31.2<br><sub>666&nbsp;s</sub> | 73.8 | 1,033&nbsp;MB | 1667.09% | S·Z | 2/2 |
| 5 | **diskus** | 46.0 | 48.6<br><sub>86.3&nbsp;s</sub> | 42.2<br><sub>20.8&nbsp;s</sub> | 47.4 | 41&nbsp;MB | <mark>**0.00%**</mark> | S | 13/13 |
| 6 | **dua‑cli** | 45.1 | 44.2<br><sub>95.0&nbsp;s</sub> | 41.8<br><sub>21.0&nbsp;s</sub> | 49.5 | 22&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 13/13 |
| 7 | **pdu** | 43.1 | 41.6<br><sub>101&nbsp;s</sub> | 40.1<br><sub>21.9&nbsp;s</sub> | 48.1 | 143&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 13/13 |
| 8 | **ncdu** | 40.3 | 26.9<br><sub>146&nbsp;s</sub> | 39.3<br><sub>26.1&nbsp;s</sub> | 61.8 | <mark>**4&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 9 | **GNU&nbsp;du** | 39.2 | 25.4<br><sub>88.4&nbsp;s</sub> | 39.1<br><sub>12.3&nbsp;s</sub> | 60.8 | 15&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 10 | **dust** | 30.1 | 37.4<br><sub>112&nbsp;s</sub> | 21.4<br><sub>41.0&nbsp;s</sub> | 34.1 | 1,128&nbsp;MB | 0.46% | S·Z | 13/13 |
| 11 | **erdtree** | 23.8 | 31.5<br><sub>81.1&nbsp;s</sub> | 16.8<br><sub>29.1&nbsp;s</sub> | 25.6 | 2,530&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 10/12 |
| 12 | **WinDirStat** | 22.3 | 22.4<br><sub>232&nbsp;s</sub> | 18.0<br><sub>29.4&nbsp;s</sub> | 27.6 | 639&nbsp;MB | 0.90% | S·F·Z | 3/3 |
| 13 | **WizTree** | 17.8 | 9.9<br><sub>429&nbsp;s</sub> | 26.4<br><sub>19.6&nbsp;s</sub> | 21.8 | 1,461&nbsp;MB | 0.90% | S·F·Z | 2/2 |
| 14 | **SpaceSniffer** | 11.8 | 13.6<br><sub>312&nbsp;s</sub> | 6.5<br><sub>80.2&nbsp;s</sub> | 18.5 | 1,590&nbsp;MB | n/a | IO | 2/2 |

未上榜（没有任何平台的有效成绩） · Unranked (no valid result anywhere)：Sysinternals du

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (97.4) · **热扫 Warm** SpaceKnife (95.2) · **均衡 Balanced** SpaceKnife (97.1) · **最省内存 Least RAM** ncdu (4 MB) · **扫描效率 I/O efficiency** BSD du (100.0) · **最准 Most accurate** diskus (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**38.7**</mark>&nbsp;/&nbsp;<mark>**3.50**</mark> | 🥇<br><mark>**13.6**</mark>&nbsp;/&nbsp;<mark>**3.37**</mark> | 🥇<br>22.1&nbsp;/&nbsp;<mark>**4.06**</mark> | 🥇<br><mark>**32.8**</mark>&nbsp;/&nbsp;<mark>**24.9**</mark> |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>38.5&nbsp;/&nbsp;3.31 | 参考<br>12.6&nbsp;/&nbsp;3.26 | 参考<br>21.2&nbsp;/&nbsp;3.64 | 参考<br>32.1&nbsp;/&nbsp;24.4 |
| **gdu** | 🥉<br>39.6&nbsp;/&nbsp;4.78 | 🥉<br>16.4&nbsp;/&nbsp;4.87 | 🥉<br>25.1&nbsp;/&nbsp;6.10 | 🥉<br>54.3&nbsp;/&nbsp;30.4 |
| **SquirrelDisk** | 🥈<br>39.8&nbsp;/&nbsp;3.64 | 🥈<br>15.8&nbsp;/&nbsp;3.49 | 🥈<br>26.8&nbsp;/&nbsp;4.15 | #7<br>91.8&nbsp;/&nbsp;43.3 |
| **diskus** | #5<br>39.3&nbsp;/&nbsp;6.25 | #4<br>16.5&nbsp;/&nbsp;6.84 | #4<br><mark>**21.3**</mark>&nbsp;/&nbsp;8.35 | 🥈<br>49.7&nbsp;/&nbsp;29.4 |
| **dua‑cli** | #6<br>41.0&nbsp;/&nbsp;8.57 | #8<br>21.9&nbsp;/&nbsp;11.9 | #6<br>35.6&nbsp;/&nbsp;12.8 | #5<br>70.4&nbsp;/&nbsp;33.0 |
| **pdu** | #4<br>40.6&nbsp;/&nbsp;5.92 | #5<br>19.4&nbsp;/&nbsp;9.02 | #5<br>29.9&nbsp;/&nbsp;7.82 | #4<br>63.9&nbsp;/&nbsp;31.1 |
| **ncdu** | #9<br>123&nbsp;/&nbsp;9.39 | #6<br>49.2&nbsp;/&nbsp;6.71 | #7<br>83.2&nbsp;/&nbsp;9.94 | #9<br>145&nbsp;/&nbsp;43.6 |
| **GNU&nbsp;du** | #10<br>124&nbsp;/&nbsp;9.62 | #7<br>50.5&nbsp;/&nbsp;6.60 | #8<br>83.4&nbsp;/&nbsp;10.1 | #8<br>144&nbsp;/&nbsp;43.2 |
| **dust** | #7<br>43.0&nbsp;/&nbsp;11.1 | #9<br>24.4&nbsp;/&nbsp;15.0 | #9<br>36.9&nbsp;/&nbsp;17.0 | #6<br>73.7&nbsp;/&nbsp;35.4 |
| **erdtree** | #8<br>46.2&nbsp;/&nbsp;10.3 | #10<br>32.5&nbsp;/&nbsp;12.8 | #10<br>51.9&nbsp;/&nbsp;13.1 | #10<br>83.5&nbsp;/&nbsp;83.7 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**29.2**</mark>&nbsp;/&nbsp;2.65 | 🥇<br><mark>**12.0**</mark>&nbsp;/&nbsp;2.84 | 🥈<br>20.4&nbsp;/&nbsp;2.52 | 🥇<br><mark>**32.3**</mark>&nbsp;/&nbsp;<mark>**22.2**</mark> |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>28.9&nbsp;/&nbsp;2.40 | 参考<br>11.4&nbsp;/&nbsp;2.56 | 参考<br>20.3&nbsp;/&nbsp;2.23 | 参考<br>29.6&nbsp;/&nbsp;22.5 |
| **gdu** | #4<br>36.2&nbsp;/&nbsp;3.65 | #4<br>15.6&nbsp;/&nbsp;3.93 | #4<br>20.5&nbsp;/&nbsp;3.59 | 🥉<br>55.6&nbsp;/&nbsp;26.8 |
| **diskus** | 🥈<br>34.7&nbsp;/&nbsp;<mark>**2.50**</mark> | 🥈<br>12.5&nbsp;/&nbsp;<mark>**2.66**</mark> | 🥇<br><mark>**20.3**</mark>&nbsp;/&nbsp;<mark>**2.38**</mark> | 🥈<br>47.4&nbsp;/&nbsp;24.2 |
| **dua‑cli** | #7<br>36.8&nbsp;/&nbsp;15.4 | #7<br>22.8&nbsp;/&nbsp;15.3 | #7<br>26.5&nbsp;/&nbsp;15.0 | #5<br>71.8&nbsp;/&nbsp;30.8 |
| **pdu** | 🥉<br>33.4&nbsp;/&nbsp;3.24 | 🥉<br>16.3&nbsp;/&nbsp;3.50 | 🥉<br>22.7&nbsp;/&nbsp;3.43 | #4<br>66.4&nbsp;/&nbsp;26.5 |
| **ncdu** | #5<br>91.6&nbsp;/&nbsp;7.00 | #5<br>50.6&nbsp;/&nbsp;7.83 | #5<br>79.1&nbsp;/&nbsp;6.47 | #7<br>140&nbsp;/&nbsp;45.9 |
| **GNU&nbsp;du** | #6<br>91.9&nbsp;/&nbsp;7.46 | #6<br>50.8&nbsp;/&nbsp;8.17 | #6<br>75.7&nbsp;/&nbsp;6.86 | #8<br>141&nbsp;/&nbsp;46.3 |
| **dust** | #8<br>38.4&nbsp;/&nbsp;16.1 | #8<br>23.5&nbsp;/&nbsp;15.5 | #8<br>28.1&nbsp;/&nbsp;16.3 | #6<br>75.8&nbsp;/&nbsp;33.6 |
| **erdtree** | #9<br>44.0&nbsp;/&nbsp;16.6 | #9<br>37.2&nbsp;/&nbsp;16.2 | #9<br>43.0&nbsp;/&nbsp;16.4 | #9<br>85.1&nbsp;/&nbsp;83.1 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | ⚠️ | ⚠️ |
| **SpaceKnife&nbsp;(0.3.4)** | ⚠️ | ⚠️ |
| **gdu** | #4<br>776&nbsp;/&nbsp;437 | 🥉<br>538&nbsp;/&nbsp;157 |
| **SquirrelDisk** | 🥇<br><mark>**461**</mark>&nbsp;/&nbsp;395 | #4<br>591&nbsp;/&nbsp;186 |
| **BSD&nbsp;du** | #6<br>697&nbsp;/&nbsp;715 | #7<br>502&nbsp;/&nbsp;620 |
| **diskus** | 🥉<br>700&nbsp;/&nbsp;404 | 🥈<br>437&nbsp;/&nbsp;160 |
| **dua‑cli** | 🥈<br>583&nbsp;/&nbsp;<mark>**378**</mark> | 🥇<br><mark>**296**</mark>&nbsp;/&nbsp;<mark>**114**</mark> |
| **pdu** | #7<br>823&nbsp;/&nbsp;628 | #6<br>606&nbsp;/&nbsp;244 |
| **ncdu** | #8<br>1,312&nbsp;/&nbsp;754 | #8<br>935&nbsp;/&nbsp;431 |
| **dust** | #5<br>728&nbsp;/&nbsp;534 | #5<br>537&nbsp;/&nbsp;262 |
| **erdtree** | ⚠️ | ⚠️ |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>ReFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**51.7**</mark>&nbsp;/&nbsp;<mark>**4.73**</mark> | 🥇<br><mark>**77.9**</mark>&nbsp;/&nbsp;<mark>**5.57**</mark> | 🥇<br><mark>**34.7**</mark>&nbsp;/&nbsp;<mark>**5.66**</mark> |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>53.6&nbsp;/&nbsp;5.12 | 参考<br>85.8&nbsp;/&nbsp;6.23 | 参考<br>93.5&nbsp;/&nbsp;14.4 |
| **gdu** | 🥈<br>82.7&nbsp;/&nbsp;7.50 | 🥈<br>476&nbsp;/&nbsp;8.14 | 🥈<br>1,852&nbsp;/&nbsp;7.03 |
| **SquirrelDisk** | #6<br>123&nbsp;/&nbsp;12.5 | — | #6<br>1,735&nbsp;/&nbsp;34.6 |
| **diskus** | #7<br>155&nbsp;/&nbsp;38.2 | #5<br>586&nbsp;/&nbsp;66.6 | #11<br>1,853&nbsp;/&nbsp;207 |
| **dua‑cli** | 🥉<br>82.9&nbsp;/&nbsp;8.92 | 🥉<br>502&nbsp;/&nbsp;11.5 | 🥉<br>1,984&nbsp;/&nbsp;7.48 |
| **pdu** | #8<br>160&nbsp;/&nbsp;39.8 | #6<br>628&nbsp;/&nbsp;68.1 | #8<br>1,801&nbsp;/&nbsp;49.4 |
| **dust** | #9<br>177&nbsp;/&nbsp;48.6 | #7<br>654&nbsp;/&nbsp;83.0 | #10<br>1,794&nbsp;/&nbsp;120 |
| **erdtree** | #11<br>210&nbsp;/&nbsp;97.1 | — | #9<br>1,499&nbsp;/&nbsp;84.0 |
| **WinDirStat** | #5<br>73.7&nbsp;/&nbsp;20.4 | #4<br>518&nbsp;/&nbsp;20.4 | #4<br>327&nbsp;/&nbsp;61.2 |
| **WizTree** | #4<br>93.8&nbsp;/&nbsp;14.8 | — | #7<br>1,965&nbsp;/&nbsp;26.0 |
| **SpaceSniffer** | #10<br>207&nbsp;/&nbsp;67.1 | — | #5<br>470&nbsp;/&nbsp;95.7 |
| **Sysinternals&nbsp;du** | ⚠️ | ⚠️ | ⚠️ |

<sub>**参考**：SpaceKnife (0.3.4) 是 SpaceKnife 的旧版本，只作对照。它的分数照常计算，但不占名次、奖牌、高亮和单项第一，后面的扫描器顺延；奖牌只给当前版本。<br><br>**参考** (reference): SpaceKnife (0.3.4) is the earlier release of SpaceKnife, kept for comparison. Its scores are computed as usual, but it takes no rank, medal, highlight or category win, and the scanners after it move up; the medals go to the current release only.<br><br>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>low</b> · 100 万文件 · 1M files · 2026-11-11 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42904743933">run 42904743933</a> · <code>d940adf</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40257058978">run 40257058978</a> 2026-10-26</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**96.8**</mark> | <mark>**97.0**</mark><br><sub>12.3&nbsp;s</sub> | <mark>**96.9**</mark><br><sub>2.61&nbsp;s</sub> | <mark>**96.5**</mark> | 222&nbsp;MB | 0.09% | S·F·Z | 13/13 |
| 参考 | **SpaceKnife&nbsp;(0.3.4)** | 92.2 | 95.2<br><sub>12.8&nbsp;s</sub> | 87.6<br><sub>2.96&nbsp;s</sub> | 93.8 | 255&nbsp;MB | 0.27% | S·F·Z | 14/14 |
| 🥈 | **SquirrelDisk** | 63.4 | 52.1<br><sub>27.6&nbsp;s</sub> | 68.7<br><sub>5.33&nbsp;s</sub> | 71.1 | 29&nbsp;MB | 0.81% | S·F·Z | 9/9 |
| 🥉 | **gdu** | 54.8 | 43.7<br><sub>27.9&nbsp;s</sub> | 60.8<br><sub>4.27&nbsp;s</sub> | 62.0 | 47&nbsp;MB | 0.58% | S·Z | 14/14 |
| 4 | **BSD&nbsp;du** | 40.0 | 33.2<br><sub>83.0&nbsp;s</sub> | 32.8<br><sub>71.2&nbsp;s</sub> | 58.7 | 474&nbsp;MB | 17.48% | S·Z | 2/2 |
| 5 | **dua‑cli** | 39.7 | 38.9<br><sub>31.4&nbsp;s</sub> | 35.4<br><sub>7.33&nbsp;s</sub> | 45.5 | 13&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 6 | **GNU&nbsp;du** | 37.7 | 24.2<br><sub>30.9&nbsp;s</sub> | 37.2<br><sub>4.62&nbsp;s</sub> | 59.3 | 9&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 7 | **diskus** | 37.1 | 40.7<br><sub>30.0&nbsp;s</sub> | 30.8<br><sub>8.44&nbsp;s</sub> | 40.9 | 25&nbsp;MB | 0.06% | S | 14/14 |
| 8 | **pdu** | 34.1 | 34.0<br><sub>35.9&nbsp;s</sub> | 29.0<br><sub>8.96&nbsp;s</sub> | 40.3 | 48&nbsp;MB | 0.06% | S·Z | 14/14 |
| 9 | **ncdu** | 33.3 | 20.6<br><sub>47.2&nbsp;s</sub> | 33.2<br><sub>8.73&nbsp;s</sub> | 53.9 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 10 | **WinDirStat** | 29.4 | 43.1<br><sub>50.4&nbsp;s</sub> | 18.0<br><sub>10.9&nbsp;s</sub> | 32.7 | 248&nbsp;MB | 0.58% | S·F·Z | 4/4 |
| 11 | **WizTree** | 27.4 | 24.4<br><sub>74.4&nbsp;s</sub> | 26.5<br><sub>7.96&nbsp;s</sub> | 31.6 | 519&nbsp;MB | 0.58% | S·F·Z | 3/3 |
| 12 | **dust** | 24.2 | 29.2<br><sub>41.9&nbsp;s</sub> | 16.6<br><sub>15.6&nbsp;s</sub> | 29.1 | 391&nbsp;MB | 0.41% | S·Z | 14/14 |
| 13 | **erdtree** | 23.4 | 27.8<br><sub>40.4&nbsp;s</sub> | 16.8<br><sub>16.1&nbsp;s</sub> | 27.3 | 858&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 14 | **SpaceSniffer** | 15.2 | 22.0<br><sub>82.7&nbsp;s</sub> | 7.2<br><sub>29.3&nbsp;s</sub> | 22.4 | 552&nbsp;MB | n/a | IO | 3/3 |
| 15 | **Sysinternals&nbsp;du** | 6.1 | 11.6<br><sub>148&nbsp;s</sub> | 2.4<br><sub>151&nbsp;s</sub> | 8.1 | 57&nbsp;MB | 34.70% | S·F·Z | 1/4 |

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (97.0) · **热扫 Warm** SpaceKnife (96.9) · **均衡 Balanced** SpaceKnife (96.5) · **最省内存 Least RAM** ncdu (3 MB) · **扫描效率 I/O efficiency** WizTree (99.7) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>12.7&nbsp;/&nbsp;<mark>**1.24**</mark> | 🥇<br><mark>**5.69**</mark>&nbsp;/&nbsp;<mark>**1.47**</mark> | 🥇<br><mark>**7.13**</mark>&nbsp;/&nbsp;<mark>**1.23**</mark> | 🥇<br><mark>**11.3**</mark>&nbsp;/&nbsp;<mark>**10.3**</mark> |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>12.9&nbsp;/&nbsp;1.42 | 参考<br>5.70&nbsp;/&nbsp;1.62 | 参考<br>7.02&nbsp;/&nbsp;1.35 | 参考<br>11.8&nbsp;/&nbsp;10.5 |
| **SquirrelDisk** | 🥈<br>13.8&nbsp;/&nbsp;1.37 | 🥈<br>7.25&nbsp;/&nbsp;1.52 | 🥈<br>8.72&nbsp;/&nbsp;1.37 | #7<br>28.6&nbsp;/&nbsp;10.7 |
| **gdu** | 🥉<br>15.3&nbsp;/&nbsp;1.69 | 🥉<br>7.33&nbsp;/&nbsp;2.11 | 🥉<br>8.26&nbsp;/&nbsp;1.85 | 🥉<br>17.1&nbsp;/&nbsp;11.3 |
| **dua‑cli** | #7<br>21.7&nbsp;/&nbsp;3.74 | #6<br>9.81&nbsp;/&nbsp;4.30 | #6<br>10.4&nbsp;/&nbsp;4.23 | #5<br>21.5&nbsp;/&nbsp;11.8 |
| **GNU&nbsp;du** | #10<br>55.7&nbsp;/&nbsp;3.60 | #8<br>20.9&nbsp;/&nbsp;3.94 | #8<br>25.9&nbsp;/&nbsp;3.25 | #10<br>50.6&nbsp;/&nbsp;24.3 |
| **diskus** | #5<br><mark>**12.5**</mark>&nbsp;/&nbsp;2.66 | #4<br>7.01&nbsp;/&nbsp;2.86 | #4<br>7.16&nbsp;/&nbsp;2.76 | 🥈<br>16.2&nbsp;/&nbsp;11.3 |
| **pdu** | #4<br>14.4&nbsp;/&nbsp;2.25 | #5<br>8.22&nbsp;/&nbsp;3.26 | #5<br>9.55&nbsp;/&nbsp;2.54 | #4<br>20.4&nbsp;/&nbsp;11.2 |
| **ncdu** | #9<br>56.0&nbsp;/&nbsp;3.39 | #7<br>20.8&nbsp;/&nbsp;3.86 | #7<br>25.7&nbsp;/&nbsp;3.20 | #9<br>49.5&nbsp;/&nbsp;24.2 |
| **dust** | #8<br>25.4&nbsp;/&nbsp;4.54 | #9<br>10.5&nbsp;/&nbsp;5.66 | #9<br>11.0&nbsp;/&nbsp;5.59 | #6<br>21.7&nbsp;/&nbsp;12.3 |
| **erdtree** | #6<br>17.5&nbsp;/&nbsp;3.68 | #10<br>13.9&nbsp;/&nbsp;4.32 | #10<br>16.2&nbsp;/&nbsp;4.23 | #8<br>23.3&nbsp;/&nbsp;16.0 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**8.67**</mark>&nbsp;/&nbsp;<mark>**0.80**</mark> | 🥈<br>4.01&nbsp;/&nbsp;0.92 | 🥇<br>6.47&nbsp;/&nbsp;<mark>**0.77**</mark> | 🥇<br><mark>**9.95**</mark>&nbsp;/&nbsp;6.27 |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>8.94&nbsp;/&nbsp;0.92 | 参考<br>3.72&nbsp;/&nbsp;1.01 | 参考<br>6.73&nbsp;/&nbsp;0.93 | 参考<br>9.25&nbsp;/&nbsp;6.25 |
| **gdu** | #4<br>9.03&nbsp;/&nbsp;1.13 | #4<br>4.82&nbsp;/&nbsp;1.23 | 🥉<br>7.10&nbsp;/&nbsp;1.10 | 🥉<br>16.6&nbsp;/&nbsp;6.89 |
| **dua‑cli** | #8<br>12.0&nbsp;/&nbsp;5.21 | #7<br>7.65&nbsp;/&nbsp;5.43 | #8<br>12.5&nbsp;/&nbsp;5.34 | #6<br>28.4&nbsp;/&nbsp;8.72 |
| **GNU&nbsp;du** | #6<br>28.9&nbsp;/&nbsp;2.41 | #6<br>15.0&nbsp;/&nbsp;2.65 | #6<br>27.4&nbsp;/&nbsp;2.16 | #8<br>46.4&nbsp;/&nbsp;13.5 |
| **diskus** | 🥈<br>8.77&nbsp;/&nbsp;0.83 | 🥇<br><mark>**3.54**</mark>&nbsp;/&nbsp;<mark>**0.88**</mark> | 🥈<br><mark>**6.13**</mark>&nbsp;/&nbsp;0.78 | 🥈<br>13.2&nbsp;/&nbsp;<mark>**6.07**</mark> |
| **pdu** | 🥉<br>9.59&nbsp;/&nbsp;1.02 | 🥉<br>5.22&nbsp;/&nbsp;1.13 | #4<br>10.0&nbsp;/&nbsp;1.07 | #4<br>20.3&nbsp;/&nbsp;6.45 |
| **ncdu** | #5<br>29.9&nbsp;/&nbsp;2.31 | #5<br>14.9&nbsp;/&nbsp;2.44 | #5<br>28.3&nbsp;/&nbsp;2.03 | #9<br>47.5&nbsp;/&nbsp;13.4 |
| **dust** | #7<br>11.7&nbsp;/&nbsp;5.21 | #8<br>8.09&nbsp;/&nbsp;5.46 | #7<br>12.3&nbsp;/&nbsp;5.42 | #5<br>25.6&nbsp;/&nbsp;9.53 |
| **erdtree** | #9<br>14.4&nbsp;/&nbsp;5.13 | #9<br>11.1&nbsp;/&nbsp;5.73 | #9<br>17.9&nbsp;/&nbsp;6.29 | #7<br>25.7&nbsp;/&nbsp;12.8 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | 🥈<br>32.1&nbsp;/&nbsp;32.9 | 🥈<br><mark>**25.5**</mark>&nbsp;/&nbsp;22.9 |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>39.4&nbsp;/&nbsp;36.3 | 参考<br>28.8&nbsp;/&nbsp;26.3 |
| **SquirrelDisk** | 🥇<br><mark>**29.8**</mark>&nbsp;/&nbsp;<mark>**28.1**</mark> | 🥇<br>30.7&nbsp;/&nbsp;<mark>**19.5**</mark> |
| **gdu** | #6<br>171&nbsp;/&nbsp;90.6 | #5<br>174&nbsp;/&nbsp;65.2 |
| **BSD&nbsp;du** | #4<br>86.1&nbsp;/&nbsp;89.0 | #4<br>79.9&nbsp;/&nbsp;57.0 |
| **dua‑cli** | 🥉<br>81.3&nbsp;/&nbsp;57.1 | 🥉<br>79.3&nbsp;/&nbsp;34.4 |
| **diskus** | #5<br>138&nbsp;/&nbsp;96.3 | #6<br>158&nbsp;/&nbsp;86.0 |
| **pdu** | #9<br>152&nbsp;/&nbsp;136 | #8<br>175&nbsp;/&nbsp;93.8 |
| **ncdu** | #10<br>235&nbsp;/&nbsp;118 | #10<br>266&nbsp;/&nbsp;140 |
| **dust** | #8<br>154&nbsp;/&nbsp;127 | #9<br>183&nbsp;/&nbsp;107 |
| **erdtree** | #7<br>158&nbsp;/&nbsp;119 | #7<br>170&nbsp;/&nbsp;88.9 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**15.5**</mark>&nbsp;/&nbsp;<mark>**1.59**</mark> | 🥇<br><mark>**37.8**</mark>&nbsp;/&nbsp;<mark>**1.60**</mark> | — | 🥇<br><mark>**22.9**</mark>&nbsp;/&nbsp;<mark>**1.64**</mark> |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>16.0&nbsp;/&nbsp;1.78 | 参考<br>36.7&nbsp;/&nbsp;1.93 | 参考<br>17.2&nbsp;/&nbsp;3.59 | 参考<br>22.5&nbsp;/&nbsp;1.95 |
| **SquirrelDisk** | #5<br>36.6&nbsp;/&nbsp;3.85 | — | 🥈<br><mark>**17.5**</mark>&nbsp;/&nbsp;22.2 | 🥈<br>627&nbsp;/&nbsp;2.42 |
| **gdu** | 🥈<br>27.2&nbsp;/&nbsp;2.35 | 🥈<br>195&nbsp;/&nbsp;2.44 | 🥇<br>22.4&nbsp;/&nbsp;<mark>**10.1**</mark> | 🥉<br>605&nbsp;/&nbsp;2.50 |
| **dua‑cli** | 🥉<br>25.8&nbsp;/&nbsp;2.79 | 🥉<br>207&nbsp;/&nbsp;3.86 | #4<br>28.2&nbsp;/&nbsp;18.5 | #5<br>611&nbsp;/&nbsp;3.14 |
| **diskus** | #7<br>45.1&nbsp;/&nbsp;12.0 | #5<br>286&nbsp;/&nbsp;21.3 | #7<br>112&nbsp;/&nbsp;115 | #11<br>597&nbsp;/&nbsp;45.9 |
| **pdu** | #8<br>47.5&nbsp;/&nbsp;12.0 | #6<br>281&nbsp;/&nbsp;22.6 | #9<br>131&nbsp;/&nbsp;125 | #8<br>548&nbsp;/&nbsp;29.9 |
| **WinDirStat** | #6<br>23.2&nbsp;/&nbsp;6.81 | #4<br>166&nbsp;/&nbsp;6.53 | #5<br>20.2&nbsp;/&nbsp;21.3 | #4<br>82.4&nbsp;/&nbsp;15.1 |
| **WizTree** | #4<br>29.5&nbsp;/&nbsp;4.81 | — | 🥉<br>21.1&nbsp;/&nbsp;18.2 | #7<br>664&nbsp;/&nbsp;5.75 |
| **dust** | #9<br>51.2&nbsp;/&nbsp;14.9 | #7<br>263&nbsp;/&nbsp;27.3 | #8<br>122&nbsp;/&nbsp;123 | #9<br>580&nbsp;/&nbsp;29.0 |
| **erdtree** | #11<br>65.0&nbsp;/&nbsp;30.7 | — | #10<br>123&nbsp;/&nbsp;123 | #10<br>520&nbsp;/&nbsp;46.7 |
| **SpaceSniffer** | #10<br>64.0&nbsp;/&nbsp;22.2 | — | #6<br>53.9&nbsp;/&nbsp;55.2 | #6<br>164&nbsp;/&nbsp;20.5 |
| **Sysinternals&nbsp;du** | ⚠️ | ⚠️ | #11<br>148&nbsp;/&nbsp;151 | ⚠️ |

<sub>**参考**：SpaceKnife (0.3.4) 是 SpaceKnife 的旧版本，只作对照。它的分数照常计算，但不占名次、奖牌、高亮和单项第一，后面的扫描器顺延；奖牌只给当前版本。<br><br>**参考** (reference): SpaceKnife (0.3.4) is the earlier release of SpaceKnife, kept for comparison. Its scores are computed as usual, but it takes no rank, medal, highlight or category win, and the scanners after it move up; the medals go to the current release only.<br><br>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>lite</b> · 40 万文件 · 400k files · 2026-11-10 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42860980701">run 42860980701</a> · <code>d36278b</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42860980701">run 42860980701</a> 2026-11-10 · 仅供参考 reference only</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**96.9**</mark> | <mark>**94.7**</mark><br><sub>4.94&nbsp;s</sub> | <mark>**98.2**</mark><br><sub>0.79&nbsp;s</sub> | <mark>**97.8**</mark> | 130&nbsp;MB | 0.14% | S·F·Z | 14/14 |
| 参考 | **SpaceKnife&nbsp;(0.3.4)** | 84.2 | 91.4<br><sub>5.12&nbsp;s</sub> | 73.9<br><sub>1.05&nbsp;s</sub> | 88.4 | 154&nbsp;MB | 0.14% | S·F·Z | 14/14 |
| 🥈 | **SquirrelDisk** | 66.1 | 55.7<br><sub>9.15&nbsp;s</sub> | 70.5<br><sub>1.51&nbsp;s</sub> | 73.4 | 18&nbsp;MB | 0.58% | S·F·Z | 9/9 |
| 🥉 | **gdu** | 58.1 | 43.9<br><sub>12.1&nbsp;s</sub> | 67.3<br><sub>1.07&nbsp;s</sub> | 66.4 | 36&nbsp;MB | 0.40% | S·Z | 11/14 |
| 4 | **BSD&nbsp;du** | 49.1 | 48.5<br><sub>10.4&nbsp;s</sub> | 34.7<br><sub>12.2&nbsp;s</sub> | 70.2 | 210&nbsp;MB | 8.74% | S·Z | 2/2 |
| 5 | **dua‑cli** | 40.7 | 43.6<br><sub>10.7&nbsp;s</sub> | 34.1<br><sub>2.26&nbsp;s</sub> | 45.3 | 6&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 6 | **GNU&nbsp;du** | 38.4 | 25.3<br><sub>11.8&nbsp;s</sub> | 37.1<br><sub>1.24&nbsp;s</sub> | 60.2 | 8&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 7 | **diskus** | 37.1 | 42.5<br><sub>11.0&nbsp;s</sub> | 29.8<br><sub>2.59&nbsp;s</sub> | 40.1 | 20&nbsp;MB | 0.14% | S | 14/14 |
| 8 | **pdu** | 35.2 | 37.9<br><sub>12.4&nbsp;s</sub> | 28.3<br><sub>2.73&nbsp;s</sub> | 40.7 | 21&nbsp;MB | 0.14% | S·Z | 14/14 |
| 9 | **WinDirStat** | 33.7 | 49.1<br><sub>22.5&nbsp;s</sub> | 20.8<br><sub>4.43&nbsp;s</sub> | 37.4 | 126&nbsp;MB | 0.41% | S·F·Z | 4/4 |
| 10 | **ncdu** | 33.1 | 21.9<br><sub>15.2&nbsp;s</sub> | 31.2<br><sub>2.30&nbsp;s</sub> | 53.0 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 11 | **WizTree** | 31.6 | 25.6<br><sub>38.7&nbsp;s</sub> | 33.9<br><sub>3.03&nbsp;s</sub> | 36.5 | 236&nbsp;MB | 0.41% | S·F·Z | 3/3 |
| 12 | **dust** | 24.0 | 32.8<br><sub>14.2&nbsp;s</sub> | 14.9<br><sub>5.19&nbsp;s</sub> | 28.1 | 149&nbsp;MB | 0.25% | S·Z | 14/14 |
| 13 | **erdtree** | 22.6 | 28.7<br><sub>14.9&nbsp;s</sub> | 15.7<br><sub>4.99&nbsp;s</sub> | 25.8 | 344&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 14 | **SpaceSniffer** | 17.6 | 26.3<br><sub>37.6&nbsp;s</sub> | 8.1<br><sub>12.7&nbsp;s</sub> | 25.6 | 240&nbsp;MB | n/a | IO | 3/3 |

未上榜（没有任何平台的有效成绩） · Unranked (no valid result anywhere)：Sysinternals du

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (94.7) · **热扫 Warm** SpaceKnife (98.2) · **均衡 Balanced** SpaceKnife (97.8) · **最省内存 Least RAM** ncdu (3 MB) · **扫描效率 I/O efficiency** WizTree (99.7) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>4.68&nbsp;/&nbsp;<mark>**0.49**</mark> | 🥇<br><mark>**2.47**</mark>&nbsp;/&nbsp;<mark>**0.69**</mark> | 🥇<br>2.38&nbsp;/&nbsp;<mark>**0.34**</mark> | 🥇<br><mark>**3.96**</mark>&nbsp;/&nbsp;<mark>**0.78**</mark> |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>4.96&nbsp;/&nbsp;0.68 | 参考<br>2.93&nbsp;/&nbsp;0.93 | 参考<br>2.62&nbsp;/&nbsp;0.49 | 参考<br>3.90&nbsp;/&nbsp;1.00 |
| **SquirrelDisk** | 🥈<br><mark>**4.37**</mark>&nbsp;/&nbsp;0.62 | 🥈<br>2.87&nbsp;/&nbsp;0.77 | 🥉<br>2.87&nbsp;/&nbsp;0.46 | 🥉<br>6.96&nbsp;/&nbsp;0.91 |
| **gdu** | 🥉<br>4.40&nbsp;/&nbsp;0.66 | ⚠️ | 🥈<br>2.36&nbsp;/&nbsp;0.41 | #4<br>6.58&nbsp;/&nbsp;1.02 |
| **dua‑cli** | #6<br>5.56&nbsp;/&nbsp;1.52 | #5<br>3.95&nbsp;/&nbsp;2.02 | #9<br>3.63&nbsp;/&nbsp;1.77 | #6<br>8.42&nbsp;/&nbsp;2.08 |
| **GNU&nbsp;du** | #10<br>21.3&nbsp;/&nbsp;1.41 | #9<br>8.30&nbsp;/&nbsp;1.98 | #7<br>10.8&nbsp;/&nbsp;0.71 | #9<br>18.3&nbsp;/&nbsp;1.91 |
| **diskus** | #4<br>4.49&nbsp;/&nbsp;1.05 | #4<br>2.98&nbsp;/&nbsp;1.47 | #4<br><mark>**2.24**</mark>&nbsp;/&nbsp;0.77 | 🥈<br>4.03&nbsp;/&nbsp;1.24 |
| **pdu** | #5<br>5.78&nbsp;/&nbsp;0.93 | 🥉<br>3.22&nbsp;/&nbsp;1.34 | #5<br>2.92&nbsp;/&nbsp;0.98 | #5<br>7.87&nbsp;/&nbsp;1.46 |
| **ncdu** | #9<br>16.3&nbsp;/&nbsp;1.33 | #8<br>8.27&nbsp;/&nbsp;1.87 | #6<br>10.7&nbsp;/&nbsp;0.69 | #10<br>18.2&nbsp;/&nbsp;1.93 |
| **dust** | #7<br>4.95&nbsp;/&nbsp;1.76 | #7<br>4.16&nbsp;/&nbsp;2.38 | #8<br>3.44&nbsp;/&nbsp;1.91 | #8<br>9.12&nbsp;/&nbsp;2.15 |
| **erdtree** | #8<br>7.84&nbsp;/&nbsp;1.40 | #6<br>5.03&nbsp;/&nbsp;1.85 | #10<br>5.70&nbsp;/&nbsp;1.56 | #7<br>8.89&nbsp;/&nbsp;2.08 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>2.92&nbsp;/&nbsp;<mark>**0.33**</mark> | 🥈<br>2.11&nbsp;/&nbsp;0.36 | 🥈<br>3.50&nbsp;/&nbsp;0.31 | 🥇<br><mark>**3.73**</mark>&nbsp;/&nbsp;0.70 |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>3.24&nbsp;/&nbsp;0.50 | 参考<br>2.62&nbsp;/&nbsp;0.54 | 参考<br>3.26&nbsp;/&nbsp;0.47 | 参考<br>3.55&nbsp;/&nbsp;0.87 |
| **gdu** | #4<br>2.91&nbsp;/&nbsp;0.44 | ⚠️ | #4<br>3.63&nbsp;/&nbsp;0.40 | 🥉<br>5.25&nbsp;/&nbsp;0.89 |
| **dua‑cli** | #8<br>3.59&nbsp;/&nbsp;2.11 | #7<br>3.59&nbsp;/&nbsp;2.08 | #8<br>5.42&nbsp;/&nbsp;2.04 | #5<br>7.72&nbsp;/&nbsp;2.42 |
| **GNU&nbsp;du** | #6<br>9.35&nbsp;/&nbsp;0.94 | #5<br>5.74&nbsp;/&nbsp;1.00 | #6<br>10.8&nbsp;/&nbsp;0.79 | #8<br>18.8&nbsp;/&nbsp;2.06 |
| **diskus** | 🥈<br><mark>**2.88**</mark>&nbsp;/&nbsp;<mark>**0.33**</mark> | 🥇<br><mark>**2.03**</mark>&nbsp;/&nbsp;<mark>**0.34**</mark> | 🥇<br><mark>**3.46**</mark>&nbsp;/&nbsp;<mark>**0.30**</mark> | 🥈<br>3.87&nbsp;/&nbsp;<mark>**0.69**</mark> |
| **pdu** | 🥉<br>3.02&nbsp;/&nbsp;0.38 | 🥉<br>2.64&nbsp;/&nbsp;0.43 | 🥉<br>3.84&nbsp;/&nbsp;0.37 | #4<br>6.64&nbsp;/&nbsp;0.79 |
| **ncdu** | #5<br>9.31&nbsp;/&nbsp;0.89 | #4<br>5.44&nbsp;/&nbsp;0.94 | #5<br>11.0&nbsp;/&nbsp;0.76 | #9<br>19.6&nbsp;/&nbsp;2.00 |
| **dust** | #7<br>3.54&nbsp;/&nbsp;2.16 | #6<br>3.59&nbsp;/&nbsp;2.06 | #7<br>4.42&nbsp;/&nbsp;1.99 | #6<br>8.69&nbsp;/&nbsp;2.41 |
| **erdtree** | #9<br>4.76&nbsp;/&nbsp;2.18 | #8<br>4.55&nbsp;/&nbsp;2.23 | #9<br>6.91&nbsp;/&nbsp;2.07 | #7<br>9.54&nbsp;/&nbsp;2.58 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | 🥇<br>6.68&nbsp;/&nbsp;<mark>**4.64**</mark> | 🥇<br><mark>**4.92**</mark>&nbsp;/&nbsp;<mark>**4.32**</mark> |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>5.19&nbsp;/&nbsp;4.16 | 参考<br>6.89&nbsp;/&nbsp;5.75 |
| **SquirrelDisk** | 🥈<br><mark>**5.66**</mark>&nbsp;/&nbsp;7.01 | 🥈<br>7.29&nbsp;/&nbsp;6.82 |
| **gdu** | ⚠️ | #5<br>52.5&nbsp;/&nbsp;21.3 |
| **BSD&nbsp;du** | #4<br>7.12&nbsp;/&nbsp;10.5 | #4<br>15.2&nbsp;/&nbsp;14.2 |
| **dua‑cli** | 🥉<br>6.48&nbsp;/&nbsp;6.56 | 🥉<br>20.3&nbsp;/&nbsp;7.90 |
| **diskus** | #7<br>18.9&nbsp;/&nbsp;14.3 | #8<br>49.7&nbsp;/&nbsp;29.6 |
| **pdu** | #5<br>8.88&nbsp;/&nbsp;16.3 | #6<br>43.9&nbsp;/&nbsp;29.7 |
| **ncdu** | #9<br>29.0&nbsp;/&nbsp;30.1 | #10<br>78.0&nbsp;/&nbsp;33.3 |
| **dust** | #6<br>15.0&nbsp;/&nbsp;18.3 | #7<br>45.7&nbsp;/&nbsp;34.4 |
| **erdtree** | #8<br>24.0&nbsp;/&nbsp;15.5 | #9<br>55.0&nbsp;/&nbsp;27.7 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**7.76**</mark>&nbsp;/&nbsp;<mark>**0.72**</mark> | 🥇<br><mark>**16.9**</mark>&nbsp;/&nbsp;<mark>**0.67**</mark> | 🥇<br>7.07&nbsp;/&nbsp;<mark>**1.36**</mark> | 🥇<br><mark>**19.2**</mark>&nbsp;/&nbsp;<mark>**1.12**</mark> |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>8.29&nbsp;/&nbsp;1.02 | 参考<br>15.3&nbsp;/&nbsp;0.98 | 参考<br>6.59&nbsp;/&nbsp;1.65 | 参考<br>19.4&nbsp;/&nbsp;1.41 |
| **SquirrelDisk** | #4<br>18.3&nbsp;/&nbsp;1.64 | — | 🥈<br><mark>**6.54**</mark>&nbsp;/&nbsp;1.75 | 🥉<br>366&nbsp;/&nbsp;1.50 |
| **gdu** | 🥈<br>12.6&nbsp;/&nbsp;0.84 | 🥈<br>105&nbsp;/&nbsp;0.95 | 🥉<br>8.39&nbsp;/&nbsp;1.70 | #4<br>361&nbsp;/&nbsp;1.72 |
| **dua‑cli** | 🥉<br>12.8&nbsp;/&nbsp;1.27 | 🥉<br>110&nbsp;/&nbsp;1.64 | #4<br>10.6&nbsp;/&nbsp;1.91 | #5<br>380&nbsp;/&nbsp;1.83 |
| **diskus** | #7<br>24.0&nbsp;/&nbsp;5.64 | #5<br>134&nbsp;/&nbsp;8.91 | #8<br>38.5&nbsp;/&nbsp;40.0 | #10<br>349&nbsp;/&nbsp;21.3 |
| **pdu** | #8<br>24.8&nbsp;/&nbsp;5.64 | #6<br>148&nbsp;/&nbsp;10.1 | #9<br>40.2&nbsp;/&nbsp;43.9 | #8<br>388&nbsp;/&nbsp;12.3 |
| **WinDirStat** | #5<br>11.7&nbsp;/&nbsp;2.85 | #4<br>108&nbsp;/&nbsp;2.82 | #6<br>8.16&nbsp;/&nbsp;6.76 | 🥈<br>24.8&nbsp;/&nbsp;7.06 |
| **WizTree** | #6<br>17.4&nbsp;/&nbsp;2.58 | — | #5<br>9.81&nbsp;/&nbsp;3.43 | #7<br>340&nbsp;/&nbsp;3.15 |
| **dust** | #9<br>27.6&nbsp;/&nbsp;6.85 | #7<br>155&nbsp;/&nbsp;11.2 | #10<br>42.5&nbsp;/&nbsp;44.0 | #9<br>360&nbsp;/&nbsp;13.2 |
| **erdtree** | #11<br>33.0&nbsp;/&nbsp;13.9 | — | #11<br>42.2&nbsp;/&nbsp;42.0 | #11<br>331&nbsp;/&nbsp;21.7 |
| **SpaceSniffer** | #10<br>30.2&nbsp;/&nbsp;10.2 | — | #7<br>18.7&nbsp;/&nbsp;17.3 | #6<br>94.1&nbsp;/&nbsp;11.6 |
| **Sysinternals&nbsp;du** | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

<sub>**参考**：SpaceKnife (0.3.4) 是 SpaceKnife 的旧版本，只作对照。它的分数照常计算，但不占名次、奖牌、高亮和单项第一，后面的扫描器顺延；奖牌只给当前版本。<br><br>**参考** (reference): SpaceKnife (0.3.4) is the earlier release of SpaceKnife, kept for comparison. Its scores are computed as usual, but it takes no rank, medal, highlight or category win, and the scanners after it move up; the medals go to the current release only.<br><br>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>very-lite</b> · 10 万文件 · 100k files · 2026-11-11 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42904737091">run 42904737091</a> · <code>d940adf</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/43146189054">run 43146189054</a> 2026-11-12 · 仅供参考 reference only</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**86.6**</mark> | <mark>**74.9**</mark><br><sub>1.26&nbsp;s</sub> | <mark>**95.6**</mark><br><sub>0.19&nbsp;s</sub> | 90.7 | 40&nbsp;MB | 0.04% | S·F·Z | 14/14 |
| 🥈 | **BSD&nbsp;du** | 76.2 | 64.6<br><sub>0.75&nbsp;s</sub> | 72.5<br><sub>0.64&nbsp;s</sub> | <mark>**94.4**</mark> | 73&nbsp;MB | 2.78% | S·Z | 2/2 |
| 🥉 | **SquirrelDisk** | 67.2 | 52.4<br><sub>1.93&nbsp;s</sub> | 76.2<br><sub>0.31&nbsp;s</sub> | 75.9 | 12&nbsp;MB | 2.02% | S·F·Z | 9/9 |
| 4 | **gdu** | 56.8 | 41.8<br><sub>2.40&nbsp;s</sub> | 70.1<br><sub>0.27&nbsp;s</sub> | 62.7 | 27&nbsp;MB | 0.27% | S·Z | 13/14 |
| 参考 | **SpaceKnife&nbsp;(0.3.4)** | 55.5 | 62.8<br><sub>1.51&nbsp;s</sub> | 42.3<br><sub>0.43&nbsp;s</sub> | 64.3 | 76&nbsp;MB | 0.04% | S·F·Z | 14/14 |
| 5 | **diskus** | 49.7 | 54.4<br><sub>1.74&nbsp;s</sub> | 44.2<br><sub>0.41&nbsp;s</sub> | 50.9 | 11&nbsp;MB | 0.15% | S | 14/14 |
| 6 | **pdu** | 45.3 | 43.7<br><sub>2.17&nbsp;s</sub> | 42.9<br><sub>0.42&nbsp;s</sub> | 49.6 | 8&nbsp;MB | 0.15% | S·Z | 14/14 |
| 7 | **dua‑cli** | 43.7 | 49.7<br><sub>1.91&nbsp;s</sub> | 35.3<br><sub>0.52&nbsp;s</sub> | 47.6 | 4&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 8 | **ncdu** | 39.6 | 26.3<br><sub>2.35&nbsp;s</sub> | 39.5<br><sub>0.43&nbsp;s</sub> | 60.0 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 9 | **GNU&nbsp;du** | 38.9 | 23.8<br><sub>2.76&nbsp;s</sub> | 40.3<br><sub>0.32&nbsp;s</sub> | 61.6 | 5&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 10 | **WinDirStat** | 38.3 | 68.8<br><sub>4.01&nbsp;s</sub> | 19.8<br><sub>1.12&nbsp;s</sub> | 41.2 | 71&nbsp;MB | 0.31% | S·F·Z | 4/4 |
| 11 | **dust** | 31.4 | 41.1<br><sub>2.30&nbsp;s</sub> | 21.7<br><sub>0.84&nbsp;s</sub> | 34.8 | 39&nbsp;MB | 0.77% | S·Z | 14/14 |
| 12 | **erdtree** | 27.6 | 32.8<br><sub>2.54&nbsp;s</sub> | 21.4<br><sub>0.85&nbsp;s</sub> | 29.9 | 88&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 13 | **WizTree** | 24.2 | 21.5<br><sub>10.5&nbsp;s</sub> | 22.1<br><sub>1.07&nbsp;s</sub> | 29.9 | 94&nbsp;MB | 0.31% | S·F·Z | 3/3 |
| 14 | **SpaceSniffer** | 16.6 | 28.3<br><sub>8.00&nbsp;s</sub> | 6.1<br><sub>3.85&nbsp;s</sub> | 26.1 | 84&nbsp;MB | n/a | IO | 3/3 |

未上榜（没有任何平台的有效成绩） · Unranked (no valid result anywhere)：Sysinternals du

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (74.9) · **热扫 Warm** SpaceKnife (95.6) · **均衡 Balanced** BSD du (94.4) · **最省内存 Least RAM** ncdu (3 MB) · **扫描效率 I/O efficiency** WizTree (99.6) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>0.87&nbsp;/&nbsp;<mark>**0.12**</mark> | 🥇<br><mark>**0.66**</mark>&nbsp;/&nbsp;0.17 | 🥇<br><mark>**0.54**</mark>&nbsp;/&nbsp;<mark>**0.14**</mark> | 🥇<br><mark>**1.33**</mark>&nbsp;/&nbsp;0.32 |
| **SquirrelDisk** | 🥉<br>1.38&nbsp;/&nbsp;0.15 | 🥈<br>0.93&nbsp;/&nbsp;<mark>**0.16**</mark> | 🥈<br>0.78&nbsp;/&nbsp;0.15 | 🥈<br>1.68&nbsp;/&nbsp;<mark>**0.31**</mark> |
| **gdu** | 🥈<br>0.92&nbsp;/&nbsp;0.17 | 🥉<br>0.79&nbsp;/&nbsp;0.22 | 🥉<br>1.04&nbsp;/&nbsp;0.17 | 🥉<br>1.59&nbsp;/&nbsp;0.40 |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>1.25&nbsp;/&nbsp;0.35 | 参考<br>1.15&nbsp;/&nbsp;0.38 | 参考<br>0.93&nbsp;/&nbsp;0.32 | 参考<br>1.63&nbsp;/&nbsp;0.54 |
| **diskus** | #4<br><mark>**0.85**</mark>&nbsp;/&nbsp;0.26 | #4<br>0.73&nbsp;/&nbsp;0.30 | #5<br>0.58&nbsp;/&nbsp;0.28 | #4<br>1.37&nbsp;/&nbsp;0.46 |
| **pdu** | #5<br>1.37&nbsp;/&nbsp;0.32 | #5<br>0.81&nbsp;/&nbsp;0.32 | #4<br>0.81&nbsp;/&nbsp;0.22 | #5<br>1.88&nbsp;/&nbsp;0.47 |
| **dua‑cli** | #8<br>1.44&nbsp;/&nbsp;0.47 | #6<br>1.01&nbsp;/&nbsp;0.46 | #7<br>1.15&nbsp;/&nbsp;0.41 | #6<br>1.95&nbsp;/&nbsp;0.63 |
| **ncdu** | #7<br>3.55&nbsp;/&nbsp;0.23 | #7<br>2.02&nbsp;/&nbsp;0.38 | #8<br>2.36&nbsp;/&nbsp;0.30 | #10<br>4.88&nbsp;/&nbsp;0.84 |
| **GNU&nbsp;du** | #6<br>3.46&nbsp;/&nbsp;0.23 | #8<br>2.04&nbsp;/&nbsp;0.40 | #10<br>2.80&nbsp;/&nbsp;0.32 | #9<br>4.85&nbsp;/&nbsp;0.85 |
| **dust** | #10<br>1.44&nbsp;/&nbsp;0.54 | #9<br>1.07&nbsp;/&nbsp;0.58 | #6<br>0.95&nbsp;/&nbsp;0.46 | #8<br>2.01&nbsp;/&nbsp;0.71 |
| **erdtree** | #9<br>1.68&nbsp;/&nbsp;0.44 | #10<br>1.40&nbsp;/&nbsp;0.45 | #9<br>1.53&nbsp;/&nbsp;0.36 | #7<br>2.29&nbsp;/&nbsp;0.61 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**0.55**</mark>&nbsp;/&nbsp;0.10 | 🥉<br>0.60&nbsp;/&nbsp;0.11 | 🥈<br>0.42&nbsp;/&nbsp;0.09 | 🥈<br><mark>**1.01**</mark>&nbsp;/&nbsp;0.18 |
| **gdu** | #4<br>0.89&nbsp;/&nbsp;0.13 | ⚠️ | #4<br>0.48&nbsp;/&nbsp;0.11 | #4<br>1.04&nbsp;/&nbsp;0.22 |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>0.94&nbsp;/&nbsp;0.31 | 参考<br>1.16&nbsp;/&nbsp;0.30 | 参考<br>0.71&nbsp;/&nbsp;0.28 | 参考<br>1.35&nbsp;/&nbsp;0.37 |
| **diskus** | 🥈<br>0.65&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥇<br><mark>**0.45**</mark>&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥇<br><mark>**0.34**</mark>&nbsp;/&nbsp;<mark>**0.08**</mark> | 🥇<br>1.13&nbsp;/&nbsp;<mark>**0.16**</mark> |
| **pdu** | 🥉<br>1.27&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥈<br>0.62&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥉<br>0.61&nbsp;/&nbsp;0.09 | 🥉<br>1.30&nbsp;/&nbsp;0.18 |
| **dua‑cli** | #8<br>1.47&nbsp;/&nbsp;0.55 | #7<br>0.90&nbsp;/&nbsp;0.52 | #8<br>0.79&nbsp;/&nbsp;0.51 | #6<br>1.31&nbsp;/&nbsp;0.57 |
| **ncdu** | #5<br>3.23&nbsp;/&nbsp;0.23 | #5<br>1.71&nbsp;/&nbsp;0.23 | #5<br>1.88&nbsp;/&nbsp;0.19 | #8<br>3.12&nbsp;/&nbsp;0.48 |
| **GNU&nbsp;du** | #6<br>3.39&nbsp;/&nbsp;0.23 | #4<br>1.55&nbsp;/&nbsp;0.23 | #6<br>1.92&nbsp;/&nbsp;0.20 | #9<br>3.48&nbsp;/&nbsp;0.48 |
| **dust** | #7<br>1.41&nbsp;/&nbsp;0.57 | #6<br>0.86&nbsp;/&nbsp;0.50 | #7<br>0.76&nbsp;/&nbsp;0.48 | #5<br>1.33&nbsp;/&nbsp;0.55 |
| **erdtree** | #9<br>1.70&nbsp;/&nbsp;0.53 | #8<br>1.28&nbsp;/&nbsp;0.48 | #9<br>1.15&nbsp;/&nbsp;0.49 | #7<br>1.61&nbsp;/&nbsp;0.55 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | #7<br>2.26&nbsp;/&nbsp;<mark>**0.50**</mark> | #8<br>2.93&nbsp;/&nbsp;<mark>**0.43**</mark> |
| **BSD&nbsp;du** | #5<br>1.10&nbsp;/&nbsp;0.79 | 🥈<br>0.51&nbsp;/&nbsp;0.52 |
| **SquirrelDisk** | 🥇<br>0.75&nbsp;/&nbsp;0.55 | #4<br>0.52&nbsp;/&nbsp;0.51 |
| **gdu** | #8<br>1.86&nbsp;/&nbsp;0.81 | #10<br>8.39&nbsp;/&nbsp;0.81 |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>1.50&nbsp;/&nbsp;0.75 | 参考<br>1.03&nbsp;/&nbsp;0.62 |
| **diskus** | #6<br>1.74&nbsp;/&nbsp;0.54 | 🥉<br>0.43&nbsp;/&nbsp;0.55 |
| **pdu** | 🥉<br>0.71&nbsp;/&nbsp;0.65 | #7<br>0.79&nbsp;/&nbsp;0.63 |
| **dua‑cli** | 🥈<br>0.79&nbsp;/&nbsp;0.55 | 🥇<br><mark>**0.34**</mark>&nbsp;/&nbsp;0.48 |
| **ncdu** | #9<br>1.56&nbsp;/&nbsp;1.29 | #9<br>1.23&nbsp;/&nbsp;1.44 |
| **dust** | #4<br><mark>**0.70**</mark>&nbsp;/&nbsp;0.67 | #5<br>0.59&nbsp;/&nbsp;0.68 |
| **erdtree** | #10<br>2.09&nbsp;/&nbsp;1.32 | #6<br>0.68&nbsp;/&nbsp;0.59 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**3.25**</mark>&nbsp;/&nbsp;<mark>**0.24**</mark> | 🥇<br><mark>**4.96**</mark>&nbsp;/&nbsp;<mark>**0.18**</mark> | 🥇<br>2.07&nbsp;/&nbsp;<mark>**0.31**</mark> | 🥇<br><mark>**2.06**</mark>&nbsp;/&nbsp;<mark>**0.17**</mark> |
| **SquirrelDisk** | 🥉<br>5.48&nbsp;/&nbsp;0.43 | — | 🥈<br><mark>**1.73**</mark>&nbsp;/&nbsp;0.54 | #4<br>59.1&nbsp;/&nbsp;0.37 |
| **gdu** | 🥈<br>4.17&nbsp;/&nbsp;0.32 | 🥈<br>16.0&nbsp;/&nbsp;0.24 | 🥉<br>2.40&nbsp;/&nbsp;0.46 | 🥉<br>65.3&nbsp;/&nbsp;0.26 |
| **SpaceKnife&nbsp;(0.3.4)** | 参考<br>3.55&nbsp;/&nbsp;0.55 | 参考<br>5.09&nbsp;/&nbsp;0.49 | 参考<br>2.10&nbsp;/&nbsp;0.62 | 参考<br>2.34&nbsp;/&nbsp;0.43 |
| **diskus** | #7<br>9.70&nbsp;/&nbsp;1.81 | #5<br>21.9&nbsp;/&nbsp;2.11 | #7<br>4.52&nbsp;/&nbsp;1.09 | #11<br>57.5&nbsp;/&nbsp;3.27 |
| **pdu** | #8<br>10.3&nbsp;/&nbsp;1.89 | #6<br>23.5&nbsp;/&nbsp;2.20 | #8<br>6.00&nbsp;/&nbsp;1.11 | #9<br>59.0&nbsp;/&nbsp;1.97 |
| **dua‑cli** | #4<br>4.02&nbsp;/&nbsp;0.62 | #4<br>15.3&nbsp;/&nbsp;0.53 | #4<br>2.00&nbsp;/&nbsp;0.57 | #5<br>56.7&nbsp;/&nbsp;0.39 |
| **WinDirStat** | #5<br>3.34&nbsp;/&nbsp;0.93 | 🥉<br>10.6&nbsp;/&nbsp;0.70 | #5<br>2.03&nbsp;/&nbsp;1.60 | 🥈<br>3.58&nbsp;/&nbsp;1.48 |
| **dust** | #10<br>9.83&nbsp;/&nbsp;3.06 | #7<br>26.0&nbsp;/&nbsp;2.51 | #9<br>5.95&nbsp;/&nbsp;1.54 | #8<br>52.6&nbsp;/&nbsp;2.05 |
| **erdtree** | #11<br>12.4&nbsp;/&nbsp;4.78 | — | #11<br>6.82&nbsp;/&nbsp;3.36 | #10<br>46.8&nbsp;/&nbsp;3.23 |
| **WizTree** | #6<br>4.89&nbsp;/&nbsp;1.25 | — | #6<br>3.72&nbsp;/&nbsp;1.11 | #7<br>64.0&nbsp;/&nbsp;0.88 |
| **SpaceSniffer** | #9<br>10.0&nbsp;/&nbsp;4.24 | — | #10<br>4.91&nbsp;/&nbsp;4.72 | #6<br>10.4&nbsp;/&nbsp;2.86 |
| **Sysinternals&nbsp;du** | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

<sub>**参考**：SpaceKnife (0.3.4) 是 SpaceKnife 的旧版本，只作对照。它的分数照常计算，但不占名次、奖牌、高亮和单项第一，后面的扫描器顺延；奖牌只给当前版本。<br><br>**参考** (reference): SpaceKnife (0.3.4) is the earlier release of SpaceKnife, kept for comparison. Its scores are computed as usual, but it takes no rank, medal, highlight or category win, and the scanners after it move up; the medals go to the current release only.<br><br>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<a id="atime-off"></a>

### 🪟 Windows 访问时间关闭对照榜 · Windows with access times off (comparison only)

> [!WARNING]
> **只作对照，不是正式排名。** 这张榜只用来展示关闭 Windows 访问时间更新（`fsutil behavior set disablelastaccess 1`）之后的效果。日常使用的 Windows 开着访问时间更新，主榜也是开着测的；关掉它反而会让排名偏离真实使用场景下的性能排序，正式排名请以主榜为准。
>
> **For comparison only, not a ranking.** This board only shows what turning Windows last-access updates off (`fsutil behavior set disablelastaccess 1`) changes. Windows in daily use keeps them on, and so does the main board; turning them off moves the ranking away from how the scanners perform in real use, so the main board is the one that counts.

同一批 Windows 平台（Win ARM64 (NTFS)、Win x64 (NTFS)、Win x64 (ReFS)）、同样的体量（`very-lite`, `lite`, `low`, `mid`, `high`）：**开** = 主榜在这些平台上的成绩（访问时间开着，日常设置），**关** = 关掉访问时间更新后另跑的一次。

Same Windows platforms (Win ARM64 (NTFS), Win x64 (NTFS), Win x64 (ReFS)) and sizes (`very-lite`, `lite`, `low`, `mid`, `high`): **On** = the main board's results there (access times on, the daily-use setting), **Off** = a separate run with last-access updates turned off.

| 扫⁠描⁠器<br>Scanner | 开&nbsp;·&nbsp;日⁠常<br>On&nbsp;·&nbsp;daily&nbsp;use | 关<br>Off | 名⁠次⁠变⁠化<br>Change |
| :--- | :---: | :---: | :---: |
| **SpaceKnife** | #1&nbsp;99.7 | #1&nbsp;90.2 | = |
| **SpaceKnife&nbsp;(0.3.4)** | 参考&nbsp;86.7 | 参考&nbsp;90.0 | — |
| **gdu** | #2&nbsp;37.4 | #2&nbsp;78.8 | = |
| **dua‑cli** | #3&nbsp;32.6 | #3&nbsp;69.0 | = |
| **WinDirStat** | #4&nbsp;25.7 | #6&nbsp;47.5 | ↓2 |
| **WizTree** | #5&nbsp;23.0 | #4&nbsp;56.0 | ↑1 |
| **SquirrelDisk** | #6&nbsp;21.6 | #5&nbsp;55.5 | ↑1 |
| **SpaceSniffer** | #7&nbsp;14.9 | #8&nbsp;19.8 | ↓1 |
| **pdu** | #8&nbsp;12.9 | #7&nbsp;20.3 | ↑1 |
| **diskus** | #9&nbsp;11.5 | #10&nbsp;17.3 | ↓1 |
| **dust** | #10&nbsp;9.7 | #9&nbsp;19.1 | ↑1 |
| **erdtree** | #11&nbsp;8.1 | #11&nbsp;12.9 | = |
| **Sysinternals&nbsp;du** | #12&nbsp;6.3 | — | — |

<details>
<summary><b>high</b> · 500 万文件 · 5M files · 关 Off: 2026-11-11 <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42904731530">run 42904731530</a></summary>

| 扫⁠描⁠器<br>Scanner | 开&nbsp;·&nbsp;分<br>On&nbsp;·&nbsp;score | 关&nbsp;·&nbsp;分<br>Off&nbsp;·&nbsp;score | 开&nbsp;冷/热<br>On&nbsp;cold/warm | 关&nbsp;冷/热<br>Off&nbsp;cold/warm |
| :--- | :---: | :---: | ---: | ---: |
| **SpaceKnife&nbsp;(0.3.4)** | 参考&nbsp;99.3 | 参考&nbsp;90.8 | 113&nbsp;s&nbsp;/&nbsp;13.9&nbsp;s | 140&nbsp;s&nbsp;/&nbsp;20.7&nbsp;s |
| **gdu** | #1&nbsp;39.8 | #2&nbsp;84.7 | 725&nbsp;s&nbsp;/&nbsp;19.0&nbsp;s | 148&nbsp;s&nbsp;/&nbsp;22.5&nbsp;s |
| **dua‑cli** | #2&nbsp;34.2 | #3&nbsp;70.3 | 759&nbsp;s&nbsp;/&nbsp;24.3&nbsp;s | 150&nbsp;s&nbsp;/&nbsp;30.5&nbsp;s |
| **WizTree** | #3&nbsp;30.2 | #5&nbsp;56.7 | 641&nbsp;s&nbsp;/&nbsp;25.5&nbsp;s | 155&nbsp;s&nbsp;/&nbsp;70.9&nbsp;s |
| **WinDirStat** | #4&nbsp;27.9 | #6&nbsp;50.6 | 433&nbsp;s&nbsp;/&nbsp;54.1&nbsp;s | 136&nbsp;s&nbsp;/&nbsp;64.9&nbsp;s |
| **SpaceSniffer** | #5&nbsp;19.2 | #8&nbsp;20.8 | 537&nbsp;s&nbsp;/&nbsp;125&nbsp;s | 398&nbsp;s&nbsp;/&nbsp;262&nbsp;s |
| **SquirrelDisk** | #6&nbsp;18.9 | #4&nbsp;64.8 | 863&nbsp;s&nbsp;/&nbsp;75.4&nbsp;s | 202&nbsp;s&nbsp;/&nbsp;37.8&nbsp;s |
| **pdu** | #7&nbsp;17.2 | #7&nbsp;21.0 | 1,009&nbsp;s&nbsp;/&nbsp;64.2&nbsp;s | 327&nbsp;s&nbsp;/&nbsp;171&nbsp;s |
| **diskus** | #8&nbsp;16.6 | #9&nbsp;19.9 | 953&nbsp;s&nbsp;/&nbsp;66.4&nbsp;s | 345&nbsp;s&nbsp;/&nbsp;170&nbsp;s |
| **dust** | #9&nbsp;10.0 | #10&nbsp;19.2 | 1,058&nbsp;s&nbsp;/&nbsp;204&nbsp;s | 350&nbsp;s&nbsp;/&nbsp;194&nbsp;s |
| **erdtree** | #10&nbsp;9.9 | #11&nbsp;13.5 | 925&nbsp;s&nbsp;/&nbsp;220&nbsp;s | 454&nbsp;s&nbsp;/&nbsp;411&nbsp;s |
| **Sysinternals&nbsp;du** | #11&nbsp;6.3 | — | 1,493&nbsp;s&nbsp;/&nbsp;458&nbsp;s | —&nbsp;/&nbsp;— |
| **SpaceKnife** | — | #1&nbsp;91.3 | —&nbsp;/&nbsp;— | 143&nbsp;s&nbsp;/&nbsp;19.3&nbsp;s |

</details>

<details>
<summary><b>mid</b> · 300 万文件 · 3M files · 关 Off: 2026-11-10 <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42904725266">run 42904725266</a></summary>

| 扫⁠描⁠器<br>Scanner | 开&nbsp;·&nbsp;分<br>On&nbsp;·&nbsp;score | 关&nbsp;·&nbsp;分<br>Off&nbsp;·&nbsp;score | 开&nbsp;冷/热<br>On&nbsp;cold/warm | 关&nbsp;冷/热<br>Off&nbsp;cold/warm |
| :--- | :---: | :---: | ---: | ---: |
| **SpaceKnife** | #1&nbsp;100.0 | #1&nbsp;84.7 | 51.9&nbsp;s&nbsp;/&nbsp;5.30&nbsp;s | 64.2&nbsp;s&nbsp;/&nbsp;7.17&nbsp;s |
| **SpaceKnife&nbsp;(0.3.4)** | 参考&nbsp;70.6 | 参考&nbsp;90.4 | 75.5&nbsp;s&nbsp;/&nbsp;7.71&nbsp;s | 70.4&nbsp;s&nbsp;/&nbsp;5.81&nbsp;s |
| **gdu** | #2&nbsp;34.9 | #2&nbsp;76.2 | 418&nbsp;s&nbsp;/&nbsp;7.54&nbsp;s | 69.8&nbsp;s&nbsp;/&nbsp;8.13&nbsp;s |
| **dua‑cli** | #3&nbsp;31.1 | #3&nbsp;70.2 | 435&nbsp;s&nbsp;/&nbsp;9.14&nbsp;s | 68.0&nbsp;s&nbsp;/&nbsp;9.78&nbsp;s |
| **WinDirStat** | #4&nbsp;22.3 | #5&nbsp;48.2 | 232&nbsp;s&nbsp;/&nbsp;29.4&nbsp;s | 56.3&nbsp;s&nbsp;/&nbsp;24.2&nbsp;s |
| **SquirrelDisk** | #5&nbsp;18.0 | #6&nbsp;43.0 | 463&nbsp;s&nbsp;/&nbsp;20.8&nbsp;s | 82.7&nbsp;s&nbsp;/&nbsp;22.7&nbsp;s |
| **WizTree** | #6&nbsp;17.8 | #4&nbsp;58.1 | 429&nbsp;s&nbsp;/&nbsp;19.6&nbsp;s | 66.4&nbsp;s&nbsp;/&nbsp;16.1&nbsp;s |
| **SpaceSniffer** | #7&nbsp;11.8 | #9&nbsp;19.3 | 312&nbsp;s&nbsp;/&nbsp;80.2&nbsp;s | 160&nbsp;s&nbsp;/&nbsp;78.7&nbsp;s |
| **pdu** | #8&nbsp;11.2 | #8&nbsp;20.7 | 565&nbsp;s&nbsp;/&nbsp;51.2&nbsp;s | 146&nbsp;s&nbsp;/&nbsp;53.2&nbsp;s |
| **diskus** | #9&nbsp;8.8 | #10&nbsp;16.3 | 553&nbsp;s&nbsp;/&nbsp;80.8&nbsp;s | 151&nbsp;s&nbsp;/&nbsp;81.4&nbsp;s |
| **dust** | #10&nbsp;8.8 | #7&nbsp;21.1 | 593&nbsp;s&nbsp;/&nbsp;78.4&nbsp;s | 143&nbsp;s&nbsp;/&nbsp;52.8&nbsp;s |
| **erdtree** | #11&nbsp;7.4 | #11&nbsp;13.4 | 561&nbsp;s&nbsp;/&nbsp;90.3&nbsp;s | 176&nbsp;s&nbsp;/&nbsp;108&nbsp;s |

</details>

<details>
<summary><b>low</b> · 100 万文件 · 1M files · 关 Off: 2026-11-10 <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42904718645">run 42904718645</a></summary>

| 扫⁠描⁠器<br>Scanner | 开&nbsp;·&nbsp;分<br>On&nbsp;·&nbsp;score | 关&nbsp;·&nbsp;分<br>Off&nbsp;·&nbsp;score | 开&nbsp;冷/热<br>On&nbsp;cold/warm | 关&nbsp;冷/热<br>Off&nbsp;cold/warm |
| :--- | :---: | :---: | ---: | ---: |
| **SpaceKnife** | #1&nbsp;99.5 | #1&nbsp;94.9 | 23.8&nbsp;s&nbsp;/&nbsp;1.61&nbsp;s | 27.3&nbsp;s&nbsp;/&nbsp;1.69&nbsp;s |
| **SpaceKnife&nbsp;(0.3.4)** | 参考&nbsp;93.0 | 参考&nbsp;89.0 | 23.7&nbsp;s&nbsp;/&nbsp;1.89&nbsp;s | 27.2&nbsp;s&nbsp;/&nbsp;1.96&nbsp;s |
| **gdu** | #2&nbsp;37.7 | #2&nbsp;75.7 | 147&nbsp;s&nbsp;/&nbsp;2.43&nbsp;s | 29.2&nbsp;s&nbsp;/&nbsp;2.55&nbsp;s |
| **dua‑cli** | #3&nbsp;32.6 | #3&nbsp;66.6 | 148&nbsp;s&nbsp;/&nbsp;3.23&nbsp;s | 29.6&nbsp;s&nbsp;/&nbsp;3.19&nbsp;s |
| **SquirrelDisk** | #4&nbsp;29.8 | #4&nbsp;61.3 | 151&nbsp;s&nbsp;/&nbsp;3.05&nbsp;s | 29.1&nbsp;s&nbsp;/&nbsp;3.73&nbsp;s |
| **WinDirStat** | #5&nbsp;27.3 | #6&nbsp;43.9 | 68.3&nbsp;s&nbsp;/&nbsp;8.76&nbsp;s | 23.6&nbsp;s&nbsp;/&nbsp;8.88&nbsp;s |
| **WizTree** | #6&nbsp;22.4 | #5&nbsp;53.4 | 140&nbsp;s&nbsp;/&nbsp;5.26&nbsp;s | 27.5&nbsp;s&nbsp;/&nbsp;5.41&nbsp;s |
| **SpaceSniffer** | #7&nbsp;14.7 | #7&nbsp;19.3 | 103&nbsp;s&nbsp;/&nbsp;21.3&nbsp;s | 64.4&nbsp;s&nbsp;/&nbsp;23.4&nbsp;s |
| **pdu** | #8&nbsp;11.2 | #8&nbsp;19.1 | 194&nbsp;s&nbsp;/&nbsp;20.1&nbsp;s | 58.1&nbsp;s&nbsp;/&nbsp;19.8&nbsp;s |
| **dust** | #9&nbsp;10.4 | #9&nbsp;17.2 | 198&nbsp;s&nbsp;/&nbsp;22.8&nbsp;s | 63.3&nbsp;s&nbsp;/&nbsp;22.9&nbsp;s |
| **diskus** | #10&nbsp;10.3 | #10&nbsp;15.9 | 197&nbsp;s&nbsp;/&nbsp;22.7&nbsp;s | 71.0&nbsp;s&nbsp;/&nbsp;23.7&nbsp;s |
| **erdtree** | #11&nbsp;7.3 | #11&nbsp;12.0 | 184&nbsp;s&nbsp;/&nbsp;37.8&nbsp;s | 69.0&nbsp;s&nbsp;/&nbsp;40.0&nbsp;s |

</details>

<details>
<summary><b>lite</b> · 40 万文件 · 400k files · 关 Off: 2026-11-10 <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42904712794">run 42904712794</a></summary>

| 扫⁠描⁠器<br>Scanner | 开&nbsp;·&nbsp;分<br>On&nbsp;·&nbsp;score | 关&nbsp;·&nbsp;分<br>Off&nbsp;·&nbsp;score | 开&nbsp;冷/热<br>On&nbsp;cold/warm | 关&nbsp;冷/热<br>Off&nbsp;cold/warm |
| :--- | :---: | :---: | ---: | ---: |
| **SpaceKnife** | #1&nbsp;98.6 | #1&nbsp;94.2 | 13.6&nbsp;s&nbsp;/&nbsp;0.81&nbsp;s | 8.81&nbsp;s&nbsp;/&nbsp;0.54&nbsp;s |
| **SpaceKnife&nbsp;(0.3.4)** | 参考&nbsp;85.8 | 参考&nbsp;81.0 | 13.5&nbsp;s&nbsp;/&nbsp;1.12&nbsp;s | 8.75&nbsp;s&nbsp;/&nbsp;0.76&nbsp;s |
| **gdu** | #2&nbsp;40.5 | #2&nbsp;80.9 | 78.3&nbsp;s&nbsp;/&nbsp;1.11&nbsp;s | 9.31&nbsp;s&nbsp;/&nbsp;0.69&nbsp;s |
| **SquirrelDisk** | #3&nbsp;33.7 | #3&nbsp;66.4 | 81.7&nbsp;s&nbsp;/&nbsp;1.57&nbsp;s | 8.03&nbsp;s&nbsp;/&nbsp;0.90&nbsp;s |
| **dua‑cli** | #4&nbsp;33.5 | #4&nbsp;66.1 | 81.2&nbsp;s&nbsp;/&nbsp;1.56&nbsp;s | 9.16&nbsp;s&nbsp;/&nbsp;1.05&nbsp;s |
| **WinDirStat** | #5&nbsp;32.1 | #6&nbsp;42.7 | 31.5&nbsp;s&nbsp;/&nbsp;3.85&nbsp;s | 7.66&nbsp;s&nbsp;/&nbsp;2.95&nbsp;s |
| **WizTree** | #6&nbsp;24.4 | #5&nbsp;49.3 | 76.9&nbsp;s&nbsp;/&nbsp;2.85&nbsp;s | 7.64&nbsp;s&nbsp;/&nbsp;1.81&nbsp;s |
| **SpaceSniffer** | #7&nbsp;16.7 | #8&nbsp;18.9 | 53.3&nbsp;s&nbsp;/&nbsp;10.9&nbsp;s | 17.4&nbsp;s&nbsp;/&nbsp;6.93&nbsp;s |
| **pdu** | #8&nbsp;11.7 | #7&nbsp;20.3 | 112&nbsp;s&nbsp;/&nbsp;8.89&nbsp;s | 18.0&nbsp;s&nbsp;/&nbsp;5.74&nbsp;s |
| **diskus** | #9&nbsp;11.2 | #10&nbsp;18.3 | 104&nbsp;s&nbsp;/&nbsp;10.2&nbsp;s | 18.0&nbsp;s&nbsp;/&nbsp;6.87&nbsp;s |
| **dust** | #10&nbsp;10.9 | #9&nbsp;18.4 | 115&nbsp;s&nbsp;/&nbsp;10.1&nbsp;s | 18.5&nbsp;s&nbsp;/&nbsp;6.86&nbsp;s |
| **erdtree** | #11&nbsp;8.5 | #11&nbsp;13.1 | 105&nbsp;s&nbsp;/&nbsp;17.4&nbsp;s | 17.7&nbsp;s&nbsp;/&nbsp;10.3&nbsp;s |

</details>

<details>
<summary><b>very-lite</b> · 10 万文件 · 100k files · 关 Off: 2026-11-10 <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42904689518">run 42904689518</a></summary>

| 扫⁠描⁠器<br>Scanner | 开&nbsp;·&nbsp;分<br>On&nbsp;·&nbsp;score | 关&nbsp;·&nbsp;分<br>Off&nbsp;·&nbsp;score | 开&nbsp;冷/热<br>On&nbsp;cold/warm | 关&nbsp;冷/热<br>Off&nbsp;cold/warm |
| :--- | :---: | :---: | ---: | ---: |
| **SpaceKnife** | #1&nbsp;100.0 | #1&nbsp;93.4 | 3.22&nbsp;s&nbsp;/&nbsp;0.20&nbsp;s | 2.90&nbsp;s&nbsp;/&nbsp;0.17&nbsp;s |
| **SpaceKnife&nbsp;(0.3.4)** | 参考&nbsp;64.2 | 参考&nbsp;58.9 | 3.48&nbsp;s&nbsp;/&nbsp;0.49&nbsp;s | 3.14&nbsp;s&nbsp;/&nbsp;0.43&nbsp;s |
| **gdu** | #2&nbsp;43.2 | #2&nbsp;74.7 | 16.3&nbsp;s&nbsp;/&nbsp;0.27&nbsp;s | 3.43&nbsp;s&nbsp;/&nbsp;0.23&nbsp;s |
| **WinDirStat** | #3&nbsp;37.7 | #5&nbsp;42.5 | 5.03&nbsp;s&nbsp;/&nbsp;0.99&nbsp;s | 2.77&nbsp;s&nbsp;/&nbsp;0.86&nbsp;s |
| **SquirrelDisk** | #4&nbsp;32.8 | #3&nbsp;64.4 | 18.0&nbsp;s&nbsp;/&nbsp;0.40&nbsp;s | 2.32&nbsp;s&nbsp;/&nbsp;0.37&nbsp;s |
| **dua‑cli** | #5&nbsp;32.6 | #4&nbsp;58.8 | 15.2&nbsp;s&nbsp;/&nbsp;0.51&nbsp;s | 2.96&nbsp;s&nbsp;/&nbsp;0.41&nbsp;s |
| **WizTree** | #6&nbsp;19.2 | #6&nbsp;42.1 | 17.7&nbsp;s&nbsp;/&nbsp;1.05&nbsp;s | 2.64&nbsp;s&nbsp;/&nbsp;0.76&nbsp;s |
| **SpaceSniffer** | #7&nbsp;15.5 | #10&nbsp;18.0 | 10.2&nbsp;s&nbsp;/&nbsp;3.48&nbsp;s | 5.18&nbsp;s&nbsp;/&nbsp;2.79&nbsp;s |
| **pdu** | #8&nbsp;12.7 | #7&nbsp;20.5 | 24.3&nbsp;s&nbsp;/&nbsp;2.01&nbsp;s | 6.02&nbsp;s&nbsp;/&nbsp;1.67&nbsp;s |
| **diskus** | #9&nbsp;12.0 | #9&nbsp;18.3 | 23.0&nbsp;s&nbsp;/&nbsp;2.32&nbsp;s | 6.28&nbsp;s&nbsp;/&nbsp;1.99&nbsp;s |
| **dust** | #10&nbsp;11.5 | #8&nbsp;18.8 | 23.8&nbsp;s&nbsp;/&nbsp;2.51&nbsp;s | 6.28&nbsp;s&nbsp;/&nbsp;1.91&nbsp;s |
| **erdtree** | #11&nbsp;8.2 | #11&nbsp;13.1 | 24.1&nbsp;s&nbsp;/&nbsp;3.93&nbsp;s | 6.00&nbsp;s&nbsp;/&nbsp;3.11&nbsp;s |

</details>

<sub>两边各自在自己的平台内算相对分（该平台最快 ÷ 自己 × 100，冷扫、热扫、均衡指数的几何平均），再对 `low` 及以上体量取几何平均，\* 为只有小体量成绩；名次变化 = 关掉以后名次的升降（↑ 升、↓ 降）。这里只列名次、不发奖牌；冷/热是有效平台上用时（秒）的几何平均。<br><br>Each side is scored within its own platforms (platform fastest / own x 100, geometric mean of cold, warm and the balanced index), then over the sizes from `low` up; \* = small sizes only. Change = how the rank moves once access times are off (↑ up, ↓ down). Ranks only, no medals; cold/warm = geometric mean of the seconds over the valid platforms.<br><br>**参考**：SpaceKnife (0.3.4) 是 SpaceKnife 的旧版本，只作对照。它的分数照常计算，但不占名次、奖牌、高亮和单项第一，后面的扫描器顺延；奖牌只给当前版本。<br><br>**参考** (reference): SpaceKnife (0.3.4) is the earlier release of SpaceKnife, kept for comparison. Its scores are computed as usual, but it takes no rank, medal, highlight or category win, and the scanners after it move up; the medals go to the current release only.</sub>

### NTFS MFT 专栏 · NTFS MFT column

直接读取 NTFS `$MFT` 的扫描模式单独比较，不和上面的普通目录遍历混排；冷热两次耗时应当接近，因为每次都要读完整张 MFT。

Scanners that read the NTFS `$MFT` directly are ranked here, apart from the directory-walking board above; their cold and warm times should be close, since every scan reads the whole MFT.

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | very‑lite\* | lite\* | low | mid | high | very‑high | before‑death |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 参考 | **SpaceKnife&nbsp;(0.3.4)** | 100.0 | 参考&nbsp;77.0<br><sub>0.98&nbsp;/&nbsp;1.00&nbsp;s</sub> | 参考&nbsp;100.0<br><sub>1.66&nbsp;/&nbsp;1.65&nbsp;s</sub> | 参考&nbsp;100.0<br><sub>3.57&nbsp;/&nbsp;3.65&nbsp;s</sub> | 参考&nbsp;100.0<br><sub>9.52&nbsp;/&nbsp;9.52&nbsp;s</sub> | 参考&nbsp;100.0<br><sub>15.6&nbsp;/&nbsp;15.6&nbsp;s</sub> | 参考&nbsp;100.0<br><sub>27.6&nbsp;/&nbsp;27.6&nbsp;s</sub> | 参考&nbsp;100.0<br><sub>31.2&nbsp;/&nbsp;31.3&nbsp;s</sub> |
| 🥇 | **WizTree** | <mark>**37.0**</mark> | 🥈&nbsp;77.4<br><sub>0.96&nbsp;/&nbsp;0.91&nbsp;s</sub> | 🥈&nbsp;56.4<br><sub>2.58&nbsp;/&nbsp;2.60&nbsp;s</sub> | 🥇&nbsp;<mark>**45.0**</mark><br><sub>6.74&nbsp;/&nbsp;6.75&nbsp;s</sub> | 🥇&nbsp;<mark>**37.7**</mark><br><sub>20.5&nbsp;/&nbsp;20.5&nbsp;s</sub> | 🥇&nbsp;<mark>**35.7**</mark><br><sub>35.4&nbsp;/&nbsp;35.2&nbsp;s</sub> | 🥇&nbsp;<mark>**35.0**</mark><br><sub>62.9&nbsp;/&nbsp;63.3&nbsp;s</sub> | 🥈&nbsp;32.8<br><sub>80.1&nbsp;/&nbsp;76.8&nbsp;s</sub> |
| 🥈 | **WinDirStat** | 35.5 | 🥇&nbsp;<mark>**100.0**</mark><br><sub>0.75&nbsp;/&nbsp;0.76&nbsp;s</sub> | 🥇&nbsp;<mark>**57.8**</mark><br><sub>2.73&nbsp;/&nbsp;2.67&nbsp;s</sub> | 🥈&nbsp;41.9<br><sub>7.75&nbsp;/&nbsp;7.96&nbsp;s</sub> | 🥈&nbsp;35.4<br><sub>23.2&nbsp;/&nbsp;23.7&nbsp;s</sub> | 🥈&nbsp;33.9<br><sub>40.0&nbsp;/&nbsp;40.0&nbsp;s</sub> | 🥈&nbsp;32.5<br><sub>74.4&nbsp;/&nbsp;71.8&nbsp;s</sub> | 🥇&nbsp;<mark>**34.7**</mark><br><sub>80.5&nbsp;/&nbsp;78.0&nbsp;s</sub> |

<sub><mark>**高亮**</mark> = 该列最高分 · <mark>**highlighted**</mark> = best in its column.<br><br>综合分 = `low` 及以上各体量 MFT 分数的几何平均，\* 为仅供参考的小体量；每格是该体量的名次和分数，下一行小字是冷扫 / 热扫秒数。⛔ 无法运行 · ❌ 违规 · ⚠️ 无效 · — 未参加。<br><br>Score = geometric mean of the MFT scores from `low` up; \* marks the reference-only small sizes. Each cell: rank and score in that size, then cold / warm seconds in small print. ⛔ cannot run · ❌ disqualified · ⚠️ invalid · — not run.</sub>

### 在你的 README 里显示成绩 · Show a score in your README

徽章由 CI 在每次发布时更新，显示该扫描器的最新名次和综合分。把对应的一行贴进任何 Markdown：

Badges are refreshed on every publish with the scanner's current rank and score. Paste a line into any Markdown file:

```markdown
[![SpaceKnife](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife-rust.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SpaceKnife (0.3.4)](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![gdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SquirrelDisk](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsquirreldisk.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![BSD du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fbsd-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![diskus](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdiskus.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![dua-cli](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdua.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![pdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fpdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![GNU du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgnu-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![ncdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fncdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![dust](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdust.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![WinDirStat](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![WizTree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwiztree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![erdtree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Ferdtree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SpaceSniffer](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspacesniffer.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![Sysinternals du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsysinternals-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
```

单个体量：文件名换成 `<扫描器>-<体量>.json`（例如 `gdu-low.json`）；MFT 专栏综合排名用 `<扫描器>-mft.json`，单个体量用 `<扫描器>-mft-<体量>.json`；也可以运行 `python scripts/readme_board.py --snippet <扫描器> [--preset low]` 生成。

One size only: use `<scanner>-<size>.json` (e.g. `gdu-low.json`). For the MFT column use `<scanner>-mft.json` (across sizes) or `<scanner>-mft-<size>.json`; `python scripts/readme_board.py --snippet <scanner> [--preset low]` prints the line.

<!-- LEADERBOARD:END -->

<!-- COMMUNITY:START -->

<a id="real-drives"></a>

## 🖥️ 社区真实盘成绩 · Community results on real drives

> ⚖️ **利益声明**：SpaceKnife (0.3.4) 和 SpaceKnife 属于本基准作者的项目，作者从它们的排名中直接受益，详见[利益声明](#利益声明--conflict-of-interest)。<br>
> ⚖️ **Conflict of interest**: SpaceKnife (0.3.4) and SpaceKnife belong to a project of this benchmark's author, who benefits directly from how they rank; see [Conflict of interest](#利益声明--conflict-of-interest).

> ⚖️ 目前收录的成绩全部来自本基准作者自己的电脑：1 块 NTFS 系统盘（已使用约 1 年）、2 块 ReFS 数据盘（已使用约 3–4 年），都是日常在用的盘。<br>
> ⚖️ Both submissions so far come from this benchmark's author's own machine: 1 NTFS system drive in use for about 1 year, 2 ReFS data drives in use for about 3–4 years, all of them in daily use.

来自 2 份提交、3 块真实硬盘。每块盘内先算相对分，再在所有盘上取几何平均；<mark>**高亮**</mark> 为该列最高分。**每份提交、每块盘的全部数据**见 [community/README.md](community/README.md)，提交方法见 [docs/LOCAL_SUITE.md](docs/LOCAL_SUITE.md)。

From 2 submissions on 3 real drives. Each drive is scored on its own, then the scores are averaged geometrically over all drives; <mark>**highlighted**</mark> = best in its column. **Every submission and every drive in full**: [community/README.md](community/README.md); how to submit: [docs/LOCAL_SUITE.md](docs/LOCAL_SUITE.md).

| 名次<br>Rank | 扫描器<br>Scanner | 综合分<br>Score | 冷扫分<br>Cold | 热扫分<br>Warm | 均衡分<br>Balanced | 盘数<br>Drives |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 🥇 | **SpaceKnife (0.3.4)** | <mark>**87.4**</mark> | 90.4 | <mark>**85.1**</mark> | <mark>**86.6**</mark> | 3 |
| 🥈 | **dua-cli** | 80.8 | <mark>**92.0**</mark> | 69.6 | 82.4 | 3 |
| 🥉 | **gdu** | 57.8 | 59.0 | 53.7 | 60.9 | 3 |
| 4 | **SquirrelDisk** | 49.6 | 35.8 | 55.3 | 61.8 | 3 |
| 5 | **WizTree** | 34.1 | 27.6 | 22.9 | 62.9 | 3 |
| 6 | **WinDirStat** | 15.5 | 11.5 | 10.4 | 31.4 | 3 |
| 7 | **dust** | 6.9 | 8.7 | 2.9 | 13.0 | 3 |
| 8 | **pdu** | 6.5 | 7.5 | 2.8 | 12.9 | 3 |
| 9 | **diskus** | 5.8 | 6.6 | 2.7 | 11.2 | 3 |
| 10 | **erdtree** | 3.2 | 3.6 | 1.2 | 7.4 | 3 |

<sub>分数在每块盘内计算：冷扫分、热扫分 = 这块盘上最快的用时 ÷ 自己的用时 × 100；均衡分同时看冷扫的墙钟时间和占用的 CPU、读盘资源（与 CI 榜单的均衡指数同一公式，只用冷扫这一次），= 这块盘上最好的均衡时间 ÷ 自己的 × 100；综合分 = 三者的几何平均。多块盘时每项先在各盘之间取几何平均，再算综合分；不同盘的原始用时从不直接比较。没能清缓存的盘只算热扫分。<br><br>Scores are computed per drive: cold and warm = the drive's fastest time / own x 100; balanced weighs the cold scan's wall time with the CPU and disk reads it used (the CI boards' balanced index, from the cold scan only) = the drive's best balanced time / own x 100; score = geometric mean of the three. Over several drives each part is first averaged geometrically across them, then combined; raw times are never compared across drives. Drives whose cache could not be purged count for the warm score only.</sub>

<!-- COMMUNITY:END -->

---

## 利益声明 · Conflict of interest

本基准的作者 [DuskXi](https://github.com/DuskXi) 也是参赛工具 [SpaceKnife](https://github.com/DuskXi/SpaceKnife) 的作者；榜上有它的两个版本：SpaceKnife 是 0.3.5，即 Rust 重写版合并进主线后的版本；SpaceKnife (0.3.4) 是之前的旧版，留作对照。测试数据、计时方法和评分规则都出自这位参赛者之手，SpaceKnife 排得越靠前，作者越直接受益。这一点不回避，也请不要只凭这份榜单下结论。下面这些都可以自己核对：

- **同一套流程**：所有扫描器由同一个脚本（[`run_cli_scanners.py`](scripts/wrappers/run_cli_scanners.py)）在同一棵树上计时（分片的平台按同一个锚点扫描器换算），冷扫前同样清缓存、同样调回访问时间，结果过同样的完整性检查。计分只用从进程外测的墙钟时间；SpaceKnife 自己报的扫描用时只列在单次运行的报告里，不计分。它的 MFT 扫描一旦退回普通遍历，成绩直接作废。
- **参数公开**：每个扫描器的版本和命令行都锁在 [`scanners_registry.json`](scripts/wrappers/scanners_registry.json) 里。SpaceKnife 的两个版本都是项目自己 CI 构建的程序：0.3.5 取自 CI 的构建产物，0.3.4 取自同一次构建发布的 v0.3.4 Release（构建产物已过期），运行编号见注册表，不是第三方发行版。
- **数据公开**：每次发布都链接到对应的 Actions 运行，发布的数据存在 [`leaderboard/data/`](leaderboard/data/)，方法见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。也可以用[本地套件](docs/LOCAL_SUITE.md)在自己的盘上跑同样版本的扫描器，成绩可以提交到上面的社区榜单。
- **欢迎挑错**：如果你觉得哪个工具的参数、口径或测试数据对它不公平，或者偏向 SpaceKnife，欢迎开 issue 或 PR。

This benchmark's author, [DuskXi](https://github.com/DuskXi), also wrote [SpaceKnife](https://github.com/DuskXi/SpaceKnife), one of the scanners it ranks; two of its versions are on the boards: SpaceKnife is 0.3.5, the Rust rewrite merged into the main line, and SpaceKnife (0.3.4) the previous version, kept for comparison. The test data, the timing method and the scoring rules all come from someone with a stake in the result, and the author benefits directly when SpaceKnife ranks well. That is stated here rather than left out; please do not judge from these boards alone. What you can check yourself:

- **One process for all**: every scanner is timed by the same script ([`run_cli_scanners.py`](scripts/wrappers/run_cli_scanners.py)) on the same tree (platforms run in shards are scaled by the same anchor scanner), with the same cache drop and access-time reset before its cold scan, and its result goes through the same completeness checks. Scores use only the wall-clock time measured from outside the process; the scan time SpaceKnife reports about itself is listed in the per-run reports and never scored. A SpaceKnife MFT scan that falls back to a directory walk is marked invalid.
- **Open settings**: every scanner's version and command line are pinned in [`scanners_registry.json`](scripts/wrappers/scanners_registry.json). Both SpaceKnife versions are built by the project's own CI: 0.3.5 from the CI build artifacts, 0.3.4 from the v0.3.4 release of the same build (its artifacts have expired); run numbers are in the registry. Neither comes from a third-party distribution.
- **Open data**: every publish links to its Actions run, the published data is kept in [`leaderboard/data/`](leaderboard/data/) and the method is in [docs/METHODOLOGY.md](docs/METHODOLOGY.md). The [local suite](docs/LOCAL_SUITE.md) runs the same scanner versions on your own drives, and its results can go to the community board above.
- **Challenges welcome**: if a tool's options, size accounting or the test data look unfair to it, or tilted towards SpaceKnife, please open an issue or a pull request.

---

## 参加测试的扫描器 · Scanners

下表由 CI 根据 [`scanners_registry.json`](scripts/wrappers/scanners_registry.json) 自动生成。版本全部锁定，各平台用同一个版本。

Generated from [`scanners_registry.json`](scripts/wrappers/scanners_registry.json). Every version is pinned and the same on all platforms.

<!-- SCANNERS:START -->

| 扫⁠描⁠器<br>Scanner | 版⁠本<br>Version | 平⁠台<br>Platforms | 架⁠构<br>Arch | 口⁠径<br>Size | 说⁠明<br>Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **gdu** | <code>5.38.0</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated<br>(Windows:&nbsp;apparent) | 命令行 CLI |
| **dua‑cli** | <code>2.46.0</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI |
| **dust** | <code>1.2.6</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated<br>(Windows:&nbsp;apparent) | 命令行 CLI |
| **ncdu** | <code>2.9.2</code> | Linux<br>macOS | `x86_64`<br>`aarch64` | allocated | 命令行 CLI |
| **WizTree** | <code>4.33</code> | Windows | `x86_64` | apparent | 命令行 CLI；参加 MFT 专栏 · in the MFT column |
| **SpaceSniffer** | <code>2.2.0.27</code> | Windows | `x86_64` | apparent | 图形界面 GUI |
| **WinDirStat** | <code>2.9.3</code> | Windows | `x86_64`<br>`aarch64` | apparent | 命令行 CLI；参加 MFT 专栏 · in the MFT column |
| **SpaceKnife&nbsp;(0.3.4)** | <code>0.3.4</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI；参加 MFT 专栏 · in the MFT column<br>⚖️ 本基准作者的项目，见[利益声明](#利益声明--conflict-of-interest)<br>⚖️ A project of this benchmark's author, see [Conflict of interest](#利益声明--conflict-of-interest) |
| **SpaceKnife** | <code>0.3.5</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI；参加 MFT 专栏 · in the MFT column<br>SpaceKnife 0.3.5：Rust 重写版合并进主线后的版本，与旧版 0.3.4 并行测试；命令行和输出与旧版相同<br>SpaceKnife 0.3.5, the Rust rewrite merged into the main line, run alongside the old 0.3.4; same command line and output<br>⚖️ 本基准作者的项目，见[利益声明](#利益声明--conflict-of-interest)<br>⚖️ A project of this benchmark's author, see [Conflict of interest](#利益声明--conflict-of-interest) |
| **SquirrelDisk** | <code>2.6.1</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI |
| **GNU&nbsp;du** | <code>coreutils</code><br><code>9.4</code> | Linux | `x86_64`<br>`aarch64` | allocated | 命令行 CLI<br>系统基线：单线程，硬链接只算一次，计入目录块<br>System baseline: single-threaded, hard links counted once, directory blocks included |
| **BSD&nbsp;du** | <code>macOS</code><br><code>system</code><br><code>/usr/bin/du</code> | macOS | `x86_64`<br>`aarch64` | allocated | 命令行 CLI<br>系统基线：单线程，硬链接只算一次，精度为 KiB<br>System baseline: single-threaded, hard links counted once, KiB granularity |
| **Sysinternals&nbsp;du** | <code>1.62</code> | Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI<br>微软 Sysinternals 出品；单线程；CSV 同时给出大小和实际占用<br>Microsoft Sysinternals; single-threaded; its CSV gives both size and size on disk |
| **pdu** | <code>0.24.0</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated<br>(Windows:&nbsp;apparent) | 命令行 CLI<br>parallel-disk-usage；用 --threads=max，因为默认的 auto 把虚拟盘误判成机械盘时会降到 1 线程；硬链接去重（-H）和块大小只在 Unix 上有<br>parallel-disk-usage; run with --threads=max because the default 'auto' drops to 1 thread on disks it takes for HDDs; hard-link dedupe (-H) and block sizes exist on Unix only |
| **diskus** | <code>0.9.0</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated<br>(Windows:&nbsp;apparent) | 命令行 CLI<br>只输出总大小；默认线程数为核数 × 3；Windows 版只报逻辑大小<br>Prints only the total; 3 threads per core by default; the Windows build reports logical sizes |
| **erdtree** | <code>3.1.2</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI<br>加 -. 和 -i 才会计入隐藏文件和被 .gitignore 忽略的文件；整棵树常驻内存<br>-. and -i make it count hidden and git-ignored files; keeps the whole tree in memory |

<sub>未参加 · Not taking part：TreeSizeFree（原因见注册表 · reason in the registry）。</sub>

<!-- SCANNERS:END -->

### 新增扫描器 · Adding a scanner

在 [`scanners_registry.json`](scripts/wrappers/scanners_registry.json) 的 `scanners` 数组里加一个对象即可，安装、计时、核验和上榜都会自动进行，不用改调度代码。可选字段（按操作系统换命令行、只报逻辑大小的平台、`system:` / `cargo:` 安装方式、不计时的核验命令等）的说明写在注册表开头。

Add an object to the `scanners` array of [`scanners_registry.json`](scripts/wrappers/scanners_registry.json); installation, timing, verification and ranking follow without code changes. Optional fields (per-OS command lines, platforms with logical sizes only, `system:` / `cargo:` installs, an untimed verification command, ...) are documented at the top of the registry.

```json
{
  "id": "my_scanner",
  "name": "my-scanner",
  "display_name": "MyScanner",
  "version": "1.0.0",
  "enabled": true,
  "runner_type": "cli",
  "platforms": ["linux", "macos", "windows"],
  "architectures": ["x86_64", "aarch64"],
  "size_metric": "allocated",
  "command_template": ["{bin}", "--no-ui", "{path}"],
  "output_parser": "human_last_line",
  "notes": "一句中文说明",
  "notes_en": "One-line English note",
  "install": {
    "linux_x86_64": "https://example.com/releases/download/v1.0.0/my-scanner-linux-amd64.tar.gz",
    "linux_aarch64": "cargo:my-scanner@1.0.0:my-scanner",
    "macos_x86_64": "https://example.com/releases/download/v1.0.0/my-scanner-darwin-amd64.tar.gz",
    "macos_aarch64": "https://example.com/releases/download/v1.0.0/my-scanner-darwin-arm64.tar.gz",
    "windows_x86_64": "https://example.com/releases/download/v1.0.0/my-scanner-windows-amd64.zip"
  }
}
```

---

## 测试体量 · Sizes

| 体量<br>Size | 文件数<br>Files | 逻辑体积<br>Logical | 说明<br>Notes |
| :--- | ---: | ---: | :--- |
| `very-lite` | 100,000 | 100&nbsp;GiB | 快速检查，仅供参考 · quick check, reference only |
| `lite` | 400,000 | 350&nbsp;GiB | 日常回归，仅供参考 · routine check, reference only |
| `low` | 1,000,000 | 500&nbsp;GiB | 标准的百万文件 · the standard million-file run |
| `mid` | 3,000,000 | 1&nbsp;TiB | 大目录树 · large tree |
| `high` | 5,000,000 | 2&nbsp;TiB | 重负载 · heavy |
| `very-high` | 9,000,000 | 3&nbsp;TiB | 极限 · extreme |
| `before-death` | 14,000,000 | 3.60&nbsp;TiB | 临终的 4&nbsp;TB 盘（尚未运行）· a dying 4&nbsp;TB disk (not run yet) |

`very-lite` 和 `lite` 的扫描只要零点几秒到几秒，计时里进程启动等固定开销占了大头，所以只作参考，不计入跨体量综合分。

`very-lite` and `lite` scans finish in well under a few seconds, so process start-up dominates their timings; they are for reference only and stay out of the overall score.

`before-death`（临死之前）：主流 4&nbsp;TB NVMe（标称 4,000&nbsp;GB）在系统里显示 3.63&nbsp;TB 左右，这一档把它塞到 3.60&nbsp;TB（3,686.4&nbsp;GiB，约 99% 满，只剩四十来 GB）、1400 万个文件，正是再不用磁盘分析工具清理垃圾就真要满死的状态。这一档已经配置好，暂时还没有运行。

`before-death`: a mainstream 4&nbsp;TB NVMe drive (rated 4,000&nbsp;GB) shows about 3.63&nbsp;TB in the OS; this size fills it to 3.60&nbsp;TB (3,686.4&nbsp;GiB, about 99% full, some 40&nbsp;GB left) with 14 million files, the state a disk reaches right before it dies of a full drive unless someone cleans it up with a disk-space analyzer. Configured, not run yet.

---

## 平台与文件系统 · Platforms and filesystems

| 平台<br>Platform | Runner | 文件系统<br>Filesystems |
| :--- | :--- | :--- |
| Linux&nbsp;x64 | `ubuntu-24.04` | ext4 · Btrfs · XFS · ZFS |
| Linux&nbsp;ARM64 | `ubuntu-24.04-arm` | ext4 · Btrfs · XFS · ZFS |
| macOS&nbsp;x64 | `macos-15-intel` | APFS |
| macOS&nbsp;ARM64 | `macos-15` | APFS |
| Windows&nbsp;x64 | `windows-latest` | NTFS · ReFS · Btrfs&nbsp;(WinBtrfs)\* |
| Windows&nbsp;ARM64 | `windows-11-arm` | NTFS |
| Windows&nbsp;x64&nbsp;MFT | `windows-latest` | NTFS，直接读 `$MFT` · raw `$MFT` |

- **Linux**：测试盘是直接 I/O 的 loop 设备；ZFS 在冷扫前导出再导入存储池。<br>The test volume is a direct-I/O loop device; the ZFS pool is exported and imported before each cold scan.
- **macOS**：APFS 磁盘镜像。<br>An APFS disk image.
- **Windows**：动态 VHDX。同一份数据在 NTFS 和 ReFS 上各跑一次，用来核查有没有偷读 MFT。<br>A dynamic VHDX. The same tree runs on NTFS and on ReFS to catch scanners that read the MFT.
- **\* WinBtrfs**：第三方 WinBtrfs 驱动，实验项，单独的工作流 `benchmark-winbtrfs.yml`。测试树由 Linux 内核在 Btrfs 上生成（带老化），整块盘打包成动态 VHDX 交给 Windows，再由 WinBtrfs 挂载扫描：直接通过 WinBtrfs 建文件的速度随目录树变大急剧下降（10 万文件 15 秒，40 万文件 13 分钟，100 万文件 100 分钟还没建完），而读取 Linux 写的 Btrfs 盘正是它的主要用途。`very-lite` / `lite` 随主测试一起跑；`low` 及以上单独触发，因为在 WinBtrfs 上光扫描就要几个小时。成绩单独存放，渲染时合并进对应体量的榜单。<br>The third-party WinBtrfs driver; experimental, in its own workflow, `benchmark-winbtrfs.yml`. The Linux kernel builds the aged tree on Btrfs, the disk travels to Windows as a dynamic VHDX and WinBtrfs mounts it for the scans: creating files through WinBtrfs slows down sharply as the tree grows (100k files: 15 s, 400k: 13 min, 1M: unfinished after 100 min), while reading a Btrfs disk written by Linux is what it is for. `very-lite` / `lite` run with the main benchmark; `low` and up are started on their own, since the scans alone take hours on WinBtrfs. The result is stored separately and merged into that size's board when the README is rendered.
- **Windows ARM64**：只跑有原生 ARM64 版本的扫描器；Defender 受篡改防护保护，无法关闭。<br>Only scanners with a native ARM64 build run here; Defender stays on because of tamper protection.
- **MFT 专栏 · MFT column**：单独的工作流 `benchmark-mft.yml`，只比较直接读 `$MFT` 的扫描模式。<br>A separate workflow, `benchmark-mft.yml`, compares only the scan modes that read `$MFT` directly.

---

## 怎么算分 · How scoring works

- **冷扫和热扫 · Cold and warm**：每次冷扫前清空测试盘的缓存（Linux、Windows 重新挂载测试盘，ZFS 导出再导入存储池，macOS 用 `purge`）。计时的冷扫不是进程第一次启动，首次启动的杀毒扫描和加载开销不算在内。冷扫之后连续热扫三次，取平均（macOS x64 从 `high` 起、macOS ARM64 和 Windows ARM64 从 `very-high` 起只热扫一次：树大了以后它们的热扫和冷扫差不多慢，三次放不进 6 小时的作业时限）。<br>Before each cold scan the test volume's caches are dropped (Linux and Windows remount the volume, ZFS exports and imports its pool, macOS runs `purge`). The timed cold scan is not the process's first launch, so first-launch antivirus and loading costs stay out. Three warm scans follow and are averaged (one on macOS x64 from `high` up and on macOS ARM64 and Windows ARM64 from `very-high` up: on a big tree their warm scans are nearly as slow as cold ones, and three do not fit in the 6-hour job limit).
- **访问时间开着，不关 · Access times stay on**：我们没有关掉访问时间更新，因为日常使用的电脑上它本来就是开着的：Linux 各发行版默认挂载为 `relatime`，Windows 从 10 起交给系统托管、常见的桌面电脑上是开着的，macOS 也默认更新。所以计时时按日常设置开着（Linux `relatime`、ZFS `atime`+`relatime`、Windows 开启（NTFS 和 ReFS 都跟这个设置），macOS 用系统默认）。关掉再测，会把用户每天实际要付的代价藏起来：一次扫描可能顺带改写成千上万条文件和文件夹的元数据，冷扫因此变慢，SSD 也多一份写入（`low` 上实测，开着比关着冷扫慢：Linux 各文件系统差别不大，Windows NTFS 2.3–3.2 倍，macOS 2–3.7 倍，ReFS 约 14 倍）；专门避开访问时间更新的扫描器（只读、不改动访问时间）也就得不到应有的回报。为了让每个扫描器付同样的代价，冷扫时整棵树的访问时间都是两天前的（文件生成时就是两天前的，文件夹扫描前调回；Linux 每个扫描器前把被改过的调回去（ZFS 调回一次后打快照，每个扫描器前回滚到快照），macOS 调回文件夹；Windows 每个扫描器用一份新复制的测试盘），不会出现第一个扫描器替后面的人把访问时间更新掉的情况；热扫前不再调回，写盘量只算冷扫。Windows 关掉访问时间更新之后的样子，见主榜旁边的[访问时间关闭对照榜](#atime-off)：它只用来展示关掉之后的效果，关掉反而会让排名偏离真实使用场景，正式排名以主榜为准。<br>Access-time updates are not turned off, because they are on on the machines people use every day: every Linux distribution mounts with `relatime` by default, Windows leaves it to the system since Windows 10 and keeps it on on common desktops, and macOS updates access times too. So the timed scans run with the daily-use setting (Linux `relatime`, ZFS `atime`+`relatime`, Windows on (NTFS and ReFS both follow it), macOS as shipped). Measuring with them off would hide a cost users pay every day: a scan can rewrite the metadata of thousands of files and folders on the side, which slows the cold scan and adds writes to the SSD (measured at `low`, cold scans with them on take about as long on Linux, 2.3-3.2x as long on Windows NTFS, 2-3.7x on macOS and about 14x on ReFS), and scanners that avoid it by reading without touching access times would get no credit for it. So that every scanner pays the same, each cold scan meets access times two days old across the tree (the tree is created that way; before each scanner Linux sets back what moved (ZFS once, then rolls back to a snapshot of that) and macOS the folders; on Windows each scanner gets a fresh copy of the volume), and none inherits the updates of the one before it; nothing is set back before the warm scans, and the disk-write column counts the cold scan only. What Windows looks like with last-access updates off is in the [access-times-off comparison](#atime-off) next to the main board: it only shows the effect of turning them off, which moves the ranking away from real use, so the main board is the one that counts.
- **平台内归一化 · Normalized per platform**：每个平台内先算相对分（该平台最快 ÷ 自己 × 100），再在平台之间取几何平均，不同 Runner 的硬件快慢在平台内就约掉了。<br>Each platform scores scanners against its fastest (fastest / own × 100), and the platforms are combined by geometric mean, so runner hardware cancels out.
- **分片 · Shards**：macOS、Windows ARM64 和 ReFS 从 `mid` 起（开着访问时间，它们的冷扫要慢 2–14 倍）、Windows x64 NTFS 从 `very-high` 起，扫描放不进一个 6 小时的作业，拆成几个作业并行，每个作业只跑一部分扫描器（按已发布成绩估算用时来分）。同型号的 Runner 之间也有快慢（CI 盘实测能差一倍），所以每个分片都额外跑一次基准扫描器 dua，各分片的冷扫、热扫用时按「参照分片的 dua 用时 ÷ 本分片的 dua 用时」换算到同一台机器的速度（dua 单次不到 20 秒时，计时波动比机器差异还大，不换算）；内存、CPU 时间和读盘次数不换算。macOS 每个分片自己生成测试树（磁盘镜像在 macOS Runner 上太慢，没法共享）；Windows 只在 x64 Runner 上生成一次再交给各分片，ARM64 的也是（ARM64 Runner 上 Defender 的实时扫描关不掉，`very-high` 生成要 5 小时，x64 上半小时到 47 分钟），所以同一平台的各分片扫的是同一份镜像。分片里镜像用 zstd 打包存放（约 70 GB 的 `very-high` NTFS 镜像打包后不到 1 GB），每个扫描器前解出一份新的来扫，Runner 上只需放得下一份。**ReFS 只测到 `high`**：它的测试树越大生成越慢（`low` 3 分钟、`mid` 25 分钟、`high` 4 小时），`high` 上一个分片跑 dua 加一个扫描器就要 4–5 小时，`very-high` 两样都放不进 6 小时的作业。macOS 从 `very-high` 起更紧：每个分片自己生成测试树就要 2–3.3 小时，Intel Mac 上生成、dua、再加一个扫描器放不进 6 小时（实测 330–380 分钟），所以 macOS x64 从 `very-high` 起、ARM64 在 `before-death` 不再每片都跑 dua，dua 和其他扫描器一样只跑一次，这些分片不做换算（`high` 上 macOS 各 Runner 的 dua 用时相差 5–15%）；`before-death` 不测 macOS x64，光生成测试树就要 4 个多小时，一个扫描器也放不下。<br>From `mid` up on macOS, Windows ARM64 and ReFS (with access times on, their cold scans take 2-14x as long), and from `very-high` up on Windows x64 NTFS, the scans do not fit in one 6-hour job, so they are split over parallel jobs, each running some of the scanners (packed by the times estimated from the published results). Runners of the same kind differ (up to 2x on the CI disks), so every shard also runs the anchor scanner dua, and each shard's cold and warm times are scaled by the reference shard's dua time / this shard's dua time (not when a dua scan takes under 20 s: timing noise then outweighs the runners' difference); memory, CPU time and disk reads are not scaled. On macOS every shard generates the tree itself (disk images are too slow on the macOS runners to hand one over); on Windows the image is generated once on an x64 runner and handed to the shards, for ARM64 too (Defender's real-time scanning cannot be turned off on the ARM64 runners, where generating a `very-high` tree took 5 h, against 31-47 min on x64), so all shards of a platform scan the same image. A shard keeps it packed with zstd (a ~70 GB `very-high` NTFS image packs to under 1 GB) and unpacks a fresh copy before each scanner, so the runner only needs room for one. **ReFS is only run up to `high`**: generating its tree slows down far faster than the tree grows (3 min at `low`, 25 min at `mid`, 4 h at `high`), and one shard of dua and one scanner took 4-5 h at `high`; at `very-high` neither fits in a 6-hour job. macOS is tighter from `very-high` up: every shard spends 2-3.3 h generating the tree itself, and on the Intel Macs generation, dua and one more scanner do not fit in 6 hours (330-380 min measured). So from `very-high` up on macOS x64, and at `before-death` on ARM64, dua no longer runs in every shard: it runs once like the other scanners, and those shards are not scaled (the macOS runners' dua times differed by 5-15% at `high`). macOS x64 is not run at `before-death`: generating its tree alone takes over 4 hours, leaving no room for a single scanner.
- **跑完入分 · Scored from what finished**（`very-high`、`before-death`）：这两档把每个作业都推到 6 小时时限边上（macOS 分片还常在队列里等满 24 小时被取消），所以哪个平台、分片或扫描器失败或超时，都不影响出分：扫描在作业时限前 20 分钟停下，每跑完一个扫描器就存一次结果，跑完的照常计分，没跑完的在这个平台标 ⏱️ 未跑完，和无效成绩一样不计入（不扣分也不加分），整个平台没出结果就不计入这个平台，榜单照常发布，并在说明里列出缺了什么。其他档仍然要求所有平台都跑完才发布。<br>These two sizes push every job to the 6-hour limit (and the macOS shards often wait out the 24-hour queue limit and get cancelled), so a platform, shard or scanner that fails or runs out of time does not hold the result back: the scans stop 20 minutes before the job's limit, the results are saved after every scanner, whatever finished counts, a scanner that did not finish is marked ⏱️ unfinished on that platform and left out like an invalid result (no penalty, no bonus), a platform without results is left out, and the board is published with a note listing what is missing. The other sizes still publish only when every platform finished.
- **均衡指数 · Balanced index**：同时看墙钟时间和占用的 CPU、磁盘资源，跑得快但把机器压得更满的工具占不到便宜。<br>Weighs wall time together with the CPU and disk resources used, so a fast scan that loads the machine harder gains nothing from it.
- **结果核验 · Verification**：只用扫描器自己报告的数字，从不拿标准答案补位；总大小、文件数、各顶层目录的大小都要对得上，漏扫的成绩判为无效。<br>Only the scanner's own numbers count, never the ground truth; its total size, file count and the size of each top-level folder must add up, or the result is invalid.
- **MFT 逃逸 · MFT escapes**：只有在 ReFS 上明显更慢、并且在 NTFS 上冷热同速时，才判定为偷读 MFT，取消 NTFS 成绩。<br>A scanner is disqualified on NTFS for reading the MFT only when it is much slower on ReFS and its NTFS cold and warm times are the same.

### CI 冷扫测的是什么 · What the CI cold scans measure

GitHub 免费 Runner 的盘都是限速的云盘：同时发 32 个随机 4&nbsp;KiB 读，`low` 档实测每秒只有约 4 千到 2.4 万次，本地 NVMe 通常能到几十万次。在 Windows 上测得更细：单个读的延迟很低（约 0.1&nbsp;ms），但每秒的读次数很快封顶（x64 约 9 千到 1 万次，ARM64 约 6 千次），同时发 1 个读和同时发 64 个读几乎一样快。所以 CI 上的冷扫比的是"在 IOPS 受限的云盘上谁读得省"：同时只排一两个读的扫描器不吃亏，并发很深的扫描器只是在盘上多排队。本地 NVMe 并发越深读得越快，冷扫排名可能和这里不同；想看自己盘上的成绩，可以用[本地套件](docs/LOCAL_SUITE.md)。

The disks of the free GitHub runners are all throttled cloud disks: with 32 random 4&nbsp;KiB reads in flight they manage only about 4,000 to 24,000 reads per second in the `low` runs, where a local NVMe drive usually does hundreds of thousands. Windows was measured in more detail: a single read is fast (about 0.1&nbsp;ms), but reads per second hit the cap at once (about 9,000-10,000 on x64 and 6,000 on ARM64), so one read in flight is nearly as fast as 64. Cold scans on CI therefore measure who reads most economically on an IOPS-capped cloud disk: a scanner that keeps one or two reads in flight loses nothing, while a deeply parallel scanner only queues longer at the disk. A local NVMe drive gets faster the more reads are in flight, so cold scans may rank differently there; the [local suite](docs/LOCAL_SUITE.md) measures your own drive.

同一棵树（100 万个文件，总大小缩到 4&nbsp;GiB）在 Windows&nbsp;x64 上放到三种盘上冷扫，每次冷扫前清空缓存，各跑两轮（单位：秒；10 月 26 日测，当时诊断工作流还没有打开访问时间更新）：

The same tree (1 million files, total size shrunk to 4&nbsp;GiB) on three kinds of volume on Windows&nbsp;x64, caches dropped before every cold scan, two rounds each (seconds; measured on 26 October, before the diagnostic workflow turned access-time updates on):

| | VHDX<br>（榜单所用 · the boards' volume） | 物理盘上的目录<br>Folder on the physical drive | 内存盘<br>RAM disk |
| :--- | ---: | ---: | ---: |
| 随机 4&nbsp;KiB 读/秒（同时 1 个 / 64 个）<br>Random 4&nbsp;KiB reads/s (1 / 64 in flight) | 9,471 / 9,928 | 8,107 / 9,123 | 38,091 / 403,548 |
| WinDirStat（默认 · default） | <mark>**14.8 / 15.7**</mark> | <mark>**15.4 / 15.6**</mark> | 12.5 / 12.9 |
| SpaceKnife&nbsp;0.3.4 | 16.8 / 17.0 | 18.6 / 18.8 | 9.4 / 9.5 |
| dua&#8209;cli | 17.7 / 17.8 | 18.1 / 19.0 | <mark>**6.6 / 6.7**</mark> |
| gdu | 17.8 / 28.3 | 18.2 / 21.0 | 6.7 / 7.7 |

- **换成物理盘，排名不变**：偏差来自云盘的 IOPS 上限，不是 VHDX。<br>**The physical drive ranks the same**: the cap of the cloud disk decides it, not the VHDX.
- **没有上限的内存盘上，排名反过来**：读盘不再是瓶颈，比的是 CPU。WinDirStat 冷扫一次约用 33 秒 CPU 时间，gdu 和 dua 约 21 秒，于是它从第一变成最后。<br>**On a RAM disk with no cap the order flips**: reading is no longer the bottleneck and CPU decides. WinDirStat uses about 33 s of CPU time per cold scan, gdu and dua about 21 s, so it drops from first to last.
- **内存盘相当于无限快的盘**：真实 NVMe 介于两者之间，单个读的延迟和云盘差不多，但同时发的读越多，每秒读得越多。内存盘装不下榜单的体量，所以不作为正式榜单。SpaceKnife 0.3.4 在内存盘上只开 13 个线程（云盘上是 73 个），这一列不代表它深并发时的表现。<br>**A RAM disk is an infinitely fast drive**: a real NVMe drive sits in between, with single reads about as fast as the cloud disk's but more reads per second the more are in flight. A RAM disk cannot hold the board's sizes, so it is not a board of its own. SpaceKnife 0.3.4 starts only 13 threads on the RAM disk (73 on the cloud disk), so its RAM-disk times do not show its deeply parallel mode.

**内存盘上开、关访问时间 · Access times off and on, on the RAM disk**：同一台 Runner、同一棵树依次跑三遍（关 → 开 → 关），每遍先探测确认设置真的生效，开着的那遍每次冷扫前把整棵树的访问时间调回两天前；每遍两轮，表里是两轮平均（单位：秒），「开 ÷ 关」用第 2 遍比第 3 遍。<br>One runner, one tree, three passes (off, on, off), each probed first to confirm the setting took effect; with access times on, the whole tree was set two days back before each cold scan. Two rounds per pass, averaged (seconds); "on ÷ off" compares pass 2 with pass 3.

| | 关 off<br>（第 1 遍 · pass 1） | 开 on<br>（第 2 遍 · pass 2） | 关 off<br>（第 3 遍 · pass 3） | 开 ÷ 关<br>on ÷ off |
| :--- | ---: | ---: | ---: | ---: |
| SpaceKnife Rust 预览版<br>Rust preview (`dev-rust` 0.4.0) | 10.3 | <mark>**9.1**</mark> | 8.8 | 1.04× |
| SpaceKnife&nbsp;0.3.4 | 9.9 | 9.8 | 9.5 | 1.03× |
| dua&#8209;cli | <mark>**7.2**</mark> | 12.1 | <mark>**6.6**</mark> | 1.84× |
| gdu | <mark>**7.2**</mark> | 12.1 | 6.7 | 1.81× |
| WinDirStat（默认 · default） | 13.8 | 18.5 | 12.7 | 1.46× |
| WinDirStat（1 线程 · 1 thread） | 33.9 | 38.2 | 31.9 | 1.20× |

- **开着访问时间，gdu、dua、WinDirStat 每次冷扫多出 5.4–6.3 秒**：多出的数额差不多，看起来是 NTFS 更新这棵树（112 万项）访问时间的大致固定成本，平均每项约 5 微秒。两个 SpaceKnife 只多约 0.3 秒，看起来扫描时基本没有触发访问时间更新，CI 榜单写盘量一栏也是这样。于是关着时 dua 和 gdu 最快，开着时（普通电脑的默认设置）两个 SpaceKnife 最快。<br>**With access times on, gdu, dua and WinDirStat take 5.4-6.3 s longer per cold scan**: about the same amount each, which looks like the rough fixed cost of NTFS updating the access times of this tree (1.12M items), some 5 µs per item. Both SpaceKnife builds take about 0.3 s longer: they seem to trigger hardly any access-time updates, as the disk-write column of the CI boards shows too. So dua and gdu are fastest with access times off, and the two SpaceKnife builds with them on, as a computer ships.
- **SpaceKnife 是本基准作者的项目**（见[利益声明](#利益声明--conflict-of-interest)）。这是一台 Runner 上的一棵合成树：第 1 遍有预热的痕迹（几项明显偏慢），第 3 遍两轮几乎一样，所以拿它作对照。<br>**SpaceKnife is a project of this benchmark's author** (see [Conflict of interest](#利益声明--conflict-of-interest)). This is one synthetic tree on one runner: pass 1 shows some warm-up (a few slow scans), pass 3's two rounds nearly match, so it is the baseline.

数据来自诊断工作流 `scanner-io-profile.yml`，它每秒记录队列深度、读次数和读延迟：[VHDX](https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40377822224) · [物理盘 · physical drive](https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40378228753) · [内存盘 · RAM disk](https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40395968314) · [内存盘开关访问时间 · RAM disk, access times off / on / off](https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42349532902)。

From the diagnostic workflow `scanner-io-profile.yml`, which records queue depth, reads and read latency every second; runs linked above.

完整说明，包括合成数据为什么这样生成、怎样模拟老化：[docs/METHODOLOGY.md](docs/METHODOLOGY.md)。

Full details, including why the test data is generated this way and how it ages: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## 自己跑 · Run it yourself

**在 CI 上 · On CI**

Actions → *Cross-Platform Disk Scanner Benchmark* → *Run workflow*，选一个体量即可。`aging`、`defender_scan`、`windows_only` 等开关用于对照实验；只有在 `main` 上用默认设置跑完标准体量，结果才会发布到上面的榜单。

Actions → *Cross-Platform Disk Scanner Benchmark* → *Run workflow*, then pick a size. Switches such as `aging`, `defender_scan` and `windows_only` are for experiments; only default runs of a standard size on `main` are published to the board above.

```bash
gh workflow run benchmark.yml -f preset=low
```

```bash
gh workflow run benchmark-mft.yml -f preset=low
```

```bash
gh workflow run benchmark-winbtrfs.yml -f preset=low
```

**在自己的硬盘上 · On your own drives**

[本地基准套件](docs/LOCAL_SUITE.md)用同样的扫描器版本扫你的真实硬盘，生成不含个人信息的成绩，可以提交到社区榜单。

The [local suite](docs/LOCAL_SUITE.md) runs the same scanner versions on your real drives and produces an anonymized result you can submit to the community board.

**只生成测试数据 · Generate a test tree only**

```bash
cargo run --release --bin fs-mirage -- --root /mnt/bench --preset low --seed 42 --manifest-out ground_truth.json
```

自定义规模用 `--preset custom --files <数量> --logical-gb <GB>`。 · For a custom size, use `--preset custom --files <count> --logical-gb <GB>`.

---

## 仓库结构 · Repository layout

```text
crates/
  fs-mirage/        合成文件树生成器 · synthetic tree generator (zones, aging, ground truth)
  hw-probe/         硬件基线探针 · hardware baseline probe (traversal, sequential, random-read IOPS, CPU)
scripts/
  disk-mgr/         测试盘与清缓存 · test volumes and cache purging (loop, dmg, VHDX, WinBtrfs)
  wrappers/         扫描器注册表与调度 · scanner registry, installer, runner, GUI monitor
  profile/          真实盘画像与布局探针 · real-drive profiles and the layout probe
  local_suite/      本地真实盘套件与社区提交 · local suite and community submissions
  report_gen.py     单平台报告 · per-platform report
  leaderboard.py    单次运行总榜 · leaderboard of one run
  readme_board.py   README 榜单与徽章 · README board and badges
  refs_audit.py     NTFS/ReFS 交叉核查 · NTFS/ReFS cross-check
leaderboard/        已发布的成绩与徽章 · published results and badges
community/          社区提交 · community submissions
docs/               方法说明、本地套件 · methodology, local suite
.github/workflows/  benchmark.yml · benchmark-mft.yml · benchmark-winbtrfs.yml · community.yml
```

---

## 许可 · License

[MIT](LICENSE) © 2026 DuskXi
