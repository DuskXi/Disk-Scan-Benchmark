# disk-scanner-bench

**跨平台硬盘空间扫描工具基准测试 · Cross-platform benchmark for disk-space scanners**

[🏆 排行榜 Leaderboard](#-排行榜--leaderboard) · [📐 方法说明 Methodology](docs/METHODOLOGY.md) · [🧪 本地套件 Local suite](docs/LOCAL_SUITE.md) · [➕ 新增扫描器 Add a scanner](#新增扫描器--adding-a-scanner)

在 GitHub Actions 的免费 Runner 上（Linux、macOS、Windows，x86_64 与 ARM64，多种文件系统），用确定性生成的合成文件树（最多 900 万个文件，逻辑上几 TB、物理上只占几 GB）给主流磁盘空间扫描工具做冷扫和热扫计时，核对每个工具自己报告的结果是否完整，再按平台归一化，排出跨平台、跨体量的总榜。合成数据会模拟用了多年的磁盘布局；生成算法只按"像不像真实的盘"取舍，不看任何扫描器的表现。

On free GitHub Actions runners (Linux, macOS and Windows, x86_64 and ARM64, several filesystems), mainstream disk-space scanners are timed on cold and warm scans of a deterministic synthetic tree (up to 9 million files, terabytes in logical size but only a few GB on disk). Each scanner's own output is checked for completeness, scores are normalized within each platform, and the results form one board across platforms and sizes. The test data imitates a drive that has been in use for years; generator choices are judged only by how closely they match real drives, never by how any scanner performs.

<!-- LEADERBOARD:START -->

## 🏆 排行榜 · Leaderboard

![updated](https://img.shields.io/badge/updated-2026--10--25-4c8eda) ![presets](https://img.shields.io/badge/presets-2%2F6-dbab09) ![scanners](https://img.shields.io/badge/scanners-15-6f42c1) ![platforms](https://img.shields.io/badge/platforms-14-0969da) ![MFT presets](https://img.shields.io/badge/MFT%20presets-3-8250df)

> 每个体量单独运行、单独更新：哪个体量跑完就刷新哪一列，其余保持上次的结果。`very-lite` / `lite` 体量过小，计时以进程启动等固定开销为主，只作参考，不计入跨体量综合分。评分方法与数据生成原理见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。
>
> Each size runs and updates on its own: a finished run refreshes its column and the others keep their last result. `very-lite` and `lite` are so small that process start-up dominates the wall clock, so they are for reference only and stay out of the overall score. Scoring and test-data design: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

### 跨体量总榜 · Overall across sizes

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | very‑lite\* | low |
| :---: | :--- | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | **88.3** | #6&nbsp;53.9 | 🥇&nbsp;88.3 |
| 🥈 | **SquirrelDisk** | **82.6** | 🥇&nbsp;86.8 | 🥈&nbsp;82.6 |
| 🥉 | **dua‑cli** | **62.6** | #7&nbsp;49.6 | 🥉&nbsp;62.6 |
| 4 | **gdu** | **58.1** | 🥈&nbsp;72.2 | #4&nbsp;58.1 |
| 5 | **WizTree** | **54.5** | #9&nbsp;46.0 | #5&nbsp;54.5 |
| 6 | **WinDirStat** | **47.1** | #8&nbsp;48.3 | #6&nbsp;47.1 |
| 7 | **BSD&nbsp;du** | **41.5** | #4&nbsp;60.5 | #7&nbsp;41.5 |
| 8 | **GNU&nbsp;du** | **40.8** | #10&nbsp;42.7 | #8&nbsp;40.8 |
| 9 | **diskus** | **39.7** | 🥉&nbsp;61.3 | #9&nbsp;39.7 |
| 10 | **pdu** | **39.4** | #5&nbsp;54.6 | #10&nbsp;39.4 |
| 11 | **ncdu** | **33.6** | #11&nbsp;41.4 | #11&nbsp;33.6 |
| 12 | **dust** | **31.1** | #12&nbsp;35.3 | #12&nbsp;31.1 |
| 13 | **erdtree** | **30.0** | #13&nbsp;29.2 | #13&nbsp;30.0 |
| 14 | **SpaceSniffer** | **20.3** | #14&nbsp;23.3 | #14&nbsp;20.3 |
| 15 | **Sysinternals&nbsp;du** | **8.4** | #15&nbsp;12.0 | #15&nbsp;8.4 |

<sub>综合分 = `low` 及以上各体量综合分的几何平均；\* 为仅供参考的小体量（综合分带 \* 的扫描器只有小体量成绩）。缺平台、缺体量都不扣分也不加分：只用它实际跑过的平台和体量计算，等于把缺的部分按它自己的平均分补上，平台多的工具不会因此更容易刷分，平台少的工具也不会因此被扣分。<br><br>Score = geometric mean of the per-size scores from `low` up; \* marks the reference-only small sizes (a score with \* comes from small sizes only). Missing platforms and sizes neither cost nor earn points: only what a scanner actually ran counts, the same as filling the gaps with its own average, so more platforms do not make a high score easier and fewer do not mark a tool down.</sub>

### 各体量详情 · Results per size

<details open>
<summary><b>low</b> · 100 万文件 · 1M files · 2026-10-25 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40209205669">run 40209205669</a> · <code>fe51464</code></summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | **88.3** | 82.2 | 92.5 | 90.5 | 246&nbsp;MB | 0.67% | S·F·Z | 7/7 |
| 🥈 | **SquirrelDisk** | **82.6** | 84.1 | 79.5 | 84.4 | 31&nbsp;MB | 0.81% | S·F·Z | 5/5 |
| 🥉 | **dua‑cli** | **62.6** | 77.4 | 50.9 | 62.4 | 52&nbsp;MB | 0.00% | S·Z | 7/7 |
| 4 | **gdu** | **58.1** | 51.4 | 61.3 | 62.1 | 48&nbsp;MB | 0.58% | S·Z | 7/7 |
| 5 | **WizTree** | **54.5** | 74.6 | 36.9 | 58.7 | 518&nbsp;MB | 0.58% | S·F·Z | 2/2 |
| 6 | **WinDirStat** | **47.1** | 100.0 | 22.3 | 47.0 | 247&nbsp;MB | 0.58% | S·F·Z | 3/3 |
| 7 | **BSD&nbsp;du** | **41.5** | 33.5 | 33.7 | 63.2 | 472&nbsp;MB | 17.48% | S·Z | 2/2 |
| 8 | **GNU&nbsp;du** | **40.8** | 28.6 | 37.4 | 63.4 | 9&nbsp;MB | 0.00% | S·Z | 2/2 |
| 9 | **diskus** | **39.7** | 54.6 | 29.2 | 39.1 | 27&nbsp;MB | 0.58% | S | 7/7 |
| 10 | **pdu** | **39.4** | 53.4 | 27.9 | 41.0 | 50&nbsp;MB | 0.58% | S·Z | 7/7 |
| 11 | **ncdu** | **33.6** | 25.2 | 29.0 | 52.0 | 212&nbsp;MB | 0.00% | S·F·Z | 4/4 |
| 12 | **dust** | **31.1** | 49.2 | 18.6 | 32.9 | 391&nbsp;MB | 0.50% | S·Z | 7/7 |
| 13 | **erdtree** | **30.0** | 48.7 | 18.3 | 30.4 | 910&nbsp;MB | 0.38% | S·F·Z | 6/6 |
| 14 | **SpaceSniffer** | **20.3** | 33.3 | 8.7 | 28.6 | 553&nbsp;MB | n/a | IO | 2/2 |
| 15 | **Sysinternals&nbsp;du** | **8.4** | 16.3 | 3.0 | 12.3 | 57&nbsp;MB | 0.86% | S·F·Z | 3/3 |

单项第一 · Category winners：**冷扫 Cold** WinDirStat (100.0) · **热扫 Warm** SpaceKnife (92.5) · **均衡 Balanced** SpaceKnife (90.5) · **最省内存 Least RAM** GNU du (9 MB) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | ARM64<br>ext4 |
| :--- | :---: | :---: |
| **SpaceKnife** | 🥈<br>11.1&nbsp;/&nbsp;1.60 | 🥈<br>8.71&nbsp;/&nbsp;0.89 |
| **SquirrelDisk** | 🥇<br>10.7&nbsp;/&nbsp;1.52 | — |
| **dua‑cli** | #6<br>12.6&nbsp;/&nbsp;4.35 | #8<br>9.45&nbsp;/&nbsp;5.25 |
| **gdu** | 🥉<br>10.1&nbsp;/&nbsp;2.14 | #4<br>8.32&nbsp;/&nbsp;1.12 |
| **GNU&nbsp;du** | #10<br>34.7&nbsp;/&nbsp;3.97 | #6<br>26.8&nbsp;/&nbsp;2.23 |
| **diskus** | #4<br>9.25&nbsp;/&nbsp;2.98 | 🥇<br>8.25&nbsp;/&nbsp;0.81 |
| **pdu** | #5<br>11.6&nbsp;/&nbsp;2.80 | 🥉<br>8.56&nbsp;/&nbsp;1.02 |
| **ncdu** | #9<br>34.6&nbsp;/&nbsp;3.91 | #5<br>26.9&nbsp;/&nbsp;2.12 |
| **dust** | #8<br>12.5&nbsp;/&nbsp;5.34 | #7<br>9.21&nbsp;/&nbsp;5.38 |
| **erdtree** | #7<br>13.9&nbsp;/&nbsp;4.27 | #9<br>12.0&nbsp;/&nbsp;5.50 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | 🥈<br>57.1&nbsp;/&nbsp;54.3 | 🥈<br>16.4&nbsp;/&nbsp;15.4 |
| **SquirrelDisk** | 🥇<br>37.5&nbsp;/&nbsp;40.0 | 🥇<br>15.9&nbsp;/&nbsp;14.1 |
| **dua‑cli** | 🥉<br>56.6&nbsp;/&nbsp;57.2 | 🥉<br>16.3&nbsp;/&nbsp;14.7 |
| **gdu** | #10<br>167&nbsp;/&nbsp;92.6 | #10<br>147&nbsp;/&nbsp;57.6 |
| **BSD&nbsp;du** | #8<br>143&nbsp;/&nbsp;131 | #7<br>37.4&nbsp;/&nbsp;37.2 |
| **diskus** | #5<br>87.8&nbsp;/&nbsp;69.8 | #4<br>23.9&nbsp;/&nbsp;13.9 |
| **pdu** | #7<br>86.3&nbsp;/&nbsp;95.9 | #5<br>23.6&nbsp;/&nbsp;21.4 |
| **ncdu** | #9<br>138&nbsp;/&nbsp;134 | #9<br>88.5&nbsp;/&nbsp;87.7 |
| **dust** | #4<br>73.6&nbsp;/&nbsp;64.1 | #8<br>36.8&nbsp;/&nbsp;31.9 |
| **erdtree** | #6<br>76.6&nbsp;/&nbsp;90.2 | #6<br>27.9&nbsp;/&nbsp;24.6 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>ReFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>27.8&nbsp;/&nbsp;2.54 | 🥇<br>42.1&nbsp;/&nbsp;1.73 | 🥇<br>18.4&nbsp;/&nbsp;1.34 |
| **SquirrelDisk** | #6<br>45.3&nbsp;/&nbsp;5.01 | — | #4<br>18.6&nbsp;/&nbsp;2.11 |
| **dua‑cli** | 🥉<br>30.0&nbsp;/&nbsp;3.57 | 🥉<br>45.9&nbsp;/&nbsp;3.66 | 🥉<br>19.4&nbsp;/&nbsp;1.82 |
| **gdu** | 🥈<br>31.1&nbsp;/&nbsp;3.00 | 🥈<br>41.1&nbsp;/&nbsp;2.17 | 🥈<br>19.8&nbsp;/&nbsp;1.49 |
| **WizTree** | #5<br>33.9&nbsp;/&nbsp;6.34 | — | #5<br>21.7&nbsp;/&nbsp;3.95 |
| **WinDirStat** | #4<br>23.1&nbsp;/&nbsp;8.47 | #4<br>26.5&nbsp;/&nbsp;6.16 | #6<br>17.7&nbsp;/&nbsp;10.2 |
| **diskus** | #7<br>68.9&nbsp;/&nbsp;18.3 | #5<br>92.0&nbsp;/&nbsp;18.0 | #10<br>33.6&nbsp;/&nbsp;28.7 |
| **pdu** | #8<br>71.3&nbsp;/&nbsp;19.7 | #6<br>105&nbsp;/&nbsp;19.0 | #7<br>26.3&nbsp;/&nbsp;14.1 |
| **dust** | #9<br>73.7&nbsp;/&nbsp;23.2 | #7<br>103&nbsp;/&nbsp;23.4 | #9<br>30.0&nbsp;/&nbsp;16.4 |
| **erdtree** | #11<br>96.1&nbsp;/&nbsp;48.9 | — | #11<br>40.6&nbsp;/&nbsp;24.5 |
| **SpaceSniffer** | #10<br>90.2&nbsp;/&nbsp;33.8 | — | #8<br>40.9&nbsp;/&nbsp;13.2 |
| **Sysinternals&nbsp;du** | #12<br>158&nbsp;/&nbsp;70.3 | #8<br>205&nbsp;/&nbsp;63.6 | #12<br>77.4&nbsp;/&nbsp;48.0 |

<sub>表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported。<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>very-lite</b> · 10 万文件 · 100k files · 2026-10-25 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40217165966">run 40217165966</a> · <code>6d7ac1c</code> · 仅供参考 reference only</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SquirrelDisk** | **86.8** | 82.8 | 84.9 | 93.1 | 12&nbsp;MB | 2.02% | S·F·Z | 9/9 |
| 🥈 | **gdu** | **72.2** | 66.9 | 75.5 | 74.6 | 26&nbsp;MB | 0.10% | S·Z | 11/14 |
| 🥉 | **diskus** | **61.3** | 74.2 | 52.0 | 59.6 | 11&nbsp;MB | 0.15% | S | 14/14 |
| 4 | **BSD&nbsp;du** | **60.5** | 57.2 | 51.6 | 75.2 | 71&nbsp;MB | 2.78% | S·Z | 2/2 |
| 5 | **pdu** | **54.6** | 57.5 | 49.4 | 57.3 | 9&nbsp;MB | 0.15% | S·Z | 14/14 |
| 6 | **SpaceKnife** | **53.9** | 54.2 | 44.3 | 65.3 | 71&nbsp;MB | 0.04% | S·F·Z | 14/14 |
| 7 | **dua‑cli** | **49.6** | 63.8 | 37.2 | 51.4 | 6&nbsp;MB | 0.00% | S·Z | 14/14 |
| 8 | **WinDirStat** | **48.3** | 92.3 | 24.8 | 49.2 | 71&nbsp;MB | 0.31% | S·F·Z | 4/4 |
| 9 | **WizTree** | **46.0** | 66.3 | 28.6 | 51.5 | 95&nbsp;MB | 0.31% | S·F·Z | 3/3 |
| 10 | **GNU&nbsp;du** | **42.7** | 24.6 | 45.5 | 69.5 | 5&nbsp;MB | 0.00% | S·Z | 8/8 |
| 11 | **ncdu** | **41.4** | 25.3 | 43.3 | 64.5 | 3&nbsp;MB | 0.00% | S·F·Z | 10/10 |
| 12 | **dust** | **35.3** | 48.8 | 24.0 | 37.7 | 41&nbsp;MB | 0.77% | S·Z | 14/14 |
| 13 | **erdtree** | **29.2** | 40.4 | 20.1 | 30.6 | 90&nbsp;MB | 0.04% | S·F·Z | 10/13 |
| 14 | **SpaceSniffer** | **23.3** | 39.4 | 9.8 | 33.1 | 86&nbsp;MB | n/a | IO | 3/3 |
| 15 | **Sysinternals&nbsp;du** | **12.0** | 19.9 | 5.2 | 16.9 | 13&nbsp;MB | 0.33% | S·F·Z | 4/4 |

单项第一 · Category winners：**冷扫 Cold** WinDirStat (92.3) · **热扫 Warm** SquirrelDisk (84.9) · **均衡 Balanced** SquirrelDisk (93.1) · **最省内存 Least RAM** ncdu (3 MB) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SquirrelDisk** | 🥇<br>1.07&nbsp;/&nbsp;0.15 | 🥇<br>0.78&nbsp;/&nbsp;0.15 | 🥈<br>1.13&nbsp;/&nbsp;0.15 | 🥈<br>1.82&nbsp;/&nbsp;0.46 |
| **gdu** | 🥈<br>1.00&nbsp;/&nbsp;0.24 | 🥈<br>0.67&nbsp;/&nbsp;0.17 | 🥇<br>1.01&nbsp;/&nbsp;0.16 | ⚠️ |
| **diskus** | 🥉<br>0.79&nbsp;/&nbsp;0.31 | 🥉<br>0.57&nbsp;/&nbsp;0.26 | 🥉<br>0.81&nbsp;/&nbsp;0.24 | 🥇<br>1.45&nbsp;/&nbsp;0.48 |
| **pdu** | #4<br>1.09&nbsp;/&nbsp;0.31 | #4<br>0.74&nbsp;/&nbsp;0.31 | #4<br>1.16&nbsp;/&nbsp;0.28 | 🥉<br>2.04&nbsp;/&nbsp;0.50 |
| **SpaceKnife** | #5<br>1.40&nbsp;/&nbsp;0.41 | #7<br>1.08&nbsp;/&nbsp;0.40 | #7<br>1.60&nbsp;/&nbsp;0.34 | #4<br>2.26&nbsp;/&nbsp;0.57 |
| **dua‑cli** | #7<br>1.33&nbsp;/&nbsp;0.48 | #8<br>0.92&nbsp;/&nbsp;0.51 | #8<br>1.25&nbsp;/&nbsp;0.50 | #5<br>2.13&nbsp;/&nbsp;0.67 |
| **GNU&nbsp;du** | #9<br>3.41&nbsp;/&nbsp;0.40 | #5<br>1.64&nbsp;/&nbsp;0.26 | #5<br>2.40&nbsp;/&nbsp;0.21 | #8<br>5.57&nbsp;/&nbsp;0.93 |
| **ncdu** | #10<br>3.44&nbsp;/&nbsp;0.40 | #6<br>1.68&nbsp;/&nbsp;0.26 | #6<br>2.56&nbsp;/&nbsp;0.23 | #7<br>5.52&nbsp;/&nbsp;0.92 |
| **dust** | #8<br>1.26&nbsp;/&nbsp;0.57 | #9<br>0.90&nbsp;/&nbsp;0.56 | #10<br>1.52&nbsp;/&nbsp;0.54 | #6<br>2.13&nbsp;/&nbsp;0.70 |
| **erdtree** | #6<br>1.35&nbsp;/&nbsp;0.43 | #10<br>1.24&nbsp;/&nbsp;0.45 | #9<br>1.77&nbsp;/&nbsp;0.43 | ⚠️ |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **gdu** | 🥉<br>0.85&nbsp;/&nbsp;0.13 | ⚠️ | 🥉<br>0.52&nbsp;/&nbsp;0.12 | ⚠️ |
| **diskus** | 🥇<br>0.56&nbsp;/&nbsp;0.09 | 🥇<br>0.38&nbsp;/&nbsp;0.09 | 🥇<br>0.32&nbsp;/&nbsp;0.07 | 🥇<br>0.78&nbsp;/&nbsp;0.16 |
| **pdu** | 🥈<br>1.22&nbsp;/&nbsp;0.09 | 🥈<br>0.58&nbsp;/&nbsp;0.10 | 🥈<br>0.52&nbsp;/&nbsp;0.09 | 🥈<br>1.31&nbsp;/&nbsp;0.17 |
| **SpaceKnife** | #4<br>1.57&nbsp;/&nbsp;0.32 | #5<br>0.95&nbsp;/&nbsp;0.31 | #4<br>0.81&nbsp;/&nbsp;0.28 | 🥉<br>1.72&nbsp;/&nbsp;0.36 |
| **dua‑cli** | #8<br>1.44&nbsp;/&nbsp;0.50 | #7<br>0.92&nbsp;/&nbsp;0.53 | #8<br>0.72&nbsp;/&nbsp;0.50 | #5<br>1.56&nbsp;/&nbsp;0.55 |
| **GNU&nbsp;du** | #6<br>3.27&nbsp;/&nbsp;0.21 | #4<br>1.51&nbsp;/&nbsp;0.22 | #5<br>1.67&nbsp;/&nbsp;0.18 | #7<br>3.39&nbsp;/&nbsp;0.45 |
| **ncdu** | #5<br>3.16&nbsp;/&nbsp;0.21 | 🥉<br>1.53&nbsp;/&nbsp;0.21 | #6<br>1.65&nbsp;/&nbsp;0.18 | #6<br>3.46&nbsp;/&nbsp;0.44 |
| **dust** | #7<br>1.36&nbsp;/&nbsp;0.49 | #6<br>0.84&nbsp;/&nbsp;0.50 | #7<br>0.67&nbsp;/&nbsp;0.51 | #4<br>1.63&nbsp;/&nbsp;0.52 |
| **erdtree** | #9<br>1.60&nbsp;/&nbsp;0.53 | #8<br>1.07&nbsp;/&nbsp;0.54 | #9<br>1.14&nbsp;/&nbsp;0.55 | ⚠️ |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SquirrelDisk** | 🥇<br>0.50&nbsp;/&nbsp;0.35 | 🥈<br>0.27&nbsp;/&nbsp;0.36 |
| **gdu** | #6<br>0.78&nbsp;/&nbsp;0.84 | #10<br>1.53&nbsp;/&nbsp;0.63 |
| **diskus** | 🥈<br>0.43&nbsp;/&nbsp;0.38 | 🥉<br>0.39&nbsp;/&nbsp;0.32 |
| **BSD&nbsp;du** | #4<br>0.74&nbsp;/&nbsp;0.65 | #6<br>0.48&nbsp;/&nbsp;0.62 |
| **pdu** | 🥉<br>0.49&nbsp;/&nbsp;0.40 | #4<br>0.46&nbsp;/&nbsp;0.41 |
| **SpaceKnife** | #7<br>1.15&nbsp;/&nbsp;0.81 | #7<br>0.61&nbsp;/&nbsp;0.42 |
| **dua‑cli** | #5<br>0.70&nbsp;/&nbsp;0.71 | 🥇<br>0.27&nbsp;/&nbsp;0.30 |
| **ncdu** | #10<br>1.32&nbsp;/&nbsp;1.08 | #8<br>1.01&nbsp;/&nbsp;0.76 |
| **dust** | #8<br>0.75&nbsp;/&nbsp;1.07 | #5<br>0.44&nbsp;/&nbsp;0.44 |
| **erdtree** | #9<br>0.85&nbsp;/&nbsp;1.08 | #9<br>0.79&nbsp;/&nbsp;0.87 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SquirrelDisk** | #4<br>2.32&nbsp;/&nbsp;0.38 | — | 🥈<br>1.57&nbsp;/&nbsp;0.53 | 🥈<br>1.72&nbsp;/&nbsp;0.22 |
| **gdu** | 🥇<br>1.73&nbsp;/&nbsp;0.20 | 🥇<br>5.00&nbsp;/&nbsp;0.23 | 🥇<br>1.60&nbsp;/&nbsp;0.36 | 🥇<br>1.74&nbsp;/&nbsp;0.16 |
| **diskus** | #7<br>3.94&nbsp;/&nbsp;1.08 | #5<br>12.1&nbsp;/&nbsp;2.08 | #7<br>4.10&nbsp;/&nbsp;0.77 | #11<br>3.06&nbsp;/&nbsp;2.26 |
| **pdu** | #8<br>4.21&nbsp;/&nbsp;1.21 | #6<br>12.0&nbsp;/&nbsp;2.23 | #8<br>4.43&nbsp;/&nbsp;0.76 | #7<br>2.25&nbsp;/&nbsp;1.22 |
| **SpaceKnife** | 🥉<br>1.77&nbsp;/&nbsp;0.39 | 🥈<br>5.11&nbsp;/&nbsp;0.46 | 🥉<br>1.82&nbsp;/&nbsp;0.59 | #4<br>1.82&nbsp;/&nbsp;0.33 |
| **dua‑cli** | 🥈<br>1.67&nbsp;/&nbsp;0.35 | #4<br>4.89&nbsp;/&nbsp;0.54 | #4<br>2.01&nbsp;/&nbsp;0.70 | 🥉<br>1.66&nbsp;/&nbsp;0.26 |
| **WinDirStat** | #5<br>1.92&nbsp;/&nbsp;0.71 | 🥉<br>3.17&nbsp;/&nbsp;0.68 | #5<br>1.74&nbsp;/&nbsp;1.30 | #6<br>1.78&nbsp;/&nbsp;1.10 |
| **WizTree** | #6<br>2.26&nbsp;/&nbsp;0.77 | — | #6<br>2.92&nbsp;/&nbsp;0.98 | #5<br>2.25&nbsp;/&nbsp;0.66 |
| **dust** | #9<br>4.34&nbsp;/&nbsp;1.39 | #7<br>13.3&nbsp;/&nbsp;2.53 | #9<br>4.81&nbsp;/&nbsp;1.09 | #8<br>2.39&nbsp;/&nbsp;1.39 |
| **erdtree** | #11<br>5.62&nbsp;/&nbsp;2.95 | — | ⚠️ | #10<br>3.11&nbsp;/&nbsp;1.84 |
| **SpaceSniffer** | #10<br>4.88&nbsp;/&nbsp;2.50 | — | #10<br>3.83&nbsp;/&nbsp;2.63 | #9<br>3.79&nbsp;/&nbsp;1.91 |
| **Sysinternals&nbsp;du** | #12<br>9.05&nbsp;/&nbsp;4.61 | #8<br>22.0&nbsp;/&nbsp;6.52 | #11<br>7.62&nbsp;/&nbsp;3.67 | #12<br>5.82&nbsp;/&nbsp;3.37 |

<sub>表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported。<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

### NTFS MFT 专栏 · NTFS MFT column

直接读取 NTFS `$MFT` 的扫描模式单独比较，不和上面的普通目录遍历混排；冷热两次耗时应当接近，因为每次都要读完整张 MFT。

Scanners that read the NTFS `$MFT` directly are ranked here, apart from the directory-walking board above; their cold and warm times should be close, since every scan reads the whole MFT.

| 扫⁠描⁠器<br>Scanner | very‑lite\* | lite\* | low |
| :--- | :---: | :---: | :---: |
| **WinDirStat** | 🥇<br>0.56&nbsp;/&nbsp;0.55&nbsp;s | 🥈<br>2.51&nbsp;/&nbsp;2.65&nbsp;s | 🥈<br>7.11&nbsp;/&nbsp;7.26&nbsp;s |
| **WizTree** | 🥈<br>0.66&nbsp;/&nbsp;0.67&nbsp;s | 🥇<br>2.36&nbsp;/&nbsp;2.36&nbsp;s | 🥇<br>6.04&nbsp;/&nbsp;5.82&nbsp;s |
| **SpaceKnife** | 🥉<br>0.79&nbsp;/&nbsp;0.75&nbsp;s | ⚠️ | ⚠️ |

<sub>名次，下一行 冷扫 / 热扫 秒 · rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 未参加 not run.</sub>

### 在你的 README 里显示成绩 · Show a score in your README

徽章由 CI 在每次发布时更新，显示该扫描器的最新名次和综合分。把对应的一行贴进任何 Markdown：

Badges are refreshed on every publish with the scanner's current rank and score. Paste a line into any Markdown file:

```markdown
[![SpaceKnife](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SquirrelDisk](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsquirreldisk.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![dua-cli](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdua.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![gdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![WizTree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwiztree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![WinDirStat](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![BSD du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fbsd-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![GNU du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgnu-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![diskus](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdiskus.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![pdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fpdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![ncdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fncdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![dust](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdust.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![erdtree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Ferdtree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SpaceSniffer](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspacesniffer.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![Sysinternals du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsysinternals-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
```

单个体量：文件名换成 `<扫描器>-<体量>.json`（例如 `gdu-low.json`）；MFT 专栏用 `<扫描器>-mft-<体量>.json`；也可以运行 `python scripts/readme_board.py --snippet <扫描器> [--preset low]` 生成。

One size only: use `<scanner>-<size>.json` (e.g. `gdu-low.json`), or `<scanner>-mft-<size>.json` for the MFT column; `python scripts/readme_board.py --snippet <scanner> [--preset low]` prints the line.

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
| **SpaceKnife** | <code>0.3.3</code><br><code>dev‑38c3b73</code> | Linux<br>macOS<br>Windows | `x86_64`<br>`aarch64` | allocated | 命令行 CLI；参加 MFT 专栏 · in the MFT column |
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

`very-lite` 和 `lite` 的扫描只要零点几秒到几秒，计时里进程启动等固定开销占了大头，所以只作参考，不计入跨体量综合分。

`very-lite` and `lite` scans finish in well under a few seconds, so process start-up dominates their timings; they are for reference only and stay out of the overall score.

---

## 平台与文件系统 · Platforms and filesystems

| 平台<br>Platform | Runner | 文件系统<br>Filesystems |
| :--- | :--- | :--- |
| Linux&nbsp;x64 | `ubuntu-24.04` | ext4 · Btrfs · XFS · ZFS |
| Linux&nbsp;ARM64 | `ubuntu-24.04-arm` | ext4 · Btrfs · XFS · ZFS |
| macOS&nbsp;x64 | `macos-15-intel` | APFS |
| macOS&nbsp;ARM64 | `macos-15` | APFS |
| Windows&nbsp;x64 | `windows-latest` | NTFS · ReFS · Btrfs&nbsp;(WinBtrfs) |
| Windows&nbsp;ARM64 | `windows-11-arm` | NTFS |
| Windows&nbsp;x64&nbsp;MFT | `windows-latest` | NTFS，直接读 `$MFT` · raw `$MFT` |

- **Linux**：测试盘是直接 I/O 的 loop 设备；ZFS 在冷扫前导出再导入存储池。<br>The test volume is a direct-I/O loop device; the ZFS pool is exported and imported before each cold scan.
- **macOS**：APFS 磁盘镜像。<br>An APFS disk image.
- **Windows**：动态 VHDX。同一份数据在 NTFS 和 ReFS 上各跑一次，用来核查有没有偷读 MFT；Btrfs 通过 WinBtrfs 驱动挂载，是实验项。<br>A dynamic VHDX. The same tree runs on NTFS and on ReFS to catch scanners that read the MFT; Btrfs is mounted through the WinBtrfs driver and is experimental.
- **Windows ARM64**：只跑有原生 ARM64 版本的扫描器；Defender 受篡改防护保护，无法关闭。<br>Only scanners with a native ARM64 build run here; Defender stays on because of tamper protection.
- **MFT 专栏 · MFT column**：单独的工作流 `benchmark-mft.yml`，只比较直接读 `$MFT` 的扫描模式。<br>A separate workflow, `benchmark-mft.yml`, compares only the scan modes that read `$MFT` directly.

---

## 怎么算分 · How scoring works

- **冷扫和热扫 · Cold and warm**：每次冷扫前清空测试盘的缓存（Linux、Windows 重新挂载测试盘，ZFS 导出再导入存储池，macOS 用 `purge`）。计时的冷扫不是进程第一次启动，首次启动的杀毒扫描和加载开销不算在内。冷扫之后连续热扫三次，取平均。<br>Before each cold scan the test volume's caches are dropped (Linux and Windows remount the volume, ZFS exports and imports its pool, macOS runs `purge`). The timed cold scan is not the process's first launch, so first-launch antivirus and loading costs stay out. Three warm scans follow and are averaged.
- **平台内归一化 · Normalized per platform**：每个平台内先算相对分（该平台最快 ÷ 自己 × 100），再在平台之间取几何平均，不同 Runner 的硬件快慢在平台内就约掉了。<br>Each platform scores scanners against its fastest (fastest / own × 100), and the platforms are combined by geometric mean, so runner hardware cancels out.
- **均衡指数 · Balanced index**：同时看墙钟时间和占用的 CPU、磁盘资源，跑得快但把机器压得更满的工具占不到便宜。<br>Weighs wall time together with the CPU and disk resources used, so a fast scan that loads the machine harder gains nothing from it.
- **结果核验 · Verification**：只用扫描器自己报告的数字，从不拿标准答案补位；总大小、文件数、各顶层目录的大小都要对得上，漏扫的成绩判为无效。<br>Only the scanner's own numbers count, never the ground truth; its total size, file count and the size of each top-level folder must add up, or the result is invalid.
- **MFT 逃逸 · MFT escapes**：只有在 ReFS 上明显更慢、并且在 NTFS 上冷热同速时，才判定为偷读 MFT，取消 NTFS 成绩。<br>A scanner is disqualified on NTFS for reading the MFT only when it is much slower on ReFS and its NTFS cold and warm times are the same.

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
.github/workflows/  benchmark.yml · benchmark-mft.yml · community.yml
```
