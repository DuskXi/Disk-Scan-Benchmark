# disk-scanner-bench

**跨平台硬盘空间扫描工具基准测试 · Cross-platform benchmark for disk-space scanners**

[🏆 排行榜 Leaderboard](#-排行榜--leaderboard) · [📐 方法说明 Methodology](docs/METHODOLOGY.md) · [🧪 本地套件 Local suite](docs/LOCAL_SUITE.md) · [➕ 新增扫描器 Add a scanner](#新增扫描器--adding-a-scanner)

在 GitHub Actions 的免费 Runner 上（Linux、macOS、Windows，x86_64 与 ARM64，多种文件系统），用确定性生成的合成文件树（最多 900 万个文件，逻辑上几 TB、物理上只占几 GB）给主流磁盘空间扫描工具做冷扫和热扫计时，核对每个工具自己报告的结果是否完整，再按平台归一化，排出跨平台、跨体量的总榜。合成数据会模拟用了多年的磁盘布局；生成算法只按"像不像真实的盘"取舍，不看任何扫描器的表现。

On free GitHub Actions runners (Linux, macOS and Windows, x86_64 and ARM64, several filesystems), mainstream disk-space scanners are timed on cold and warm scans of a deterministic synthetic tree (up to 9 million files, terabytes in logical size but only a few GB on disk). Each scanner's own output is checked for completeness, scores are normalized within each platform, and the results form one board across platforms and sizes. The test data imitates a drive that has been in use for years; generator choices are judged only by how closely they match real drives, never by how any scanner performs.

<!-- LEADERBOARD:START -->

## 🏆 排行榜 · Leaderboard

![updated](https://img.shields.io/badge/updated-2026--10--29-4c8eda) ![presets](https://img.shields.io/badge/presets-5%2F7-dbab09) ![scanners](https://img.shields.io/badge/scanners-15-6f42c1) ![platforms](https://img.shields.io/badge/platforms-14-0969da) ![MFT presets](https://img.shields.io/badge/MFT%20presets-7-8250df)

> 每个体量单独运行、单独更新：哪个体量跑完就刷新哪一列，其余保持上次的结果。`very-lite` / `lite` 体量过小，计时以进程启动等固定开销为主，只作参考，不计入跨体量综合分。评分方法与数据生成原理见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。
>
> Each size runs and updates on its own: a finished run refreshes its column and the others keep their last result. `very-lite` and `lite` are so small that process start-up dominates the wall clock, so they are for reference only and stay out of the overall score. Scoring and test-data design: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

### 各项前四名 · Top 4 of each category

| 名⁠次<br>Rank | 综⁠合<br>Overall | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 内⁠存⁠峰⁠值\*<br>Peak&nbsp;RAM\* | 扫⁠描⁠效⁠率\*<br>I/O&nbsp;efficiency\* | 写⁠盘⁠量\*<br>Disk&nbsp;writes\* |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife**<br><sub>97.4</sub> | **SpaceKnife**<br><sub>96.7</sub> | **SpaceKnife**<br><sub>97.3</sub> | **ncdu**<br><sub>3.6&nbsp;MB</sub> | **WizTree**<br><sub>99.9</sub> | **SpaceKnife**<br><sub>0.0%&nbsp;·&nbsp;0.2&nbsp;MB</sub> |
| 🥈 | **gdu**<br><sub>63.0</sub> | **diskus**<br><sub>54.2</sub> | **gdu**<br><sub>68.1</sub> | **GNU&nbsp;du**<br><sub>14&nbsp;MB</sub> | **GNU&nbsp;du**<br><sub>99.2</sub> | **SpaceSniffer**<br><sub>81%&nbsp;·&nbsp;2,070.3&nbsp;MB</sub> |
| 🥉 | **SquirrelDisk**<br><sub>58.8</sub> | **gdu**<br><sub>54.1</sub> | **SquirrelDisk**<br><sub>61.0</sub> | **dua‑cli**<br><sub>22&nbsp;MB</sub> | **SpaceKnife**<br><sub>98.6</sub> | **WinDirStat**<br><sub>84%&nbsp;·&nbsp;631.6&nbsp;MB</sub> |
| 4 | **diskus**<br><sub>48.5</sub> | **dua‑cli**<br><sub>51.9</sub> | **diskus**<br><sub>42.0</sub> | **BSD&nbsp;du**<br><sub>485&nbsp;MB</sub> | **ncdu**<br><sub>96.5</sub> | **gdu**<br><sub>93%&nbsp;·&nbsp;577.3&nbsp;MB</sub> |

<sub>**\* 只作参考，不计入综合分**（综合 = 冷扫、热扫、均衡指数）· † 只有小体量成绩 · 各列按 `low` 及以上体量合并<br>**内存峰值**：各平台、各体量的中位数，含放进 tmpfs 的数据（Linux）和被压缩的内存（macOS）<br>**扫描效率**：1 ÷ (IOPS × 扫描时间) = 1 ÷ 冷扫读盘次数，平台内最少 ÷ 自己 × 100<br>**写盘量**：扫描器自己写的文件（如磁盘缓存）+ 冷扫时更新访问时间写的盘（[按日常设置开着](#怎么算分--how-scoring-works)）。百分比 = 自己 ÷ 同平台典型扫描器，排名按它（NTFS 每项写的是 ext4 的近 4 倍，平台内比才公平）；MB 是每百万项实测值。macOS 的写入计数是整台机器的，不参与<br><br>**\* For reference, not in the overall score** (overall = cold, warm, balanced index) · † small sizes only · each column combines the sizes from `low` up<br>**Peak RAM**: median over platforms and sizes, including data parked in tmpfs (Linux) and compressed memory (macOS)<br>**I/O efficiency**: 1 / (IOPS x scan time) = 1 / cold-scan disk reads, platform's fewest / own x 100<br>**Disk writes**: files the scanner writes itself (e.g. a disk cache) + what the cold scan writes for access-time updates ([on, as in daily use](#怎么算分--how-scoring-works)). The percentage is own / the platform's typical scanner and sets the rank (NTFS writes nearly 4x what ext4 does per item, so platforms are compared within themselves); MB is measured per million items. macOS stays out: its write counter covers the whole machine.</sub>

### 跨体量总榜 · Overall across sizes

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | very‑lite\* | lite\* | low | mid | high |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**97.4**</mark> | 🥉&nbsp;61.2 | 🥈&nbsp;85.6 | 🥇&nbsp;<mark>**95.9**</mark> | 🥇&nbsp;<mark>**99.2**</mark> | 🥇&nbsp;<mark>**97.2**</mark> |
| 🥈 | **gdu** | 63.0 | 🥈&nbsp;63.7 | 🥉&nbsp;83.7 | 🥉&nbsp;57.6 | 🥈&nbsp;61.3 | 🥈&nbsp;70.8 |
| 🥉 | **SquirrelDisk** | 58.8 | 🥇&nbsp;<mark>**73.7**</mark> | 🥇&nbsp;<mark>**88.3**</mark> | 🥈&nbsp;64.0 | 🥉&nbsp;55.3 | #5&nbsp;57.3 |
| 4 | **diskus** | 48.5 | #5&nbsp;51.2 | #8&nbsp;48.1 | #6&nbsp;38.4 | #5&nbsp;48.4 | 🥉&nbsp;61.5 |
| 5 | **dua‑cli** | 48.2 | #7&nbsp;43.1 | #5&nbsp;53.3 | #4&nbsp;41.4 | #6&nbsp;46.7 | #4&nbsp;57.9 |
| 6 | **pdu** | 43.2 | #6&nbsp;46.4 | #9&nbsp;45.5 | #7&nbsp;35.3 | #7&nbsp;42.8 | #8&nbsp;53.3 |
| 7 | **GNU&nbsp;du** | 37.5 | #8&nbsp;43.0 | #10&nbsp;39.0 | #5&nbsp;40.2 | #9&nbsp;36.2 | #10&nbsp;36.3 |
| 8 | **BSD&nbsp;du** | 36.8 | #4&nbsp;61.2 | #6&nbsp;52.3 | #8&nbsp;34.9 | #4&nbsp;48.8 | #12&nbsp;29.3 |
| 9 | **WinDirStat** | 36.7 | #10&nbsp;39.7 | #7&nbsp;49.3 | #10&nbsp;31.1 | #11&nbsp;29.6 | #6&nbsp;53.7 |
| 10 | **ncdu** | 35.7 | #9&nbsp;40.8 | #11&nbsp;36.5 | #9&nbsp;34.9 | #8&nbsp;36.6 | #11&nbsp;35.7 |
| 11 | **WizTree** | 34.4 | #13&nbsp;29.3 | #4&nbsp;59.4 | #11&nbsp;29.2 | #12&nbsp;25.9 | #7&nbsp;53.6 |
| 12 | **dust** | 32.0 | #11&nbsp;31.8 | #12&nbsp;32.1 | #12&nbsp;26.0 | #10&nbsp;31.9 | #9&nbsp;39.5 |
| 13 | **erdtree** | 25.6 | #12&nbsp;29.8 | #13&nbsp;27.6 | #13&nbsp;25.0 | #13&nbsp;24.6 | #13&nbsp;27.4 |
| 14 | **SpaceSniffer** | 18.9 | #14&nbsp;22.5 | #14&nbsp;21.5 | #14&nbsp;15.9 | #14&nbsp;18.4 | #14&nbsp;23.3 |
| 15 | **Sysinternals&nbsp;du** | 7.4 | #15&nbsp;8.9 | #15&nbsp;8.9 | #15&nbsp;5.9 | #15&nbsp;7.3 | #15&nbsp;9.5 |

<sub><mark>**高亮**</mark> = 该列最高分 · <mark>**highlighted**</mark> = best in its column.<br><br>综合分 = `low` 及以上各体量综合分的几何平均；\* 为仅供参考的小体量（综合分带 \* 的扫描器只有小体量成绩）。缺平台、缺体量都不扣分也不加分：只用它实际跑过的平台和体量计算，等于把缺的部分按它自己的平均分补上，平台多的工具不会因此更容易刷分，平台少的工具也不会因此被扣分。<br><br>Score = geometric mean of the per-size scores from `low` up; \* marks the reference-only small sizes (a score with \* comes from small sizes only). Missing platforms and sizes neither cost nor earn points: only what a scanner actually ran counts, the same as filling the gaps with its own average, so more platforms do not make a high score easier and fewer do not mark a tool down.</sub>

### 冷扫综合榜 · Cold scans across sizes

> CI Runner 的盘是 IOPS 受限的云盘，冷扫比的是在这种盘上谁读得省，和本地 NVMe 上的冷扫排名可能不同，见[CI 冷扫测的是什么](#ci-冷扫测的是什么--what-the-ci-cold-scans-measure)。<br>The CI runners' disks are IOPS-capped cloud disks: cold scans here measure who reads most economically on such a disk, and may rank differently on a local NVMe drive; see [What the CI cold scans measure](#ci-冷扫测的是什么--what-the-ci-cold-scans-measure).

| # | 扫⁠描⁠器<br>Scanner | **冷⁠扫⁠分**<br>**Cold** | very‑lite\* | lite\* | low | mid | high |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**96.7**</mark> | 🥇&nbsp;<mark>**70.8**</mark> | 🥈&nbsp;85.3 | 🥇&nbsp;<mark>**96.4**</mark> | 🥇&nbsp;<mark>**100.0**</mark> | 🥈&nbsp;93.9 |
| 🥈 | **diskus** | 54.2 | #4&nbsp;56.1 | #7&nbsp;58.0 | #6&nbsp;40.3 | 🥉&nbsp;51.8 | 🥉&nbsp;76.3 |
| 🥉 | **gdu** | 54.1 | #6&nbsp;47.6 | 🥉&nbsp;84.3 | 🥉&nbsp;44.7 | #4&nbsp;51.1 | #5&nbsp;69.5 |
| 4 | **dua‑cli** | 51.9 | #8&nbsp;42.9 | #6&nbsp;65.1 | #4&nbsp;41.6 | #5&nbsp;45.5 | #4&nbsp;73.7 |
| 5 | **SquirrelDisk** | 51.6 | #5&nbsp;53.3 | #4&nbsp;83.0 | 🥈&nbsp;53.6 | #6&nbsp;44.4 | #8&nbsp;57.8 |
| 6 | **WinDirStat** | 49.6 | 🥉&nbsp;57.4 | 🥇&nbsp;<mark>**93.9**</mark> | #5&nbsp;41.1 | #10&nbsp;29.7 | 🥇&nbsp;<mark>**100.0**</mark> |
| 7 | **pdu** | 44.6 | #7&nbsp;43.0 | #8&nbsp;53.7 | #7&nbsp;35.0 | #7&nbsp;42.0 | #7&nbsp;60.3 |
| 8 | **dust** | 40.4 | #9&nbsp;38.8 | #9&nbsp;47.6 | #9&nbsp;30.9 | #8&nbsp;38.1 | #9&nbsp;55.8 |
| 9 | **erdtree** | 35.0 | #10&nbsp;37.3 | #11&nbsp;36.2 | #10&nbsp;30.8 | #9&nbsp;33.9 | #10&nbsp;41.0 |
| 10 | **BSD&nbsp;du** | 33.8 | 🥈&nbsp;64.1 | #10&nbsp;46.8 | #8&nbsp;31.4 | 🥈&nbsp;59.0 | #14&nbsp;20.9 |
| 11 | **WizTree** | 29.1 | #14&nbsp;23.1 | #5&nbsp;72.1 | #12&nbsp;25.2 | #14&nbsp;14.6 | #6&nbsp;67.0 |
| 12 | **GNU&nbsp;du** | 24.9 | #12&nbsp;26.9 | #13&nbsp;25.2 | #11&nbsp;26.0 | #12&nbsp;22.7 | #12&nbsp;26.2 |
| 13 | **ncdu** | 24.1 | #13&nbsp;26.9 | #14&nbsp;24.3 | #14&nbsp;22.4 | #11&nbsp;24.4 | #13&nbsp;25.5 |
| 14 | **SpaceSniffer** | 23.9 | #11&nbsp;29.7 | #12&nbsp;32.9 | #13&nbsp;22.5 | #13&nbsp;19.3 | #11&nbsp;31.3 |
| 15 | **Sysinternals&nbsp;du** | 10.7 | #15&nbsp;9.9 | #15&nbsp;15.3 | #15&nbsp;7.9 | #15&nbsp;10.0 | #15&nbsp;15.5 |

<sub>只看冷扫：每个体量取冷扫相对分（该平台最快 ÷ 自己 × 100，跨平台几何平均），再对 `low` 及以上取几何平均；格子里是该体量冷扫的名次和分数，<mark>**高亮**</mark> = 该列最高分。<br><br>The cold-scan score alone: each size's cold-scan relative score (platform fastest / own x 100, geometric mean across platforms), then the geometric mean from `low` up; each cell is the cold-scan rank and score in that size, <mark>**highlighted**</mark> = best in its column.</sub>

### 热扫综合榜 · Warm scans across sizes

| # | 扫⁠描⁠器<br>Scanner | **热⁠扫⁠分**<br>**Warm** | very‑lite\* | lite\* | low | mid | high |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**97.3**</mark> | #4&nbsp;46.0 | 🥉&nbsp;80.0 | 🥇&nbsp;<mark>**94.7**</mark> | 🥇&nbsp;<mark>**98.4**</mark> | 🥇&nbsp;<mark>**98.8**</mark> |
| 🥈 | **gdu** | 68.1 | 🥈&nbsp;77.4 | 🥈&nbsp;81.0 | 🥉&nbsp;66.1 | 🥈&nbsp;69.4 | 🥈&nbsp;68.8 |
| 🥉 | **SquirrelDisk** | 61.0 | 🥇&nbsp;<mark>**89.1**</mark> | 🥇&nbsp;<mark>**91.1**</mark> | 🥈&nbsp;69.1 | 🥉&nbsp;62.0 | 🥉&nbsp;52.9 |
| 4 | **diskus** | 42.0 | #5&nbsp;45.1 | #7&nbsp;39.1 | #7&nbsp;33.4 | #4&nbsp;44.4 | #4&nbsp;49.8 |
| 5 | **dua‑cli** | 41.2 | #9&nbsp;38.9 | #6&nbsp;42.0 | #5&nbsp;36.4 | #5&nbsp;43.7 | #5&nbsp;43.9 |
| 6 | **pdu** | 37.3 | #6&nbsp;44.9 | #9&nbsp;35.4 | #8&nbsp;30.6 | #6&nbsp;39.3 | #6&nbsp;43.3 |
| 7 | **GNU&nbsp;du** | 35.8 | #7&nbsp;44.3 | #8&nbsp;37.0 | #4&nbsp;40.1 | #8&nbsp;36.8 | #8&nbsp;31.0 |
| 8 | **WizTree** | 35.4 | #10&nbsp;30.9 | #4&nbsp;44.6 | #9&nbsp;29.5 | #7&nbsp;38.9 | #7&nbsp;38.5 |
| 9 | **ncdu** | 33.1 | #8&nbsp;41.1 | #10&nbsp;34.4 | #6&nbsp;34.2 | #9&nbsp;34.9 | #9&nbsp;30.4 |
| 10 | **BSD&nbsp;du** | 25.9 | 🥉&nbsp;47.1 | #5&nbsp;42.2 | #10&nbsp;26.1 | #10&nbsp;28.3 | #12&nbsp;23.5 |
| 11 | **WinDirStat** | 25.0 | #11&nbsp;24.8 | #11&nbsp;25.7 | #11&nbsp;21.2 | #11&nbsp;24.8 | #10&nbsp;29.6 |
| 12 | **dust** | 22.4 | #12&nbsp;23.3 | #12&nbsp;19.7 | #12&nbsp;18.7 | #12&nbsp;23.7 | #11&nbsp;25.6 |
| 13 | **erdtree** | 17.2 | #13&nbsp;21.9 | #13&nbsp;19.5 | #13&nbsp;17.9 | #13&nbsp;16.8 | #13&nbsp;16.9 |
| 14 | **SpaceSniffer** | 10.2 | #14&nbsp;11.4 | #14&nbsp;9.8 | #14&nbsp;7.7 | #14&nbsp;11.3 | #14&nbsp;12.1 |
| 15 | **Sysinternals&nbsp;du** | 3.3 | #15&nbsp;5.0 | #15&nbsp;3.5 | #15&nbsp;2.8 | #15&nbsp;3.4 | #15&nbsp;3.9 |

<sub>只看热扫：每个体量取热扫相对分（该平台最快 ÷ 自己 × 100，跨平台几何平均），再对 `low` 及以上取几何平均；格子里是该体量热扫的名次和分数，<mark>**高亮**</mark> = 该列最高分。<br><br>The warm-scan score alone: each size's warm-scan relative score (platform fastest / own x 100, geometric mean across platforms), then the geometric mean from `low` up; each cell is the warm-scan rank and score in that size, <mark>**highlighted**</mark> = best in its column.</sub>

### 各体量详情 · Results per size

<details open>
<summary><b>high</b> · 500 万文件 · 5M files · 2026-10-27 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40422473391">run 40422473391</a> · <code>d6be58b</code></summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**97.2**</mark> | 93.9<br><sub>54.6&nbsp;s</sub> | <mark>**98.8**</mark><br><sub>10.6&nbsp;s</sub> | <mark>**98.8**</mark> | 921&nbsp;MB | 0.55% | S·F·Z | 11/13 |
| 🥈 | **gdu** | 70.8 | 69.5<br><sub>95.0&nbsp;s</sub> | 68.8<br><sub>25.0&nbsp;s</sub> | 74.3 | 108&nbsp;MB | 0.57% | S·Z | 13/13 |
| 🥉 | **diskus** | 61.5 | 76.3<br><sub>86.4&nbsp;s</sub> | 49.8<br><sub>34.5&nbsp;s</sub> | 61.0 | 45&nbsp;MB | <mark>**0.00%**</mark> | S | 13/13 |
| 4 | **dua‑cli** | 57.9 | 73.7<br><sub>89.5&nbsp;s</sub> | 43.9<br><sub>39.2&nbsp;s</sub> | 60.0 | 43&nbsp;MB | 0.09% | S·Z | 13/13 |
| 5 | **SquirrelDisk** | 57.3 | 57.8<br><sub>143&nbsp;s</sub> | 52.9<br><sub>54.6&nbsp;s</sub> | 61.6 | 134&nbsp;MB | 1.02% | S·F·Z | 8/8 |
| 6 | **WinDirStat** | 53.7 | <mark>**100.0**</mark><br><sub>102&nbsp;s</sub> | 29.6<br><sub>52.4&nbsp;s</sub> | 52.3 | 1,023&nbsp;MB | 0.79% | S·F·Z | 3/3 |
| 7 | **WizTree** | 53.6 | 67.0<br><sub>141&nbsp;s</sub> | 38.5<br><sub>52.5&nbsp;s</sub> | 59.8 | 2,388&nbsp;MB | 0.79% | S·F·Z | 2/2 |
| 8 | **pdu** | 53.3 | 60.3<br><sub>109&nbsp;s</sub> | 43.3<br><sub>39.7&nbsp;s</sub> | 58.1 | 240&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 13/13 |
| 9 | **dust** | 39.5 | 55.8<br><sub>118&nbsp;s</sub> | 25.6<br><sub>67.3&nbsp;s</sub> | 43.1 | 1,918&nbsp;MB | 0.68% | S·Z | 13/13 |
| 10 | **GNU&nbsp;du** | 36.3 | 26.2<br><sub>151&nbsp;s</sub> | 31.0<br><sub>29.1&nbsp;s</sub> | 59.1 | 18&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 11 | **ncdu** | 35.7 | 25.5<br><sub>228&nbsp;s</sub> | 30.4<br><sub>58.5&nbsp;s</sub> | 58.7 | <mark>**4&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 12 | **BSD&nbsp;du** | 29.3 | 20.9<br><sub>1,264&nbsp;s</sub> | 23.5<br><sub>1,141&nbsp;s</sub> | 51.3 | 2,095&nbsp;MB | 918.47% | S·Z | 2/2 |
| 13 | **erdtree** | 27.4 | 41.0<br><sub>115&nbsp;s</sub> | 16.9<br><sub>62.5&nbsp;s</sub> | 29.5 | 4,260&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 10/12 |
| 14 | **SpaceSniffer** | 23.3 | 31.3<br><sub>302&nbsp;s</sub> | 12.1<br><sub>167&nbsp;s</sub> | 33.5 | 2,246&nbsp;MB | n/a | IO | 2/2 |
| 15 | **Sysinternals&nbsp;du** | 9.5 | 15.5<br><sub>655&nbsp;s</sub> | 3.9<br><sub>397&nbsp;s</sub> | 14.1 | 253&nbsp;MB | 1.00% | S·F·Z | 3/3 |

单项第一 · Category winners：**冷扫 Cold** WinDirStat (100.0) · **热扫 Warm** SpaceKnife (98.8) · **均衡 Balanced** SpaceKnife (98.8) · **最省内存 Least RAM** ncdu (4 MB) · **扫描效率 I/O efficiency** GNU du (100.0) · **最准 Most accurate** diskus (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**67.6**</mark>&nbsp;/&nbsp;8.04 | 🥇<br><mark>**30.0**</mark>&nbsp;/&nbsp;<mark>**7.84**</mark> | 🥇<br><mark>**37.2**</mark>&nbsp;/&nbsp;<mark>**6.29**</mark> | 🥇<br><mark>**46.7**</mark>&nbsp;/&nbsp;<mark>**42.5**</mark> |
| **gdu** | 🥉<br>69.3&nbsp;/&nbsp;11.0 | 🥉<br>37.7&nbsp;/&nbsp;11.7 | 🥉<br>43.2&nbsp;/&nbsp;10.7 | 🥉<br>50.7&nbsp;/&nbsp;44.7 |
| **diskus** | #5<br>72.3&nbsp;/&nbsp;16.1 | #4<br>35.7&nbsp;/&nbsp;15.8 | #4<br>38.1&nbsp;/&nbsp;14.4 | 🥈<br>49.0&nbsp;/&nbsp;42.7 |
| **dua‑cli** | #6<br>82.6&nbsp;/&nbsp;21.2 | #6<br>53.1&nbsp;/&nbsp;22.3 | #6<br>56.1&nbsp;/&nbsp;21.2 | #6<br>67.0&nbsp;/&nbsp;60.7 |
| **SquirrelDisk** | 🥈<br>79.6&nbsp;/&nbsp;<mark>**7.86**</mark> | 🥈<br>38.8&nbsp;/&nbsp;8.26 | 🥈<br>46.2&nbsp;/&nbsp;7.01 | #7<br>92.6&nbsp;/&nbsp;88.2 |
| **pdu** | #4<br>76.2&nbsp;/&nbsp;13.8 | #5<br>43.5&nbsp;/&nbsp;16.5 | #5<br>50.1&nbsp;/&nbsp;13.1 | #4<br>66.7&nbsp;/&nbsp;52.2 |
| **dust** | #7<br>73.2&nbsp;/&nbsp;25.5 | #8<br>54.1&nbsp;/&nbsp;28.9 | #7<br>57.2&nbsp;/&nbsp;27.7 | #5<br>68.9&nbsp;/&nbsp;57.0 |
| **GNU&nbsp;du** | #9<br>240&nbsp;/&nbsp;22.6 | #10<br>126&nbsp;/&nbsp;22.0 | #9<br>141&nbsp;/&nbsp;18.2 | #8<br>183&nbsp;/&nbsp;168 |
| **ncdu** | #10<br>270&nbsp;/&nbsp;21.8 | #9<br>125&nbsp;/&nbsp;22.0 | #8<br>144&nbsp;/&nbsp;17.9 | #9<br>180&nbsp;/&nbsp;170 |
| **erdtree** | #8<br>107&nbsp;/&nbsp;33.0 | #7<br>59.4&nbsp;/&nbsp;23.0 | #10<br>91.7&nbsp;/&nbsp;24.7 | #10<br>148&nbsp;/&nbsp;152 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**55.7**</mark>&nbsp;/&nbsp;<mark>**4.14**</mark> | 🥇<br>20.1&nbsp;/&nbsp;<mark>**4.49**</mark> | 🥇<br>36.8&nbsp;/&nbsp;<mark>**3.71**</mark> | 🥇<br><mark>**44.0**</mark>&nbsp;/&nbsp;38.9 |
| **gdu** | #4<br>55.9&nbsp;/&nbsp;6.81 | #4<br>26.0&nbsp;/&nbsp;7.65 | 🥉<br>38.8&nbsp;/&nbsp;6.76 | 🥉<br>51.4&nbsp;/&nbsp;45.0 |
| **diskus** | 🥈<br>56.1&nbsp;/&nbsp;4.54 | 🥈<br><mark>**20.0**</mark>&nbsp;/&nbsp;4.92 | 🥈<br><mark>**35.4**</mark>&nbsp;/&nbsp;4.16 | 🥈<br>46.4&nbsp;/&nbsp;<mark>**37.9**</mark> |
| **dua‑cli** | #5<br>59.5&nbsp;/&nbsp;23.3 | #7<br>35.3&nbsp;/&nbsp;25.6 | #7<br>61.8&nbsp;/&nbsp;24.5 | #6<br>71.6&nbsp;/&nbsp;67.6 |
| **pdu** | 🥉<br>57.3&nbsp;/&nbsp;5.98 | 🥉<br>25.6&nbsp;/&nbsp;6.51 | #4<br>63.5&nbsp;/&nbsp;5.72 | #4<br>66.9&nbsp;/&nbsp;51.0 |
| **dust** | #8<br>60.8&nbsp;/&nbsp;25.3 | #8<br>36.7&nbsp;/&nbsp;26.9 | #8<br>62.5&nbsp;/&nbsp;26.1 | #5<br>72.4&nbsp;/&nbsp;56.2 |
| **GNU&nbsp;du** | #6<br>166&nbsp;/&nbsp;13.2 | #6<br>71.4&nbsp;/&nbsp;14.3 | #6<br>170&nbsp;/&nbsp;11.6 | #8<br>174&nbsp;/&nbsp;153 |
| **ncdu** | #7<br>176&nbsp;/&nbsp;12.7 | #5<br>73.3&nbsp;/&nbsp;13.6 | #5<br>156&nbsp;/&nbsp;11.0 | #7<br>164&nbsp;/&nbsp;150 |
| **erdtree** | #9<br>68.5&nbsp;/&nbsp;33.8 | #9<br>51.2&nbsp;/&nbsp;30.4 | #9<br>95.3&nbsp;/&nbsp;30.9 | #9<br>131&nbsp;/&nbsp;144 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | ⚠️ | ⚠️ |
| **gdu** | #5<br>1,354&nbsp;/&nbsp;677 | #5<br>945&nbsp;/&nbsp;248 |
| **diskus** | 🥈<br>488&nbsp;/&nbsp;460 | 🥈<br><mark>**170**</mark>&nbsp;/&nbsp;182 |
| **dua‑cli** | 🥇<br><mark>**410**</mark>&nbsp;/&nbsp;<mark>**421**</mark> | 🥇<br>174&nbsp;/&nbsp;<mark>**171**</mark> |
| **SquirrelDisk** | #6<br>825&nbsp;/&nbsp;1,042 | #6<br>598&nbsp;/&nbsp;751 |
| **pdu** | #4<br>621&nbsp;/&nbsp;633 | #4<br>396&nbsp;/&nbsp;359 |
| **dust** | 🥉<br>576&nbsp;/&nbsp;613 | 🥉<br>389&nbsp;/&nbsp;298 |
| **ncdu** | #8<br>1,383&nbsp;/&nbsp;1,279 | #7<br>928&nbsp;/&nbsp;877 |
| **BSD&nbsp;du** | #7<br>1,285&nbsp;/&nbsp;1,307 | #8<br>1,244&nbsp;/&nbsp;996 |
| **erdtree** | ⚠️ | ⚠️ |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>ReFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>63.7&nbsp;/&nbsp;<mark>**6.36**</mark> | 🥇<br>130&nbsp;/&nbsp;<mark>**9.08**</mark> | 🥈<br>241&nbsp;/&nbsp;69.7 |
| **gdu** | 🥈<br>64.5&nbsp;/&nbsp;7.13 | 🥈<br>153&nbsp;/&nbsp;12.7 | 🥉<br>245&nbsp;/&nbsp;100 |
| **diskus** | #7<br>145&nbsp;/&nbsp;51.8 | #5<br>394&nbsp;/&nbsp;113 | #10<br>357&nbsp;/&nbsp;367 |
| **dua‑cli** | 🥉<br>62.5&nbsp;/&nbsp;8.66 | 🥉<br>143&nbsp;/&nbsp;21.5 | 🥇<br>243&nbsp;/&nbsp;<mark>**64.4**</mark> |
| **SquirrelDisk** | #6<br>99.2&nbsp;/&nbsp;14.7 | — | #6<br>272&nbsp;/&nbsp;172 |
| **WinDirStat** | #5<br><mark>**53.4**</mark>&nbsp;/&nbsp;25.2 | #4<br><mark>**118**</mark>&nbsp;/&nbsp;42.8 | #4<br><mark>**167**</mark>&nbsp;/&nbsp;133 |
| **WizTree** | #4<br>75.1&nbsp;/&nbsp;17.7 | — | #5<br>264&nbsp;/&nbsp;156 |
| **pdu** | #8<br>154&nbsp;/&nbsp;54.3 | #6<br>389&nbsp;/&nbsp;116 | #7<br>318&nbsp;/&nbsp;245 |
| **dust** | #9<br>162&nbsp;/&nbsp;60.7 | #7<br>441&nbsp;/&nbsp;156 | #8<br>346&nbsp;/&nbsp;291 |
| **erdtree** | #11<br>215&nbsp;/&nbsp;141 | — | #11<br>491&nbsp;/&nbsp;500 |
| **SpaceSniffer** | #10<br>198&nbsp;/&nbsp;82.0 | — | #9<br>461&nbsp;/&nbsp;342 |
| **Sysinternals&nbsp;du** | #12<br>355&nbsp;/&nbsp;192 | #8<br>897&nbsp;/&nbsp;381 | #12<br>880&nbsp;/&nbsp;854 |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>mid</b> · 300 万文件 · 3M files · 2026-10-29 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40748199548">run 40748199548</a> · <code>7486b60</code></summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**99.2**</mark> | <mark>**100.0**</mark><br><sub>31.1&nbsp;s</sub> | <mark>**98.4**</mark><br><sub>5.48&nbsp;s</sub> | <mark>**99.3**</mark> | 593&nbsp;MB | 0.04% | S·F·Z | 11/13 |
| 🥈 | **gdu** | 61.3 | 51.1<br><sub>89.3&nbsp;s</sub> | 69.4<br><sub>12.7&nbsp;s</sub> | 65.0 | 84&nbsp;MB | 0.12% | S·Z | 13/13 |
| 🥉 | **SquirrelDisk** | 55.3 | 44.4<br><sub>141&nbsp;s</sub> | 62.0<br><sub>21.8&nbsp;s</sub> | 61.4 | 78&nbsp;MB | 1.15% | S·F·Z | 8/8 |
| 4 | **BSD&nbsp;du** | 48.8 | 59.0<br><sub>636&nbsp;s</sub> | 28.3<br><sub>465&nbsp;s</sub> | 69.9 | 93&nbsp;MB | 1667.09% | S·Z | 2/2 |
| 5 | **diskus** | 48.4 | 51.8<br><sub>88.1&nbsp;s</sub> | 44.4<br><sub>19.8&nbsp;s</sub> | 49.4 | 35&nbsp;MB | <mark>**0.00%**</mark> | S | 13/13 |
| 6 | **dua‑cli** | 46.7 | 45.5<br><sub>100&nbsp;s</sub> | 43.7<br><sub>20.2&nbsp;s</sub> | 51.2 | 22&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 13/13 |
| 7 | **pdu** | 42.8 | 42.0<br><sub>109&nbsp;s</sub> | 39.3<br><sub>22.4&nbsp;s</sub> | 47.6 | 143&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 13/13 |
| 8 | **ncdu** | 36.6 | 24.4<br><sub>159&nbsp;s</sub> | 34.9<br><sub>26.0&nbsp;s</sub> | 57.7 | <mark>**4&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 9 | **GNU&nbsp;du** | 36.2 | 22.7<br><sub>97.3&nbsp;s</sub> | 36.8<br><sub>12.6&nbsp;s</sub> | 56.9 | 14&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 10 | **dust** | 31.9 | 38.1<br><sub>120&nbsp;s</sub> | 23.7<br><sub>37.2&nbsp;s</sub> | 35.9 | 1,128&nbsp;MB | 0.46% | S·Z | 13/13 |
| 11 | **WinDirStat** | 29.6 | 29.7<br><sub>262&nbsp;s</sub> | 24.8<br><sub>32.4&nbsp;s</sub> | 35.2 | 636&nbsp;MB | 0.90% | S·F·Z | 3/3 |
| 12 | **WizTree** | 25.9 | 14.6<br><sub>524&nbsp;s</sub> | 38.9<br><sub>23.8&nbsp;s</sub> | 30.4 | 1,460&nbsp;MB | 0.90% | S·F·Z | 2/2 |
| 13 | **erdtree** | 24.6 | 33.9<br><sub>83.5&nbsp;s</sub> | 16.8<br><sub>31.8&nbsp;s</sub> | 26.1 | 2,530&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 10/12 |
| 14 | **SpaceSniffer** | 18.4 | 19.3<br><sub>397&nbsp;s</sub> | 11.3<br><sub>82.0&nbsp;s</sub> | 28.4 | 1,590&nbsp;MB | n/a | IO | 2/2 |
| 15 | **Sysinternals&nbsp;du** | 7.3 | 10.0<br><sub>776&nbsp;s</sub> | 3.4<br><sub>237&nbsp;s</sub> | 11.7 | 155&nbsp;MB | 1.22% | S·F·Z | 3/3 |

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (100.0) · **热扫 Warm** SpaceKnife (98.4) · **均衡 Balanced** SpaceKnife (99.3) · **最省内存 Least RAM** ncdu (4 MB) · **扫描效率 I/O efficiency** BSD du (100.0) · **最准 Most accurate** diskus (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**37.5**</mark>&nbsp;/&nbsp;<mark>**3.14**</mark> | 🥇<br><mark>**14.7**</mark>&nbsp;/&nbsp;<mark>**4.14**</mark> | 🥇<br><mark>**20.0**</mark>&nbsp;/&nbsp;<mark>**2.74**</mark> | 🥇<br><mark>**26.3**</mark>&nbsp;/&nbsp;<mark>**21.1**</mark> |
| **gdu** | 🥉<br>38.7&nbsp;/&nbsp;4.53 | 🥉<br>18.4&nbsp;/&nbsp;5.39 | 🥉<br>20.5&nbsp;/&nbsp;4.21 | 🥉<br>45.6&nbsp;/&nbsp;25.7 |
| **SquirrelDisk** | 🥈<br>39.2&nbsp;/&nbsp;3.65 | 🥈<br>20.3&nbsp;/&nbsp;4.24 | 🥈<br>22.0&nbsp;/&nbsp;3.09 | #7<br>81.1&nbsp;/&nbsp;36.9 |
| **diskus** | #5<br>38.6&nbsp;/&nbsp;6.06 | #4<br>18.6&nbsp;/&nbsp;8.28 | #4<br>20.8&nbsp;/&nbsp;5.56 | 🥈<br>40.0&nbsp;/&nbsp;24.1 |
| **dua‑cli** | #6<br>39.6&nbsp;/&nbsp;8.37 | #6<br>25.2&nbsp;/&nbsp;10.6 | #6<br>24.7&nbsp;/&nbsp;8.12 | #5<br>65.5&nbsp;/&nbsp;30.8 |
| **pdu** | #4<br>39.9&nbsp;/&nbsp;5.94 | #5<br>28.4&nbsp;/&nbsp;8.42 | #5<br>23.4&nbsp;/&nbsp;5.45 | #4<br>62.3&nbsp;/&nbsp;27.4 |
| **ncdu** | #9<br>122&nbsp;/&nbsp;8.89 | #10<br>95.5&nbsp;/&nbsp;11.4 | #9<br>76.5&nbsp;/&nbsp;7.59 | #9<br>145&nbsp;/&nbsp;37.5 |
| **GNU&nbsp;du** | #10<br>118&nbsp;/&nbsp;9.35 | #9<br>78.7&nbsp;/&nbsp;12.1 | #10<br>76.4&nbsp;/&nbsp;7.94 | #8<br>144&nbsp;/&nbsp;35.9 |
| **dust** | #7<br>40.8&nbsp;/&nbsp;10.8 | #7<br>31.6&nbsp;/&nbsp;13.7 | #7<br>25.4&nbsp;/&nbsp;10.0 | #6<br>69.0&nbsp;/&nbsp;30.8 |
| **erdtree** | #8<br>44.1&nbsp;/&nbsp;10.2 | #8<br>36.6&nbsp;/&nbsp;11.7 | #8<br>39.4&nbsp;/&nbsp;9.59 | #10<br>77.8&nbsp;/&nbsp;75.6 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**30.2**</mark>&nbsp;/&nbsp;<mark>**2.55**</mark> | 🥇<br><mark>**11.9**</mark>&nbsp;/&nbsp;<mark>**2.64**</mark> | 🥇<br>20.3&nbsp;/&nbsp;<mark>**2.24**</mark> | 🥇<br><mark>**26.6**</mark>&nbsp;/&nbsp;<mark>**19.4**</mark> |
| **gdu** | #4<br>30.5&nbsp;/&nbsp;3.87 | #4<br>16.9&nbsp;/&nbsp;3.90 | 🥉<br>22.5&nbsp;/&nbsp;3.89 | 🥉<br>50.5&nbsp;/&nbsp;24.8 |
| **diskus** | 🥈<br>30.4&nbsp;/&nbsp;2.70 | 🥈<br>12.3&nbsp;/&nbsp;2.69 | 🥈<br><mark>**20.2**</mark>&nbsp;/&nbsp;2.36 | 🥈<br>42.5&nbsp;/&nbsp;22.6 |
| **dua‑cli** | #6<br>35.4&nbsp;/&nbsp;15.4 | #7<br>22.3&nbsp;/&nbsp;14.3 | #7<br>37.9&nbsp;/&nbsp;14.5 | #5<br>66.5&nbsp;/&nbsp;29.6 |
| **pdu** | 🥉<br>34.0&nbsp;/&nbsp;3.63 | 🥉<br>16.3&nbsp;/&nbsp;3.61 | #4<br>30.1&nbsp;/&nbsp;3.27 | #4<br>62.9&nbsp;/&nbsp;27.1 |
| **ncdu** | #5<br>104&nbsp;/&nbsp;7.62 | #5<br>45.0&nbsp;/&nbsp;7.79 | #5<br>88.8&nbsp;/&nbsp;6.31 | #8<br>142&nbsp;/&nbsp;42.7 |
| **GNU&nbsp;du** | #8<br>130&nbsp;/&nbsp;8.49 | #6<br>49.8&nbsp;/&nbsp;8.36 | #6<br>86.8&nbsp;/&nbsp;6.66 | #7<br>140&nbsp;/&nbsp;42.9 |
| **dust** | #7<br>37.5&nbsp;/&nbsp;16.8 | #8<br>22.9&nbsp;/&nbsp;14.9 | #8<br>38.0&nbsp;/&nbsp;15.8 | #6<br>68.2&nbsp;/&nbsp;31.5 |
| **erdtree** | #9<br>46.6&nbsp;/&nbsp;17.0 | #9<br>33.3&nbsp;/&nbsp;15.9 | #9<br>52.4&nbsp;/&nbsp;16.5 | #9<br>78.4&nbsp;/&nbsp;76.1 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | ⚠️ | ⚠️ |
| **gdu** | 🥉<br>654&nbsp;/&nbsp;379 | 🥉<br>595&nbsp;/&nbsp;96.1 |
| **SquirrelDisk** | 🥇<br><mark>**390**</mark>&nbsp;/&nbsp;<mark>**241**</mark> | #6<br>654&nbsp;/&nbsp;145 |
| **BSD&nbsp;du** | #7<br>603&nbsp;/&nbsp;665 | #7<br>670&nbsp;/&nbsp;325 |
| **diskus** | #4<br>648&nbsp;/&nbsp;397 | 🥈<br>507&nbsp;/&nbsp;83.2 |
| **dua‑cli** | 🥈<br>480&nbsp;/&nbsp;327 | 🥇<br><mark>**360**</mark>&nbsp;/&nbsp;<mark>**71.7**</mark> |
| **pdu** | #5<br>634&nbsp;/&nbsp;467 | #5<br>625&nbsp;/&nbsp;176 |
| **ncdu** | #8<br>1,210&nbsp;/&nbsp;585 | #8<br>1,130&nbsp;/&nbsp;520 |
| **dust** | #6<br>734&nbsp;/&nbsp;467 | #4<br>654&nbsp;/&nbsp;138 |
| **erdtree** | ⚠️ | ⚠️ |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>ReFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**80.4**</mark>&nbsp;/&nbsp;<mark>**7.19**</mark> | 🥇<br><mark>**80.2**</mark>&nbsp;/&nbsp;<mark>**6.02**</mark> | 🥇<br><mark>**73.1**</mark>&nbsp;/&nbsp;14.2 |
| **gdu** | 🥈<br>139&nbsp;/&nbsp;11.3 | 🥈<br>678&nbsp;/&nbsp;7.94 | #4<br>1,608&nbsp;/&nbsp;17.8 |
| **SquirrelDisk** | #6<br>223&nbsp;/&nbsp;19.1 | — | #7<br>1,973&nbsp;/&nbsp;43.1 |
| **diskus** | #7<br>255&nbsp;/&nbsp;59.2 | #5<br>853&nbsp;/&nbsp;70.1 | #11<br>1,405&nbsp;/&nbsp;207 |
| **dua‑cli** | 🥉<br>140&nbsp;/&nbsp;12.6 | 🥉<br>744&nbsp;/&nbsp;12.5 | 🥉<br>1,804&nbsp;/&nbsp;<mark>**11.9**</mark> |
| **pdu** | #8<br>280&nbsp;/&nbsp;61.7 | #6<br>906&nbsp;/&nbsp;72.4 | #9<br>1,695&nbsp;/&nbsp;114 |
| **dust** | #9<br>269&nbsp;/&nbsp;73.1 | #7<br>976&nbsp;/&nbsp;82.7 | #10<br>1,618&nbsp;/&nbsp;120 |
| **WinDirStat** | #5<br>120&nbsp;/&nbsp;27.1 | #4<br>668&nbsp;/&nbsp;20.8 | 🥈<br>225&nbsp;/&nbsp;60.0 |
| **WizTree** | #4<br>153&nbsp;/&nbsp;19.7 | — | #6<br>1,788&nbsp;/&nbsp;28.7 |
| **erdtree** | #11<br>338&nbsp;/&nbsp;152 | — | #12<br>1,554&nbsp;/&nbsp;238 |
| **SpaceSniffer** | #10<br>329&nbsp;/&nbsp;94.5 | — | #5<br>478&nbsp;/&nbsp;71.1 |
| **Sysinternals&nbsp;du** | #12<br>516&nbsp;/&nbsp;215 | #8<br>1,350&nbsp;/&nbsp;285 | #8<br>670&nbsp;/&nbsp;218 |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>low</b> · 100 万文件 · 1M files · 2026-10-29 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40878578291">run 40878578291</a> · <code>fe4f85b</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40257058978">run 40257058978</a> 2026-10-26</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**95.9**</mark> | <mark>**96.4**</mark><br><sub>14.1&nbsp;s</sub> | <mark>**94.7**</mark><br><sub>3.07&nbsp;s</sub> | <mark>**96.5**</mark> | 258&nbsp;MB | 0.29% | S·F·Z | 14/14 |
| 🥈 | **SquirrelDisk** | 64.0 | 53.6<br><sub>30.9&nbsp;s</sub> | 69.1<br><sub>6.15&nbsp;s</sub> | 70.7 | 29&nbsp;MB | 0.81% | S·F·Z | 9/9 |
| 🥉 | **gdu** | 57.6 | 44.7<br><sub>30.3&nbsp;s</sub> | 66.1<br><sub>4.40&nbsp;s</sub> | 64.5 | 47&nbsp;MB | 0.40% | S·Z | 14/14 |
| 4 | **dua‑cli** | 41.4 | 41.6<br><sub>32.6&nbsp;s</sub> | 36.4<br><sub>7.99&nbsp;s</sub> | 46.8 | 13&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 5 | **GNU&nbsp;du** | 40.2 | 26.0<br><sub>29.6&nbsp;s</sub> | 40.1<br><sub>4.28&nbsp;s</sub> | 62.3 | 9&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 6 | **diskus** | 38.4 | 40.3<br><sub>33.7&nbsp;s</sub> | 33.4<br><sub>8.71&nbsp;s</sub> | 41.9 | 25&nbsp;MB | 0.06% | S | 14/14 |
| 7 | **pdu** | 35.3 | 35.0<br><sub>38.7&nbsp;s</sub> | 30.6<br><sub>9.51&nbsp;s</sub> | 41.1 | 48&nbsp;MB | 0.06% | S·Z | 14/14 |
| 8 | **BSD&nbsp;du** | 34.9 | 31.4<br><sub>118&nbsp;s</sub> | 26.1<br><sub>118&nbsp;s</sub> | 52.0 | 485&nbsp;MB | 17.48% | S·Z | 2/2 |
| 9 | **ncdu** | 34.9 | 22.4<br><sub>47.0&nbsp;s</sub> | 34.2<br><sub>8.96&nbsp;s</sub> | 55.2 | <mark>**4&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 10 | **WinDirStat** | 31.1 | 41.1<br><sub>62.0&nbsp;s</sub> | 21.2<br><sub>12.1&nbsp;s</sub> | 34.5 | 248&nbsp;MB | 0.58% | S·F·Z | 4/4 |
| 11 | **WizTree** | 29.2 | 25.2<br><sub>91.8&nbsp;s</sub> | 29.5<br><sub>9.39&nbsp;s</sub> | 33.6 | 517&nbsp;MB | 0.58% | S·F·Z | 3/3 |
| 12 | **dust** | 26.0 | 30.9<br><sub>43.9&nbsp;s</sub> | 18.7<br><sub>15.6&nbsp;s</sub> | 30.6 | 391&nbsp;MB | 0.43% | S·Z | 14/14 |
| 13 | **erdtree** | 25.0 | 30.8<br><sub>41.1&nbsp;s</sub> | 17.9<br><sub>16.7&nbsp;s</sub> | 28.3 | 857&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 14 | **SpaceSniffer** | 15.9 | 22.5<br><sub>103&nbsp;s</sub> | 7.7<br><sub>35.9&nbsp;s</sub> | 23.0 | 552&nbsp;MB | n/a | IO | 3/3 |
| 15 | **Sysinternals&nbsp;du** | 5.9 | 7.9<br><sub>325&nbsp;s</sub> | 2.8<br><sub>91.7&nbsp;s</sub> | 9.4 | 57&nbsp;MB | 0.86% | S·F·Z | 4/4 |

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (96.4) · **热扫 Warm** SpaceKnife (94.7) · **均衡 Balanced** SpaceKnife (96.5) · **最省内存 Least RAM** ncdu (4 MB) · **扫描效率 I/O efficiency** WizTree (99.7) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥈<br>12.3&nbsp;/&nbsp;1.18 | 🥇<br><mark>**5.37**</mark>&nbsp;/&nbsp;1.72 | 🥇<br><mark>**7.44**</mark>&nbsp;/&nbsp;<mark>**1.07**</mark> | 🥇<br><mark>**11.6**</mark>&nbsp;/&nbsp;<mark>**10.9**</mark> |
| **SquirrelDisk** | 🥇<br><mark>**11.9**</mark>&nbsp;/&nbsp;<mark>**1.17**</mark> | 🥈<br>6.79&nbsp;/&nbsp;<mark>**1.67**</mark> | 🥈<br>9.03&nbsp;/&nbsp;1.12 | #7<br>29.5&nbsp;/&nbsp;11.8 |
| **gdu** | 🥉<br>12.2&nbsp;/&nbsp;1.40 | 🥉<br>7.30&nbsp;/&nbsp;2.21 | 🥉<br>7.48&nbsp;/&nbsp;1.40 | 🥈<br>16.8&nbsp;/&nbsp;<mark>**10.9**</mark> |
| **dua‑cli** | #6<br>13.4&nbsp;/&nbsp;2.85 | #6<br>9.61&nbsp;/&nbsp;4.78 | #8<br>10.4&nbsp;/&nbsp;4.85 | #5<br>21.9&nbsp;/&nbsp;12.1 |
| **GNU&nbsp;du** | #10<br>37.8&nbsp;/&nbsp;2.91 | #10<br>20.1&nbsp;/&nbsp;4.74 | #6<br>23.4&nbsp;/&nbsp;1.95 | #10<br>58.2&nbsp;/&nbsp;25.1 |
| **diskus** | #5<br>12.1&nbsp;/&nbsp;1.90 | #4<br>7.12&nbsp;/&nbsp;3.43 | #4<br>7.47&nbsp;/&nbsp;2.24 | 🥉<br>16.6&nbsp;/&nbsp;11.7 |
| **pdu** | #4<br>12.4&nbsp;/&nbsp;1.82 | #5<br>7.90&nbsp;/&nbsp;3.52 | #5<br>9.72&nbsp;/&nbsp;2.82 | #4<br>22.1&nbsp;/&nbsp;11.6 |
| **ncdu** | #9<br>37.4&nbsp;/&nbsp;2.86 | #9<br>20.3&nbsp;/&nbsp;4.55 | #7<br>23.8&nbsp;/&nbsp;2.01 | #9<br>57.8&nbsp;/&nbsp;25.0 |
| **dust** | #8<br>12.9&nbsp;/&nbsp;3.53 | #8<br>10.2&nbsp;/&nbsp;5.70 | #9<br>10.7&nbsp;/&nbsp;5.31 | #6<br>22.4&nbsp;/&nbsp;12.0 |
| **erdtree** | #7<br>13.4&nbsp;/&nbsp;2.92 | #7<br>12.3&nbsp;/&nbsp;4.50 | #10<br>15.2&nbsp;/&nbsp;4.36 | #8<br>23.2&nbsp;/&nbsp;16.1 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥈<br>8.65&nbsp;/&nbsp;0.95 | 🥇<br><mark>**4.07**</mark>&nbsp;/&nbsp;0.99 | 🥈<br>7.38&nbsp;/&nbsp;0.83 | 🥇<br><mark>**9.40**</mark>&nbsp;/&nbsp;6.49 |
| **gdu** | #4<br>8.64&nbsp;/&nbsp;1.11 | 🥉<br>6.05&nbsp;/&nbsp;1.19 | #4<br>7.39&nbsp;/&nbsp;1.03 | 🥉<br>17.2&nbsp;/&nbsp;7.12 |
| **dua‑cli** | #8<br>11.8&nbsp;/&nbsp;5.33 | #7<br>8.99&nbsp;/&nbsp;4.97 | #7<br>9.33&nbsp;/&nbsp;4.97 | #5<br>23.1&nbsp;/&nbsp;8.96 |
| **GNU&nbsp;du** | #6<br>30.5&nbsp;/&nbsp;2.39 | #6<br>18.4&nbsp;/&nbsp;2.55 | #6<br>21.0&nbsp;/&nbsp;2.01 | #8<br>48.7&nbsp;/&nbsp;13.8 |
| **diskus** | 🥇<br><mark>**8.60**</mark>&nbsp;/&nbsp;<mark>**0.83**</mark> | 🥈<br>4.43&nbsp;/&nbsp;<mark>**0.88**</mark> | 🥇<br><mark>**6.87**</mark>&nbsp;/&nbsp;<mark>**0.73**</mark> | 🥈<br>14.1&nbsp;/&nbsp;<mark>**6.27**</mark> |
| **pdu** | 🥉<br>9.52&nbsp;/&nbsp;1.03 | #4<br>6.70&nbsp;/&nbsp;1.16 | 🥉<br>7.24&nbsp;/&nbsp;0.94 | #4<br>20.2&nbsp;/&nbsp;6.41 |
| **ncdu** | #5<br>30.2&nbsp;/&nbsp;2.29 | #5<br>17.7&nbsp;/&nbsp;2.46 | #5<br>20.7&nbsp;/&nbsp;1.93 | #9<br>50.4&nbsp;/&nbsp;13.9 |
| **dust** | #7<br>11.7&nbsp;/&nbsp;5.31 | #8<br>9.21&nbsp;/&nbsp;5.07 | #8<br>9.39&nbsp;/&nbsp;5.17 | #6<br>25.1&nbsp;/&nbsp;9.37 |
| **erdtree** | #9<br>13.4&nbsp;/&nbsp;6.27 | #9<br>14.1&nbsp;/&nbsp;5.58 | #9<br>12.7&nbsp;/&nbsp;5.38 | #7<br>26.7&nbsp;/&nbsp;12.7 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | 🥈<br>57.8&nbsp;/&nbsp;50.2 | 🥇<br>35.2&nbsp;/&nbsp;<mark>**25.6**</mark> |
| **SquirrelDisk** | 🥇<br><mark>**39.9**</mark>&nbsp;/&nbsp;<mark>**36.8**</mark> | 🥈<br><mark>**34.2**</mark>&nbsp;/&nbsp;31.1 |
| **gdu** | #6<br>189&nbsp;/&nbsp;97.7 | #5<br>181&nbsp;/&nbsp;82.8 |
| **dua‑cli** | 🥉<br>78.6&nbsp;/&nbsp;65.5 | 🥉<br>92.2&nbsp;/&nbsp;55.4 |
| **diskus** | #5<br>165&nbsp;/&nbsp;112 | #6<br>164&nbsp;/&nbsp;94.2 |
| **pdu** | #8<br>170&nbsp;/&nbsp;137 | #9<br>197&nbsp;/&nbsp;101 |
| **BSD&nbsp;du** | #4<br>114&nbsp;/&nbsp;120 | #4<br>121&nbsp;/&nbsp;115 |
| **ncdu** | #10<br>277&nbsp;/&nbsp;168 | #10<br>325&nbsp;/&nbsp;201 |
| **dust** | #9<br>190&nbsp;/&nbsp;126 | #8<br>202&nbsp;/&nbsp;90.9 |
| **erdtree** | #7<br>184&nbsp;/&nbsp;117 | #7<br>198&nbsp;/&nbsp;88.4 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**27.3**</mark>&nbsp;/&nbsp;<mark>**2.61**</mark> | 🥇<br><mark>**34.1**</mark>&nbsp;/&nbsp;<mark>**2.03**</mark> | 🥇<br><mark>**17.2**</mark>&nbsp;/&nbsp;<mark>**3.59**</mark> | 🥇<br><mark>**26.4**</mark>&nbsp;/&nbsp;<mark>**2.26**</mark> |
| **SquirrelDisk** | #6<br>70.1&nbsp;/&nbsp;5.87 | — | 🥉<br>17.5&nbsp;/&nbsp;22.2 | #4<br>705&nbsp;/&nbsp;3.29 |
| **gdu** | 🥈<br>49.0&nbsp;/&nbsp;3.50 | 🥈<br>288&nbsp;/&nbsp;2.47 | 🥈<br>22.4&nbsp;/&nbsp;10.1 | 🥉<br>696&nbsp;/&nbsp;3.15 |
| **dua‑cli** | 🥉<br>49.0&nbsp;/&nbsp;4.27 | 🥉<br>331&nbsp;/&nbsp;4.12 | #5<br>28.2&nbsp;/&nbsp;18.5 | #5<br>688&nbsp;/&nbsp;3.88 |
| **diskus** | #7<br>87.0&nbsp;/&nbsp;18.9 | #5<br>345&nbsp;/&nbsp;23.2 | #8<br>112&nbsp;/&nbsp;115 | #11<br>675&nbsp;/&nbsp;46.9 |
| **pdu** | #8<br>87.6&nbsp;/&nbsp;20.0 | #7<br>380&nbsp;/&nbsp;33.8 | #10<br>131&nbsp;/&nbsp;125 | #8<br>589&nbsp;/&nbsp;27.9 |
| **WinDirStat** | #5<br>40.1&nbsp;/&nbsp;9.12 | #4<br>319&nbsp;/&nbsp;6.72 | #6<br>20.2&nbsp;/&nbsp;21.3 | 🥈<br>57.2&nbsp;/&nbsp;16.3 |
| **WizTree** | #4<br>54.4&nbsp;/&nbsp;6.55 | — | #4<br>21.1&nbsp;/&nbsp;18.2 | #7<br>675&nbsp;/&nbsp;6.94 |
| **dust** | #9<br>91.7&nbsp;/&nbsp;23.3 | #6<br>390&nbsp;/&nbsp;31.4 | #9<br>122&nbsp;/&nbsp;123 | #9<br>737&nbsp;/&nbsp;29.1 |
| **erdtree** | #11<br>118&nbsp;/&nbsp;49.5 | — | #11<br>123&nbsp;/&nbsp;123 | #10<br>485&nbsp;/&nbsp;54.5 |
| **SpaceSniffer** | #10<br>109&nbsp;/&nbsp;30.9 | — | #7<br>53.9&nbsp;/&nbsp;55.2 | #6<br>186&nbsp;/&nbsp;27.1 |
| **Sysinternals&nbsp;du** | #12<br>172&nbsp;/&nbsp;69.9 | #8<br>504&nbsp;/&nbsp;98.7 | #12<br>148&nbsp;/&nbsp;151 | #12<br>864&nbsp;/&nbsp;68.0 |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>lite</b> · 40 万文件 · 400k files · 2026-10-26 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40257044247">run 40257044247</a> · <code>252bc42</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40257044247">run 40257044247</a> 2026-10-26 · 仅供参考 reference only</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SquirrelDisk** | <mark>**88.3**</mark> | 83.0<br><sub>5.59&nbsp;s</sub> | <mark>**91.1**</mark><br><sub>1.32&nbsp;s</sub> | 91.1 | 18&nbsp;MB | 0.58% | S·F·Z | 9/9 |
| 🥈 | **SpaceKnife** | 85.6 | 85.3<br><sub>4.71&nbsp;s</sub> | 80.0<br><sub>1.05&nbsp;s</sub> | <mark>**91.9**</mark> | 152&nbsp;MB | 0.14% | S·F·Z | 14/14 |
| 🥉 | **gdu** | 83.7 | 84.3<br><sub>4.85&nbsp;s</sub> | 81.0<br><sub>0.81&nbsp;s</sub> | 86.0 | 35&nbsp;MB | 0.36% | S·Z | 12/14 |
| 4 | **WizTree** | 59.4 | 72.1<br><sub>12.5&nbsp;s</sub> | 44.6<br><sub>2.94&nbsp;s</sub> | 65.1 | 235&nbsp;MB | 0.41% | S·F·Z | 3/3 |
| 5 | **dua‑cli** | 53.3 | 65.1<br><sub>6.16&nbsp;s</sub> | 42.0<br><sub>2.01&nbsp;s</sub> | 55.4 | 8&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 6 | **BSD&nbsp;du** | 52.3 | 46.8<br><sub>7.68&nbsp;s</sub> | 42.2<br><sub>9.16&nbsp;s</sub> | 72.2 | 203&nbsp;MB | 8.74% | S·Z | 2/2 |
| 7 | **WinDirStat** | 49.3 | <mark>**93.9**</mark><br><sub>9.98&nbsp;s</sub> | 25.7<br><sub>4.62&nbsp;s</sub> | 49.9 | 126&nbsp;MB | 0.41% | S·F·Z | 4/4 |
| 8 | **diskus** | 48.1 | 58.0<br><sub>6.92&nbsp;s</sub> | 39.1<br><sub>2.15&nbsp;s</sub> | 49.1 | 21&nbsp;MB | 0.14% | S | 14/14 |
| 9 | **pdu** | 45.5 | 53.7<br><sub>7.48&nbsp;s</sub> | 35.4<br><sub>2.38&nbsp;s</sub> | 49.7 | 23&nbsp;MB | 0.14% | S·Z | 14/14 |
| 10 | **GNU&nbsp;du** | 39.0 | 25.2<br><sub>10.7&nbsp;s</sub> | 37.0<br><sub>1.31&nbsp;s</sub> | 63.6 | 8&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 11 | **ncdu** | 36.5 | 24.3<br><sub>11.8&nbsp;s</sub> | 34.4<br><sub>2.14&nbsp;s</sub> | 58.1 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 12 | **dust** | 32.1 | 47.6<br><sub>8.43&nbsp;s</sub> | 19.7<br><sub>4.28&nbsp;s</sub> | 35.2 | 151&nbsp;MB | 0.25% | S·Z | 14/14 |
| 13 | **erdtree** | 27.6 | 36.2<br><sub>10.3&nbsp;s</sub> | 19.5<br><sub>4.31&nbsp;s</sub> | 29.9 | 342&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 14 | **SpaceSniffer** | 21.5 | 32.9<br><sub>27.4&nbsp;s</sub> | 9.8<br><sub>13.3&nbsp;s</sub> | 30.9 | 242&nbsp;MB | n/a | IO | 3/3 |
| 15 | **Sysinternals&nbsp;du** | 8.9 | 15.3<br><sub>61.4&nbsp;s</sub> | 3.5<br><sub>33.4&nbsp;s</sub> | 13.0 | 28&nbsp;MB | 0.47% | S·F·Z | 4/4 |

单项第一 · Category winners：**冷扫 Cold** WinDirStat (93.9) · **热扫 Warm** SquirrelDisk (91.1) · **均衡 Balanced** SpaceKnife (91.9) · **最省内存 Least RAM** ncdu (3 MB) · **扫描效率 I/O efficiency** WizTree (100.0) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SquirrelDisk** | 🥇<br><mark>**4.07**</mark>&nbsp;/&nbsp;<mark>**0.46**</mark> | 🥇<br>2.72&nbsp;/&nbsp;<mark>**0.62**</mark> | 🥇<br>2.57&nbsp;/&nbsp;<mark>**0.51**</mark> | 🥈<br>5.73&nbsp;/&nbsp;<mark>**1.06**</mark> |
| **SpaceKnife** | 🥈<br>4.88&nbsp;/&nbsp;0.56 | 🥈<br><mark>**2.59**</mark>&nbsp;/&nbsp;0.82 | 🥈<br>2.59&nbsp;/&nbsp;0.58 | 🥇<br><mark>**4.31**</mark>&nbsp;/&nbsp;1.21 |
| **gdu** | 🥉<br>4.56&nbsp;/&nbsp;0.63 | 🥉<br>2.95&nbsp;/&nbsp;0.91 | 🥉<br>2.48&nbsp;/&nbsp;0.63 | 🥉<br>4.84&nbsp;/&nbsp;1.39 |
| **dua‑cli** | #6<br>4.52&nbsp;/&nbsp;1.21 | #6<br>3.90&nbsp;/&nbsp;1.90 | #6<br>3.45&nbsp;/&nbsp;1.31 | #7<br>6.40&nbsp;/&nbsp;1.97 |
| **diskus** | #5<br>4.49&nbsp;/&nbsp;0.82 | #4<br><mark>**2.59**</mark>&nbsp;/&nbsp;1.25 | #5<br><mark>**2.31**</mark>&nbsp;/&nbsp;0.81 | #4<br>4.44&nbsp;/&nbsp;1.47 |
| **pdu** | #4<br>4.59&nbsp;/&nbsp;0.73 | #5<br>3.02&nbsp;/&nbsp;1.16 | #4<br>2.73&nbsp;/&nbsp;0.73 | #5<br>6.12&nbsp;/&nbsp;1.45 |
| **GNU&nbsp;du** | #10<br>13.5&nbsp;/&nbsp;1.22 | #10<br>8.36&nbsp;/&nbsp;1.67 | #10<br>9.28&nbsp;/&nbsp;1.14 | #10<br>18.8&nbsp;/&nbsp;3.30 |
| **ncdu** | #9<br>13.6&nbsp;/&nbsp;1.20 | #9<br>8.38&nbsp;/&nbsp;1.63 | #9<br>9.68&nbsp;/&nbsp;1.10 | #9<br>18.7&nbsp;/&nbsp;3.28 |
| **dust** | #7<br>4.69&nbsp;/&nbsp;1.32 | #8<br>3.91&nbsp;/&nbsp;2.25 | #7<br>3.35&nbsp;/&nbsp;1.44 | #6<br>6.65&nbsp;/&nbsp;1.88 |
| **erdtree** | #8<br>5.03&nbsp;/&nbsp;1.25 | #7<br>4.51&nbsp;/&nbsp;1.77 | #8<br>4.94&nbsp;/&nbsp;1.30 | #8<br>7.83&nbsp;/&nbsp;2.06 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥉<br>3.46&nbsp;/&nbsp;0.47 | #4<br>2.00&nbsp;/&nbsp;0.50 | 🥉<br>2.75&nbsp;/&nbsp;0.46 | 🥈<br>2.91&nbsp;/&nbsp;0.86 |
| **gdu** | 🥈<br>3.02&nbsp;/&nbsp;0.45 | 🥉<br>1.65&nbsp;/&nbsp;0.47 | 🥈<br>2.50&nbsp;/&nbsp;0.41 | 🥉<br>3.77&nbsp;/&nbsp;0.83 |
| **dua‑cli** | #8<br>5.59&nbsp;/&nbsp;2.01 | #8<br>2.76&nbsp;/&nbsp;2.12 | #8<br>4.39&nbsp;/&nbsp;2.09 | #6<br>5.32&nbsp;/&nbsp;2.34 |
| **diskus** | 🥇<br><mark>**2.80**</mark>&nbsp;/&nbsp;<mark>**0.32**</mark> | 🥇<br><mark>**1.50**</mark>&nbsp;/&nbsp;<mark>**0.33**</mark> | 🥇<br><mark>**2.23**</mark>&nbsp;/&nbsp;<mark>**0.29**</mark> | 🥇<br><mark>**2.88**</mark>&nbsp;/&nbsp;<mark>**0.64**</mark> |
| **pdu** | #4<br>4.93&nbsp;/&nbsp;0.38 | 🥈<br>1.74&nbsp;/&nbsp;0.41 | #4<br>3.82&nbsp;/&nbsp;0.37 | #4<br>4.64&nbsp;/&nbsp;0.73 |
| **GNU&nbsp;du** | #6<br>13.2&nbsp;/&nbsp;0.87 | #6<br>4.80&nbsp;/&nbsp;0.91 | #6<br>10.4&nbsp;/&nbsp;0.75 | #8<br>13.5&nbsp;/&nbsp;1.89 |
| **ncdu** | #5<br>13.7&nbsp;/&nbsp;0.83 | #5<br>4.63&nbsp;/&nbsp;0.88 | #5<br>10.3&nbsp;/&nbsp;0.74 | #7<br>12.6&nbsp;/&nbsp;1.88 |
| **dust** | #7<br>5.33&nbsp;/&nbsp;2.01 | #7<br>2.81&nbsp;/&nbsp;2.03 | #7<br>4.40&nbsp;/&nbsp;1.97 | #5<br>5.37&nbsp;/&nbsp;2.17 |
| **erdtree** | #9<br>6.34&nbsp;/&nbsp;2.20 | #9<br>3.56&nbsp;/&nbsp;2.14 | #9<br>6.44&nbsp;/&nbsp;2.29 | #9<br>6.86&nbsp;/&nbsp;2.51 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SquirrelDisk** | 🥈<br>5.67&nbsp;/&nbsp;6.37 | 🥇<br><mark>**2.81**</mark>&nbsp;/&nbsp;<mark>**2.94**</mark> |
| **SpaceKnife** | 🥇<br><mark>**4.60**</mark>&nbsp;/&nbsp;<mark>**5.09**</mark> | 🥈<br>3.49&nbsp;/&nbsp;2.95 |
| **gdu** | ⚠️ | ⚠️ |
| **dua‑cli** | 🥉<br>7.17&nbsp;/&nbsp;5.12 | 🥉<br>4.24&nbsp;/&nbsp;3.55 |
| **BSD&nbsp;du** | #4<br>7.44&nbsp;/&nbsp;10.0 | #4<br>7.93&nbsp;/&nbsp;8.34 |
| **diskus** | #7<br>12.7&nbsp;/&nbsp;8.27 | #7<br>14.1&nbsp;/&nbsp;6.50 |
| **pdu** | #5<br>8.24&nbsp;/&nbsp;10.4 | #6<br>6.73&nbsp;/&nbsp;13.4 |
| **ncdu** | #9<br>21.7&nbsp;/&nbsp;22.1 | #9<br>13.9&nbsp;/&nbsp;12.5 |
| **dust** | #6<br>9.02&nbsp;/&nbsp;10.2 | #5<br>6.64&nbsp;/&nbsp;9.23 |
| **erdtree** | #8<br>12.7&nbsp;/&nbsp;10.7 | #8<br>22.7&nbsp;/&nbsp;6.33 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SquirrelDisk** | #6<br>21.9&nbsp;/&nbsp;2.04 | — | 🥈<br><mark>**5.94**</mark>&nbsp;/&nbsp;1.71 | 🥇<br>15.8&nbsp;/&nbsp;<mark>**1.19**</mark> |
| **SpaceKnife** | 🥉<br>14.7&nbsp;/&nbsp;1.65 | 🥈<br>13.8&nbsp;/&nbsp;0.92 | 🥇<br>6.35&nbsp;/&nbsp;1.59 | #4<br>16.3&nbsp;/&nbsp;1.89 |
| **gdu** | 🥇<br>12.6&nbsp;/&nbsp;<mark>**1.23**</mark> | 🥇<br>13.6&nbsp;/&nbsp;<mark>**0.88**</mark> | 🥉<br>8.89&nbsp;/&nbsp;<mark>**1.54**</mark> | 🥈<br>14.7&nbsp;/&nbsp;1.28 |
| **WizTree** | #4<br>13.3&nbsp;/&nbsp;2.75 | — | #5<br>9.08&nbsp;/&nbsp;3.30 | #5<br>16.2&nbsp;/&nbsp;2.79 |
| **dua‑cli** | 🥈<br>12.2&nbsp;/&nbsp;1.52 | 🥉<br>14.1&nbsp;/&nbsp;1.67 | #4<br>10.7&nbsp;/&nbsp;1.84 | 🥉<br>14.5&nbsp;/&nbsp;1.62 |
| **WinDirStat** | #5<br><mark>**9.99**</mark>&nbsp;/&nbsp;3.70 | #4<br><mark>**10.5**</mark>&nbsp;/&nbsp;2.63 | #6<br>7.64&nbsp;/&nbsp;6.42 | #6<br><mark>**12.4**</mark>&nbsp;/&nbsp;7.29 |
| **diskus** | #7<br>30.3&nbsp;/&nbsp;6.95 | #5<br>32.0&nbsp;/&nbsp;7.75 | #8<br>37.6&nbsp;/&nbsp;30.7 | #10<br>27.4&nbsp;/&nbsp;21.5 |
| **pdu** | #8<br>31.5&nbsp;/&nbsp;7.82 | #6<br>33.2&nbsp;/&nbsp;8.35 | #9<br>38.3&nbsp;/&nbsp;41.7 | #7<br>21.8&nbsp;/&nbsp;12.9 |
| **dust** | #9<br>30.8&nbsp;/&nbsp;8.89 | #7<br>37.3&nbsp;/&nbsp;10.5 | #10<br>40.5&nbsp;/&nbsp;41.5 | #9<br>22.6&nbsp;/&nbsp;13.3 |
| **erdtree** | #11<br>41.8&nbsp;/&nbsp;18.8 | — | #11<br>38.9&nbsp;/&nbsp;40.9 | #11<br>35.0&nbsp;/&nbsp;21.2 |
| **SpaceSniffer** | #10<br>35.9&nbsp;/&nbsp;13.4 | — | #7<br>18.1&nbsp;/&nbsp;14.7 | #8<br>31.9&nbsp;/&nbsp;12.0 |
| **Sysinternals&nbsp;du** | #12<br>68.1&nbsp;/&nbsp;26.6 | #8<br>69.9&nbsp;/&nbsp;26.7 | #12<br>49.4&nbsp;/&nbsp;52.9 | #12<br>60.4&nbsp;/&nbsp;33.0 |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>very-lite</b> · 10 万文件 · 100k files · 2026-10-29 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40974150487">run 40974150487</a> · <code>1813c5c</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40974150487">run 40974150487</a> 2026-10-29 · 仅供参考 reference only</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SquirrelDisk** | <mark>**73.7**</mark> | 53.3<br><sub>1.91&nbsp;s</sub> | <mark>**89.1**</mark><br><sub>0.29&nbsp;s</sub> | <mark>**84.2**</mark> | 12&nbsp;MB | 2.02% | S·F·Z | 9/9 |
| 🥈 | **gdu** | 63.7 | 47.6<br><sub>2.07&nbsp;s</sub> | 77.4<br><sub>0.27&nbsp;s</sub> | 70.1 | 26&nbsp;MB | 0.27% | S·Z | 13/14 |
| 🥉 | **SpaceKnife** | 61.2 | <mark>**70.8**</mark><br><sub>1.38&nbsp;s</sub> | 46.0<br><sub>0.42&nbsp;s</sub> | 70.5 | 78&nbsp;MB | 0.04% | S·F·Z | 14/14 |
| 4 | **BSD&nbsp;du** | 61.2 | 64.1<br><sub>0.70&nbsp;s</sub> | 47.1<br><sub>0.73&nbsp;s</sub> | 75.8 | 74&nbsp;MB | 2.78% | S·Z | 2/2 |
| 5 | **diskus** | 51.2 | 56.1<br><sub>1.75&nbsp;s</sub> | 45.1<br><sub>0.43&nbsp;s</sub> | 53.0 | 11&nbsp;MB | 0.15% | S | 14/14 |
| 6 | **pdu** | 46.4 | 43.0<br><sub>2.28&nbsp;s</sub> | 44.9<br><sub>0.43&nbsp;s</sub> | 51.6 | 7&nbsp;MB | 0.15% | S·Z | 14/14 |
| 7 | **dua‑cli** | 43.1 | 42.9<br><sub>2.28&nbsp;s</sub> | 38.9<br><sub>0.50&nbsp;s</sub> | 47.9 | 4&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 8 | **GNU&nbsp;du** | 43.0 | 26.9<br><sub>2.71&nbsp;s</sub> | 44.3<br><sub>0.31&nbsp;s</sub> | 66.8 | 5&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 9 | **ncdu** | 40.8 | 26.9<br><sub>2.46&nbsp;s</sub> | 41.1<br><sub>0.41&nbsp;s</sub> | 61.2 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 10 | **WinDirStat** | 39.7 | 57.4<br><sub>4.55&nbsp;s</sub> | 24.8<br><sub>1.17&nbsp;s</sub> | 44.0 | 71&nbsp;MB | 0.31% | S·F·Z | 4/4 |
| 11 | **dust** | 31.8 | 38.8<br><sub>2.53&nbsp;s</sub> | 23.3<br><sub>0.84&nbsp;s</sub> | 35.5 | 39&nbsp;MB | 0.77% | S·Z | 14/14 |
| 12 | **erdtree** | 29.8 | 37.3<br><sub>2.40&nbsp;s</sub> | 21.9<br><sub>0.89&nbsp;s</sub> | 32.3 | 88&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 13 | **WizTree** | 29.3 | 23.1<br><sub>10.7&nbsp;s</sub> | 30.9<br><sub>1.05&nbsp;s</sub> | 35.3 | 94&nbsp;MB | 0.31% | S·F·Z | 3/3 |
| 14 | **SpaceSniffer** | 22.5 | 29.7<br><sub>8.29&nbsp;s</sub> | 11.4<br><sub>2.83&nbsp;s</sub> | 33.4 | 85&nbsp;MB | n/a | IO | 3/3 |
| 15 | **Sysinternals&nbsp;du** | 8.9 | 9.9<br><sub>26.3&nbsp;s</sub> | 5.0<br><sub>5.78&nbsp;s</sub> | 14.0 | 13&nbsp;MB | 0.33% | S·F·Z | 4/4 |

单项第一 · Category winners：**冷扫 Cold** SpaceKnife (70.8) · **热扫 Warm** SquirrelDisk (89.1) · **均衡 Balanced** SquirrelDisk (84.2) · **最省内存 Least RAM** ncdu (3 MB) · **扫描效率 I/O efficiency** WizTree (99.6) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SquirrelDisk** | 🥈<br>0.93&nbsp;/&nbsp;<mark>**0.15**</mark> | 🥇<br>0.93&nbsp;/&nbsp;<mark>**0.16**</mark> | 🥇<br>0.93&nbsp;/&nbsp;<mark>**0.16**</mark> | 🥉<br>2.13&nbsp;/&nbsp;<mark>**0.31**</mark> |
| **gdu** | 🥇<br>0.67&nbsp;/&nbsp;<mark>**0.15**</mark> | 🥈<br>0.82&nbsp;/&nbsp;0.23 | 🥈<br>0.87&nbsp;/&nbsp;0.21 | #6<br>3.49&nbsp;/&nbsp;0.33 |
| **SpaceKnife** | #4<br>1.00&nbsp;/&nbsp;0.29 | #5<br>1.18&nbsp;/&nbsp;0.38 | #5<br>1.08&nbsp;/&nbsp;0.40 | 🥈<br>1.40&nbsp;/&nbsp;0.44 |
| **diskus** | 🥉<br><mark>**0.60**</mark>&nbsp;/&nbsp;0.22 | 🥉<br><mark>**0.77**</mark>&nbsp;/&nbsp;0.32 | 🥉<br><mark>**0.81**</mark>&nbsp;/&nbsp;0.31 | 🥇<br><mark>**1.07**</mark>&nbsp;/&nbsp;0.40 |
| **pdu** | #5<br>1.02&nbsp;/&nbsp;0.26 | #4<br>0.83&nbsp;/&nbsp;0.32 | #4<br>1.02&nbsp;/&nbsp;0.29 | #4<br>2.25&nbsp;/&nbsp;0.38 |
| **dua‑cli** | #9<br>1.14&nbsp;/&nbsp;0.45 | #6<br>1.01&nbsp;/&nbsp;0.46 | #6<br>1.13&nbsp;/&nbsp;0.46 | #7<br>2.75&nbsp;/&nbsp;0.52 |
| **GNU&nbsp;du** | #6<br>3.05&nbsp;/&nbsp;0.20 | #8<br>2.13&nbsp;/&nbsp;0.39 | #8<br>2.85&nbsp;/&nbsp;0.34 | #9<br>4.99&nbsp;/&nbsp;0.75 |
| **ncdu** | #7<br>3.26&nbsp;/&nbsp;0.21 | #7<br>2.14&nbsp;/&nbsp;0.38 | #7<br>2.84&nbsp;/&nbsp;0.34 | #10<br>5.27&nbsp;/&nbsp;0.73 |
| **dust** | #10<br>1.08&nbsp;/&nbsp;0.50 | #9<br>1.06&nbsp;/&nbsp;0.58 | #9<br>1.22&nbsp;/&nbsp;0.59 | #8<br>2.66&nbsp;/&nbsp;0.55 |
| **erdtree** | #8<br>1.23&nbsp;/&nbsp;0.38 | #10<br>1.46&nbsp;/&nbsp;0.44 | #10<br>1.67&nbsp;/&nbsp;0.44 | #5<br>1.81&nbsp;/&nbsp;0.50 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **gdu** | 🥈<br><mark>**0.62**</mark>&nbsp;/&nbsp;0.14 | ⚠️ | 🥉<br>0.71&nbsp;/&nbsp;0.14 | 🥉<br>1.01&nbsp;/&nbsp;0.24 |
| **SpaceKnife** | #4<br>0.80&nbsp;/&nbsp;0.30 | 🥉<br><mark>**0.92**</mark>&nbsp;/&nbsp;0.31 | #4<br>0.87&nbsp;/&nbsp;0.30 | #4<br>1.11&nbsp;/&nbsp;0.39 |
| **diskus** | 🥇<br>0.90&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥇<br>1.05&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥇<br><mark>**0.51**</mark>&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥇<br><mark>**0.70**</mark>&nbsp;/&nbsp;<mark>**0.17**</mark> |
| **pdu** | 🥉<br>1.21&nbsp;/&nbsp;0.10 | 🥈<br>1.06&nbsp;/&nbsp;0.11 | 🥈<br>0.99&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥈<br>1.11&nbsp;/&nbsp;0.19 |
| **dua‑cli** | #8<br>1.21&nbsp;/&nbsp;0.53 | #8<br>1.53&nbsp;/&nbsp;0.55 | #8<br>1.24&nbsp;/&nbsp;0.55 | #5<br>1.31&nbsp;/&nbsp;0.58 |
| **GNU&nbsp;du** | #5<br>2.41&nbsp;/&nbsp;0.23 | #4<br>1.58&nbsp;/&nbsp;0.23 | #5<br>2.63&nbsp;/&nbsp;0.20 | #8<br>3.19&nbsp;/&nbsp;0.48 |
| **ncdu** | #6<br>2.49&nbsp;/&nbsp;0.23 | #5<br>1.76&nbsp;/&nbsp;0.23 | #6<br>2.86&nbsp;/&nbsp;0.20 | #9<br>3.76&nbsp;/&nbsp;0.51 |
| **dust** | #7<br>1.07&nbsp;/&nbsp;0.54 | #7<br>1.38&nbsp;/&nbsp;0.56 | #7<br>1.23&nbsp;/&nbsp;0.55 | #6<br>1.40&nbsp;/&nbsp;0.58 |
| **erdtree** | #9<br>1.24&nbsp;/&nbsp;0.51 | #6<br>1.21&nbsp;/&nbsp;0.55 | #9<br>2.01&nbsp;/&nbsp;0.56 | #7<br>1.68&nbsp;/&nbsp;0.59 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SquirrelDisk** | 🥇<br>0.79&nbsp;/&nbsp;<mark>**0.35**</mark> | 🥇<br>0.49&nbsp;/&nbsp;0.38 |
| **gdu** | 🥉<br><mark>**0.55**</mark>&nbsp;/&nbsp;0.54 | #10<br>3.50&nbsp;/&nbsp;0.87 |
| **SpaceKnife** | #8<br>1.27&nbsp;/&nbsp;0.78 | #6<br>0.99&nbsp;/&nbsp;0.46 |
| **BSD&nbsp;du** | #7<br>0.67&nbsp;/&nbsp;0.87 | #4<br>0.72&nbsp;/&nbsp;0.61 |
| **diskus** | #6<br>0.71&nbsp;/&nbsp;0.65 | 🥈<br><mark>**0.36**</mark>&nbsp;/&nbsp;0.58 |
| **pdu** | 🥈<br><mark>**0.55**</mark>&nbsp;/&nbsp;0.57 | 🥉<br>0.63&nbsp;/&nbsp;0.56 |
| **dua‑cli** | #4<br>0.64&nbsp;/&nbsp;0.58 | #7<br>1.73&nbsp;/&nbsp;<mark>**0.33**</mark> |
| **ncdu** | #10<br>1.17&nbsp;/&nbsp;1.14 | #9<br>1.40&nbsp;/&nbsp;1.02 |
| **dust** | #5<br>0.71&nbsp;/&nbsp;0.57 | #5<br>0.67&nbsp;/&nbsp;0.53 |
| **erdtree** | #9<br>0.84&nbsp;/&nbsp;1.07 | #8<br>0.85&nbsp;/&nbsp;0.74 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SquirrelDisk** | 🥉<br>5.03&nbsp;/&nbsp;0.43 | — | 🥇<br><mark>**1.72**</mark>&nbsp;/&nbsp;0.54 | #4<br>59.3&nbsp;/&nbsp;0.37 |
| **gdu** | 🥇<br>3.84&nbsp;/&nbsp;<mark>**0.33**</mark> | 🥈<br>14.8&nbsp;/&nbsp;<mark>**0.20**</mark> | 🥈<br>2.45&nbsp;/&nbsp;<mark>**0.40**</mark> | 🥉<br>63.9&nbsp;/&nbsp;<mark>**0.26**</mark> |
| **SpaceKnife** | 🥈<br><mark>**3.28**</mark>&nbsp;/&nbsp;0.60 | 🥇<br><mark>**3.10**</mark>&nbsp;/&nbsp;0.46 | #4<br>2.18&nbsp;/&nbsp;0.64 | 🥇<br><mark>**2.65**</mark>&nbsp;/&nbsp;0.47 |
| **diskus** | #7<br>7.99&nbsp;/&nbsp;2.02 | #5<br>27.0&nbsp;/&nbsp;2.03 | #7<br>5.31&nbsp;/&nbsp;1.12 | #11<br>61.9&nbsp;/&nbsp;4.39 |
| **pdu** | #9<br>9.19&nbsp;/&nbsp;2.43 | #6<br>27.6&nbsp;/&nbsp;2.10 | #8<br>6.78&nbsp;/&nbsp;1.11 | #8<br>62.7&nbsp;/&nbsp;2.78 |
| **dua‑cli** | #4<br>4.04&nbsp;/&nbsp;0.52 | 🥉<br>18.1&nbsp;/&nbsp;0.50 | 🥉<br>2.03&nbsp;/&nbsp;0.56 | #5<br>59.3&nbsp;/&nbsp;0.50 |
| **WinDirStat** | #5<br>3.39&nbsp;/&nbsp;1.08 | #4<br>19.4&nbsp;/&nbsp;0.68 | #5<br>2.08&nbsp;/&nbsp;1.63 | 🥈<br>3.12&nbsp;/&nbsp;1.54 |
| **dust** | #8<br>8.70&nbsp;/&nbsp;2.28 | #7<br>28.7&nbsp;/&nbsp;2.87 | #10<br>6.54&nbsp;/&nbsp;1.57 | #9<br>59.5&nbsp;/&nbsp;2.97 |
| **erdtree** | #11<br>12.9&nbsp;/&nbsp;6.84 | — | #11<br>6.86&nbsp;/&nbsp;3.40 | #10<br>51.4&nbsp;/&nbsp;3.38 |
| **WizTree** | #6<br>4.51&nbsp;/&nbsp;0.99 | — | #6<br>4.13&nbsp;/&nbsp;1.32 | #7<br>64.9&nbsp;/&nbsp;0.87 |
| **SpaceSniffer** | #10<br>9.11&nbsp;/&nbsp;3.46 | — | #9<br>4.50&nbsp;/&nbsp;2.95 | #6<br>13.9&nbsp;/&nbsp;2.21 |
| **Sysinternals&nbsp;du** | #12<br>17.0&nbsp;/&nbsp;7.00 | #8<br>40.3&nbsp;/&nbsp;7.19 | #12<br>9.27&nbsp;/&nbsp;4.81 | #12<br>75.6&nbsp;/&nbsp;4.60 |

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
[![SpaceKnife](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![gdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SquirrelDisk](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsquirreldisk.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![diskus](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdiskus.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![dua-cli](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdua.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![pdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fpdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![GNU du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgnu-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![BSD du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fbsd-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![WinDirStat](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![ncdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fncdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![WizTree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwiztree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![dust](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdust.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![erdtree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Ferdtree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SpaceSniffer](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspacesniffer.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![Sysinternals du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsysinternals-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
```

单个体量：文件名换成 `<扫描器>-<体量>.json`（例如 `gdu-low.json`）；MFT 专栏综合排名用 `<扫描器>-mft.json`，单个体量用 `<扫描器>-mft-<体量>.json`；也可以运行 `python scripts/readme_board.py --snippet <扫描器> [--preset low]` 生成。

One size only: use `<scanner>-<size>.json` (e.g. `gdu-low.json`). For the MFT column use `<scanner>-mft.json` (across sizes) or `<scanner>-mft-<size>.json`; `python scripts/readme_board.py --snippet <scanner> [--preset low]` prints the line.

<!-- LEADERBOARD:END -->

<!-- COMMUNITY:START -->

## 🖥️ 社区真实盘成绩 · Community results on real drives

_还没有社区提交。_ 用 [本地基准套件](docs/LOCAL_SUITE.md) 在自己的硬盘上跑一遍，再提交成绩，就会出现在这里。

_No submissions yet._ Run the [local suite](docs/LOCAL_SUITE.md) on your own drives and submit the result to see it here.

<!-- COMMUNITY:END -->

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
| **SpaceKnife** | <code>0.3.4</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI；参加 MFT 专栏 · in the MFT column |
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

- **冷扫和热扫 · Cold and warm**：每次冷扫前清空测试盘的缓存（Linux、Windows 重新挂载测试盘，ZFS 导出再导入存储池，macOS 用 `purge`）。计时的冷扫不是进程第一次启动，首次启动的杀毒扫描和加载开销不算在内。访问时间按日常设置开着（Linux `relatime`、ZFS `atime`+`relatime`、Windows 开启（NTFS 和 ReFS 都跟这个设置），macOS 用系统默认），每个扫描器冷扫时整棵树的访问时间都是两天前的（文件生成时就是两天前的，文件夹扫描前调回；Linux 每个扫描器前把被改过的调回去，macOS 调回文件夹；Windows 每个扫描器用一份新复制的测试盘）：每个扫描器都要为它更新的访问时间付出同样的代价，不会出现第一个扫描器替后面的人把访问时间更新掉的情况；热扫前不再调回，写盘量只算冷扫。这样做是为了贴近日常使用的系统：Linux 各发行版默认就是 `relatime`，Windows 从 10 起交给系统托管、常见的桌面电脑上是开着的，macOS 也默认更新。关掉访问时间来测，会把用户每天实际要付的代价藏起来：一次扫描可能顺带改写成千上万条文件和文件夹的元数据，冷扫因此变慢，SSD 也多一份写入；专门避开访问时间更新的扫描器（只读、不改动访问时间）也就得不到应有的回报。冷扫之后连续热扫三次，取平均（macOS x64 从 `high` 起只热扫一次：它的热扫和冷扫一样慢，三次放不进 6 小时的作业时限）。<br>Before each cold scan the test volume's caches are dropped (Linux and Windows remount the volume, ZFS exports and imports its pool, macOS runs `purge`). The timed cold scan is not the process's first launch, so first-launch antivirus and loading costs stay out. Access times are on as in daily use (Linux `relatime`, ZFS `atime`+`relatime`, Windows on (NTFS and ReFS both follow it), macOS as shipped), and every scanner's cold scan meets access times two days old across the tree (the tree is created that way; before each scanner Linux sets back what moved and macOS the folders; on Windows each scanner gets a fresh copy of the volume): each scanner pays the same for the access times it updates, and none inherits the updates of the one before it; nothing is set back before the warm scans, and the disk-write column counts the cold scan only. This is how everyday systems are set up: every Linux distribution mounts with `relatime` by default, Windows leaves it to the system since Windows 10 and keeps it on on common desktops, and macOS updates access times too. Measuring with access times off would hide a cost users pay every day (a scan can rewrite the metadata of thousands of files and folders on the side, which slows the cold scan and adds writes to the SSD) and would give no credit to scanners that avoid it by reading without touching access times. Three warm scans follow and are averaged (one on macOS x64 from `high` up: its warm scans are as slow as its cold ones, and three do not fit in the 6-hour job limit).
- **平台内归一化 · Normalized per platform**：每个平台内先算相对分（该平台最快 ÷ 自己 × 100），再在平台之间取几何平均，不同 Runner 的硬件快慢在平台内就约掉了。<br>Each platform scores scanners against its fastest (fastest / own × 100), and the platforms are combined by geometric mean, so runner hardware cancels out.
- **分片 · Shards**：macOS、Windows ARM64 和 ReFS 从 `mid` 起（开着访问时间，它们的冷扫要慢 2–14 倍）扫描放不进一个 6 小时的作业，拆成几个作业并行，每个作业只跑一部分扫描器（按已发布成绩估算用时来分）。同型号的 Runner 之间也有快慢（CI 盘实测能差一倍），所以每个分片都额外跑一次基准扫描器 dua，各分片的冷扫、热扫用时按「参照分片的 dua 用时 ÷ 本分片的 dua 用时」换算到同一台机器的速度（dua 单次不到 20 秒时，计时波动比机器差异还大，不换算）；内存、CPU 时间和读盘次数不换算。macOS 每个分片自己生成测试树（磁盘镜像在 macOS Runner 上太慢，没法共享），Windows ARM64 从 `very-high` 起也是（镜像在 Runner 上放不下两份；`mid`、`high` 生成一次再交给各分片），ReFS 只生成一次再交给各分片。<br>From `mid` up on macOS, Windows ARM64 and ReFS (with access times on, their cold scans take 2-14x as long) the scans do not fit in one 6-hour job, so they are split over parallel jobs, each running some of the scanners (packed by the times estimated from the published results). Runners of the same kind differ (up to 2x on the CI disks), so every shard also runs the anchor scanner dua, and each shard's cold and warm times are scaled by the reference shard's dua time / this shard's dua time (not when a dua scan takes under 20 s: timing noise then outweighs the runners' difference); memory, CPU time and disk reads are not scaled. On macOS every shard generates the tree itself (disk images are too slow on the macOS runners to hand one over), and so does Windows ARM64 from `very-high` (its image does not fit twice on the runner; at `mid` and `high` it is generated once and handed over); ReFS is generated once and handed to the shards.
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
