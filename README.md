# disk-scanner-bench

**跨平台硬盘空间扫描工具基准测试 · Cross-platform benchmark for disk-space scanners**

> [!IMPORTANT]
> 本基准的作者也是参赛工具 SpaceKnife 的作者，SpaceKnife 排名靠前作者直接受益，见[利益声明](#利益声明--conflict-of-interest)。<br>
> This benchmark's author also wrote SpaceKnife, one of the scanners it ranks, and benefits when it ranks well: see [Conflict of interest](#利益声明--conflict-of-interest).

[🏆 排行榜 Leaderboard](#-排行榜--leaderboard) · [🖥️ 真实盘成绩 Real drives](#real-drives) · [⚖️ 利益声明 Conflict of interest](#利益声明--conflict-of-interest) · [📐 方法说明 Methodology](docs/METHODOLOGY.md) · [🧪 本地套件 Local suite](docs/LOCAL_SUITE.md) · [➕ 新增扫描器 Add a scanner](#新增扫描器--adding-a-scanner)

在 GitHub Actions 的免费 Runner 上（Linux、macOS、Windows，x86_64 与 ARM64，多种文件系统），用确定性生成的合成文件树（最多 900 万个文件，逻辑上几 TB、物理上只占几 GB）给主流磁盘空间扫描工具做冷扫和热扫计时，核对每个工具自己报告的结果是否完整，再按平台归一化，排出跨平台、跨体量的总榜。合成数据会模拟用了多年的磁盘布局；生成算法只按"像不像真实的盘"取舍，不看任何扫描器的表现。

On free GitHub Actions runners (Linux, macOS and Windows, x86_64 and ARM64, several filesystems), mainstream disk-space scanners are timed on cold and warm scans of a deterministic synthetic tree (up to 9 million files, terabytes in logical size but only a few GB on disk). Each scanner's own output is checked for completeness, scores are normalized within each platform, and the results form one board across platforms and sizes. The test data imitates a drive that has been in use for years; generator choices are judged only by how closely they match real drives, never by how any scanner performs.

<!-- COMMUNITY-ENTRY:START -->

> 🖥️ **真实盘成绩 · Real drives**：除了 CI 上的合成数据，这里还有在真实硬盘上跑出的成绩，已收录 1 份提交、2 块盘。目前收录的这份成绩来自本基准作者自己的电脑：2 块 ReFS 数据盘（已使用约 3–4 年），都是日常在用的盘。[看榜单](#real-drives) · [每块盘的全部数据](community/README.md) · [提交你的成绩](docs/LOCAL_SUITE.md)<br>
> Besides the synthetic CI data: results on real drives, 1 submissions on 2 drives so far. The only submission so far comes from this benchmark's author's own machine: 2 ReFS data drives in use for about 3–4 years, all of them in daily use. [Board](#real-drives) · [every drive in full](community/README.md) · [submit yours](docs/LOCAL_SUITE.md)

<!-- COMMUNITY-ENTRY:END -->

<!-- LEADERBOARD:START -->

## 🏆 排行榜 · Leaderboard

![updated](https://img.shields.io/badge/updated-2026--11--06-4c8eda) ![presets](https://img.shields.io/badge/presets-5%2F7-dbab09) ![scanners](https://img.shields.io/badge/scanners-16-6f42c1) ![platforms](https://img.shields.io/badge/platforms-14-0969da) ![MFT presets](https://img.shields.io/badge/MFT%20presets-7-8250df)

> ⚖️ **利益声明**：SpaceKnife 和 SpaceKnife (Rust) 属于本基准作者的项目，作者从它们的排名中直接受益，详见[利益声明](#利益声明--conflict-of-interest)。<br>
> ⚖️ **Conflict of interest**: SpaceKnife and SpaceKnife (Rust) belong to a project of this benchmark's author, who benefits directly from how they rank; see [Conflict of interest](#利益声明--conflict-of-interest).

> 每个体量单独运行、单独更新：哪个体量跑完就刷新哪一列，其余保持上次的结果。`very-lite` / `lite` 体量过小，计时以进程启动等固定开销为主，只作参考，不计入跨体量综合分。评分方法与数据生成原理见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。
>
> Each size runs and updates on its own: a finished run refreshes its column and the others keep their last result. `very-lite` and `lite` are so small that process start-up dominates the wall clock, so they are for reference only and stay out of the overall score. Scoring and test-data design: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

### 各项前四名 · Top 4 of each category

| 名⁠次<br>Rank | 综⁠合<br>Overall | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 内⁠存⁠峰⁠值\*<br>Peak&nbsp;RAM\* | 扫⁠描⁠效⁠率\*<br>I/O&nbsp;efficiency\* | 写⁠盘⁠量\*<br>Disk&nbsp;writes\* |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife&nbsp;(Rust)**<br><sub>96.3</sub> | **SpaceKnife**<br><sub>97.2</sub> | **SpaceKnife&nbsp;(Rust)**<br><sub>96.7</sub> | **ncdu**<br><sub>3.5&nbsp;MB</sub> | **WizTree**<br><sub>99.8</sub> | **SpaceKnife**<br><sub>0.0%&nbsp;·&nbsp;0.0&nbsp;MB</sub> |
| 🥈 | **SpaceKnife**<br><sub>94.6</sub> | **SpaceKnife&nbsp;(Rust)**<br><sub>95.7</sub> | **SpaceKnife**<br><sub>91.4</sub> | **BSD&nbsp;du**<br><sub>463&nbsp;MB</sub> | **GNU&nbsp;du**<br><sub>99.3</sub> | **SpaceKnife&nbsp;(Rust)**<br><sub>0.0%&nbsp;·&nbsp;0.2&nbsp;MB</sub> |
| 🥉 | **gdu**<br><sub>57.9</sub> | **BSD&nbsp;du**<br><sub>52.6</sub> | **gdu**<br><sub>64.4</sub> | **GNU&nbsp;du**<br><sub>14&nbsp;MB</sub> | **SpaceKnife**<br><sub>98.6</sub> | **SpaceSniffer**<br><sub>82%&nbsp;·&nbsp;2,155.0&nbsp;MB</sub> |
| 4 | **SquirrelDisk**<br><sub>52.2</sub> | **gdu**<br><sub>46.7</sub> | **SquirrelDisk**<br><sub>53.0</sub> | **dua‑cli**<br><sub>22&nbsp;MB</sub> | **SpaceKnife&nbsp;(Rust)**<br><sub>97.5</sub> | **WinDirStat**<br><sub>84%&nbsp;·&nbsp;631.6&nbsp;MB</sub> |

<sub>**\* 只作参考，不计入综合分**（综合 = 冷扫、热扫、均衡指数）· † 只有小体量成绩 · 各列按 `low` 及以上体量合并<br>**内存峰值**：各平台、各体量的中位数，含放进 tmpfs 的数据（Linux）和被压缩的内存（macOS）<br>**扫描效率**：1 ÷ (IOPS × 扫描时间) = 1 ÷ 冷扫读盘次数，平台内最少 ÷ 自己 × 100<br>**写盘量**：扫描器自己写的文件（如磁盘缓存）+ 冷扫时更新访问时间写的盘（[按日常设置开着](#怎么算分--how-scoring-works)）。百分比 = 自己 ÷ 同平台典型扫描器，排名按它（NTFS 每项写的是 ext4 的近 4 倍，平台内比才公平）；MB 是每百万项实测值。macOS 的写入计数是整台机器的，不参与<br><br>**\* For reference, not in the overall score** (overall = cold, warm, balanced index) · † small sizes only · each column combines the sizes from `low` up<br>**Peak RAM**: median over platforms and sizes, including data parked in tmpfs (Linux) and compressed memory (macOS)<br>**I/O efficiency**: 1 / (IOPS x scan time) = 1 / cold-scan disk reads, platform's fewest / own x 100<br>**Disk writes**: files the scanner writes itself (e.g. a disk cache) + what the cold scan writes for access-time updates ([on, as in daily use](#怎么算分--how-scoring-works)). The percentage is own / the platform's typical scanner and sets the rank (NTFS writes nearly 4x what ext4 does per item, so platforms are compared within themselves); MB is measured per million items. macOS stays out: its write counter covers the whole machine.</sub>

### 跨体量总榜 · Overall across sizes

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | very‑lite\* | lite\* | low | mid | high |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife&nbsp;(Rust)** | <mark>**96.3**</mark> | 🥇&nbsp;<mark>**97.2**</mark> | 🥇&nbsp;<mark>**97.5**</mark> | 🥇&nbsp;<mark>**97.0**</mark> | 🥇&nbsp;<mark>**95.6**</mark> | — |
| 🥈 | **SpaceKnife** | 94.6 | 🥉&nbsp;53.4 | 🥈&nbsp;79.4 | 🥈&nbsp;88.7 | 🥈&nbsp;95.5 | 🥇&nbsp;<mark>**99.8**</mark> |
| 🥉 | **gdu** | 57.9 | #4&nbsp;52.3 | #4&nbsp;61.4 | #4&nbsp;53.2 | 🥉&nbsp;61.9 | 🥈&nbsp;58.9 |
| 4 | **SquirrelDisk** | 52.2 | 🥈&nbsp;61.0 | 🥉&nbsp;65.9 | 🥉&nbsp;59.5 | #4&nbsp;50.5 | #5&nbsp;47.4 |
| 5 | **BSD&nbsp;du** | 47.5 | #6&nbsp;42.9 | #5&nbsp;45.5 | #5&nbsp;40.5 | #5&nbsp;50.2 | 🥉&nbsp;52.5 |
| 6 | **diskus** | 44.3 | #5&nbsp;45.6 | #8&nbsp;35.0 | #7&nbsp;37.1 | #6&nbsp;48.0 | #4&nbsp;48.7 |
| 7 | **dua‑cli** | 41.9 | #9&nbsp;38.7 | #6&nbsp;38.6 | #6&nbsp;38.2 | #7&nbsp;45.2 | #6&nbsp;42.8 |
| 8 | **pdu** | 39.7 | #7&nbsp;42.7 | #9&nbsp;33.0 | #9&nbsp;33.4 | #8&nbsp;43.8 | #7&nbsp;42.7 |
| 9 | **GNU&nbsp;du** | 36.8 | #8&nbsp;39.6 | #7&nbsp;36.3 | #8&nbsp;36.8 | #10&nbsp;37.9 | #9&nbsp;35.7 |
| 10 | **ncdu** | 36.0 | #10&nbsp;36.8 | #10&nbsp;32.0 | #10&nbsp;32.5 | #9&nbsp;38.6 | #8&nbsp;37.3 |
| 11 | **WinDirStat** | 28.9 | #11&nbsp;34.4 | #11&nbsp;31.4 | #11&nbsp;31.0 | #12&nbsp;27.8 | #11&nbsp;27.9 |
| 12 | **dust** | 27.4 | #12&nbsp;28.5 | #13&nbsp;22.9 | #13&nbsp;23.9 | #11&nbsp;31.8 | #12&nbsp;27.2 |
| 13 | **WizTree** | 26.8 | #14&nbsp;23.9 | #12&nbsp;29.4 | #12&nbsp;28.2 | #14&nbsp;22.5 | #10&nbsp;30.2 |
| 14 | **erdtree** | 22.9 | #13&nbsp;27.0 | #14&nbsp;21.6 | #14&nbsp;23.0 | #13&nbsp;24.4 | #13&nbsp;21.4 |
| 15 | **SpaceSniffer** | 17.5 | #15&nbsp;16.9 | #15&nbsp;16.1 | #15&nbsp;15.6 | #15&nbsp;18.1 | #14&nbsp;19.2 |
| 16 | **Sysinternals&nbsp;du** | 6.2 | — | — | #16&nbsp;6.1 | — | #15&nbsp;6.3 |

<sub><mark>**高亮**</mark> = 该列最高分 · <mark>**highlighted**</mark> = best in its column.<br><br>综合分 = `low` 及以上各体量综合分的几何平均；\* 为仅供参考的小体量（综合分带 \* 的扫描器只有小体量成绩）。缺平台、缺体量都不扣分也不加分：只用它实际跑过的平台和体量计算，等于把缺的部分按它自己的平均分补上，平台多的工具不会因此更容易刷分，平台少的工具也不会因此被扣分。<br><br>Score = geometric mean of the per-size scores from `low` up; \* marks the reference-only small sizes (a score with \* comes from small sizes only). Missing platforms and sizes neither cost nor earn points: only what a scanner actually ran counts, the same as filling the gaps with its own average, so more platforms do not make a high score easier and fewer do not mark a tool down.</sub>

### 冷扫综合榜 · Cold scans across sizes

> CI Runner 的盘是 IOPS 受限的云盘，冷扫比的是在这种盘上谁读得省，和本地 NVMe 上的冷扫排名可能不同，见[CI 冷扫测的是什么](#ci-冷扫测的是什么--what-the-ci-cold-scans-measure)。<br>The CI runners' disks are IOPS-capped cloud disks: cold scans here measure who reads most economically on such a disk, and may rank differently on a local NVMe drive; see [What the CI cold scans measure](#ci-冷扫测的是什么--what-the-ci-cold-scans-measure).

| # | 扫⁠描⁠器<br>Scanner | **冷⁠扫⁠分**<br>**Cold** | very‑lite\* | lite\* | low | mid | high |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**97.2**</mark> | 🥈&nbsp;64.2 | 🥈&nbsp;87.1 | 🥈&nbsp;92.5 | 🥇&nbsp;<mark>**99.1**</mark> | 🥇&nbsp;<mark>**100.0**</mark> |
| 🥈 | **SpaceKnife&nbsp;(Rust)** | 95.7 | 🥇&nbsp;<mark>**92.9**</mark> | 🥇&nbsp;<mark>**95.1**</mark> | 🥇&nbsp;<mark>**95.2**</mark> | 🥈&nbsp;96.2 | — |
| 🥉 | **BSD&nbsp;du** | 52.6 | #11&nbsp;35.2 | #5&nbsp;47.7 | #8&nbsp;35.5 | 🥉&nbsp;59.0 | 🥈&nbsp;69.4 |
| 4 | **gdu** | 46.7 | #8&nbsp;40.1 | #4&nbsp;51.0 | #4&nbsp;45.2 | #5&nbsp;49.4 | #4&nbsp;45.7 |
| 5 | **diskus** | 46.1 | #5&nbsp;49.8 | #7&nbsp;40.5 | #6&nbsp;42.3 | #4&nbsp;50.2 | 🥉&nbsp;46.2 |
| 6 | **SquirrelDisk** | 45.4 | #4&nbsp;50.0 | 🥉&nbsp;55.4 | 🥉&nbsp;49.8 | #7&nbsp;44.0 | #6&nbsp;42.7 |
| 7 | **dua‑cli** | 43.5 | #6&nbsp;41.9 | #8&nbsp;40.5 | #7&nbsp;39.9 | #6&nbsp;46.3 | #5&nbsp;44.4 |
| 8 | **pdu** | 38.7 | #7&nbsp;41.7 | #9&nbsp;35.8 | #9&nbsp;33.6 | #8&nbsp;43.5 | #7&nbsp;39.5 |
| 9 | **dust** | 35.1 | #9&nbsp;36.6 | #10&nbsp;30.9 | #10&nbsp;30.5 | #9&nbsp;38.6 | #8&nbsp;36.9 |
| 10 | **WinDirStat** | 30.7 | 🥉&nbsp;58.5 | #6&nbsp;44.1 | #5&nbsp;43.4 | #13&nbsp;25.5 | #11&nbsp;26.1 |
| 11 | **erdtree** | 30.3 | #10&nbsp;35.3 | #11&nbsp;27.8 | #11&nbsp;28.0 | #10&nbsp;33.9 | #10&nbsp;29.2 |
| 12 | **ncdu** | 25.9 | #13&nbsp;26.0 | #15&nbsp;22.0 | #15&nbsp;21.1 | #11&nbsp;27.9 | #9&nbsp;29.7 |
| 13 | **GNU&nbsp;du** | 25.1 | #12&nbsp;28.3 | #12&nbsp;24.9 | #13&nbsp;24.1 | #12&nbsp;25.8 | #12&nbsp;25.3 |
| 14 | **SpaceSniffer** | 20.1 | #14&nbsp;25.1 | #14&nbsp;22.4 | #14&nbsp;23.0 | #14&nbsp;18.9 | #13&nbsp;18.7 |
| 15 | **WizTree** | 18.2 | #15&nbsp;21.6 | #13&nbsp;22.7 | #12&nbsp;25.6 | #15&nbsp;15.0 | #14&nbsp;15.7 |
| 16 | **Sysinternals&nbsp;du** | 9.4 | — | — | #16&nbsp;11.6 | — | #15&nbsp;7.6 |

<sub>只看冷扫：每个体量取冷扫相对分（该平台最快 ÷ 自己 × 100，跨平台几何平均），再对 `low` 及以上取几何平均；格子里是该体量冷扫的名次和分数，<mark>**高亮**</mark> = 该列最高分。<br><br>The cold-scan score alone: each size's cold-scan relative score (platform fastest / own x 100, geometric mean across platforms), then the geometric mean from `low` up; each cell is the cold-scan rank and score in that size, <mark>**highlighted**</mark> = best in its column.</sub>

### 热扫综合榜 · Warm scans across sizes

| # | 扫⁠描⁠器<br>Scanner | **热⁠扫⁠分**<br>**Warm** | very‑lite\* | lite\* | low | mid | high |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife&nbsp;(Rust)** | <mark>**96.7**</mark> | 🥇&nbsp;<mark>**100.0**</mark> | 🥇&nbsp;<mark>**99.5**</mark> | 🥇&nbsp;<mark>**99.2**</mark> | 🥇&nbsp;<mark>**94.2**</mark> | — |
| 🥈 | **SpaceKnife** | 91.4 | #7&nbsp;38.3 | 🥉&nbsp;68.9 | 🥈&nbsp;83.7 | 🥈&nbsp;91.9 | 🥇&nbsp;<mark>**99.3**</mark> |
| 🥉 | **gdu** | 64.4 | 🥉&nbsp;61.1 | #4&nbsp;67.1 | #4&nbsp;55.5 | 🥉&nbsp;70.9 | 🥈&nbsp;67.9 |
| 4 | **SquirrelDisk** | 53.0 | 🥈&nbsp;64.9 | 🥈&nbsp;70.8 | 🥉&nbsp;63.0 | #4&nbsp;51.5 | #5&nbsp;45.8 |
| 5 | **diskus** | 40.2 | #4&nbsp;40.2 | #10&nbsp;27.8 | #9&nbsp;30.0 | #5&nbsp;43.8 | #4&nbsp;49.3 |
| 6 | **dua‑cli** | 36.1 | #10&nbsp;32.6 | #6&nbsp;32.7 | #6&nbsp;32.2 | #6&nbsp;40.0 | #7&nbsp;36.5 |
| 7 | **WizTree** | 35.6 | #11&nbsp;22.2 | #7&nbsp;32.6 | #11&nbsp;27.1 | #11&nbsp;27.8 | 🥉&nbsp;59.9 |
| 8 | **pdu** | 35.5 | #5&nbsp;39.9 | #11&nbsp;26.3 | #10&nbsp;28.4 | #7&nbsp;39.2 | #6&nbsp;40.3 |
| 9 | **GNU&nbsp;du** | 34.5 | #8&nbsp;36.1 | #5&nbsp;33.6 | #5&nbsp;35.7 | #8&nbsp;36.0 | #8&nbsp;32.0 |
| 10 | **ncdu** | 31.9 | #9&nbsp;34.6 | #9&nbsp;29.1 | #8&nbsp;31.3 | #9&nbsp;34.6 | #9&nbsp;30.1 |
| 11 | **BSD&nbsp;du** | 29.2 | #6&nbsp;39.4 | #8&nbsp;31.0 | #7&nbsp;31.5 | #10&nbsp;29.4 | #10&nbsp;27.0 |
| 12 | **WinDirStat** | 23.0 | #14&nbsp;18.6 | #12&nbsp;20.1 | #12&nbsp;19.7 | #12&nbsp;24.3 | #11&nbsp;25.3 |
| 13 | **dust** | 18.3 | #12&nbsp;20.0 | #14&nbsp;14.4 | #14&nbsp;15.8 | #13&nbsp;22.9 | #12&nbsp;16.8 |
| 14 | **erdtree** | 15.4 | #13&nbsp;19.2 | #13&nbsp;14.8 | #13&nbsp;16.4 | #14&nbsp;16.4 | #13&nbsp;13.7 |
| 15 | **SpaceSniffer** | 9.9 | #15&nbsp;7.6 | #15&nbsp;7.7 | #15&nbsp;7.2 | #15&nbsp;11.0 | #14&nbsp;12.2 |
| 16 | **Sysinternals&nbsp;du** | 2.7 | — | — | #16&nbsp;2.4 | — | #15&nbsp;3.0 |

<sub>只看热扫：每个体量取热扫相对分（该平台最快 ÷ 自己 × 100，跨平台几何平均），再对 `low` 及以上取几何平均；格子里是该体量热扫的名次和分数，<mark>**高亮**</mark> = 该列最高分。<br><br>The warm-scan score alone: each size's warm-scan relative score (platform fastest / own x 100, geometric mean across platforms), then the geometric mean from `low` up; each cell is the warm-scan rank and score in that size, <mark>**highlighted**</mark> = best in its column.</sub>

### 各体量详情 · Results per size

<details open>
<summary><b>high</b> · 500 万文件 · 5M files · 2026-10-30 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40974157411">run 40974157411</a> · <code>1813c5c</code></summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**99.8**</mark> | <mark>**100.0**</mark><br><sub>53.8&nbsp;s</sub> | <mark>**99.3**</mark><br><sub>7.07&nbsp;s</sub> | <mark>**100.0**</mark> | 923&nbsp;MB | 0.55% | S·F·Z | 9/11 |
| 🥈 | **gdu** | 58.9 | 45.7<br><sub>199&nbsp;s</sub> | 67.9<br><sub>21.0&nbsp;s</sub> | 65.9 | 118&nbsp;MB | 0.56% | S·Z | 11/11 |
| 🥉 | **BSD&nbsp;du** | 52.5 | 69.4<br><sub>1,384&nbsp;s</sub> | 27.0<br><sub>1,279&nbsp;s</sub> | 77.3 | 1,141&nbsp;MB | 918.47% | S·Z | 2/2 |
| 4 | **diskus** | 48.7 | 46.2<br><sub>197&nbsp;s</sub> | 49.3<br><sub>28.9&nbsp;s</sub> | 50.8 | 46&nbsp;MB | <mark>**0.00%**</mark> | S | 11/11 |
| 5 | **SquirrelDisk** | 47.4 | 42.7<br><sub>304&nbsp;s</sub> | 45.8<br><sub>55.0&nbsp;s</sub> | 54.5 | 148&nbsp;MB | 1.09% | S·F·Z | 7/7 |
| 6 | **dua‑cli** | 42.8 | 44.4<br><sub>204&nbsp;s</sub> | 36.5<br><sub>39.1&nbsp;s</sub> | 48.3 | 41&nbsp;MB | 0.09% | S·Z | 11/11 |
| 7 | **pdu** | 42.7 | 39.5<br><sub>230&nbsp;s</sub> | 40.3<br><sub>35.4&nbsp;s</sub> | 49.0 | 241&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 11/11 |
| 8 | **ncdu** | 37.3 | 29.7<br><sub>282&nbsp;s</sub> | 30.1<br><sub>48.1&nbsp;s</sub> | 58.3 | <mark>**5&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 8/8 |
| 9 | **GNU&nbsp;du** | 35.7 | 25.3<br><sub>147&nbsp;s</sub> | 32.0<br><sub>15.7&nbsp;s</sub> | 56.4 | 19&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 6/6 |
| 10 | **WizTree** | 30.2 | 15.7<br><sub>641&nbsp;s</sub> | 59.9<br><sub>25.5&nbsp;s</sub> | 29.4 | 2,390&nbsp;MB | 0.79% | S·F·Z | 2/2 |
| 11 | **WinDirStat** | 27.9 | 26.1<br><sub>433&nbsp;s</sub> | 25.3<br><sub>54.1&nbsp;s</sub> | 33.1 | 1,024&nbsp;MB | 0.79% | S·F·Z | 3/3 |
| 12 | **dust** | 27.2 | 36.9<br><sub>246&nbsp;s</sub> | 16.8<br><sub>84.7&nbsp;s</sub> | 32.4 | 1,916&nbsp;MB | 0.68% | S·Z | 11/11 |
| 13 | **erdtree** | 21.4 | 29.2<br><sub>163&nbsp;s</sub> | 13.7<br><sub>48.5&nbsp;s</sub> | 24.4 | 4,284&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 8/10 |
| 14 | **SpaceSniffer** | 19.2 | 18.7<br><sub>537&nbsp;s</sub> | 12.2<br><sub>125&nbsp;s</sub> | 30.9 | 2,628&nbsp;MB | n/a | IO | 2/2 |
| 15 | **Sysinternals&nbsp;du** | 6.3 | 7.6<br><sub>1,493&nbsp;s</sub> | 3.0<br><sub>458&nbsp;s</sub> | 11.1 | 253&nbsp;MB | 1.00% | S·F·Z | 3/3 |

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (100.0) · **热扫 Warm** SpaceKnife (99.3) · **均衡 Balanced** SpaceKnife (100.0) · **最省内存 Least RAM** ncdu (5 MB) · **扫描效率 I/O efficiency** BSD du (100.0) · **最准 Most accurate** diskus (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**59.8**</mark>&nbsp;/&nbsp;<mark>**5.16**</mark> | 🥇<br><mark>**29.5**</mark>&nbsp;/&nbsp;<mark>**7.54**</mark> | 🥇<br><mark>**37.3**</mark>&nbsp;/&nbsp;<mark>**5.97**</mark> |
| **gdu** | 🥉<br>71.0&nbsp;/&nbsp;7.90 | 🥉<br>54.1&nbsp;/&nbsp;13.4 | 🥉<br>46.6&nbsp;/&nbsp;10.5 |
| **diskus** | #4<br>70.8&nbsp;/&nbsp;11.5 | #4<br>49.6&nbsp;/&nbsp;18.1 | #4<br>44.8&nbsp;/&nbsp;14.2 |
| **SquirrelDisk** | 🥈<br>71.2&nbsp;/&nbsp;5.84 | 🥈<br>43.8&nbsp;/&nbsp;8.27 | 🥈<br>47.9&nbsp;/&nbsp;7.02 |
| **dua‑cli** | #8<br>84.0&nbsp;/&nbsp;22.1 | #6<br>73.8&nbsp;/&nbsp;25.2 | #6<br>58.0&nbsp;/&nbsp;20.7 |
| **pdu** | #5<br>81.6&nbsp;/&nbsp;15.4 | #5<br>62.5&nbsp;/&nbsp;21.9 | #5<br>54.3&nbsp;/&nbsp;13.4 |
| **ncdu** | #6<br>189&nbsp;/&nbsp;12.4 | #9<br>136&nbsp;/&nbsp;28.1 | #7<br>150&nbsp;/&nbsp;16.8 |
| **GNU&nbsp;du** | #7<br>195&nbsp;/&nbsp;12.2 | #7<br>136&nbsp;/&nbsp;22.8 | #8<br>149&nbsp;/&nbsp;17.3 |
| **dust** | #9<br>85.0&nbsp;/&nbsp;26.9 | #8<br>78.6&nbsp;/&nbsp;30.4 | #9<br>61.7&nbsp;/&nbsp;28.8 |
| **erdtree** | #10<br>95.5&nbsp;/&nbsp;30.5 | #10<br>104&nbsp;/&nbsp;26.2 | #10<br>95.1&nbsp;/&nbsp;26.6 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**55.7**</mark>&nbsp;/&nbsp;<mark>**4.14**</mark> | 🥇<br><mark>**20.0**</mark>&nbsp;/&nbsp;<mark>**4.55**</mark> | 🥇<br><mark>**35.5**</mark>&nbsp;/&nbsp;<mark>**3.70**</mark> |
| **gdu** | #4<br>68.2&nbsp;/&nbsp;6.87 | 🥉<br>37.0&nbsp;/&nbsp;8.70 | #4<br>41.6&nbsp;/&nbsp;6.48 |
| **diskus** | 🥈<br>69.2&nbsp;/&nbsp;4.61 | 🥈<br>26.0&nbsp;/&nbsp;4.90 | 🥈<br>38.3&nbsp;/&nbsp;4.13 |
| **dua‑cli** | #7<br>74.7&nbsp;/&nbsp;24.9 | #5<br>52.0&nbsp;/&nbsp;24.6 | #7<br>46.1&nbsp;/&nbsp;23.1 |
| **pdu** | 🥉<br>70.5&nbsp;/&nbsp;5.97 | #4<br>47.6&nbsp;/&nbsp;7.58 | 🥉<br>42.6&nbsp;/&nbsp;5.56 |
| **ncdu** | #5<br>194&nbsp;/&nbsp;13.2 | #8<br>101&nbsp;/&nbsp;20.1 | #5<br>123&nbsp;/&nbsp;11.4 |
| **GNU&nbsp;du** | #6<br>202&nbsp;/&nbsp;13.7 | #7<br>104&nbsp;/&nbsp;19.4 | #6<br>121&nbsp;/&nbsp;11.9 |
| **dust** | #8<br>79.5&nbsp;/&nbsp;28.3 | #6<br>53.1&nbsp;/&nbsp;25.9 | #8<br>49.1&nbsp;/&nbsp;25.9 |
| **erdtree** | #9<br>99.8&nbsp;/&nbsp;34.9 | #9<br>93.6&nbsp;/&nbsp;28.0 | #9<br>66.9&nbsp;/&nbsp;30.5 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | ⚠️ | ⚠️ |
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
| **SpaceKnife** | 🥇<br><mark>**70.0**</mark>&nbsp;/&nbsp;<mark>**8.22**</mark> | 🥇<br><mark>**144**</mark>&nbsp;/&nbsp;<mark>**11.0**</mark> | 🥇<br><mark>**144**</mark>&nbsp;/&nbsp;30.1 |
| **gdu** | 🥈<br>123&nbsp;/&nbsp;10.7 | 🥈<br>903&nbsp;/&nbsp;16.1 | #4<br>3,437&nbsp;/&nbsp;39.6 |
| **diskus** | #7<br>211&nbsp;/&nbsp;67.6 | #5<br>1,315&nbsp;/&nbsp;126 | #7<br>3,121&nbsp;/&nbsp;34.4 |
| **SquirrelDisk** | #5<br>177&nbsp;/&nbsp;20.1 | — | #11<br>4,206&nbsp;/&nbsp;282 |
| **dua‑cli** | 🥉<br>119&nbsp;/&nbsp;14.0 | 🥉<br>1,036&nbsp;/&nbsp;23.8 | #5<br>3,543&nbsp;/&nbsp;43.0 |
| **pdu** | #8<br>219&nbsp;/&nbsp;67.6 | #6<br>1,361&nbsp;/&nbsp;138 | 🥉<br>3,448&nbsp;/&nbsp;28.4 |
| **WizTree** | #4<br>126&nbsp;/&nbsp;22.9 | — | #8<br>3,257&nbsp;/&nbsp;<mark>**28.3**</mark> |
| **WinDirStat** | #6<br>110&nbsp;/&nbsp;34.7 | #4<br>1,423&nbsp;/&nbsp;64.6 | 🥈<br>520&nbsp;/&nbsp;70.5 |
| **dust** | #9<br>230&nbsp;/&nbsp;84.4 | #8<br>1,444&nbsp;/&nbsp;706 | #9<br>3,570&nbsp;/&nbsp;142 |
| **erdtree** | #12<br>343&nbsp;/&nbsp;211 | — | #10<br>2,496&nbsp;/&nbsp;229 |
| **SpaceSniffer** | #10<br>294&nbsp;/&nbsp;93.0 | — | #6<br>978&nbsp;/&nbsp;167 |
| **Sysinternals&nbsp;du** | #11<br>471&nbsp;/&nbsp;206 | #7<br>1,738&nbsp;/&nbsp;450 | #12<br>4,061&nbsp;/&nbsp;1,031 |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>mid</b> · 300 万文件 · 3M files · 2026-11-06 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42225935035">run 42225935035</a> · <code>699efc3</code></summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife&nbsp;(Rust)** | <mark>**95.6**</mark> | 96.2<br><sub>34.0&nbsp;s</sub> | <mark>**94.2**</mark><br><sub>5.54&nbsp;s</sub> | <mark>**96.5**</mark> | 617&nbsp;MB | 0.04% | S·F·Z | 11/13 |
| 🥈 | **SpaceKnife** | 95.5 | <mark>**99.1**</mark><br><sub>33.0&nbsp;s</sub> | 91.9<br><sub>5.68&nbsp;s</sub> | 95.7 | 606&nbsp;MB | 0.04% | S·F·Z | 11/13 |
| 🥉 | **gdu** | 61.9 | 49.4<br><sub>98.8&nbsp;s</sub> | 70.9<br><sub>12.7&nbsp;s</sub> | 67.7 | 82&nbsp;MB | 0.17% | S·Z | 13/13 |
| 4 | **SquirrelDisk** | 50.5 | 44.0<br><sub>154&nbsp;s</sub> | 51.5<br><sub>27.3&nbsp;s</sub> | 56.7 | 78&nbsp;MB | 1.30% | S·F·Z | 8/8 |
| 5 | **BSD&nbsp;du** | 50.2 | 59.0<br><sub>745&nbsp;s</sub> | 29.4<br><sub>615&nbsp;s</sub> | 73.2 | 124&nbsp;MB | 1667.09% | S·Z | 2/2 |
| 6 | **diskus** | 48.0 | 50.2<br><sub>97.2&nbsp;s</sub> | 43.8<br><sub>20.6&nbsp;s</sub> | 50.2 | 43&nbsp;MB | <mark>**0.00%**</mark> | S | 13/13 |
| 7 | **dua‑cli** | 45.2 | 46.3<br><sub>106&nbsp;s</sub> | 40.0<br><sub>22.5&nbsp;s</sub> | 49.8 | 22&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 13/13 |
| 8 | **pdu** | 43.8 | 43.5<br><sub>112&nbsp;s</sub> | 39.2<br><sub>23.0&nbsp;s</sub> | 49.3 | 143&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 13/13 |
| 9 | **ncdu** | 38.6 | 27.9<br><sub>156&nbsp;s</sub> | 34.6<br><sub>30.1&nbsp;s</sub> | 59.7 | <mark>**4&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 10 | **GNU&nbsp;du** | 37.9 | 25.8<br><sub>94.2&nbsp;s</sub> | 36.0<br><sub>14.2&nbsp;s</sub> | 58.5 | 14&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 11 | **dust** | 31.8 | 38.6<br><sub>126&nbsp;s</sub> | 22.9<br><sub>39.3&nbsp;s</sub> | 36.3 | 1,128&nbsp;MB | 0.46% | S·Z | 13/13 |
| 12 | **WinDirStat** | 27.8 | 25.5<br><sub>284&nbsp;s</sub> | 24.3<br><sub>22.8&nbsp;s</sub> | 34.6 | 640&nbsp;MB | 0.90% | S·F·Z | 3/3 |
| 13 | **erdtree** | 24.4 | 33.9<br><sub>86.1&nbsp;s</sub> | 16.4<br><sub>31.6&nbsp;s</sub> | 26.1 | 2,522&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 10/12 |
| 14 | **WizTree** | 22.5 | 15.0<br><sub>404&nbsp;s</sub> | 27.8<br><sub>19.5&nbsp;s</sub> | 27.3 | 1,461&nbsp;MB | 0.90% | S·F·Z | 2/2 |
| 15 | **SpaceSniffer** | 18.1 | 18.9<br><sub>321&nbsp;s</sub> | 11.0<br><sub>49.3&nbsp;s</sub> | 28.3 | 1,591&nbsp;MB | n/a | IO | 2/2 |

未上榜（没有任何平台的有效成绩） · Unranked (no valid result anywhere)：Sysinternals du

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (99.1) · **热扫 Warm** SpaceKnife (Rust) (94.2) · **均衡 Balanced** SpaceKnife (Rust) (96.5) · **最省内存 Least RAM** ncdu (4 MB) · **扫描效率 I/O efficiency** BSD du (100.0) · **最准 Most accurate** diskus (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥈<br><mark>**39.0**</mark>&nbsp;/&nbsp;3.26 | 🥇<br><mark>**15.8**</mark>&nbsp;/&nbsp;<mark>**4.34**</mark> | 🥈<br><mark>**20.1**</mark>&nbsp;/&nbsp;2.94 | 🥇<br><mark>**50.9**</mark>&nbsp;/&nbsp;<mark>**40.6**</mark> |
| **SpaceKnife** | 🥇<br>39.2&nbsp;/&nbsp;<mark>**3.14**</mark> | 🥈<br>16.0&nbsp;/&nbsp;4.36 | 🥇<br>20.2&nbsp;/&nbsp;<mark>**2.88**</mark> | 🥈<br>52.3&nbsp;/&nbsp;41.8 |
| **gdu** | #4<br>39.8&nbsp;/&nbsp;4.44 | #4<br>22.9&nbsp;/&nbsp;6.40 | #4<br>20.7&nbsp;/&nbsp;4.62 | #4<br>86.4&nbsp;/&nbsp;43.3 |
| **SquirrelDisk** | 🥉<br>39.8&nbsp;/&nbsp;3.54 | 🥉<br>22.3&nbsp;/&nbsp;4.64 | 🥉<br>23.5&nbsp;/&nbsp;3.44 | #8<br>119&nbsp;/&nbsp;68.6 |
| **diskus** | #6<br>40.4&nbsp;/&nbsp;5.90 | #5<br>22.1&nbsp;/&nbsp;8.90 | #5<br>21.0&nbsp;/&nbsp;5.93 | 🥉<br>81.1&nbsp;/&nbsp;43.2 |
| **dua‑cli** | #7<br>40.6&nbsp;/&nbsp;8.23 | #7<br>30.6&nbsp;/&nbsp;12.3 | #7<br>25.5&nbsp;/&nbsp;8.87 | #7<br>116&nbsp;/&nbsp;48.8 |
| **pdu** | #5<br>41.3&nbsp;/&nbsp;5.65 | #6<br>26.2&nbsp;/&nbsp;9.99 | #6<br>24.5&nbsp;/&nbsp;5.89 | #5<br>107&nbsp;/&nbsp;43.5 |
| **ncdu** | #10<br>115&nbsp;/&nbsp;8.85 | #10<br>78.4&nbsp;/&nbsp;11.9 | #10<br>80.1&nbsp;/&nbsp;8.22 | #10<br>181&nbsp;/&nbsp;92.5 |
| **GNU&nbsp;du** | #11<br>113&nbsp;/&nbsp;9.17 | #11<br>78.1&nbsp;/&nbsp;12.2 | #11<br>79.1&nbsp;/&nbsp;8.47 | #9<br>180&nbsp;/&nbsp;92.9 |
| **dust** | #8<br>42.6&nbsp;/&nbsp;10.4 | #8<br>34.1&nbsp;/&nbsp;16.2 | #8<br>26.0&nbsp;/&nbsp;11.0 | #6<br>113&nbsp;/&nbsp;49.1 |
| **erdtree** | #9<br>45.2&nbsp;/&nbsp;9.89 | #9<br>46.5&nbsp;/&nbsp;13.1 | #9<br>41.5&nbsp;/&nbsp;9.88 | #11<br>129&nbsp;/&nbsp;122 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥈<br>28.9&nbsp;/&nbsp;2.43 | 🥇<br>11.3&nbsp;/&nbsp;<mark>**2.51**</mark> | 🥇<br><mark>**20.0**</mark>&nbsp;/&nbsp;<mark>**2.24**</mark> | 🥇<br><mark>**30.1**</mark>&nbsp;/&nbsp;<mark>**21.6**</mark> |
| **SpaceKnife** | 🥇<br><mark>**28.7**</mark>&nbsp;/&nbsp;<mark>**2.38**</mark> | 🥈<br><mark>**11.1**</mark>&nbsp;/&nbsp;2.58 | 🥈<br>20.1&nbsp;/&nbsp;2.25 | 🥈<br>30.5&nbsp;/&nbsp;22.5 |
| **gdu** | #5<br>36.2&nbsp;/&nbsp;3.69 | #5<br>16.1&nbsp;/&nbsp;3.82 | #5<br>20.5&nbsp;/&nbsp;3.63 | #4<br>57.6&nbsp;/&nbsp;27.2 |
| **diskus** | 🥉<br>32.7&nbsp;/&nbsp;2.60 | 🥉<br>12.0&nbsp;/&nbsp;2.62 | 🥉<br>20.3&nbsp;/&nbsp;2.39 | 🥉<br>49.3&nbsp;/&nbsp;24.4 |
| **dua‑cli** | #7<br>37.7&nbsp;/&nbsp;14.4 | #8<br>22.4&nbsp;/&nbsp;14.9 | #8<br>26.0&nbsp;/&nbsp;14.5 | #6<br>76.9&nbsp;/&nbsp;30.6 |
| **pdu** | #4<br>34.3&nbsp;/&nbsp;3.39 | #4<br>15.4&nbsp;/&nbsp;3.40 | #4<br>22.0&nbsp;/&nbsp;3.32 | #5<br>69.4&nbsp;/&nbsp;25.9 |
| **ncdu** | #6<br>100&nbsp;/&nbsp;7.20 | #6<br>44.3&nbsp;/&nbsp;7.53 | #6<br>73.5&nbsp;/&nbsp;6.42 | #9<br>148&nbsp;/&nbsp;46.4 |
| **GNU&nbsp;du** | #8<br>104&nbsp;/&nbsp;7.79 | #7<br>45.1&nbsp;/&nbsp;7.88 | #7<br>72.7&nbsp;/&nbsp;6.67 | #8<br>144&nbsp;/&nbsp;46.0 |
| **dust** | #9<br>39.5&nbsp;/&nbsp;15.6 | #9<br>23.2&nbsp;/&nbsp;15.5 | #9<br>27.1&nbsp;/&nbsp;16.7 | #7<br>78.7&nbsp;/&nbsp;33.9 |
| **erdtree** | #10<br>48.1&nbsp;/&nbsp;16.6 | #10<br>34.2&nbsp;/&nbsp;15.8 | #10<br>41.8&nbsp;/&nbsp;16.1 | #10<br>84.3&nbsp;/&nbsp;84.1 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | ⚠️ | ⚠️ |
| **SpaceKnife** | ⚠️ | ⚠️ |
| **gdu** | 🥉<br>1,107&nbsp;/&nbsp;344 | 🥉<br>547&nbsp;/&nbsp;149 |
| **SquirrelDisk** | 🥇<br><mark>**551**</mark>&nbsp;/&nbsp;360 | #6<br>619&nbsp;/&nbsp;281 |
| **BSD&nbsp;du** | #7<br>874&nbsp;/&nbsp;725 | #7<br>635&nbsp;/&nbsp;521 |
| **diskus** | #6<br>986&nbsp;/&nbsp;527 | 🥈<br>457&nbsp;/&nbsp;<mark>**99.3**</mark> |
| **dua‑cli** | 🥈<br>659&nbsp;/&nbsp;<mark>**329**</mark> | 🥇<br><mark>**351**</mark>&nbsp;/&nbsp;121 |
| **pdu** | #4<br>894&nbsp;/&nbsp;503 | #5<br>749&nbsp;/&nbsp;232 |
| **ncdu** | #8<br>1,329&nbsp;/&nbsp;797 | #8<br>988&nbsp;/&nbsp;597 |
| **dust** | #5<br>1,108&nbsp;/&nbsp;419 | #4<br>717&nbsp;/&nbsp;231 |
| **erdtree** | ⚠️ | ⚠️ |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>ReFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**44.8**</mark>&nbsp;/&nbsp;<mark>**4.00**</mark> | 🥇<br><mark>**104**</mark>&nbsp;/&nbsp;<mark>**5.71**</mark> | 🥈<br>123&nbsp;/&nbsp;13.2 |
| **SpaceKnife** | 🥈<br>46.0&nbsp;/&nbsp;4.38 | 🥈<br><mark>**104**</mark>&nbsp;/&nbsp;5.97 | 🥇<br><mark>**81.9**</mark>&nbsp;/&nbsp;14.8 |
| **gdu** | 🥉<br>82.2&nbsp;/&nbsp;5.85 | 🥉<br>666&nbsp;/&nbsp;12.8 | 🥉<br>2,280&nbsp;/&nbsp;<mark>**7.39**</mark> |
| **SquirrelDisk** | #7<br>121&nbsp;/&nbsp;10.5 | — | #8<br>3,122&nbsp;/&nbsp;75.0 |
| **diskus** | #8<br>137&nbsp;/&nbsp;34.7 | #6<br>905&nbsp;/&nbsp;68.3 | #11<br>2,057&nbsp;/&nbsp;178 |
| **dua‑cli** | #4<br>78.8&nbsp;/&nbsp;8.02 | #4<br>769&nbsp;/&nbsp;16.2 | #6<br>2,316&nbsp;/&nbsp;18.0 |
| **pdu** | #9<br>141&nbsp;/&nbsp;34.5 | #7<br>967&nbsp;/&nbsp;78.5 | #9<br>2,147&nbsp;/&nbsp;109 |
| **dust** | #10<br>145&nbsp;/&nbsp;41.3 | #8<br>956&nbsp;/&nbsp;89.1 | #10<br>2,301&nbsp;/&nbsp;122 |
| **WinDirStat** | #6<br>71.2&nbsp;/&nbsp;16.4 | #5<br>791&nbsp;/&nbsp;19.9 | #4<br>407&nbsp;/&nbsp;36.1 |
| **erdtree** | #12<br>187&nbsp;/&nbsp;82.8 | — | #12<br>1,846&nbsp;/&nbsp;217 |
| **WizTree** | #5<br>83.3&nbsp;/&nbsp;13.4 | — | #7<br>1,955&nbsp;/&nbsp;28.4 |
| **SpaceSniffer** | #11<br>194&nbsp;/&nbsp;51.3 | — | #5<br>533&nbsp;/&nbsp;47.4 |
| **Sysinternals&nbsp;du** | ⚠️ | ⚠️ | ⚠️ |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>low</b> · 100 万文件 · 1M files · 2026-11-06 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42146494033">run 42146494033</a> · <code>4e5aedc</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40257058978">run 40257058978</a> 2026-10-26</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife&nbsp;(Rust)** | <mark>**97.0**</mark> | <mark>**95.2**</mark><br><sub>13.0&nbsp;s</sub> | <mark>**99.2**</mark><br><sub>2.63&nbsp;s</sub> | <mark>**96.7**</mark> | 226&nbsp;MB | 0.09% | S·F·Z | 13/13 |
| 🥈 | **SpaceKnife** | 88.7 | 92.5<br><sub>13.7&nbsp;s</sub> | 83.7<br><sub>3.19&nbsp;s</sub> | 90.2 | 263&nbsp;MB | 0.29% | S·F·Z | 14/14 |
| 🥉 | **SquirrelDisk** | 59.5 | 49.8<br><sub>31.1&nbsp;s</sub> | 63.0<br><sub>6.28&nbsp;s</sub> | 67.2 | 29&nbsp;MB | 0.81% | S·F·Z | 9/9 |
| 4 | **gdu** | 53.2 | 45.2<br><sub>28.0&nbsp;s</sub> | 55.5<br><sub>4.81&nbsp;s</sub> | 60.0 | 48&nbsp;MB | 0.39% | S·Z | 14/14 |
| 5 | **BSD&nbsp;du** | 40.5 | 35.5<br><sub>94.5&nbsp;s</sub> | 31.5<br><sub>95.8&nbsp;s</sub> | 59.6 | 463&nbsp;MB | 17.48% | S·Z | 2/2 |
| 6 | **dua‑cli** | 38.2 | 39.9<br><sub>31.8&nbsp;s</sub> | 32.2<br><sub>8.31&nbsp;s</sub> | 43.5 | 13&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 7 | **diskus** | 37.1 | 42.3<br><sub>30.0&nbsp;s</sub> | 30.0<br><sub>8.91&nbsp;s</sub> | 40.4 | 25&nbsp;MB | 0.06% | S | 14/14 |
| 8 | **GNU&nbsp;du** | 36.8 | 24.1<br><sub>29.7&nbsp;s</sub> | 35.7<br><sub>4.44&nbsp;s</sub> | 57.9 | 9&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 9 | **pdu** | 33.4 | 33.6<br><sub>37.7&nbsp;s</sub> | 28.4<br><sub>9.42&nbsp;s</sub> | 39.2 | 48&nbsp;MB | 0.06% | S·Z | 14/14 |
| 10 | **ncdu** | 32.5 | 21.1<br><sub>46.3&nbsp;s</sub> | 31.3<br><sub>9.15&nbsp;s</sub> | 51.9 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 11 | **WinDirStat** | 31.0 | 43.4<br><sub>56.4&nbsp;s</sub> | 19.7<br><sub>11.4&nbsp;s</sub> | 34.7 | 248&nbsp;MB | 0.58% | S·F·Z | 4/4 |
| 12 | **WizTree** | 28.2 | 25.6<br><sub>89.7&nbsp;s</sub> | 27.1<br><sub>9.24&nbsp;s</sub> | 32.3 | 517&nbsp;MB | 0.58% | S·F·Z | 3/3 |
| 13 | **dust** | 23.9 | 30.5<br><sub>41.6&nbsp;s</sub> | 15.8<br><sub>16.9&nbsp;s</sub> | 28.2 | 391&nbsp;MB | 0.44% | S·Z | 14/14 |
| 14 | **erdtree** | 23.0 | 28.0<br><sub>42.3&nbsp;s</sub> | 16.4<br><sub>16.9&nbsp;s</sub> | 26.4 | 857&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 15 | **SpaceSniffer** | 15.6 | 23.0<br><sub>99.7&nbsp;s</sub> | 7.2<br><sub>34.7&nbsp;s</sub> | 22.8 | 552&nbsp;MB | n/a | IO | 3/3 |
| 16 | **Sysinternals&nbsp;du** | 6.1 | 11.6<br><sub>148&nbsp;s</sub> | 2.4<br><sub>151&nbsp;s</sub> | 8.1 | 57&nbsp;MB | 34.70% | S·F·Z | 1/4 |

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (Rust) (95.2) · **热扫 Warm** SpaceKnife (Rust) (99.2) · **均衡 Balanced** SpaceKnife (Rust) (96.7) · **最省内存 Least RAM** ncdu (3 MB) · **扫描效率 I/O efficiency** WizTree (99.7) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**8.75**</mark>&nbsp;/&nbsp;<mark>**1.26**</mark> | 🥇<br><mark>**4.19**</mark>&nbsp;/&nbsp;<mark>**0.98**</mark> | 🥇<br><mark>**6.67**</mark>&nbsp;/&nbsp;<mark>**1.13**</mark> | 🥇<br>15.8&nbsp;/&nbsp;<mark>**12.1**</mark> |
| **SpaceKnife** | 🥈<br>9.03&nbsp;/&nbsp;1.53 | 🥈<br>4.30&nbsp;/&nbsp;1.21 | 🥈<br>7.30&nbsp;/&nbsp;1.43 | 🥈<br><mark>**15.2**</mark>&nbsp;/&nbsp;12.8 |
| **SquirrelDisk** | 🥉<br>11.0&nbsp;/&nbsp;1.52 | 🥉<br>6.12&nbsp;/&nbsp;1.22 | 🥉<br>9.65&nbsp;/&nbsp;1.37 | #8<br>36.9&nbsp;/&nbsp;14.7 |
| **gdu** | #4<br>9.92&nbsp;/&nbsp;2.03 | #4<br>5.00&nbsp;/&nbsp;1.47 | #4<br>8.37&nbsp;/&nbsp;1.95 | #4<br>23.5&nbsp;/&nbsp;13.8 |
| **dua‑cli** | #7<br>13.1&nbsp;/&nbsp;4.22 | #9<br>7.52&nbsp;/&nbsp;4.75 | #7<br>12.0&nbsp;/&nbsp;4.29 | #6<br>28.7&nbsp;/&nbsp;15.3 |
| **diskus** | #5<br>9.07&nbsp;/&nbsp;2.80 | #5<br>4.97&nbsp;/&nbsp;2.27 | #5<br>7.29&nbsp;/&nbsp;2.74 | 🥉<br>20.3&nbsp;/&nbsp;13.5 |
| **GNU&nbsp;du** | #11<br>37.7&nbsp;/&nbsp;3.70 | #8<br>14.6&nbsp;/&nbsp;2.35 | #10<br>33.9&nbsp;/&nbsp;3.44 | #11<br>59.2&nbsp;/&nbsp;28.9 |
| **pdu** | #6<br>12.1&nbsp;/&nbsp;3.01 | #6<br>6.71&nbsp;/&nbsp;3.03 | #6<br>10.7&nbsp;/&nbsp;2.57 | #5<br>27.8&nbsp;/&nbsp;13.8 |
| **ncdu** | #10<br>38.1&nbsp;/&nbsp;3.65 | #7<br>14.1&nbsp;/&nbsp;2.40 | #9<br>33.3&nbsp;/&nbsp;3.29 | #10<br>59.3&nbsp;/&nbsp;28.8 |
| **dust** | #9<br>13.6&nbsp;/&nbsp;5.73 | #10<br>7.82&nbsp;/&nbsp;5.30 | #8<br>12.6&nbsp;/&nbsp;5.85 | #7<br>29.1&nbsp;/&nbsp;15.4 |
| **erdtree** | #8<br>14.6&nbsp;/&nbsp;4.29 | #11<br>10.5&nbsp;/&nbsp;4.36 | #11<br>18.7&nbsp;/&nbsp;4.42 | #9<br>31.1&nbsp;/&nbsp;20.8 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**8.93**</mark>&nbsp;/&nbsp;<mark>**0.72**</mark> | 🥇<br><mark>**3.22**</mark>&nbsp;/&nbsp;<mark>**0.73**</mark> | 🥇<br>6.35&nbsp;/&nbsp;<mark>**0.71**</mark> | 🥈<br>12.7&nbsp;/&nbsp;<mark>**6.46**</mark> |
| **SpaceKnife** | 🥉<br>9.20&nbsp;/&nbsp;0.89 | 🥉<br>3.60&nbsp;/&nbsp;0.94 | 🥉<br>6.63&nbsp;/&nbsp;0.88 | 🥇<br><mark>**10.2**</mark>&nbsp;/&nbsp;6.73 |
| **gdu** | #5<br>9.13&nbsp;/&nbsp;1.06 | #4<br>4.37&nbsp;/&nbsp;1.10 | #4<br>7.01&nbsp;/&nbsp;1.14 | #4<br>18.4&nbsp;/&nbsp;7.46 |
| **dua‑cli** | #8<br>11.2&nbsp;/&nbsp;5.06 | #9<br>6.72&nbsp;/&nbsp;5.39 | #9<br>12.9&nbsp;/&nbsp;5.34 | #6<br>25.5&nbsp;/&nbsp;9.25 |
| **diskus** | 🥈<br>8.99&nbsp;/&nbsp;0.80 | 🥈<br>3.37&nbsp;/&nbsp;0.83 | 🥈<br><mark>**6.34**</mark>&nbsp;/&nbsp;0.78 | 🥉<br>13.9&nbsp;/&nbsp;6.54 |
| **GNU&nbsp;du** | #7<br>26.4&nbsp;/&nbsp;2.31 | #7<br>12.9&nbsp;/&nbsp;2.46 | #7<br>28.9&nbsp;/&nbsp;2.19 | #10<br>54.9&nbsp;/&nbsp;14.2 |
| **pdu** | #4<br>8.96&nbsp;/&nbsp;0.97 | #5<br>4.97&nbsp;/&nbsp;1.04 | #5<br>10.5&nbsp;/&nbsp;1.08 | #5<br>22.1&nbsp;/&nbsp;6.81 |
| **ncdu** | #6<br>26.4&nbsp;/&nbsp;2.16 | #6<br>12.5&nbsp;/&nbsp;2.31 | #6<br>24.9&nbsp;/&nbsp;2.01 | #9<br>54.3&nbsp;/&nbsp;13.9 |
| **dust** | #9<br>11.2&nbsp;/&nbsp;5.34 | #8<br>6.87&nbsp;/&nbsp;5.00 | #8<br>11.9&nbsp;/&nbsp;5.40 | #7<br>26.1&nbsp;/&nbsp;9.73 |
| **erdtree** | #10<br>12.7&nbsp;/&nbsp;5.70 | #10<br>10.3&nbsp;/&nbsp;5.19 | #10<br>18.1&nbsp;/&nbsp;5.87 | #8<br>27.9&nbsp;/&nbsp;13.5 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥈<br>48.4&nbsp;/&nbsp;43.8 | 🥇<br><mark>**33.8**</mark>&nbsp;/&nbsp;<mark>**23.2**</mark> |
| **SpaceKnife** | 🥉<br>55.7&nbsp;/&nbsp;45.9 | 🥉<br>39.1&nbsp;/&nbsp;34.6 |
| **SquirrelDisk** | 🥇<br><mark>**33.2**</mark>&nbsp;/&nbsp;<mark>**39.3**</mark> | 🥈<br>39.9&nbsp;/&nbsp;26.0 |
| **gdu** | #6<br>189&nbsp;/&nbsp;86.5 | #9<br>180&nbsp;/&nbsp;95.0 |
| **BSD&nbsp;du** | #5<br>114&nbsp;/&nbsp;113 | #5<br>78.2&nbsp;/&nbsp;80.9 |
| **dua‑cli** | #4<br>79.7&nbsp;/&nbsp;57.2 | #4<br>103&nbsp;/&nbsp;46.9 |
| **diskus** | #10<br>168&nbsp;/&nbsp;128 | #7<br>154&nbsp;/&nbsp;89.0 |
| **pdu** | #7<br>179&nbsp;/&nbsp;107 | #8<br>166&nbsp;/&nbsp;105 |
| **ncdu** | #11<br>254&nbsp;/&nbsp;158 | #11<br>373&nbsp;/&nbsp;225 |
| **dust** | #9<br>164&nbsp;/&nbsp;130 | #10<br>212&nbsp;/&nbsp;135 |
| **erdtree** | #8<br>184&nbsp;/&nbsp;115 | #6<br>190&nbsp;/&nbsp;65.6 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**22.5**</mark>&nbsp;/&nbsp;<mark>**1.86**</mark> | 🥇<br><mark>**29.6**</mark>&nbsp;/&nbsp;<mark>**1.65**</mark> | — | 🥇<br><mark>**31.1**</mark>&nbsp;/&nbsp;<mark>**2.35**</mark> |
| **SpaceKnife** | 🥈<br>23.3&nbsp;/&nbsp;2.26 | 🥈<br>29.8&nbsp;/&nbsp;1.97 | 🥇<br><mark>**17.2**</mark>&nbsp;/&nbsp;<mark>**3.59**</mark> | 🥈<br>32.4&nbsp;/&nbsp;2.72 |
| **SquirrelDisk** | #7<br>56.3&nbsp;/&nbsp;4.63 | — | 🥉<br>17.5&nbsp;/&nbsp;22.2 | #5<br>861&nbsp;/&nbsp;3.88 |
| **gdu** | #4<br>39.8&nbsp;/&nbsp;3.85 | 🥉<br>163&nbsp;/&nbsp;3.44 | 🥈<br>22.4&nbsp;/&nbsp;10.1 | #4<br>749&nbsp;/&nbsp;4.11 |
| **dua‑cli** | 🥉<br>39.5&nbsp;/&nbsp;3.58 | #4<br>166&nbsp;/&nbsp;5.42 | #5<br>28.2&nbsp;/&nbsp;18.5 | #6<br>823&nbsp;/&nbsp;4.43 |
| **diskus** | #8<br>66.6&nbsp;/&nbsp;15.4 | #6<br>212&nbsp;/&nbsp;20.7 | #8<br>112&nbsp;/&nbsp;115 | #11<br>648&nbsp;/&nbsp;59.9 |
| **pdu** | #9<br>71.6&nbsp;/&nbsp;16.1 | #7<br>209&nbsp;/&nbsp;24.7 | #10<br>131&nbsp;/&nbsp;125 | #9<br>796&nbsp;/&nbsp;32.4 |
| **WinDirStat** | #6<br>32.1&nbsp;/&nbsp;7.36 | #5<br>168&nbsp;/&nbsp;6.54 | #6<br>20.2&nbsp;/&nbsp;21.3 | 🥉<br>92.9&nbsp;/&nbsp;16.6 |
| **WizTree** | #5<br>41.3&nbsp;/&nbsp;5.75 | — | #4<br>21.1&nbsp;/&nbsp;18.2 | #8<br>829&nbsp;/&nbsp;7.51 |
| **dust** | #10<br>71.3&nbsp;/&nbsp;19.5 | #8<br>210&nbsp;/&nbsp;28.1 | #9<br>122&nbsp;/&nbsp;123 | #10<br>785&nbsp;/&nbsp;35.0 |
| **erdtree** | #12<br>90.3&nbsp;/&nbsp;39.9 | — | #11<br>123&nbsp;/&nbsp;123 | #12<br>618&nbsp;/&nbsp;60.4 |
| **SpaceSniffer** | #11<br>87.1&nbsp;/&nbsp;27.5 | — | #7<br>53.9&nbsp;/&nbsp;55.2 | #7<br>211&nbsp;/&nbsp;27.5 |
| **Sysinternals&nbsp;du** | ⚠️ | ⚠️ | #12<br>148&nbsp;/&nbsp;151 | ⚠️ |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>lite</b> · 40 万文件 · 400k files · 2026-11-06 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42146485017">run 42146485017</a> · <code>4e5aedc</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42146485017">run 42146485017</a> 2026-11-06 · 仅供参考 reference only</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife&nbsp;(Rust)** | <mark>**97.5**</mark> | <mark>**95.1**</mark><br><sub>4.36&nbsp;s</sub> | <mark>**99.5**</mark><br><sub>0.72&nbsp;s</sub> | <mark>**98.0**</mark> | 125&nbsp;MB | 0.12% | S·F·Z | 14/14 |
| 🥈 | **SpaceKnife** | 79.4 | 87.1<br><sub>4.76&nbsp;s</sub> | 68.9<br><sub>1.05&nbsp;s</sub> | 83.5 | 151&nbsp;MB | 0.12% | S·F·Z | 14/14 |
| 🥉 | **SquirrelDisk** | 65.9 | 55.4<br><sub>8.32&nbsp;s</sub> | 70.8<br><sub>1.41&nbsp;s</sub> | 73.0 | 18&nbsp;MB | 0.58% | S·F·Z | 9/9 |
| 4 | **gdu** | 61.4 | 51.0<br><sub>7.83&nbsp;s</sub> | 67.1<br><sub>0.80&nbsp;s</sub> | 67.8 | 36&nbsp;MB | 0.40% | S·Z | 12/14 |
| 5 | **BSD&nbsp;du** | 45.5 | 47.7<br><sub>10.8&nbsp;s</sub> | 31.0<br><sub>13.2&nbsp;s</sub> | 63.9 | 195&nbsp;MB | 8.74% | S·Z | 2/2 |
| 6 | **dua‑cli** | 38.6 | 40.5<br><sub>10.2&nbsp;s</sub> | 32.7<br><sub>2.20&nbsp;s</sub> | 43.4 | 6&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 7 | **GNU&nbsp;du** | 36.3 | 24.9<br><sub>11.0&nbsp;s</sub> | 33.6<br><sub>1.31&nbsp;s</sub> | 57.2 | 8&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 8 | **diskus** | 35.0 | 40.5<br><sub>10.2&nbsp;s</sub> | 27.8<br><sub>2.59&nbsp;s</sub> | 38.0 | 20&nbsp;MB | 0.14% | S | 14/14 |
| 9 | **pdu** | 33.0 | 35.8<br><sub>11.6&nbsp;s</sub> | 26.3<br><sub>2.74&nbsp;s</sub> | 38.1 | 21&nbsp;MB | 0.14% | S·Z | 14/14 |
| 10 | **ncdu** | 32.0 | 22.0<br><sub>14.1&nbsp;s</sub> | 29.1<br><sub>2.36&nbsp;s</sub> | 51.0 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 11 | **WinDirStat** | 31.4 | 44.1<br><sub>19.2&nbsp;s</sub> | 20.1<br><sub>4.03&nbsp;s</sub> | 35.0 | 125&nbsp;MB | 0.41% | S·F·Z | 4/4 |
| 12 | **WizTree** | 29.4 | 22.7<br><sub>32.3&nbsp;s</sub> | 32.6<br><sub>2.63&nbsp;s</sub> | 34.5 | 237&nbsp;MB | 0.41% | S·F·Z | 3/3 |
| 13 | **dust** | 22.9 | 30.9<br><sub>13.4&nbsp;s</sub> | 14.4<br><sub>4.99&nbsp;s</sub> | 27.1 | 149&nbsp;MB | 0.25% | S·Z | 14/14 |
| 14 | **erdtree** | 21.6 | 27.8<br><sub>13.7&nbsp;s</sub> | 14.8<br><sub>4.89&nbsp;s</sub> | 24.7 | 338&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 15 | **SpaceSniffer** | 16.1 | 22.4<br><sub>32.7&nbsp;s</sub> | 7.7<br><sub>11.1&nbsp;s</sub> | 24.3 | 240&nbsp;MB | n/a | IO | 3/3 |

未上榜（没有任何平台的有效成绩） · Unranked (no valid result anywhere)：Sysinternals du

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (Rust) (95.1) · **热扫 Warm** SpaceKnife (Rust) (99.5) · **均衡 Balanced** SpaceKnife (Rust) (98.0) · **最省内存 Least RAM** ncdu (3 MB) · **扫描效率 I/O efficiency** WizTree (99.7) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**3.15**</mark>&nbsp;/&nbsp;<mark>**0.36**</mark> | 🥇<br>2.31&nbsp;/&nbsp;<mark>**0.48**</mark> | 🥇<br><mark>**2.76**</mark>&nbsp;/&nbsp;<mark>**0.46**</mark> | 🥇<br><mark>**4.65**</mark>&nbsp;/&nbsp;<mark>**1.16**</mark> |
| **SpaceKnife** | 🥉<br>3.48&nbsp;/&nbsp;0.60 | 🥈<br>2.42&nbsp;/&nbsp;0.72 | 🥈<br>3.03&nbsp;/&nbsp;0.71 | 🥈<br>5.10&nbsp;/&nbsp;1.43 |
| **SquirrelDisk** | 🥈<br>3.32&nbsp;/&nbsp;0.46 | #4<br>3.32&nbsp;/&nbsp;0.61 | 🥉<br>3.62&nbsp;/&nbsp;0.61 | 🥉<br>6.33&nbsp;/&nbsp;1.37 |
| **gdu** | #4<br>3.32&nbsp;/&nbsp;0.58 | 🥉<br>2.49&nbsp;/&nbsp;0.70 | #4<br>3.42&nbsp;/&nbsp;0.74 | #4<br>6.10&nbsp;/&nbsp;1.61 |
| **dua‑cli** | #9<br>3.70&nbsp;/&nbsp;1.60 | #7<br>4.38&nbsp;/&nbsp;1.49 | #7<br>4.66&nbsp;/&nbsp;1.76 | #7<br>7.62&nbsp;/&nbsp;2.62 |
| **GNU&nbsp;du** | #7<br>9.54&nbsp;/&nbsp;0.79 | #11<br>12.7&nbsp;/&nbsp;1.51 | #9<br>12.7&nbsp;/&nbsp;1.31 | #11<br>19.1&nbsp;/&nbsp;3.73 |
| **diskus** | #5<br>3.25&nbsp;/&nbsp;0.89 | #5<br><mark>**2.20**</mark>&nbsp;/&nbsp;1.09 | #5<br>2.87&nbsp;/&nbsp;1.12 | #5<br>5.26&nbsp;/&nbsp;1.97 |
| **pdu** | #6<br>3.52&nbsp;/&nbsp;0.93 | #6<br>2.67&nbsp;/&nbsp;1.01 | #6<br>4.18&nbsp;/&nbsp;1.04 | #6<br>7.18&nbsp;/&nbsp;1.94 |
| **ncdu** | #8<br>10.0&nbsp;/&nbsp;0.81 | #10<br>8.52&nbsp;/&nbsp;1.42 | #10<br>13.1&nbsp;/&nbsp;1.28 | #10<br>18.8&nbsp;/&nbsp;3.62 |
| **dust** | #11<br>3.97&nbsp;/&nbsp;1.99 | #8<br>4.26&nbsp;/&nbsp;1.74 | #8<br>4.82&nbsp;/&nbsp;2.26 | #8<br>7.77&nbsp;/&nbsp;2.71 |
| **erdtree** | #10<br>4.33&nbsp;/&nbsp;1.56 | #9<br>5.34&nbsp;/&nbsp;1.44 | #11<br>7.68&nbsp;/&nbsp;1.72 | #9<br>8.65&nbsp;/&nbsp;2.48 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥈<br>3.37&nbsp;/&nbsp;<mark>**0.32**</mark> | 🥇<br><mark>**1.94**</mark>&nbsp;/&nbsp;<mark>**0.30**</mark> | 🥇<br>2.71&nbsp;/&nbsp;<mark>**0.27**</mark> | 🥇<br><mark>**2.85**</mark>&nbsp;/&nbsp;<mark>**0.58**</mark> |
| **SpaceKnife** | 🥉<br>3.22&nbsp;/&nbsp;0.55 | #4<br>2.40&nbsp;/&nbsp;0.50 | #4<br>3.03&nbsp;/&nbsp;0.49 | 🥉<br>3.13&nbsp;/&nbsp;0.81 |
| **gdu** | #4<br>3.50&nbsp;/&nbsp;0.48 | #5<br>2.42&nbsp;/&nbsp;0.49 | #5<br>3.64&nbsp;/&nbsp;0.42 | #5<br>3.93&nbsp;/&nbsp;0.81 |
| **dua‑cli** | #9<br>6.12&nbsp;/&nbsp;2.26 | #9<br>3.35&nbsp;/&nbsp;1.98 | #8<br>3.36&nbsp;/&nbsp;2.11 | #7<br>5.73&nbsp;/&nbsp;2.13 |
| **GNU&nbsp;du** | #7<br>14.1&nbsp;/&nbsp;0.99 | #7<br>5.47&nbsp;/&nbsp;0.96 | #7<br>7.47&nbsp;/&nbsp;0.80 | #9<br>13.2&nbsp;/&nbsp;1.91 |
| **diskus** | 🥇<br><mark>**2.81**</mark>&nbsp;/&nbsp;0.34 | 🥈<br>2.20&nbsp;/&nbsp;0.33 | 🥉<br>3.35&nbsp;/&nbsp;0.30 | 🥈<br>2.89&nbsp;/&nbsp;0.63 |
| **pdu** | #5<br>5.34&nbsp;/&nbsp;0.43 | 🥉<br>2.40&nbsp;/&nbsp;0.41 | 🥈<br><mark>**2.34**</mark>&nbsp;/&nbsp;0.36 | #4<br>4.37&nbsp;/&nbsp;0.70 |
| **ncdu** | #6<br>13.1&nbsp;/&nbsp;0.91 | #6<br>5.59&nbsp;/&nbsp;0.93 | #6<br>7.63&nbsp;/&nbsp;0.76 | #10<br>13.5&nbsp;/&nbsp;1.90 |
| **dust** | #8<br>6.19&nbsp;/&nbsp;2.19 | #8<br>3.28&nbsp;/&nbsp;1.96 | #9<br>4.51&nbsp;/&nbsp;2.06 | #6<br>5.76&nbsp;/&nbsp;2.10 |
| **erdtree** | #10<br>7.04&nbsp;/&nbsp;2.36 | #10<br>4.74&nbsp;/&nbsp;2.00 | #10<br>4.93&nbsp;/&nbsp;2.00 | #8<br>6.35&nbsp;/&nbsp;2.21 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**7.55**</mark>&nbsp;/&nbsp;<mark>**4.86**</mark> | 🥈<br>4.17&nbsp;/&nbsp;3.66 |
| **SpaceKnife** | 🥈<br>11.0&nbsp;/&nbsp;6.14 | 🥉<br>4.46&nbsp;/&nbsp;4.35 |
| **SquirrelDisk** | 🥉<br>8.68&nbsp;/&nbsp;9.08 | 🥇<br><mark>**3.50**</mark>&nbsp;/&nbsp;<mark>**3.43**</mark> |
| **gdu** | ⚠️ | ⚠️ |
| **BSD&nbsp;du** | #5<br>11.9&nbsp;/&nbsp;18.5 | #4<br>9.73&nbsp;/&nbsp;9.37 |
| **dua‑cli** | #4<br>11.1&nbsp;/&nbsp;6.61 | #5<br>20.3&nbsp;/&nbsp;8.84 |
| **diskus** | #8<br>17.4&nbsp;/&nbsp;18.5 | #8<br>46.9&nbsp;/&nbsp;23.3 |
| **pdu** | #7<br>15.7&nbsp;/&nbsp;19.1 | #10<br>43.9&nbsp;/&nbsp;37.4 |
| **ncdu** | #10<br>33.5&nbsp;/&nbsp;33.8 | #7<br>59.7&nbsp;/&nbsp;23.8 |
| **dust** | #6<br>10.4&nbsp;/&nbsp;18.2 | #9<br>49.8&nbsp;/&nbsp;27.5 |
| **erdtree** | #9<br>28.1&nbsp;/&nbsp;22.1 | #6<br>43.6&nbsp;/&nbsp;20.5 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**6.83**</mark>&nbsp;/&nbsp;<mark>**0.59**</mark> | 🥇<br><mark>**13.1**</mark>&nbsp;/&nbsp;<mark>**0.69**</mark> | 🥇<br>5.14&nbsp;/&nbsp;<mark>**1.03**</mark> | 🥇<br><mark>**13.0**</mark>&nbsp;/&nbsp;<mark>**1.04**</mark> |
| **SpaceKnife** | 🥈<br>7.03&nbsp;/&nbsp;0.84 | 🥈<br>13.8&nbsp;/&nbsp;1.01 | 🥈<br>4.75&nbsp;/&nbsp;1.30 | 🥈<br>14.2&nbsp;/&nbsp;1.32 |
| **SquirrelDisk** | #5<br>15.1&nbsp;/&nbsp;1.47 | — | 🥉<br><mark>**4.43**</mark>&nbsp;/&nbsp;1.37 | #4<br>370&nbsp;/&nbsp;1.45 |
| **gdu** | 🥉<br>10.9&nbsp;/&nbsp;1.02 | 🥉<br>85.0&nbsp;/&nbsp;0.95 | #4<br>8.27&nbsp;/&nbsp;1.20 | #5<br>332&nbsp;/&nbsp;1.63 |
| **dua‑cli** | #4<br>10.4&nbsp;/&nbsp;1.07 | #4<br>78.2&nbsp;/&nbsp;1.69 | #5<br>9.08&nbsp;/&nbsp;1.42 | #6<br>360&nbsp;/&nbsp;1.90 |
| **diskus** | #8<br>19.4&nbsp;/&nbsp;4.75 | #6<br>110&nbsp;/&nbsp;9.38 | #9<br>35.6&nbsp;/&nbsp;31.7 | #12<br>339&nbsp;/&nbsp;21.8 |
| **pdu** | #9<br>20.2&nbsp;/&nbsp;4.79 | #7<br>127&nbsp;/&nbsp;10.1 | #11<br>34.6&nbsp;/&nbsp;35.3 | #9<br>349&nbsp;/&nbsp;12.7 |
| **WinDirStat** | #7<br>9.63&nbsp;/&nbsp;2.63 | #5<br>94.0&nbsp;/&nbsp;2.77 | #7<br>6.12&nbsp;/&nbsp;5.17 | 🥉<br>24.5&nbsp;/&nbsp;7.03 |
| **WizTree** | #6<br>12.0&nbsp;/&nbsp;2.15 | — | #6<br>7.64&nbsp;/&nbsp;2.67 | #8<br>366&nbsp;/&nbsp;3.16 |
| **dust** | #10<br>21.1&nbsp;/&nbsp;5.76 | #8<br>122&nbsp;/&nbsp;11.6 | #10<br>35.1&nbsp;/&nbsp;34.1 | #10<br>396&nbsp;/&nbsp;13.2 |
| **erdtree** | #12<br>27.1&nbsp;/&nbsp;12.3 | — | #12<br>38.9&nbsp;/&nbsp;38.6 | #11<br>278&nbsp;/&nbsp;21.4 |
| **SpaceSniffer** | #11<br>26.7&nbsp;/&nbsp;10.5 | — | #8<br>14.9&nbsp;/&nbsp;11.1 | #7<br>88.2&nbsp;/&nbsp;11.8 |
| **Sysinternals&nbsp;du** | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>very-lite</b> · 10 万文件 · 100k files · 2026-11-06 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42146475859">run 42146475859</a> · <code>4e5aedc</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/42146475859">run 42146475859</a> 2026-11-06 · 仅供参考 reference only</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife&nbsp;(Rust)** | <mark>**97.2**</mark> | <mark>**92.9**</mark><br><sub>0.96&nbsp;s</sub> | <mark>**100.0**</mark><br><sub>0.16&nbsp;s</sub> | <mark>**98.8**</mark> | 42&nbsp;MB | 0.04% | S·F·Z | 14/14 |
| 🥈 | **SquirrelDisk** | 61.0 | 50.0<br><sub>1.77&nbsp;s</sub> | 64.9<br><sub>0.29&nbsp;s</sub> | 69.8 | 12&nbsp;MB | 2.02% | S·F·Z | 9/9 |
| 🥉 | **SpaceKnife** | 53.4 | 64.2<br><sub>1.39&nbsp;s</sub> | 38.3<br><sub>0.41&nbsp;s</sub> | 62.0 | 77&nbsp;MB | 0.04% | S·F·Z | 14/14 |
| 4 | **gdu** | 52.3 | 40.1<br><sub>2.23&nbsp;s</sub> | 61.1<br><sub>0.27&nbsp;s</sub> | 58.5 | 26&nbsp;MB | 0.27% | S·Z | 13/14 |
| 5 | **diskus** | 45.6 | 49.8<br><sub>1.80&nbsp;s</sub> | 40.2<br><sub>0.39&nbsp;s</sub> | 47.3 | 11&nbsp;MB | 0.15% | S | 14/14 |
| 6 | **BSD&nbsp;du** | 42.9 | 35.2<br><sub>0.77&nbsp;s</sub> | 39.4<br><sub>0.64&nbsp;s</sub> | 56.9 | 74&nbsp;MB | 2.78% | S·Z | 2/2 |
| 7 | **pdu** | 42.7 | 41.7<br><sub>2.14&nbsp;s</sub> | 39.9<br><sub>0.39&nbsp;s</sub> | 46.9 | 8&nbsp;MB | 0.15% | S·Z | 14/14 |
| 8 | **GNU&nbsp;du** | 39.6 | 28.3<br><sub>2.62&nbsp;s</sub> | 36.1<br><sub>0.34&nbsp;s</sub> | 60.6 | 5&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 9 | **dua‑cli** | 38.7 | 41.9<br><sub>2.14&nbsp;s</sub> | 32.6<br><sub>0.48&nbsp;s</sub> | 42.6 | 4&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 10 | **ncdu** | 36.8 | 26.0<br><sub>2.33&nbsp;s</sub> | 34.6<br><sub>0.41&nbsp;s</sub> | 55.2 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 11 | **WinDirStat** | 34.4 | 58.5<br><sub>4.04&nbsp;s</sub> | 18.6<br><sub>1.03&nbsp;s</sub> | 37.3 | 71&nbsp;MB | 0.31% | S·F·Z | 4/4 |
| 12 | **dust** | 28.5 | 36.6<br><sub>2.44&nbsp;s</sub> | 20.0<br><sub>0.78&nbsp;s</sub> | 31.8 | 39&nbsp;MB | 0.77% | S·Z | 14/14 |
| 13 | **erdtree** | 27.0 | 35.3<br><sub>2.24&nbsp;s</sub> | 19.2<br><sub>0.80&nbsp;s</sub> | 28.9 | 89&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 14 | **WizTree** | 23.9 | 21.6<br><sub>8.98&nbsp;s</sub> | 22.2<br><sub>0.89&nbsp;s</sub> | 28.4 | 95&nbsp;MB | 0.31% | S·F·Z | 3/3 |
| 15 | **SpaceSniffer** | 16.9 | 25.1<br><sub>7.74&nbsp;s</sub> | 7.6<br><sub>2.60&nbsp;s</sub> | 25.3 | 86&nbsp;MB | n/a | IO | 3/3 |

未上榜（没有任何平台的有效成绩） · Unranked (no valid result anywhere)：Sysinternals du

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (Rust) (92.9) · **热扫 Warm** SpaceKnife (Rust) (100.0) · **均衡 Balanced** SpaceKnife (Rust) (98.8) · **最省内存 Least RAM** ncdu (3 MB) · **扫描效率 I/O efficiency** WizTree (99.5) · **最准 Most accurate** GNU du (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br>0.85&nbsp;/&nbsp;<mark>**0.14**</mark> | 🥈<br>0.84&nbsp;/&nbsp;<mark>**0.15**</mark> | 🥇<br>1.55&nbsp;/&nbsp;<mark>**0.11**</mark> | 🥇<br><mark>**1.31**</mark>&nbsp;/&nbsp;<mark>**0.29**</mark> |
| **SquirrelDisk** | 🥈<br>1.07&nbsp;/&nbsp;0.16 | 🥇<br>0.77&nbsp;/&nbsp;0.16 | 🥈<br>1.12&nbsp;/&nbsp;0.16 | 🥈<br>1.67&nbsp;/&nbsp;0.31 |
| **SpaceKnife** | #6<br>1.23&nbsp;/&nbsp;0.38 | #6<br>1.17&nbsp;/&nbsp;0.39 | #6<br>1.47&nbsp;/&nbsp;0.34 | #5<br>1.60&nbsp;/&nbsp;0.54 |
| **gdu** | 🥉<br>0.92&nbsp;/&nbsp;0.22 | 🥉<br>0.75&nbsp;/&nbsp;0.23 | #5<br>1.51&nbsp;/&nbsp;0.19 | 🥉<br>1.61&nbsp;/&nbsp;0.41 |
| **diskus** | #4<br><mark>**0.82**</mark>&nbsp;/&nbsp;0.31 | #4<br><mark>**0.71**</mark>&nbsp;/&nbsp;0.31 | 🥉<br><mark>**0.79**</mark>&nbsp;/&nbsp;0.27 | #4<br>1.38&nbsp;/&nbsp;0.46 |
| **pdu** | #5<br>1.07&nbsp;/&nbsp;0.30 | #5<br>0.82&nbsp;/&nbsp;0.34 | #4<br>1.10&nbsp;/&nbsp;0.23 | #6<br>1.88&nbsp;/&nbsp;0.48 |
| **GNU&nbsp;du** | #10<br>3.01&nbsp;/&nbsp;0.37 | #10<br>2.10&nbsp;/&nbsp;0.38 | #7<br>2.52&nbsp;/&nbsp;0.32 | #11<br>5.01&nbsp;/&nbsp;0.86 |
| **dua‑cli** | #7<br>1.18&nbsp;/&nbsp;0.46 | #7<br>1.00&nbsp;/&nbsp;0.46 | #10<br>1.92&nbsp;/&nbsp;0.40 | #7<br>2.03&nbsp;/&nbsp;0.63 |
| **ncdu** | #11<br>3.12&nbsp;/&nbsp;0.36 | #9<br>2.10&nbsp;/&nbsp;0.38 | #8<br>2.67&nbsp;/&nbsp;0.31 | #10<br>4.97&nbsp;/&nbsp;0.85 |
| **dust** | #9<br>1.25&nbsp;/&nbsp;0.58 | #11<br>1.04&nbsp;/&nbsp;0.58 | #11<br>2.28&nbsp;/&nbsp;0.46 | #9<br>2.08&nbsp;/&nbsp;0.71 |
| **erdtree** | #8<br>1.35&nbsp;/&nbsp;0.42 | #8<br>1.26&nbsp;/&nbsp;0.41 | #9<br>1.81&nbsp;/&nbsp;0.37 | #8<br>2.32&nbsp;/&nbsp;0.62 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**0.58**</mark>&nbsp;/&nbsp;<mark>**0.08**</mark> | 🥇<br>0.91&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥇<br><mark>**0.41**</mark>&nbsp;/&nbsp;<mark>**0.08**</mark> | 🥇<br><mark>**0.71**</mark>&nbsp;/&nbsp;<mark>**0.16**</mark> |
| **SpaceKnife** | #5<br>0.99&nbsp;/&nbsp;0.30 | #4<br>1.08&nbsp;/&nbsp;0.30 | #5<br>0.77&nbsp;/&nbsp;0.27 | #5<br>1.24&nbsp;/&nbsp;0.38 |
| **gdu** | #4<br>1.13&nbsp;/&nbsp;0.13 | ⚠️ | 🥈<br>0.48&nbsp;/&nbsp;0.12 | #4<br>1.08&nbsp;/&nbsp;0.24 |
| **diskus** | 🥉<br>0.86&nbsp;/&nbsp;0.10 | 🥈<br><mark>**0.90**</mark>&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥉<br>1.01&nbsp;/&nbsp;<mark>**0.08**</mark> | 🥈<br>1.02&nbsp;/&nbsp;0.17 |
| **pdu** | 🥈<br>0.92&nbsp;/&nbsp;0.09 | 🥉<br>1.09&nbsp;/&nbsp;0.11 | #4<br>0.90&nbsp;/&nbsp;0.09 | 🥉<br>1.13&nbsp;/&nbsp;0.18 |
| **GNU&nbsp;du** | #6<br>2.45&nbsp;/&nbsp;0.23 | #6<br>2.12&nbsp;/&nbsp;0.23 | #7<br>1.79&nbsp;/&nbsp;0.20 | #9<br>2.95&nbsp;/&nbsp;0.49 |
| **dua‑cli** | #10<br>1.36&nbsp;/&nbsp;0.53 | #8<br>1.48&nbsp;/&nbsp;0.55 | #9<br>1.01&nbsp;/&nbsp;0.50 | #6<br>1.35&nbsp;/&nbsp;0.58 |
| **ncdu** | #7<br>2.45&nbsp;/&nbsp;0.23 | #5<br>2.05&nbsp;/&nbsp;0.23 | #6<br>1.72&nbsp;/&nbsp;0.19 | #10<br>3.40&nbsp;/&nbsp;0.48 |
| **dust** | #8<br>1.05&nbsp;/&nbsp;0.53 | #7<br>1.34&nbsp;/&nbsp;0.53 | #8<br>0.76&nbsp;/&nbsp;0.51 | #7<br>1.43&nbsp;/&nbsp;0.59 |
| **erdtree** | #9<br>1.19&nbsp;/&nbsp;0.52 | #9<br>1.73&nbsp;/&nbsp;0.56 | #10<br>1.36&nbsp;/&nbsp;0.50 | #8<br>1.71&nbsp;/&nbsp;0.59 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**0.37**</mark>&nbsp;/&nbsp;<mark>**0.27**</mark> | 🥇<br><mark>**0.20**</mark>&nbsp;/&nbsp;<mark>**0.23**</mark> |
| **SquirrelDisk** | #6<br>0.65&nbsp;/&nbsp;0.77 | 🥈<br>0.47&nbsp;/&nbsp;0.24 |
| **SpaceKnife** | #7<br>0.97&nbsp;/&nbsp;0.56 | #5<br>0.52&nbsp;/&nbsp;0.46 |
| **gdu** | #8<br>1.03&nbsp;/&nbsp;0.46 | #11<br>4.04&nbsp;/&nbsp;1.06 |
| **diskus** | 🥈<br>0.55&nbsp;/&nbsp;0.39 | 🥉<br>0.31&nbsp;/&nbsp;0.38 |
| **BSD&nbsp;du** | #9<br>0.93&nbsp;/&nbsp;0.71 | #7<br>0.64&nbsp;/&nbsp;0.57 |
| **pdu** | 🥉<br>0.63&nbsp;/&nbsp;0.45 | #6<br>0.64&nbsp;/&nbsp;0.42 |
| **dua‑cli** | #5<br>0.75&nbsp;/&nbsp;0.47 | #4<br>0.49&nbsp;/&nbsp;0.34 |
| **ncdu** | #11<br>0.95&nbsp;/&nbsp;1.08 | #10<br>1.97&nbsp;/&nbsp;0.80 |
| **dust** | #4<br>0.65&nbsp;/&nbsp;0.43 | #8<br>0.68&nbsp;/&nbsp;0.69 |
| **erdtree** | #10<br>0.82&nbsp;/&nbsp;0.66 | #9<br>0.72&nbsp;/&nbsp;0.84 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife&nbsp;(Rust)** | 🥇<br><mark>**1.54**</mark>&nbsp;/&nbsp;<mark>**0.15**</mark> | 🥇<br><mark>**4.27**</mark>&nbsp;/&nbsp;<mark>**0.17**</mark> | 🥇<br>2.39&nbsp;/&nbsp;<mark>**0.30**</mark> | 🥇<br><mark>**2.27**</mark>&nbsp;/&nbsp;<mark>**0.17**</mark> |
| **SquirrelDisk** | #5<br>2.92&nbsp;/&nbsp;0.37 | — | 🥈<br>2.17&nbsp;/&nbsp;0.53 | #5<br>56.3&nbsp;/&nbsp;0.37 |
| **SpaceKnife** | 🥉<br>1.82&nbsp;/&nbsp;0.39 | 🥈<br>4.94&nbsp;/&nbsp;0.49 | #4<br>2.62&nbsp;/&nbsp;0.61 | 🥈<br>2.52&nbsp;/&nbsp;0.43 |
| **gdu** | 🥈<br>2.49&nbsp;/&nbsp;0.21 | 🥉<br>19.3&nbsp;/&nbsp;0.22 | 🥉<br>2.81&nbsp;/&nbsp;0.40 | #4<br>61.0&nbsp;/&nbsp;0.25 |
| **diskus** | #8<br>4.49&nbsp;/&nbsp;1.11 | #6<br>31.5&nbsp;/&nbsp;2.09 | #8<br>5.03&nbsp;/&nbsp;1.11 | #12<br>58.4&nbsp;/&nbsp;3.20 |
| **pdu** | #9<br>4.75&nbsp;/&nbsp;1.14 | #7<br>36.9&nbsp;/&nbsp;2.11 | #9<br>5.74&nbsp;/&nbsp;1.10 | #9<br>58.5&nbsp;/&nbsp;1.92 |
| **dua‑cli** | #4<br>2.35&nbsp;/&nbsp;0.35 | #5<br>25.0&nbsp;/&nbsp;0.56 | #5<br>2.59&nbsp;/&nbsp;0.56 | #6<br>58.4&nbsp;/&nbsp;0.39 |
| **WinDirStat** | #6<br>2.19&nbsp;/&nbsp;0.72 | #4<br>19.6&nbsp;/&nbsp;0.71 | #6<br><mark>**2.10**</mark>&nbsp;/&nbsp;1.59 | 🥉<br>2.96&nbsp;/&nbsp;1.36 |
| **dust** | #10<br>5.07&nbsp;/&nbsp;1.41 | #8<br>34.2&nbsp;/&nbsp;2.47 | #10<br>6.10&nbsp;/&nbsp;1.52 | #10<br>61.5&nbsp;/&nbsp;2.02 |
| **erdtree** | #12<br>6.74&nbsp;/&nbsp;2.99 | — | #12<br>6.32&nbsp;/&nbsp;3.33 | #11<br>43.1&nbsp;/&nbsp;3.24 |
| **WizTree** | #7<br>3.10&nbsp;/&nbsp;0.79 | — | #7<br>3.88&nbsp;/&nbsp;1.07 | #8<br>60.3&nbsp;/&nbsp;0.84 |
| **SpaceSniffer** | #11<br>6.11&nbsp;/&nbsp;2.42 | — | #11<br>6.97&nbsp;/&nbsp;3.09 | #7<br>10.9&nbsp;/&nbsp;2.35 |
| **Sysinternals&nbsp;du** | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

### NTFS MFT 专栏 · NTFS MFT column

直接读取 NTFS `$MFT` 的扫描模式单独比较，不和上面的普通目录遍历混排；冷热两次耗时应当接近，因为每次都要读完整张 MFT。

Scanners that read the NTFS `$MFT` directly are ranked here, apart from the directory-walking board above; their cold and warm times should be close, since every scan reads the whole MFT.

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | very‑lite\* | lite\* | low | mid | high | very‑high | before‑death |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**100.0**</mark> | 🥉&nbsp;77.0<br><sub>0.98&nbsp;/&nbsp;1.00&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>1.66&nbsp;/&nbsp;1.65&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>3.57&nbsp;/&nbsp;3.65&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>9.52&nbsp;/&nbsp;9.52&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>15.6&nbsp;/&nbsp;15.6&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>27.6&nbsp;/&nbsp;27.6&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>31.2&nbsp;/&nbsp;31.3&nbsp;s</sub> |
| 🥈 | **WizTree** | 37.0 | 🥈&nbsp;77.4<br><sub>0.96&nbsp;/&nbsp;0.91&nbsp;s</sub> | 🥉&nbsp;56.4<br><sub>2.58&nbsp;/&nbsp;2.60&nbsp;s</sub> | 🥈&nbsp;45.0<br><sub>6.74&nbsp;/&nbsp;6.75&nbsp;s</sub> | 🥈&nbsp;37.7<br><sub>20.5&nbsp;/&nbsp;20.5&nbsp;s</sub> | 🥈&nbsp;35.7<br><sub>35.4&nbsp;/&nbsp;35.2&nbsp;s</sub> | 🥈&nbsp;35.0<br><sub>62.9&nbsp;/&nbsp;63.3&nbsp;s</sub> | 🥉&nbsp;32.8<br><sub>80.1&nbsp;/&nbsp;76.8&nbsp;s</sub> |
| 🥉 | **WinDirStat** | 35.5 | 🥇&nbsp;<mark>**100.0**</mark><br><sub>0.75&nbsp;/&nbsp;0.76&nbsp;s</sub> | 🥈&nbsp;57.8<br><sub>2.73&nbsp;/&nbsp;2.67&nbsp;s</sub> | 🥉&nbsp;41.9<br><sub>7.75&nbsp;/&nbsp;7.96&nbsp;s</sub> | 🥉&nbsp;35.4<br><sub>23.2&nbsp;/&nbsp;23.7&nbsp;s</sub> | 🥉&nbsp;33.9<br><sub>40.0&nbsp;/&nbsp;40.0&nbsp;s</sub> | 🥉&nbsp;32.5<br><sub>74.4&nbsp;/&nbsp;71.8&nbsp;s</sub> | 🥈&nbsp;34.7<br><sub>80.5&nbsp;/&nbsp;78.0&nbsp;s</sub> |

<sub><mark>**高亮**</mark> = 该列最高分 · <mark>**highlighted**</mark> = best in its column.<br><br>综合分 = `low` 及以上各体量 MFT 分数的几何平均，\* 为仅供参考的小体量；每格是该体量的名次和分数，下一行小字是冷扫 / 热扫秒数。⛔ 无法运行 · ❌ 违规 · ⚠️ 无效 · — 未参加。<br><br>Score = geometric mean of the MFT scores from `low` up; \* marks the reference-only small sizes. Each cell: rank and score in that size, then cold / warm seconds in small print. ⛔ cannot run · ❌ disqualified · ⚠️ invalid · — not run.</sub>

### 在你的 README 里显示成绩 · Show a score in your README

徽章由 CI 在每次发布时更新，显示该扫描器的最新名次和综合分。把对应的一行贴进任何 Markdown：

Badges are refreshed on every publish with the scanner's current rank and score. Paste a line into any Markdown file:

```markdown
[![SpaceKnife (Rust)](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife-rust.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SpaceKnife](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![gdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SquirrelDisk](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsquirreldisk.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![BSD du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fbsd-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![diskus](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdiskus.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![dua-cli](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdua.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![pdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fpdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![GNU du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgnu-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![ncdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fncdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![WinDirStat](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![dust](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdust.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
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

> ⚖️ **利益声明**：SpaceKnife 和 SpaceKnife (Rust) 属于本基准作者的项目，作者从它们的排名中直接受益，详见[利益声明](#利益声明--conflict-of-interest)。<br>
> ⚖️ **Conflict of interest**: SpaceKnife and SpaceKnife (Rust) belong to a project of this benchmark's author, who benefits directly from how they rank; see [Conflict of interest](#利益声明--conflict-of-interest).

> ⚖️ 目前收录的这份成绩来自本基准作者自己的电脑：2 块 ReFS 数据盘（已使用约 3–4 年），都是日常在用的盘。<br>
> ⚖️ The only submission so far comes from this benchmark's author's own machine: 2 ReFS data drives in use for about 3–4 years, all of them in daily use.

来自 1 份提交、2 块真实硬盘。每块盘内先算相对分，再在所有盘上取几何平均；<mark>**高亮**</mark> 为该列最高分。**每份提交、每块盘的全部数据**见 [community/README.md](community/README.md)，提交方法见 [docs/LOCAL_SUITE.md](docs/LOCAL_SUITE.md)。

From 1 submissions on 2 real drives. Each drive is scored on its own, then the scores are averaged geometrically over all drives; <mark>**highlighted**</mark> = best in its column. **Every submission and every drive in full**: [community/README.md](community/README.md); how to submit: [docs/LOCAL_SUITE.md](docs/LOCAL_SUITE.md).

| 名次<br>Rank | 扫描器<br>Scanner | 综合分<br>Score | 冷扫分<br>Cold | 热扫分<br>Warm | 均衡分<br>Balanced | 盘数<br>Drives |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 🥇 | **SpaceKnife** | <mark>**90.9**</mark> | 86.0 | <mark>**93.2**</mark> | 93.7 | 2 |
| 🥈 | **dua-cli** | 83.9 | <mark>**99.7**</mark> | 60.1 | <mark>**98.7**</mark> | 2 |
| 🥉 | **gdu** | 70.6 | 98.8 | 39.3 | 90.4 | 2 |
| 4 | **SquirrelDisk** | 45.0 | 27.0 | 55.6 | 60.8 | 2 |
| 5 | **WizTree** | 25.7 | 21.5 | 15.8 | 49.9 | 2 |
| 6 | **WinDirStat** | 13.7 | 10.1 | 7.4 | 34.3 | 2 |
| 7 | **pdu** | 7.8 | 9.2 | 2.7 | 19.4 | 2 |
| 8 | **dust** | 7.6 | 9.6 | 2.4 | 19.6 | 2 |
| 9 | **diskus** | 6.7 | 7.7 | 2.3 | 17.5 | 2 |
| 10 | **erdtree** | 3.3 | 3.8 | 0.9 | 11.5 | 2 |

<sub>分数在每块盘内计算：冷扫分、热扫分 = 这块盘上最快的用时 ÷ 自己的用时 × 100；均衡分同时看冷扫的墙钟时间和占用的 CPU、读盘资源（与 CI 榜单的均衡指数同一公式，只用冷扫这一次），= 这块盘上最好的均衡时间 ÷ 自己的 × 100；综合分 = 三者的几何平均。多块盘时每项先在各盘之间取几何平均，再算综合分；不同盘的原始用时从不直接比较。没能清缓存的盘只算热扫分。<br><br>Scores are computed per drive: cold and warm = the drive's fastest time / own x 100; balanced weighs the cold scan's wall time with the CPU and disk reads it used (the CI boards' balanced index, from the cold scan only) = the drive's best balanced time / own x 100; score = geometric mean of the three. Over several drives each part is first averaged geometrically across them, then combined; raw times are never compared across drives. Drives whose cache could not be purged count for the warm score only.</sub>

<!-- COMMUNITY:END -->

---

## 利益声明 · Conflict of interest

本基准的作者 [DuskXi](https://github.com/DuskXi) 也是参赛工具 [SpaceKnife](https://github.com/DuskXi/SpaceKnife) 的作者；榜上的 SpaceKnife (Rust) 是同一项目的 Rust 重写版（构建取自 [Ry3nZhao/SpaceKnife](https://github.com/Ry3nZhao/SpaceKnife) 的 `dev-rust` 分支）。测试数据、计时方法和评分规则都出自这位参赛者之手，SpaceKnife 排得越靠前，作者越直接受益。这一点不回避，也请不要只凭这份榜单下结论。下面这些都可以自己核对：

- **同一套流程**：所有扫描器由同一个脚本（[`run_cli_scanners.py`](scripts/wrappers/run_cli_scanners.py)）在同一棵树上计时（分片的平台按同一个锚点扫描器换算），冷扫前同样清缓存、同样调回访问时间，结果过同样的完整性检查。计分只用从进程外测的墙钟时间；SpaceKnife 自己报的扫描用时只列在单次运行的报告里，不计分。它的 MFT 扫描一旦退回普通遍历，成绩直接作废。
- **参数公开**：每个扫描器的版本和命令行都锁在 [`scanners_registry.json`](scripts/wrappers/scanners_registry.json) 里。SpaceKnife 的两个版本用的是项目自己 CI 构建的程序（运行编号见注册表），不是第三方发行版。
- **数据公开**：每次发布都链接到对应的 Actions 运行，发布的数据存在 [`leaderboard/data/`](leaderboard/data/)，方法见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。也可以用[本地套件](docs/LOCAL_SUITE.md)在自己的盘上跑同样版本的扫描器，成绩可以提交到上面的社区榜单。
- **欢迎挑错**：如果你觉得哪个工具的参数、口径或测试数据对它不公平，或者偏向 SpaceKnife，欢迎开 issue 或 PR。

This benchmark's author, [DuskXi](https://github.com/DuskXi), also wrote [SpaceKnife](https://github.com/DuskXi/SpaceKnife), one of the scanners it ranks; SpaceKnife (Rust) on the boards is the same project's Rust rewrite (built from the `dev-rust` branch of [Ry3nZhao/SpaceKnife](https://github.com/Ry3nZhao/SpaceKnife)). The test data, the timing method and the scoring rules all come from someone with a stake in the result, and the author benefits directly when SpaceKnife ranks well. That is stated here rather than left out; please do not judge from these boards alone. What you can check yourself:

- **One process for all**: every scanner is timed by the same script ([`run_cli_scanners.py`](scripts/wrappers/run_cli_scanners.py)) on the same tree (platforms run in shards are scaled by the same anchor scanner), with the same cache drop and access-time reset before its cold scan, and its result goes through the same completeness checks. Scores use only the wall-clock time measured from outside the process; the scan time SpaceKnife reports about itself is listed in the per-run reports and never scored. A SpaceKnife MFT scan that falls back to a directory walk is marked invalid.
- **Open settings**: every scanner's version and command line are pinned in [`scanners_registry.json`](scripts/wrappers/scanners_registry.json). Both SpaceKnife builds come from the project's own CI runs (run numbers in the registry), not from a third-party distribution.
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
| **SpaceKnife** | <code>0.3.4</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI；参加 MFT 专栏 · in the MFT column<br>⚖️ 本基准作者的项目，见[利益声明](#利益声明--conflict-of-interest)<br>⚖️ A project of this benchmark's author, see [Conflict of interest](#利益声明--conflict-of-interest) |
| **SpaceKnife&nbsp;(Rust)** | <code>0.4.0</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI；参加 MFT 专栏 · in the MFT column<br>SpaceKnife 的 Rust 重写版（dev-rust 分支），与原版并行测试；命令行和输出与原版相同<br>The Rust rewrite of SpaceKnife (dev-rust branch), run alongside the original; same command line and output<br>⚖️ 本基准作者的项目，见[利益声明](#利益声明--conflict-of-interest)<br>⚖️ A project of this benchmark's author, see [Conflict of interest](#利益声明--conflict-of-interest) |
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
- **访问时间开着，不关 · Access times stay on**：我们没有关掉访问时间更新，因为日常使用的电脑上它本来就是开着的：Linux 各发行版默认挂载为 `relatime`，Windows 从 10 起交给系统托管、常见的桌面电脑上是开着的，macOS 也默认更新。所以计时时按日常设置开着（Linux `relatime`、ZFS `atime`+`relatime`、Windows 开启（NTFS 和 ReFS 都跟这个设置），macOS 用系统默认）。关掉再测，会把用户每天实际要付的代价藏起来：一次扫描可能顺带改写成千上万条文件和文件夹的元数据，冷扫因此变慢，SSD 也多一份写入（`low` 上实测，开着比关着冷扫慢：Linux 各文件系统差别不大，Windows NTFS 2.3–3.2 倍，macOS 2–3.7 倍，ReFS 约 14 倍）；专门避开访问时间更新的扫描器（只读、不改动访问时间）也就得不到应有的回报。为了让每个扫描器付同样的代价，冷扫时整棵树的访问时间都是两天前的（文件生成时就是两天前的，文件夹扫描前调回；Linux 每个扫描器前把被改过的调回去（ZFS 调回一次后打快照，每个扫描器前回滚到快照），macOS 调回文件夹；Windows 每个扫描器用一份新复制的测试盘），不会出现第一个扫描器替后面的人把访问时间更新掉的情况；热扫前不再调回，写盘量只算冷扫。<br>Access-time updates are not turned off, because they are on on the machines people use every day: every Linux distribution mounts with `relatime` by default, Windows leaves it to the system since Windows 10 and keeps it on on common desktops, and macOS updates access times too. So the timed scans run with the daily-use setting (Linux `relatime`, ZFS `atime`+`relatime`, Windows on (NTFS and ReFS both follow it), macOS as shipped). Measuring with them off would hide a cost users pay every day: a scan can rewrite the metadata of thousands of files and folders on the side, which slows the cold scan and adds writes to the SSD (measured at `low`, cold scans with them on take about as long on Linux, 2.3-3.2x as long on Windows NTFS, 2-3.7x on macOS and about 14x on ReFS), and scanners that avoid it by reading without touching access times would get no credit for it. So that every scanner pays the same, each cold scan meets access times two days old across the tree (the tree is created that way; before each scanner Linux sets back what moved (ZFS once, then rolls back to a snapshot of that) and macOS the folders; on Windows each scanner gets a fresh copy of the volume), and none inherits the updates of the one before it; nothing is set back before the warm scans, and the disk-write column counts the cold scan only.
- **平台内归一化 · Normalized per platform**：每个平台内先算相对分（该平台最快 ÷ 自己 × 100），再在平台之间取几何平均，不同 Runner 的硬件快慢在平台内就约掉了。<br>Each platform scores scanners against its fastest (fastest / own × 100), and the platforms are combined by geometric mean, so runner hardware cancels out.
- **分片 · Shards**：macOS、Windows ARM64 和 ReFS 从 `mid` 起（开着访问时间，它们的冷扫要慢 2–14 倍）、Windows x64 NTFS 从 `very-high` 起，扫描放不进一个 6 小时的作业，拆成几个作业并行，每个作业只跑一部分扫描器（按已发布成绩估算用时来分）。同型号的 Runner 之间也有快慢（CI 盘实测能差一倍），所以每个分片都额外跑一次基准扫描器 dua，各分片的冷扫、热扫用时按「参照分片的 dua 用时 ÷ 本分片的 dua 用时」换算到同一台机器的速度（dua 单次不到 20 秒时，计时波动比机器差异还大，不换算）；内存、CPU 时间和读盘次数不换算。macOS 每个分片自己生成测试树（磁盘镜像在 macOS Runner 上太慢，没法共享）；Windows 只在 x64 Runner 上生成一次再交给各分片，ARM64 的也是（ARM64 Runner 上 Defender 的实时扫描关不掉，`very-high` 生成要 5 小时，x64 上半小时到 47 分钟），所以同一平台的各分片扫的是同一份镜像。分片里镜像用 zstd 打包存放（约 70 GB 的 `very-high` NTFS 镜像打包后不到 1 GB），每个扫描器前解出一份新的来扫，Runner 上只需放得下一份。**ReFS 只测到 `high`**：它的测试树越大生成越慢（`low` 3 分钟、`mid` 25 分钟、`high` 4 小时），`high` 上一个分片跑 dua 加一个扫描器就要 4–5 小时，`very-high` 两样都放不进 6 小时的作业。<br>From `mid` up on macOS, Windows ARM64 and ReFS (with access times on, their cold scans take 2-14x as long), and from `very-high` up on Windows x64 NTFS, the scans do not fit in one 6-hour job, so they are split over parallel jobs, each running some of the scanners (packed by the times estimated from the published results). Runners of the same kind differ (up to 2x on the CI disks), so every shard also runs the anchor scanner dua, and each shard's cold and warm times are scaled by the reference shard's dua time / this shard's dua time (not when a dua scan takes under 20 s: timing noise then outweighs the runners' difference); memory, CPU time and disk reads are not scaled. On macOS every shard generates the tree itself (disk images are too slow on the macOS runners to hand one over); on Windows the image is generated once on an x64 runner and handed to the shards, for ARM64 too (Defender's real-time scanning cannot be turned off on the ARM64 runners, where generating a `very-high` tree took 5 h, against 31-47 min on x64), so all shards of a platform scan the same image. A shard keeps it packed with zstd (a ~70 GB `very-high` NTFS image packs to under 1 GB) and unpacks a fresh copy before each scanner, so the runner only needs room for one. **ReFS is only run up to `high`**: generating its tree slows down far faster than the tree grows (3 min at `low`, 25 min at `mid`, 4 h at `high`), and one shard of dua and one scanner took 4-5 h at `high`; at `very-high` neither fits in a 6-hour job.
- **均衡指数 · Balanced index**：同时看墙钟时间和占用的 CPU、磁盘资源，跑得快但把机器压得更满的工具占不到便宜。<br>Weighs wall time together with the CPU and disk resources used, so a fast scan that loads the machine harder gains nothing from it.
- **结果核验 · Verification**：只用扫描器自己报告的数字，从不拿标准答案补位；总大小、文件数、各顶层目录的大小都要对得上，漏扫的成绩判为无效。<br>Only the scanner's own numbers count, never the ground truth; its total size, file count and the size of each top-level folder must add up, or the result is invalid.
- **MFT 逃逸 · MFT escapes**：只有在 ReFS 上明显更慢、并且在 NTFS 上冷热同速时，才判定为偷读 MFT，取消 NTFS 成绩。<br>A scanner is disqualified on NTFS for reading the MFT only when it is much slower on ReFS and its NTFS cold and warm times are the same.

### CI 冷扫测的是什么 · What the CI cold scans measure

GitHub 免费 Runner 的盘都是限速的云盘：同时发 32 个随机 4&nbsp;KiB 读，`low` 档实测每秒只有约 4 千到 2.4 万次，本地 NVMe 通常能到几十万次。在 Windows 上测得更细：单个读的延迟很低（约 0.1&nbsp;ms），但每秒的读次数很快封顶（x64 约 9 千到 1 万次，ARM64 约 6 千次），同时发 1 个读和同时发 64 个读几乎一样快。所以 CI 上的冷扫比的是"在 IOPS 受限的云盘上谁读得省"：同时只排一两个读的扫描器不吃亏，并发很深的扫描器只是在盘上多排队。本地 NVMe 并发越深读得越快，冷扫排名可能和这里不同；想看自己盘上的成绩，可以用[本地套件](docs/LOCAL_SUITE.md)。

The disks of the free GitHub runners are all throttled cloud disks: with 32 random 4&nbsp;KiB reads in flight they manage only about 4,000 to 24,000 reads per second in the `low` runs, where a local NVMe drive usually does hundreds of thousands. Windows was measured in more detail: a single read is fast (about 0.1&nbsp;ms), but reads per second hit the cap at once (about 9,000-10,000 on x64 and 6,000 on ARM64), so one read in flight is nearly as fast as 64. Cold scans on CI therefore measure who reads most economically on an IOPS-capped cloud disk: a scanner that keeps one or two reads in flight loses nothing, while a deeply parallel scanner only queues longer at the disk. A local NVMe drive gets faster the more reads are in flight, so cold scans may rank differently there; the [local suite](docs/LOCAL_SUITE.md) measures your own drive.

同一棵树（100 万个文件，总大小缩到 4&nbsp;GiB）在 Windows&nbsp;x64 上放到三种盘上冷扫，每次冷扫前清空缓存，各跑两轮（单位：秒）：

The same tree (1 million files, total size shrunk to 4&nbsp;GiB) on three kinds of volume on Windows&nbsp;x64, caches dropped before every cold scan, two rounds each (seconds):

| | VHDX<br>（榜单所用 · the boards' volume） | 物理盘上的目录<br>Folder on the physical drive | 内存盘<br>RAM disk |
| :--- | ---: | ---: | ---: |
| 随机 4&nbsp;KiB 读/秒（同时 1 个 / 64 个）<br>Random 4&nbsp;KiB reads/s (1 / 64 in flight) | 9,471 / 9,928 | 8,107 / 9,123 | 38,091 / 403,548 |
| WinDirStat（默认 · default） | <mark>**14.8 / 15.7**</mark> | <mark>**15.4 / 15.6**</mark> | 12.5 / 12.9 |
| SpaceKnife | 16.8 / 17.0 | 18.6 / 18.8 | 9.4 / 9.5 |
| dua&#8209;cli | 17.7 / 17.8 | 18.1 / 19.0 | <mark>**6.6 / 6.7**</mark> |
| gdu | 17.8 / 28.3 | 18.2 / 21.0 | 6.7 / 7.7 |

- **换成物理盘，排名不变**：偏差来自云盘的 IOPS 上限，不是 VHDX。<br>**The physical drive ranks the same**: the cap of the cloud disk decides it, not the VHDX.
- **没有上限的内存盘上，排名反过来**：读盘不再是瓶颈，比的是 CPU。WinDirStat 冷扫一次约用 33 秒 CPU 时间，gdu 和 dua 约 21 秒，于是它从第一变成最后。<br>**On a RAM disk with no cap the order flips**: reading is no longer the bottleneck and CPU decides. WinDirStat uses about 33 s of CPU time per cold scan, gdu and dua about 21 s, so it drops from first to last.
- **内存盘相当于无限快的盘**：真实 NVMe 介于两者之间，单个读的延迟和云盘差不多，但同时发的读越多，每秒读得越多。内存盘装不下榜单的体量，所以不作为正式榜单。SpaceKnife 在内存盘上只开 13 个线程（云盘上是 73 个），这一列不代表它深并发时的表现。<br>**A RAM disk is an infinitely fast drive**: a real NVMe drive sits in between, with single reads about as fast as the cloud disk's but more reads per second the more are in flight. A RAM disk cannot hold the board's sizes, so it is not a board of its own. SpaceKnife starts only 13 threads on the RAM disk (73 on the cloud disk), so its RAM-disk times do not show its deeply parallel mode.

数据来自诊断工作流 `scanner-io-profile.yml`，它每秒记录队列深度、读次数和读延迟：[VHDX](https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40377822224) · [物理盘 · physical drive](https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40378228753) · [内存盘 · RAM disk](https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40395968314)。

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
