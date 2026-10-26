# disk-scanner-bench

**跨平台硬盘空间扫描工具基准测试 · Cross-platform benchmark for disk-space scanners**

[🏆 排行榜 Leaderboard](#-排行榜--leaderboard) · [📐 方法说明 Methodology](docs/METHODOLOGY.md) · [🧪 本地套件 Local suite](docs/LOCAL_SUITE.md) · [➕ 新增扫描器 Add a scanner](#新增扫描器--adding-a-scanner)

在 GitHub Actions 的免费 Runner 上（Linux、macOS、Windows，x86_64 与 ARM64，多种文件系统），用确定性生成的合成文件树（最多 900 万个文件，逻辑上几 TB、物理上只占几 GB）给主流磁盘空间扫描工具做冷扫和热扫计时，核对每个工具自己报告的结果是否完整，再按平台归一化，排出跨平台、跨体量的总榜。合成数据会模拟用了多年的磁盘布局；生成算法只按"像不像真实的盘"取舍，不看任何扫描器的表现。

On free GitHub Actions runners (Linux, macOS and Windows, x86_64 and ARM64, several filesystems), mainstream disk-space scanners are timed on cold and warm scans of a deterministic synthetic tree (up to 9 million files, terabytes in logical size but only a few GB on disk). Each scanner's own output is checked for completeness, scores are normalized within each platform, and the results form one board across platforms and sizes. The test data imitates a drive that has been in use for years; generator choices are judged only by how closely they match real drives, never by how any scanner performs.

<!-- LEADERBOARD:START -->

## 🏆 排行榜 · Leaderboard

![updated](https://img.shields.io/badge/updated-2026--10--26-4c8eda) ![presets](https://img.shields.io/badge/presets-4%2F7-dbab09) ![scanners](https://img.shields.io/badge/scanners-15-6f42c1) ![platforms](https://img.shields.io/badge/platforms-14-0969da) ![MFT presets](https://img.shields.io/badge/MFT%20presets-7-8250df)

> 每个体量单独运行、单独更新：哪个体量跑完就刷新哪一列，其余保持上次的结果。`very-lite` / `lite` 体量过小，计时以进程启动等固定开销为主，只作参考，不计入跨体量综合分。评分方法与数据生成原理见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。
>
> Each size runs and updates on its own: a finished run refreshes its column and the others keep their last result. `very-lite` and `lite` are so small that process start-up dominates the wall clock, so they are for reference only and stay out of the overall score. Scoring and test-data design: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

### 跨体量总榜 · Overall across sizes

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | very‑lite\* | lite\* | low | mid |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**93.0**</mark> | #5&nbsp;59.0 | 🥈&nbsp;85.6 | 🥇&nbsp;<mark>**92.9**</mark> | 🥇&nbsp;<mark>**93.1**</mark> |
| 🥈 | **gdu** | 75.1 | 🥈&nbsp;74.1 | 🥉&nbsp;83.7 | 🥉&nbsp;72.5 | 🥈&nbsp;77.9 |
| 🥉 | **SquirrelDisk** | 74.2 | 🥇&nbsp;<mark>**84.0**</mark> | 🥇&nbsp;<mark>**88.3**</mark> | 🥈&nbsp;82.3 | 🥉&nbsp;66.8 |
| 4 | **dua‑cli** | 54.6 | #7&nbsp;51.3 | #5&nbsp;53.3 | #4&nbsp;53.0 | #5&nbsp;56.2 |
| 5 | **diskus** | 53.7 | #4&nbsp;59.2 | #8&nbsp;48.1 | #5&nbsp;48.3 | #4&nbsp;59.8 |
| 6 | **WizTree** | 50.5 | #9&nbsp;45.5 | #4&nbsp;59.4 | #6&nbsp;46.1 | #6&nbsp;55.2 |
| 7 | **pdu** | 48.6 | #6&nbsp;52.2 | #9&nbsp;45.5 | #8&nbsp;44.9 | #7&nbsp;52.7 |
| 8 | **WinDirStat** | 47.3 | #8&nbsp;50.2 | #7&nbsp;49.3 | #7&nbsp;45.0 | #8&nbsp;49.6 |
| 9 | **GNU&nbsp;du** | 40.4 | #11&nbsp;41.5 | #10&nbsp;39.0 | #9&nbsp;40.2 | #10&nbsp;40.5 |
| 10 | **ncdu** | 40.3 | #10&nbsp;41.6 | #11&nbsp;36.5 | #10&nbsp;39.2 | #9&nbsp;41.4 |
| 11 | **BSD&nbsp;du** | 38.0 | 🥉&nbsp;66.3 | #6&nbsp;52.3 | #11&nbsp;38.0 | — |
| 12 | **dust** | 35.7 | #12&nbsp;35.9 | #12&nbsp;32.1 | #12&nbsp;32.9 | #11&nbsp;38.7 |
| 13 | **erdtree** | 28.7 | #13&nbsp;31.5 | #13&nbsp;27.6 | #13&nbsp;29.1 | #12&nbsp;28.3 |
| 14 | **SpaceSniffer** | 21.3 | #14&nbsp;23.8 | #14&nbsp;21.5 | #14&nbsp;20.5 | #13&nbsp;22.0 |
| 15 | **Sysinternals&nbsp;du** | 8.4 | #15&nbsp;12.0 | #15&nbsp;8.9 | #15&nbsp;8.3 | #14&nbsp;8.5 |

<sub><mark>**高亮**</mark> = 该列最高分 · <mark>**highlighted**</mark> = best in its column.<br><br>综合分 = `low` 及以上各体量综合分的几何平均；\* 为仅供参考的小体量（综合分带 \* 的扫描器只有小体量成绩）。缺平台、缺体量都不扣分也不加分：只用它实际跑过的平台和体量计算，等于把缺的部分按它自己的平均分补上，平台多的工具不会因此更容易刷分，平台少的工具也不会因此被扣分。<br><br>Score = geometric mean of the per-size scores from `low` up; \* marks the reference-only small sizes (a score with \* comes from small sizes only). Missing platforms and sizes neither cost nor earn points: only what a scanner actually ran counts, the same as filling the gaps with its own average, so more platforms do not make a high score easier and fewer do not mark a tool down.</sub>

### 各体量详情 · Results per size

<details open>
<summary><b>mid</b> · 300 万文件 · 3M files · 2026-10-25 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40225628228">run 40225628228</a> · <code>6e409cd</code></summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**93.1**</mark> | 82.1<br><sub>38.0&nbsp;s</sub> | <mark>**100.0**</mark><br><sub>5.44&nbsp;s</sub> | <mark>**98.3**</mark> | 579&nbsp;MB | 0.04% | S·F·Z | 11/13 |
| 🥈 | **gdu** | 77.9 | 81.9<br><sub>46.5&nbsp;s</sub> | 72.3<br><sub>12.1&nbsp;s</sub> | 79.7 | 82&nbsp;MB | 0.17% | S·Z | 13/13 |
| 🥉 | **SquirrelDisk** | 66.8 | 74.2<br><sub>49.6&nbsp;s</sub> | 58.3<br><sub>12.2&nbsp;s</sub> | 69.0 | 75&nbsp;MB | 1.30% | S·F·Z | 6/8 |
| 4 | **diskus** | 59.8 | 78.9<br><sub>48.3&nbsp;s</sub> | 45.5<br><sub>19.3&nbsp;s</sub> | 59.5 | 41&nbsp;MB | <mark>**0.00%**</mark> | S | 13/13 |
| 5 | **dua‑cli** | 56.2 | 73.8<br><sub>51.6&nbsp;s</sub> | 41.6<br><sub>21.1&nbsp;s</sub> | 57.9 | 24&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 13/13 |
| 6 | **WizTree** | 55.2 | 65.7<br><sub>88.2&nbsp;s</sub> | 41.2<br><sub>16.8&nbsp;s</sub> | 62.1 | 1,461&nbsp;MB | 0.90% | S·F·Z | 2/2 |
| 7 | **pdu** | 52.7 | 65.7<br><sub>47.5&nbsp;s</sub> | 40.1<br><sub>13.6&nbsp;s</sub> | 55.5 | 143&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 11/13 |
| 8 | **WinDirStat** | 49.6 | <mark>**100.0**</mark><br><sub>61.6&nbsp;s</sub> | 24.0<br><sub>25.3&nbsp;s</sub> | 50.9 | 637&nbsp;MB | 0.90% | S·F·Z | 3/3 |
| 9 | **ncdu** | 41.4 | 29.6<br><sub>81.6&nbsp;s</sub> | 37.3<br><sub>14.0&nbsp;s</sub> | 64.4 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 8/10 |
| 10 | **GNU&nbsp;du** | 40.5 | 28.9<br><sub>83.7&nbsp;s</sub> | 36.5<br><sub>14.3&nbsp;s</sub> | 63.2 | 13&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 11 | **dust** | 38.7 | 58.1<br><sub>65.6&nbsp;s</sub> | 23.8<br><sub>37.0&nbsp;s</sub> | 42.1 | 1,128&nbsp;MB | 0.46% | S·Z | 13/13 |
| 12 | **erdtree** | 28.3 | 44.8<br><sub>64.2&nbsp;s</sub> | 16.7<br><sub>33.0&nbsp;s</sub> | 30.2 | 2,522&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 10/12 |
| 13 | **SpaceSniffer** | 22.0 | 32.0<br><sub>181&nbsp;s</sub> | 10.4<br><sub>66.7&nbsp;s</sub> | 32.2 | 1,590&nbsp;MB | n/a | IO | 2/2 |
| 14 | **Sysinternals&nbsp;du** | 8.5 | 15.7<br><sub>393&nbsp;s</sub> | 3.1<br><sub>197&nbsp;s</sub> | 12.8 | 155&nbsp;MB | 1.22% | S·F·Z | 3/3 |

未上榜（没有任何平台的有效成绩） · Unranked (no valid result anywhere)：BSD du

单项第一 · Category winners：**冷扫 Cold** WinDirStat (100.0) · **热扫 Warm** SpaceKnife (100.0) · **均衡 Balanced** SpaceKnife (98.3) · **最省内存 Least RAM** ncdu (3 MB) · **最准 Most accurate** diskus (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>34.4&nbsp;/&nbsp;<mark>**4.33**</mark> | 🥇<br>20.2&nbsp;/&nbsp;<mark>**4.58**</mark> | 🥇<br>26.4&nbsp;/&nbsp;<mark>**3.74**</mark> | #4<br>73.8&nbsp;/&nbsp;<mark>**36.5**</mark> |
| **gdu** | 🥉<br>32.1&nbsp;/&nbsp;6.60 | 🥉<br>20.9&nbsp;/&nbsp;6.85 | 🥉<br><mark>**24.2**</mark>&nbsp;/&nbsp;5.86 | 🥈<br>65.5&nbsp;/&nbsp;38.4 |
| **SquirrelDisk** | 🥈<br>32.9&nbsp;/&nbsp;4.59 | 🥈<br><mark>**19.9**</mark>&nbsp;/&nbsp;4.80 | 🥈<br>26.3&nbsp;/&nbsp;3.99 | #7<br>87.0&nbsp;/&nbsp;62.7 |
| **diskus** | #4<br><mark>**29.9**</mark>&nbsp;/&nbsp;9.12 | #4<br>20.0&nbsp;/&nbsp;9.37 | #5<br><mark>**24.2**</mark>&nbsp;/&nbsp;8.47 | 🥇<br><mark>**51.8**</mark>&nbsp;/&nbsp;38.0 |
| **dua‑cli** | #6<br>40.2&nbsp;/&nbsp;13.3 | #6<br>29.0&nbsp;/&nbsp;13.6 | #6<br>31.9&nbsp;/&nbsp;12.5 | #6<br>76.3&nbsp;/&nbsp;43.1 |
| **pdu** | #5<br>36.3&nbsp;/&nbsp;8.70 | #5<br>22.6&nbsp;/&nbsp;9.62 | #4<br>28.4&nbsp;/&nbsp;7.71 | 🥉<br>69.9&nbsp;/&nbsp;37.5 |
| **ncdu** | #9<br>110&nbsp;/&nbsp;12.1 | #9<br>61.1&nbsp;/&nbsp;12.6 | #9<br>79.6&nbsp;/&nbsp;10.4 | #8<br>181&nbsp;/&nbsp;83.2 |
| **GNU&nbsp;du** | #10<br>112&nbsp;/&nbsp;12.3 | #10<br>61.3&nbsp;/&nbsp;12.9 | #8<br>78.5&nbsp;/&nbsp;10.5 | #9<br>206&nbsp;/&nbsp;82.9 |
| **dust** | #8<br>40.1&nbsp;/&nbsp;17.0 | #8<br>29.5&nbsp;/&nbsp;17.0 | #7<br>32.4&nbsp;/&nbsp;15.6 | #5<br>77.3&nbsp;/&nbsp;42.7 |
| **erdtree** | #7<br>44.1&nbsp;/&nbsp;13.1 | #7<br>32.7&nbsp;/&nbsp;13.6 | #10<br>50.7&nbsp;/&nbsp;12.5 | #10<br>138&nbsp;/&nbsp;118 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>29.0&nbsp;/&nbsp;<mark>**2.34**</mark> | 🥈<br>16.9&nbsp;/&nbsp;<mark>**2.39**</mark> | 🥇<br>20.6&nbsp;/&nbsp;<mark>**1.93**</mark> | 🥈<br>35.1&nbsp;/&nbsp;<mark>**18.6**</mark> |
| **gdu** | #4<br><mark>**27.8**</mark>&nbsp;/&nbsp;3.84 | #4<br>14.4&nbsp;/&nbsp;3.76 | #4<br>20.0&nbsp;/&nbsp;3.26 | 🥉<br>31.6&nbsp;/&nbsp;21.0 |
| **diskus** | 🥈<br><mark>**27.8**</mark>&nbsp;/&nbsp;2.72 | 🥇<br><mark>**10.8**</mark>&nbsp;/&nbsp;2.60 | 🥈<br><mark>**19.3**</mark>&nbsp;/&nbsp;2.20 | 🥇<br><mark>**26.8**</mark>&nbsp;/&nbsp;18.9 |
| **dua‑cli** | #8<br>32.8&nbsp;/&nbsp;14.7 | #8<br>24.1&nbsp;/&nbsp;15.8 | #8<br>24.4&nbsp;/&nbsp;15.1 | #6<br>41.9&nbsp;/&nbsp;27.2 |
| **pdu** | 🥉<br>29.2&nbsp;/&nbsp;3.38 | 🥉<br>17.3&nbsp;/&nbsp;3.40 | 🥉<br>20.5&nbsp;/&nbsp;2.95 | #4<br>36.0&nbsp;/&nbsp;19.9 |
| **ncdu** | #5<br>88.5&nbsp;/&nbsp;7.02 | #5<br>46.2&nbsp;/&nbsp;7.20 | #5<br>54.7&nbsp;/&nbsp;5.65 | #7<br>91.4&nbsp;/&nbsp;38.6 |
| **GNU&nbsp;du** | #6<br>95.2&nbsp;/&nbsp;7.41 | #6<br>45.3&nbsp;/&nbsp;7.40 | #6<br>54.9&nbsp;/&nbsp;5.88 | #8<br>91.4&nbsp;/&nbsp;38.9 |
| **dust** | #7<br>31.0&nbsp;/&nbsp;15.5 | #7<br>23.6&nbsp;/&nbsp;14.8 | #7<br>24.0&nbsp;/&nbsp;14.5 | #5<br>41.2&nbsp;/&nbsp;27.2 |
| **erdtree** | #9<br>41.1&nbsp;/&nbsp;16.9 | #9<br>35.6&nbsp;/&nbsp;18.7 | #9<br>33.2&nbsp;/&nbsp;16.9 | #9<br>66.9&nbsp;/&nbsp;73.8 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | ⚠️ | ⚠️ |
| **gdu** | 🥉<br>254&nbsp;/&nbsp;190 | 🥉<br>123&nbsp;/&nbsp;128 |
| **SquirrelDisk** | ⚠️ | ⚠️ |
| **diskus** | 🥈<br>188&nbsp;/&nbsp;<mark>**183**</mark> | 🥈<br>82.5&nbsp;/&nbsp;109 |
| **dua‑cli** | 🥇<br><mark>**172**</mark>&nbsp;/&nbsp;194 | 🥇<br><mark>**76.5**</mark>&nbsp;/&nbsp;<mark>**82.6**</mark> |
| **pdu** | ⚠️ | ⚠️ |
| **ncdu** | ⚠️ | ⚠️ |
| **dust** | #4<br>241&nbsp;/&nbsp;223 | #4<br>151&nbsp;/&nbsp;157 |
| **erdtree** | ⚠️ | ⚠️ |
| **BSD&nbsp;du** | ⚠️ | ⚠️ |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>ReFS |
| :--- | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>40.6&nbsp;/&nbsp;<mark>**3.48**</mark> | 🥇<br>87.5&nbsp;/&nbsp;<mark>**4.70**</mark> | 🥇<br>139&nbsp;/&nbsp;<mark>**13.8**</mark> |
| **gdu** | 🥈<br>41.4&nbsp;/&nbsp;4.18 | 🥈<br>92.2&nbsp;/&nbsp;7.32 | 🥈<br>149&nbsp;/&nbsp;16.7 |
| **SquirrelDisk** | #6<br>64.0&nbsp;/&nbsp;8.19 | — | #6<br>156&nbsp;/&nbsp;73.5 |
| **diskus** | #7<br>89.4&nbsp;/&nbsp;27.1 | #5<br>218&nbsp;/&nbsp;61.4 | #10<br>221&nbsp;/&nbsp;191 |
| **dua‑cli** | 🥉<br>40.0&nbsp;/&nbsp;5.43 | 🥉<br>104&nbsp;/&nbsp;11.9 | 🥉<br>147&nbsp;/&nbsp;17.0 |
| **WizTree** | #4<br>49.0&nbsp;/&nbsp;10.5 | — | #4<br>159&nbsp;/&nbsp;27.0 |
| **pdu** | #8<br>95.5&nbsp;/&nbsp;26.1 | #6<br>250&nbsp;/&nbsp;62.8 | #8<br>190&nbsp;/&nbsp;107 |
| **WinDirStat** | #5<br><mark>**33.1**</mark>&nbsp;/&nbsp;15.1 | #4<br><mark>**69.7**</mark>&nbsp;/&nbsp;19.3 | #5<br><mark>**101**</mark>&nbsp;/&nbsp;55.9 |
| **dust** | #9<br>102&nbsp;/&nbsp;34.1 | #7<br>255&nbsp;/&nbsp;76.7 | #9<br>206&nbsp;/&nbsp;151 |
| **erdtree** | #11<br>124&nbsp;/&nbsp;66.2 | — | #11<br>289&nbsp;/&nbsp;225 |
| **SpaceSniffer** | #10<br>119&nbsp;/&nbsp;47.3 | — | #7<br>275&nbsp;/&nbsp;94.0 |
| **Sysinternals&nbsp;du** | #12<br>209&nbsp;/&nbsp;103 | #8<br>556&nbsp;/&nbsp;206 | #12<br>523&nbsp;/&nbsp;361 |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

<details>
<summary><b>low</b> · 100 万文件 · 1M files · 2026-10-26 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40257046516">run 40257046516</a> · <code>252bc42</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40229660882">run 40229660882</a> 2026-10-25</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**92.9**</mark> | 87.9<br><sub>13.2&nbsp;s</sub> | <mark>**94.9**</mark><br><sub>2.96&nbsp;s</sub> | <mark>**96.1**</mark> | 261&nbsp;MB | 0.28% | S·F·Z | 14/14 |
| 🥈 | **SquirrelDisk** | 82.3 | 79.0<br><sub>17.7&nbsp;s</sub> | 82.4<br><sub>5.03&nbsp;s</sub> | 85.5 | 30&nbsp;MB | 0.81% | S·F·Z | 9/9 |
| 🥉 | **gdu** | 72.5 | 67.7<br><sub>17.1&nbsp;s</sub> | 73.8<br><sub>3.81&nbsp;s</sub> | 76.1 | 48&nbsp;MB | 0.45% | S·Z | 14/14 |
| 4 | **dua‑cli** | 53.0 | 64.8<br><sub>17.9&nbsp;s</sub> | 41.5<br><sub>6.79&nbsp;s</sub> | 55.3 | 15&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 5 | **diskus** | 48.3 | 60.8<br><sub>19.1&nbsp;s</sub> | 38.0<br><sub>7.41&nbsp;s</sub> | 48.8 | 26&nbsp;MB | 0.06% | S | 14/14 |
| 6 | **WizTree** | 46.1 | 57.1<br><sub>30.2&nbsp;s</sub> | 33.5<br><sub>6.44&nbsp;s</sub> | 51.3 | 520&nbsp;MB | 0.58% | S·F·Z | 3/3 |
| 7 | **WinDirStat** | 45.0 | <mark>**92.3**</mark><br><sub>20.7&nbsp;s</sub> | 22.0<br><sub>9.44&nbsp;s</sub> | 45.0 | 247&nbsp;MB | 0.58% | S·F·Z | 4/4 |
| 8 | **pdu** | 44.9 | 53.4<br><sub>21.7&nbsp;s</sub> | 34.9<br><sub>8.07&nbsp;s</sub> | 48.7 | 49&nbsp;MB | 0.06% | S·Z | 14/14 |
| 9 | **GNU&nbsp;du** | 40.2 | 25.9<br><sub>28.6&nbsp;s</sub> | 39.0<br><sub>4.74&nbsp;s</sub> | 64.1 | 9&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 10 | **ncdu** | 39.2 | 26.3<br><sub>36.1&nbsp;s</sub> | 37.0<br><sub>8.58&nbsp;s</sub> | 62.0 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 11 | **BSD&nbsp;du** | 38.0 | 24.6<br><sub>103&nbsp;s</sub> | 38.6<br><sub>71.5&nbsp;s</sub> | 57.9 | 473&nbsp;MB | 17.48% | S·Z | 2/2 |
| 12 | **dust** | 32.9 | 47.5<br><sub>24.4&nbsp;s</sub> | 20.7<br><sub>13.6&nbsp;s</sub> | 36.0 | 391&nbsp;MB | 0.42% | S·Z | 14/14 |
| 13 | **erdtree** | 29.1 | 39.6<br><sub>27.5&nbsp;s</sub> | 20.0<br><sub>14.5&nbsp;s</sub> | 31.2 | 860&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 14 | **SpaceSniffer** | 20.5 | 34.0<br><sub>50.7&nbsp;s</sub> | 8.9<br><sub>24.3&nbsp;s</sub> | 28.5 | 553&nbsp;MB | n/a | IO | 3/3 |
| 15 | **Sysinternals&nbsp;du** | 8.3 | 15.4<br><sub>124&nbsp;s</sub> | 3.1<br><sub>66.4&nbsp;s</sub> | 11.9 | 57&nbsp;MB | 0.86% | S·F·Z | 4/4 |

单项第一 · Category winners：**冷扫 Cold** WinDirStat (92.3) · **热扫 Warm** SpaceKnife (94.9) · **均衡 Balanced** SpaceKnife (96.1) · **最省内存 Least RAM** ncdu (3 MB) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br><mark>**8.99**</mark>&nbsp;/&nbsp;1.65 | 🥇<br><mark>**5.88**</mark>&nbsp;/&nbsp;<mark>**1.64**</mark> | 🥇<br>7.27&nbsp;/&nbsp;1.41 | 🥇<br><mark>**17.0**</mark>&nbsp;/&nbsp;<mark>**13.7**</mark> |
| **SquirrelDisk** | 🥈<br>10.4&nbsp;/&nbsp;<mark>**1.52**</mark> | 🥈<br>6.79&nbsp;/&nbsp;1.72 | 🥈<br>9.19&nbsp;/&nbsp;<mark>**1.37**</mark> | #7<br>24.2&nbsp;/&nbsp;16.8 |
| **gdu** | 🥉<br>9.74&nbsp;/&nbsp;2.12 | 🥉<br>7.06&nbsp;/&nbsp;2.21 | 🥉<br>8.88&nbsp;/&nbsp;1.95 | 🥉<br>18.7&nbsp;/&nbsp;14.5 |
| **dua‑cli** | #6<br>13.0&nbsp;/&nbsp;4.49 | #6<br>9.77&nbsp;/&nbsp;4.59 | #6<br>12.5&nbsp;/&nbsp;4.37 | #6<br>23.4&nbsp;/&nbsp;16.9 |
| **diskus** | #4<br>9.34&nbsp;/&nbsp;3.06 | #4<br>6.59&nbsp;/&nbsp;3.11 | #4<br><mark>**6.98**</mark>&nbsp;/&nbsp;2.82 | 🥈<br>17.6&nbsp;/&nbsp;14.5 |
| **pdu** | #5<br>11.4&nbsp;/&nbsp;2.83 | #5<br>7.61&nbsp;/&nbsp;3.06 | #5<br>9.98&nbsp;/&nbsp;2.58 | #4<br>21.9&nbsp;/&nbsp;14.8 |
| **GNU&nbsp;du** | #10<br>35.5&nbsp;/&nbsp;4.00 | #10<br>21.5&nbsp;/&nbsp;4.20 | #9<br>30.5&nbsp;/&nbsp;3.50 | #10<br>53.2&nbsp;/&nbsp;32.0 |
| **ncdu** | #9<br>35.8&nbsp;/&nbsp;3.94 | #9<br>21.7&nbsp;/&nbsp;4.17 | #8<br>30.6&nbsp;/&nbsp;3.44 | #9<br>53.2&nbsp;/&nbsp;32.0 |
| **dust** | #8<br>12.7&nbsp;/&nbsp;5.54 | #8<br>9.85&nbsp;/&nbsp;5.60 | #7<br>11.3&nbsp;/&nbsp;5.43 | #5<br>23.0&nbsp;/&nbsp;16.3 |
| **erdtree** | #7<br>14.1&nbsp;/&nbsp;4.28 | #7<br>11.3&nbsp;/&nbsp;4.38 | #10<br>18.3&nbsp;/&nbsp;4.20 | #8<br>32.2&nbsp;/&nbsp;21.4 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥈<br>8.43&nbsp;/&nbsp;0.92 | 🥈<br>3.69&nbsp;/&nbsp;0.96 | 🥈<br>6.81&nbsp;/&nbsp;0.79 | 🥈<br>8.52&nbsp;/&nbsp;5.91 |
| **gdu** | #4<br>8.09&nbsp;/&nbsp;1.14 | 🥉<br>5.07&nbsp;/&nbsp;1.19 | 🥉<br>6.59&nbsp;/&nbsp;0.99 | 🥉<br>9.73&nbsp;/&nbsp;6.48 |
| **dua‑cli** | #7<br>9.56&nbsp;/&nbsp;4.96 | #8<br>8.21&nbsp;/&nbsp;5.13 | #8<br>11.3&nbsp;/&nbsp;4.80 | #5<br>13.4&nbsp;/&nbsp;8.50 |
| **diskus** | 🥇<br><mark>**8.03**</mark>&nbsp;/&nbsp;<mark>**0.84**</mark> | 🥇<br><mark>**3.67**</mark>&nbsp;/&nbsp;<mark>**0.86**</mark> | 🥇<br><mark>**6.07**</mark>&nbsp;/&nbsp;<mark>**0.71**</mark> | 🥇<br><mark>**8.21**</mark>&nbsp;/&nbsp;<mark>**5.80**</mark> |
| **pdu** | 🥉<br>8.33&nbsp;/&nbsp;1.08 | #4<br>6.06&nbsp;/&nbsp;1.14 | #4<br>9.59&nbsp;/&nbsp;0.94 | #4<br>11.3&nbsp;/&nbsp;5.93 |
| **GNU&nbsp;du** | #6<br>27.6&nbsp;/&nbsp;2.36 | #6<br>16.0&nbsp;/&nbsp;2.44 | #6<br>25.1&nbsp;/&nbsp;1.90 | #8<br>32.9&nbsp;/&nbsp;12.5 |
| **ncdu** | #5<br>26.3&nbsp;/&nbsp;2.22 | #5<br>16.0&nbsp;/&nbsp;2.36 | #5<br>24.7&nbsp;/&nbsp;1.83 | #9<br>34.8&nbsp;/&nbsp;12.3 |
| **dust** | #8<br>9.86&nbsp;/&nbsp;5.23 | #7<br>8.03&nbsp;/&nbsp;5.28 | #7<br>10.5&nbsp;/&nbsp;4.96 | #6<br>13.6&nbsp;/&nbsp;8.66 |
| **erdtree** | #9<br>11.5&nbsp;/&nbsp;5.69 | #9<br>10.3&nbsp;/&nbsp;6.02 | #9<br>15.6&nbsp;/&nbsp;5.16 | #7<br>19.2&nbsp;/&nbsp;12.4 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SpaceKnife** | 🥈<br>43.3&nbsp;/&nbsp;40.6 | 🥈<br>28.4&nbsp;/&nbsp;24.6 |
| **SquirrelDisk** | 🥇<br><mark>**31.7**</mark>&nbsp;/&nbsp;<mark>**36.7**</mark> | 🥉<br>30.5&nbsp;/&nbsp;28.1 |
| **gdu** | #8<br>137&nbsp;/&nbsp;78.0 | #9<br>92.3&nbsp;/&nbsp;33.7 |
| **dua‑cli** | 🥉<br>59.2&nbsp;/&nbsp;53.0 | 🥇<br><mark>**20.3**</mark>&nbsp;/&nbsp;<mark>**20.7**</mark> |
| **diskus** | #5<br>72.6&nbsp;/&nbsp;54.0 | #5<br>39.8&nbsp;/&nbsp;26.6 |
| **pdu** | #7<br>79.7&nbsp;/&nbsp;88.2 | #6<br>27.6&nbsp;/&nbsp;42.8 |
| **ncdu** | #10<br>149&nbsp;/&nbsp;131 | #10<br>55.8&nbsp;/&nbsp;77.6 |
| **BSD&nbsp;du** | #9<br>124&nbsp;/&nbsp;121 | #8<br>85.5&nbsp;/&nbsp;42.3 |
| **dust** | #6<br>79.8&nbsp;/&nbsp;75.4 | #4<br>33.4&nbsp;/&nbsp;32.1 |
| **erdtree** | #4<br>68.1&nbsp;/&nbsp;55.6 | #7<br>52.2&nbsp;/&nbsp;49.7 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SpaceKnife** | 🥇<br>12.5&nbsp;/&nbsp;<mark>**1.17**</mark> | 🥇<br>36.8&nbsp;/&nbsp;<mark>**1.85**</mark> | 🥇<br>14.6&nbsp;/&nbsp;<mark>**2.88**</mark> | 🥇<br>49.3&nbsp;/&nbsp;<mark>**2.99**</mark> |
| **SquirrelDisk** | #4<br>19.0&nbsp;/&nbsp;2.19 | — | 🥈<br><mark>**12.4**</mark>&nbsp;/&nbsp;3.35 | #4<br>48.2&nbsp;/&nbsp;4.50 |
| **gdu** | 🥈<br>12.5&nbsp;/&nbsp;1.23 | 🥈<br>40.1&nbsp;/&nbsp;2.19 | 🥉<br>19.9&nbsp;/&nbsp;4.54 | 🥈<br>48.9&nbsp;/&nbsp;3.68 |
| **dua‑cli** | 🥉<br><mark>**12.0**</mark>&nbsp;/&nbsp;1.48 | 🥉<br>45.8&nbsp;/&nbsp;3.69 | #5<br>24.8&nbsp;/&nbsp;10.9 | 🥉<br>48.1&nbsp;/&nbsp;4.22 |
| **diskus** | #8<br>30.4&nbsp;/&nbsp;7.72 | #5<br>99.7&nbsp;/&nbsp;18.9 | #11<br>114&nbsp;/&nbsp;103 | #10<br>77.1&nbsp;/&nbsp;60.4 |
| **WizTree** | #6<br>31.0&nbsp;/&nbsp;3.49 | — | #4<br>17.0&nbsp;/&nbsp;11.8 | #5<br>52.2&nbsp;/&nbsp;6.50 |
| **WinDirStat** | #5<br>12.6&nbsp;/&nbsp;4.97 | #4<br><mark>**26.0**</mark>&nbsp;/&nbsp;6.22 | #6<br>16.3&nbsp;/&nbsp;16.1 | #6<br><mark>**34.4**</mark>&nbsp;/&nbsp;15.9 |
| **pdu** | #7<br>30.5&nbsp;/&nbsp;7.81 | #6<br>107&nbsp;/&nbsp;20.1 | #9<br>104&nbsp;/&nbsp;113 | #8<br>66.9&nbsp;/&nbsp;32.5 |
| **dust** | #9<br>33.4&nbsp;/&nbsp;9.42 | #7<br>107&nbsp;/&nbsp;25.3 | #8<br>106&nbsp;/&nbsp;107 | #9<br>70.8&nbsp;/&nbsp;35.5 |
| **erdtree** | #11<br>39.4&nbsp;/&nbsp;18.9 | — | #12<br>104&nbsp;/&nbsp;111 | #11<br>107&nbsp;/&nbsp;61.1 |
| **SpaceSniffer** | #10<br>35.5&nbsp;/&nbsp;14.1 | — | #7<br>39.4&nbsp;/&nbsp;35.0 | #7<br>93.4&nbsp;/&nbsp;28.9 |
| **Sysinternals&nbsp;du** | #12<br>59.6&nbsp;/&nbsp;29.7 | #8<br>205&nbsp;/&nbsp;64.1 | #10<br>118&nbsp;/&nbsp;111 | #12<br>166&nbsp;/&nbsp;92.1 |

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

单项第一 · Category winners：**冷扫 Cold** WinDirStat (93.9) · **热扫 Warm** SquirrelDisk (91.1) · **均衡 Balanced** SpaceKnife (91.9) · **最省内存 Least RAM** ncdu (3 MB) · **最准 Most accurate** dua-cli (±0.00%)

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
<summary><b>very-lite</b> · 10 万文件 · 100k files · 2026-10-26 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40257041859">run 40257041859</a> · <code>252bc42</code> · Win x64 (Btrfs): <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40257041859">run 40257041859</a> 2026-10-26 · 仅供参考 reference only</summary>

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | 冷⁠扫<br>Cold | 热⁠扫<br>Warm | 均⁠衡<br>Balanced | 内⁠存<br>RAM | 误⁠差<br>Error | 核⁠验<br>Check | 平⁠台<br>Platforms |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **SquirrelDisk** | <mark>**84.0**</mark> | 76.7<br><sub>1.21&nbsp;s</sub> | <mark>**85.9**</mark><br><sub>0.30&nbsp;s</sub> | <mark>**89.9**</mark> | 11&nbsp;MB | 2.02% | S·F·Z | 9/9 |
| 🥈 | **gdu** | 74.1 | 68.5<br><sub>1.42&nbsp;s</sub> | 78.0<br><sub>0.27&nbsp;s</sub> | 76.3 | 27&nbsp;MB | 0.27% | S·Z | 12/14 |
| 🥉 | **BSD&nbsp;du** | 66.3 | 72.9<br><sub>0.61&nbsp;s</sub> | 48.4<br><sub>0.65&nbsp;s</sub> | 82.4 | 74&nbsp;MB | 2.78% | S·Z | 2/2 |
| 4 | **diskus** | 59.2 | 72.7<br><sub>1.19&nbsp;s</sub> | 49.5<br><sub>0.39&nbsp;s</sub> | 57.6 | 11&nbsp;MB | 0.15% | S | 14/14 |
| 5 | **SpaceKnife** | 59.0 | 59.4<br><sub>1.45&nbsp;s</sub> | 50.0<br><sub>0.39&nbsp;s</sub> | 69.0 | 77&nbsp;MB | 0.04% | S·F·Z | 14/14 |
| 6 | **pdu** | 52.2 | 53.4<br><sub>1.61&nbsp;s</sub> | 48.1<br><sub>0.40&nbsp;s</sub> | 55.3 | 9&nbsp;MB | 0.15% | S·Z | 14/14 |
| 7 | **dua‑cli** | 51.3 | 64.1<br><sub>1.35&nbsp;s</sub> | 39.7<br><sub>0.49&nbsp;s</sub> | 53.2 | 6&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 14/14 |
| 8 | **WinDirStat** | 50.2 | <mark>**91.6**</mark><br><sub>2.32&nbsp;s</sub> | 26.9<br><sub>1.02&nbsp;s</sub> | 51.4 | 71&nbsp;MB | 0.31% | S·F·Z | 4/4 |
| 9 | **WizTree** | 45.5 | 61.1<br><sub>3.19&nbsp;s</sub> | 30.0<br><sub>1.00&nbsp;s</sub> | 51.5 | 95&nbsp;MB | 0.31% | S·F·Z | 3/3 |
| 10 | **ncdu** | 41.6 | 25.5<br><sub>2.36&nbsp;s</sub> | 43.6<br><sub>0.38&nbsp;s</sub> | 64.6 | <mark>**3&nbsp;MB**</mark> | <mark>**0.00%**</mark> | S·F·Z | 10/10 |
| 11 | **GNU&nbsp;du** | 41.5 | 23.1<br><sub>2.80&nbsp;s</sub> | 45.7<br><sub>0.31&nbsp;s</sub> | 67.6 | 5&nbsp;MB | <mark>**0.00%**</mark> | S·Z | 8/8 |
| 12 | **dust** | 35.9 | 47.6<br><sub>1.81&nbsp;s</sub> | 25.2<br><sub>0.77&nbsp;s</sub> | 38.5 | 41&nbsp;MB | 0.77% | S·Z | 14/14 |
| 13 | **erdtree** | 31.5 | 39.7<br><sub>1.99&nbsp;s</sub> | 24.0<br><sub>0.80&nbsp;s</sub> | 32.8 | 91&nbsp;MB | <mark>**0.00%**</mark> | S·F·Z | 13/13 |
| 14 | **SpaceSniffer** | 23.8 | 34.1<br><sub>5.71&nbsp;s</sub> | 11.6<br><sub>2.60&nbsp;s</sub> | 34.2 | 84&nbsp;MB | n/a | IO | 3/3 |
| 15 | **Sysinternals&nbsp;du** | 12.0 | 19.0<br><sub>11.2&nbsp;s</sub> | 5.3<br><sub>5.16&nbsp;s</sub> | 17.0 | 13&nbsp;MB | 0.33% | S·F·Z | 4/4 |

单项第一 · Category winners：**冷扫 Cold** WinDirStat (91.6) · **热扫 Warm** SquirrelDisk (85.9) · **均衡 Balanced** SquirrelDisk (89.9) · **最省内存 Least RAM** ncdu (3 MB) · **最准 Most accurate** dua-cli (±0.00%)

**各平台名次 · Per platform**

**Linux&nbsp;x64**

| 扫⁠描⁠器<br>Scanner | x64<br>ext4 | x64<br>Btrfs | x64<br>XFS | x64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **SquirrelDisk** | 🥈<br>1.68&nbsp;/&nbsp;<mark>**0.15**</mark> | 🥇<br>0.63&nbsp;/&nbsp;<mark>**0.15**</mark> | 🥇<br>0.78&nbsp;/&nbsp;<mark>**0.16**</mark> | 🥉<br>1.82&nbsp;/&nbsp;0.46 |
| **gdu** | 🥇<br>1.34&nbsp;/&nbsp;0.18 | ⚠️ | 🥉<br>0.78&nbsp;/&nbsp;<mark>**0.16**</mark> | 🥈<br>1.74&nbsp;/&nbsp;<mark>**0.44**</mark> |
| **diskus** | 🥉<br><mark>**1.06**</mark>&nbsp;/&nbsp;0.25 | 🥈<br><mark>**0.49**</mark>&nbsp;/&nbsp;0.22 | 🥈<br><mark>**0.46**</mark>&nbsp;/&nbsp;0.23 | 🥇<br><mark>**1.50**</mark>&nbsp;/&nbsp;0.49 |
| **SpaceKnife** | #5<br>1.59&nbsp;/&nbsp;0.35 | #4<br>1.07&nbsp;/&nbsp;0.26 | #5<br>0.75&nbsp;/&nbsp;0.26 | #4<br>1.76&nbsp;/&nbsp;0.60 |
| **pdu** | #4<br>1.72&nbsp;/&nbsp;0.29 | 🥉<br>0.60&nbsp;/&nbsp;0.20 | #4<br>0.73&nbsp;/&nbsp;0.19 | #5<br>2.12&nbsp;/&nbsp;0.51 |
| **dua‑cli** | #9<br>1.75&nbsp;/&nbsp;0.49 | #6<br>0.70&nbsp;/&nbsp;0.33 | #6<br>0.84&nbsp;/&nbsp;0.33 | #6<br>2.21&nbsp;/&nbsp;0.71 |
| **ncdu** | #7<br>3.97&nbsp;/&nbsp;0.26 | #9<br>1.78&nbsp;/&nbsp;0.33 | #8<br>2.38&nbsp;/&nbsp;0.28 | #9<br>5.42&nbsp;/&nbsp;0.94 |
| **GNU&nbsp;du** | #6<br>3.49&nbsp;/&nbsp;0.25 | #8<br>1.74&nbsp;/&nbsp;0.33 | #10<br>2.48&nbsp;/&nbsp;0.29 | #10<br>5.48&nbsp;/&nbsp;0.94 |
| **dust** | #10<br>1.86&nbsp;/&nbsp;0.54 | #5<br>0.68&nbsp;/&nbsp;0.35 | #7<br>1.09&nbsp;/&nbsp;0.35 | #7<br>2.23&nbsp;/&nbsp;0.74 |
| **erdtree** | #8<br>1.86&nbsp;/&nbsp;0.43 | #7<br>0.84&nbsp;/&nbsp;0.32 | #9<br>1.55&nbsp;/&nbsp;0.32 | #8<br>2.58&nbsp;/&nbsp;0.65 |

**Linux&nbsp;ARM64**

| 扫⁠描⁠器<br>Scanner | ARM64<br>ext4 | ARM64<br>Btrfs | ARM64<br>XFS | ARM64<br>ZFS |
| :--- | :---: | :---: | :---: | :---: |
| **gdu** | 🥈<br>0.81&nbsp;/&nbsp;0.13 | ⚠️ | 🥉<br>0.65&nbsp;/&nbsp;0.12 | 🥉<br>1.20&nbsp;/&nbsp;0.23 |
| **diskus** | 🥇<br><mark>**0.57**</mark>&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥇<br><mark>**0.35**</mark>&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥇<br><mark>**0.50**</mark>&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥇<br><mark>**0.90**</mark>&nbsp;/&nbsp;<mark>**0.16**</mark> |
| **SpaceKnife** | #4<br>0.88&nbsp;/&nbsp;0.29 | #5<br>1.04&nbsp;/&nbsp;0.28 | #4<br>1.17&nbsp;/&nbsp;0.29 | #4<br>1.21&nbsp;/&nbsp;0.38 |
| **pdu** | 🥉<br>1.24&nbsp;/&nbsp;0.10 | 🥈<br>0.54&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥈<br>0.95&nbsp;/&nbsp;<mark>**0.09**</mark> | 🥈<br>1.54&nbsp;/&nbsp;0.18 |
| **dua‑cli** | #8<br>1.42&nbsp;/&nbsp;0.51 | #7<br>0.78&nbsp;/&nbsp;0.53 | #8<br>1.20&nbsp;/&nbsp;0.53 | #5<br>1.72&nbsp;/&nbsp;0.58 |
| **ncdu** | #6<br>3.40&nbsp;/&nbsp;0.22 | #4<br>1.40&nbsp;/&nbsp;0.21 | #5<br>2.69&nbsp;/&nbsp;0.19 | #8<br>3.98&nbsp;/&nbsp;0.46 |
| **GNU&nbsp;du** | #5<br>3.19&nbsp;/&nbsp;0.21 | 🥉<br>1.39&nbsp;/&nbsp;0.21 | #6<br>2.78&nbsp;/&nbsp;0.20 | #7<br>3.76&nbsp;/&nbsp;0.47 |
| **dust** | #7<br>1.34&nbsp;/&nbsp;0.50 | #6<br>0.79&nbsp;/&nbsp;0.50 | #7<br>1.10&nbsp;/&nbsp;0.52 | #6<br>1.93&nbsp;/&nbsp;0.58 |
| **erdtree** | #9<br>1.60&nbsp;/&nbsp;0.52 | #8<br>1.03&nbsp;/&nbsp;0.52 | #9<br>1.81&nbsp;/&nbsp;0.53 | #9<br>2.21&nbsp;/&nbsp;0.61 |

**macOS**

| 扫⁠描⁠器<br>Scanner | x64<br>APFS | ARM64<br>APFS |
| :--- | :---: | :---: |
| **SquirrelDisk** | 🥇<br>0.80&nbsp;/&nbsp;<mark>**0.41**</mark> | 🥉<br>0.41&nbsp;/&nbsp;0.40 |
| **gdu** | #5<br>0.88&nbsp;/&nbsp;0.74 | #10<br>1.22&nbsp;/&nbsp;0.66 |
| **BSD&nbsp;du** | #6<br>0.90&nbsp;/&nbsp;0.97 | 🥈<br>0.41&nbsp;/&nbsp;0.43 |
| **diskus** | 🥉<br>0.68&nbsp;/&nbsp;0.52 | #4<br>0.44&nbsp;/&nbsp;0.36 |
| **SpaceKnife** | #4<br>1.21&nbsp;/&nbsp;0.60 | #7<br>1.06&nbsp;/&nbsp;0.44 |
| **pdu** | #8<br>1.13&nbsp;/&nbsp;0.70 | #5<br>0.49&nbsp;/&nbsp;0.41 |
| **dua‑cli** | #7<br>0.77&nbsp;/&nbsp;0.96 | 🥇<br><mark>**0.36**</mark>&nbsp;/&nbsp;<mark>**0.24**</mark> |
| **ncdu** | #10<br>1.21&nbsp;/&nbsp;1.03 | #9<br>0.95&nbsp;/&nbsp;0.74 |
| **dust** | 🥈<br><mark>**0.54**</mark>&nbsp;/&nbsp;0.56 | #6<br>0.57&nbsp;/&nbsp;0.57 |
| **erdtree** | #9<br>0.94&nbsp;/&nbsp;0.96 | #8<br>0.76&nbsp;/&nbsp;0.65 |

**Windows**

| 扫⁠描⁠器<br>Scanner | x64<br>NTFS | ARM64<br>NTFS | x64<br>Btrfs | x64<br>ReFS |
| :--- | :---: | :---: | :---: | :---: |
| **SquirrelDisk** | #4<br>3.97&nbsp;/&nbsp;0.43 | — | 🥇<br><mark>**1.27**</mark>&nbsp;/&nbsp;<mark>**0.38**</mark> | 🥈<br>2.32&nbsp;/&nbsp;0.37 |
| **gdu** | 🥇<br>3.13&nbsp;/&nbsp;<mark>**0.30**</mark> | 🥇<br>3.69&nbsp;/&nbsp;<mark>**0.21**</mark> | #4<br>2.09&nbsp;/&nbsp;0.42 | 🥇<br>2.32&nbsp;/&nbsp;<mark>**0.24**</mark> |
| **diskus** | #7<br>7.03&nbsp;/&nbsp;1.89 | #5<br>8.20&nbsp;/&nbsp;2.06 | #7<br>3.39&nbsp;/&nbsp;0.77 | #12<br>5.93&nbsp;/&nbsp;5.05 |
| **SpaceKnife** | 🥈<br>3.15&nbsp;/&nbsp;0.51 | 🥈<br>3.82&nbsp;/&nbsp;0.46 | 🥈<br>1.65&nbsp;/&nbsp;0.47 | #4<br>2.44&nbsp;/&nbsp;0.44 |
| **pdu** | #8<br>7.31&nbsp;/&nbsp;1.88 | #6<br>8.46&nbsp;/&nbsp;2.13 | #8<br>4.52&nbsp;/&nbsp;0.77 | #9<br>3.42&nbsp;/&nbsp;3.65 |
| **dua‑cli** | 🥉<br>3.03&nbsp;/&nbsp;0.51 | #4<br>3.73&nbsp;/&nbsp;0.64 | 🥉<br>1.85&nbsp;/&nbsp;0.41 | 🥉<br><mark>**2.13**</mark>&nbsp;/&nbsp;0.42 |
| **WinDirStat** | #5<br><mark>**2.75**</mark>&nbsp;/&nbsp;0.92 | 🥉<br><mark>**2.74**</mark>&nbsp;/&nbsp;0.68 | #5<br>1.62&nbsp;/&nbsp;1.27 | #6<br>2.37&nbsp;/&nbsp;1.36 |
| **WizTree** | #6<br>3.54&nbsp;/&nbsp;0.95 | — | #6<br>3.32&nbsp;/&nbsp;0.92 | #5<br>2.77&nbsp;/&nbsp;1.15 |
| **dust** | #10<br>7.74&nbsp;/&nbsp;2.20 | #7<br>9.06&nbsp;/&nbsp;2.42 | #10<br>7.80&nbsp;/&nbsp;1.11 | #8<br>3.49&nbsp;/&nbsp;3.39 |
| **erdtree** | #11<br>9.78&nbsp;/&nbsp;4.73 | — | #11<br>5.29&nbsp;/&nbsp;2.21 | #10<br>4.90&nbsp;/&nbsp;3.33 |
| **SpaceSniffer** | #9<br>7.72&nbsp;/&nbsp;2.84 | — | #9<br>4.40&nbsp;/&nbsp;2.37 | #7<br>5.49&nbsp;/&nbsp;2.61 |
| **Sysinternals&nbsp;du** | #12<br>15.5&nbsp;/&nbsp;6.63 | #8<br>19.3&nbsp;/&nbsp;6.46 | #12<br>6.40&nbsp;/&nbsp;3.56 | #11<br>8.13&nbsp;/&nbsp;4.64 |

<sub>冷扫、热扫下方的小字是它在有效平台上用时（秒）的几何平均；各平台硬件不同、每个扫描器参加的平台也不同，用时只作参考，名次按相对分 · Small print under Cold / Warm: the geometric mean of its seconds over its valid platforms; hardware and the set of platforms differ between scanners, so it is for reference only and the ranks follow the relative scores. <mark>**高亮**</mark> = 该列最好（分数取最高，内存、误差取最低；各平台表格里是该平台最快的冷扫、热扫用时）· <mark>**Highlighted**</mark> = best in its column (highest score, least RAM and error; in the per-platform tables the platform's fastest cold and warm time). 表头 Columns：内存 RAM = 峰值内存 peak memory · 误差 Error = 大小误差 size error（n/a = 未核验 not verified）· 平台 Platforms = 有效 / 参加的平台数 valid / entered · 核验 Check：S = 总大小 total size · F = 文件数 file count · Z = 各顶层目录 top-level folders · IO = 只有 I/O 次数（图形界面工具没有输出 / GUI tool without output）。<br><br>各平台表格：名次，下一行 冷扫 / 热扫 秒 · Per platform: rank, then cold / warm seconds. ⛔ 无法运行 cannot run · ❌ 违规 disqualified · ⚠️ 无效 invalid · — 不支持 not supported · ❕ 报得比测试树多，成绩照常计入 reported more than the tree holds, still counted。<br><br>少报判无效，多报只警告：扫描器报告的大小、文件数或某个顶层目录明显少于测试树，说明它漏扫了，成绩无效；报得比测试树多（跟进了链接、重复计数等）只标 ❕ 警告，成绩照常计入，因为多扫只会让它更慢、不会占便宜。<br><br>Reporting less invalidates, reporting more only warns: a size, file count or top-level folder clearly below the tree means a skipped part, so the result is invalid; reporting more (links followed, entries counted twice) only gets a ❕ warning and still counts, since the extra work can only slow it down.<br><br>计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。<br><br>缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看有效平台数。<br><br>Scoring: within each platform a scanner gets relative scores first: cold / warm = the platform's fastest time / the scanner's time x 100, balanced = the scanner's balanced index / the platform's best x 100 (geometric mean of cold and warm). Across platforms the scores are combined by geometric mean, so each runner's hardware speed cancels out inside its own platform. Score = geometric mean of cold, warm and balanced. Peak RAM and size error are medians over the valid platforms (absolute error). Only valid results count; disqualified, invalid and unrunnable platforms are left out but marked in the per-platform table, and — means not supported or no native build.<br><br>Missing platforms neither cost nor earn points: a scanner is scored only on the platforms it runs on, which is the same as filling every missing platform with its own average. Running on more platforms therefore does not make a high score easier, and a Windows-only tool is not marked down for lacking Linux or macOS. The flip side: a tool with few platforms was only compared where it runs, which the Platforms column shows.<br><br>Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。<br><br>Win ARM64 has no ReFS counterpart, so its column is not cross-checked for MFT escapes.</sub>

</details>

### NTFS MFT 专栏 · NTFS MFT column

直接读取 NTFS `$MFT` 的扫描模式单独比较，不和上面的普通目录遍历混排；冷热两次耗时应当接近，因为每次都要读完整张 MFT。

Scanners that read the NTFS `$MFT` directly are ranked here, apart from the directory-walking board above; their cold and warm times should be close, since every scan reads the whole MFT.

| # | 扫⁠描⁠器<br>Scanner | **综⁠合⁠分**<br>**Score** | very‑lite\* | lite\* | low | mid | high | very‑high | before‑death |
| :---: | :--- | ---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | **SpaceKnife** | <mark>**100.0**</mark> | 🥉&nbsp;77.0<br><sub>0.98&nbsp;/&nbsp;1.00&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>1.66&nbsp;/&nbsp;1.65&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>3.57&nbsp;/&nbsp;3.65&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>9.52&nbsp;/&nbsp;9.52&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>15.5&nbsp;/&nbsp;15.4&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>28.8&nbsp;/&nbsp;28.5&nbsp;s</sub> | 🥇&nbsp;<mark>**100.0**</mark><br><sub>31.2&nbsp;/&nbsp;31.1&nbsp;s</sub> |
| 🥈 | **WizTree** | 37.3 | 🥈&nbsp;77.4<br><sub>0.96&nbsp;/&nbsp;0.91&nbsp;s</sub> | 🥉&nbsp;56.4<br><sub>2.58&nbsp;/&nbsp;2.60&nbsp;s</sub> | 🥈&nbsp;45.0<br><sub>6.74&nbsp;/&nbsp;6.75&nbsp;s</sub> | 🥈&nbsp;37.7<br><sub>20.5&nbsp;/&nbsp;20.5&nbsp;s</sub> | 🥈&nbsp;36.5<br><sub>33.8&nbsp;/&nbsp;33.9&nbsp;s</sub> | 🥈&nbsp;35.5<br><sub>65.2&nbsp;/&nbsp;65.1&nbsp;s</sub> | 🥉&nbsp;32.8<br><sub>78.2&nbsp;/&nbsp;76.9&nbsp;s</sub> |
| 🥉 | **WinDirStat** | 35.7 | 🥇&nbsp;<mark>**100.0**</mark><br><sub>0.75&nbsp;/&nbsp;0.76&nbsp;s</sub> | 🥈&nbsp;57.8<br><sub>2.73&nbsp;/&nbsp;2.67&nbsp;s</sub> | 🥉&nbsp;41.9<br><sub>7.75&nbsp;/&nbsp;7.96&nbsp;s</sub> | 🥉&nbsp;35.4<br><sub>23.2&nbsp;/&nbsp;23.7&nbsp;s</sub> | 🥉&nbsp;34.5<br><sub>38.7&nbsp;/&nbsp;38.6&nbsp;s</sub> | 🥉&nbsp;34.0<br><sub>73.0&nbsp;/&nbsp;71.8&nbsp;s</sub> | 🥈&nbsp;33.4<br><sub>83.5&nbsp;/&nbsp;78.3&nbsp;s</sub> |

<sub><mark>**高亮**</mark> = 该列最高分 · <mark>**highlighted**</mark> = best in its column.<br><br>综合分 = `low` 及以上各体量 MFT 分数的几何平均，\* 为仅供参考的小体量；每格是该体量的名次和分数，下一行小字是冷扫 / 热扫秒数。⛔ 无法运行 · ❌ 违规 · ⚠️ 无效 · — 未参加。<br><br>Score = geometric mean of the MFT scores from `low` up; \* marks the reference-only small sizes. Each cell: rank and score in that size, then cold / warm seconds in small print. ⛔ cannot run · ❌ disqualified · ⚠️ invalid · — not run.</sub>

### 在你的 README 里显示成绩 · Show a score in your README

徽章由 CI 在每次发布时更新，显示该扫描器的最新名次和综合分。把对应的一行贴进任何 Markdown：

Badges are refreshed on every publish with the scanner's current rank and score. Paste a line into any Markdown file:

```markdown
[![SpaceKnife](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![gdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![SquirrelDisk](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsquirreldisk.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![dua-cli](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdua.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![diskus](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdiskus.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![WizTree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwiztree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![pdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fpdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![WinDirStat](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![GNU du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgnu-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![ncdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fncdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
[![BSD du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fbsd-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜--leaderboard)
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
