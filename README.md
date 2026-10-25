# `disk-scanner-bench`

跨平台硬盘空间扫描工具基准测试框架（Cross-Platform Disk Space Scanner Benchmark Framework）。

本框架在 GitHub Actions 的免费 Runner（Linux / macOS / Windows，x86_64 与 ARM64）上，用确定性生成的合成文件树（最多 900 万文件、逻辑上数 TB、物理上只占几 GB）对主流磁盘空间扫描工具做冷扫 / 热扫计时，核对扫描结果是否正确，并按平台归一化后排出跨平台、跨体量的总榜。合成数据会模拟多年使用后的磁盘布局（老化），设计理由与公平性说明见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。

<!-- LEADERBOARD:START -->

## 🏆 排行榜 Leaderboard

![最近更新](https://img.shields.io/badge/%E6%9C%80%E8%BF%91%E6%9B%B4%E6%96%B0-2026--10--25-4c8eda) ![已测体量](https://img.shields.io/badge/%E5%B7%B2%E6%B5%8B%E4%BD%93%E9%87%8F-2%2F6-dbab09) ![扫描器](https://img.shields.io/badge/%E6%89%AB%E6%8F%8F%E5%99%A8-15-6f42c1) ![平台](https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-14-0969da) ![MFT 专栏](https://img.shields.io/badge/MFT%20%E4%B8%93%E6%A0%8F-3%20%E4%B8%AA%E4%BD%93%E9%87%8F-8250df)

> 每个体量单独运行、单独更新：哪个体量跑完就刷新哪一列，其余保持上次的结果。`very-lite` / `lite` 体量过小，计时以进程启动等固定开销为主，只作参考，不计入跨体量综合分。评分方法与数据生成原理见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。

### 跨体量总榜

| 名次 | 扫描器 | **综合分**（low 及以上） | very-lite* | low | 徽章 |
| :---: | :--- | ---: | :---: | :---: | :---: |
| 🥇 | **spaceknife-backend** | **88.3** | #6 53.9 | 🥇 88.3 | ![spaceknife-backend](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife.json) |
| 🥈 | **squirreldisk** | **82.6** | 🥇 86.8 | 🥈 82.6 | ![squirreldisk](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsquirreldisk.json) |
| 🥉 | **dua-cli** | **62.6** | #7 49.6 | 🥉 62.6 | ![dua-cli](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdua.json) |
| 4 | **gdu** | **58.1** | 🥈 72.2 | #4 58.1 | ![gdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgdu.json) |
| 5 | **WizTree64** | **54.5** | #9 46.0 | #5 54.5 | ![WizTree64](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwiztree.json) |
| 6 | **WinDirStat** | **47.1** | #8 48.3 | #6 47.1 | ![WinDirStat](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat.json) |
| 7 | **BSD du** | **41.5** | #4 60.5 | #7 41.5 | ![BSD du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fbsd-du.json) |
| 8 | **GNU du** | **40.8** | #10 42.7 | #8 40.8 | ![GNU du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgnu-du.json) |
| 9 | **diskus** | **39.7** | 🥉 61.3 | #9 39.7 | ![diskus](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdiskus.json) |
| 10 | **pdu** | **39.4** | #5 54.6 | #10 39.4 | ![pdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fpdu.json) |
| 11 | **ncdu** | **33.6** | #11 41.4 | #11 33.6 | ![ncdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fncdu.json) |
| 12 | **dust** | **31.1** | #12 35.3 | #12 31.1 | ![dust](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdust.json) |
| 13 | **erdtree** | **30.0** | #13 29.2 | #13 30.0 | ![erdtree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Ferdtree.json) |
| 14 | **SpaceSniffer** | **20.3** | #14 23.3 | #14 20.3 | ![SpaceSniffer](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspacesniffer.json) |
| 15 | **Sysinternals du** | **8.4** | #15 12.0 | #15 8.4 | ![Sysinternals du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsysinternals-du.json) |

<sub>* 仅供参考的小体量；综合分带 * 的扫描器只有小体量成绩。综合分 = 各体量综合分的几何平均。缺平台、缺体量都不扣分也不加分：只用它实际跑过的平台和体量计算，等于把缺的部分按它自己的平均分补上，平台多的工具不会因此更容易刷分，平台少的工具也不会因此被扣分。</sub>

### 各体量详情

<details open>
<summary><b>low</b> · 100 万文件 · 2026-10-25 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40209205669">run 40209205669</a> · commit <code>fe51464</code></summary>

| 名次 | 扫描器 | **综合分** | 冷扫 | 热扫 | 均衡指数 | 峰值内存 | 大小误差 | 核验 | 有效平台 | 平台第一 |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: | :---: |
| 🥇 | **spaceknife-backend** | **88.3** | 82.2 | 92.5 | 90.5 | 246 MB | 0.67% | 大小 + 文件数 + 区域 | 7/7 | 3 |
| 🥈 | **squirreldisk** | **82.6** | 84.1 | 79.5 | 84.4 | 31 MB | 0.81% | 大小 + 文件数 + 区域 | 5/5 | 3 |
| 🥉 | **dua-cli** | **62.6** | 77.4 | 50.9 | 62.4 | 52 MB | 0.00% | 大小 + 区域 | 7/7 | - |
| 4 | **gdu** | **58.1** | 51.4 | 61.3 | 62.1 | 48 MB | 0.58% | 大小 + 区域 | 7/7 | - |
| 5 | **WizTree64** | **54.5** | 74.6 | 36.9 | 58.7 | 518 MB | 0.58% | 大小 + 文件数 + 区域 | 2/2 | - |
| 6 | **WinDirStat** | **47.1** | 100.0 | 22.3 | 47.0 | 247 MB | 0.58% | 大小 + 文件数 + 区域 | 3/3 | - |
| 7 | **BSD du** | **41.5** | 33.5 | 33.7 | 63.2 | 472 MB | 17.48% | 大小 + 区域 | 2/2 | - |
| 8 | **GNU du** | **40.8** | 28.6 | 37.4 | 63.4 | 9 MB | 0.00% | 大小 + 区域 | 2/2 | - |
| 9 | **diskus** | **39.7** | 54.6 | 29.2 | 39.1 | 27 MB | 0.58% | 大小 | 7/7 | 1 |
| 10 | **pdu** | **39.4** | 53.4 | 27.9 | 41.0 | 50 MB | 0.58% | 大小 + 区域 | 7/7 | - |
| 11 | **ncdu** | **33.6** | 25.2 | 29.0 | 52.0 | 212 MB | 0.00% | 大小 + 文件数 + 区域 | 4/4 | - |
| 12 | **dust** | **31.1** | 49.2 | 18.6 | 32.9 | 391 MB | 0.50% | 大小 + 区域 | 7/7 | - |
| 13 | **erdtree** | **30.0** | 48.7 | 18.3 | 30.4 | 910 MB | 0.38% | 大小 + 文件数 + 区域 | 6/6 | - |
| 14 | **SpaceSniffer** | **20.3** | 33.3 | 8.7 | 28.6 | 553 MB | 未核验 | 仅 I/O | 2/2 | - |
| 15 | **Sysinternals du** | **8.4** | 16.3 | 3.0 | 12.3 | 57 MB | 0.86% | 大小 + 文件数 + 区域 | 3/3 | - |

单项第一：**冷扫** WinDirStat（100.0） · **热扫** spaceknife-backend（92.5） · **均衡** spaceknife-backend（90.5） · **最省内存** GNU du（9 MB） · **最准** dua-cli（误差 0.00%）

**各平台名次（冷扫 / 热扫 秒）**

| 扫描器 | Linux x64 (ext4) | Linux ARM64 (ext4) | macOS x64 (APFS) | macOS ARM64 (APFS) | Win x64 (NTFS) | Win ARM64 (NTFS) | Win x64 (ReFS) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **spaceknife-backend** | 🥈 11.1 / 1.60 | 🥈 8.71 / 0.89 | 🥈 57.1 / 54.3 | 🥈 16.4 / 15.4 | 🥇 27.8 / 2.54 | 🥇 42.1 / 1.73 | 🥇 18.4 / 1.34 |
| **squirreldisk** | 🥇 10.7 / 1.52 | — | 🥇 37.5 / 40.0 | 🥇 15.9 / 14.1 | #6 45.3 / 5.01 | — | #4 18.6 / 2.11 |
| **dua-cli** | #6 12.6 / 4.35 | #8 9.45 / 5.25 | 🥉 56.6 / 57.2 | 🥉 16.3 / 14.7 | 🥉 30.0 / 3.57 | 🥉 45.9 / 3.66 | 🥉 19.4 / 1.82 |
| **gdu** | 🥉 10.1 / 2.14 | #4 8.32 / 1.12 | #10 167 / 92.6 | #10 147 / 57.6 | 🥈 31.1 / 3.00 | 🥈 41.1 / 2.17 | 🥈 19.8 / 1.49 |
| **WizTree64** | — | — | — | — | #5 33.9 / 6.34 | — | #5 21.7 / 3.95 |
| **WinDirStat** | — | — | — | — | #4 23.1 / 8.47 | #4 26.5 / 6.16 | #6 17.7 / 10.2 |
| **BSD du** | — | — | #8 143 / 131 | #7 37.4 / 37.2 | — | — | — |
| **GNU du** | #10 34.7 / 3.97 | #6 26.8 / 2.23 | — | — | — | — | — |
| **diskus** | #4 9.25 / 2.98 | 🥇 8.25 / 0.81 | #5 87.8 / 69.8 | #4 23.9 / 13.9 | #7 68.9 / 18.3 | #5 92.0 / 18.0 | #10 33.6 / 28.7 |
| **pdu** | #5 11.6 / 2.80 | 🥉 8.56 / 1.02 | #7 86.3 / 95.9 | #5 23.6 / 21.4 | #8 71.3 / 19.7 | #6 105 / 19.0 | #7 26.3 / 14.1 |
| **ncdu** | #9 34.6 / 3.91 | #5 26.9 / 2.12 | #9 138 / 134 | #9 88.5 / 87.7 | — | — | — |
| **dust** | #8 12.5 / 5.34 | #7 9.21 / 5.38 | #4 73.6 / 64.1 | #8 36.8 / 31.9 | #9 73.7 / 23.2 | #7 103 / 23.4 | #9 30.0 / 16.4 |
| **erdtree** | #7 13.9 / 4.27 | #9 12.0 / 5.50 | #6 76.6 / 90.2 | #6 27.9 / 24.6 | #11 96.1 / 48.9 | — | #11 40.6 / 24.5 |
| **SpaceSniffer** | — | — | — | — | #10 90.2 / 33.8 | — | #8 40.9 / 13.2 |
| **Sysinternals du** | — | — | — | — | #12 158 / 70.3 | #8 205 / 63.6 | #12 77.4 / 48.0 |

<sub>
计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。
缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看「有效平台」列。
Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。
</sub>

</details>

<details>
<summary><b>very-lite</b> · 10 万文件 · 2026-10-25 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40217165966">run 40217165966</a> · commit <code>6d7ac1c</code> · 仅供参考</summary>

| 名次 | 扫描器 | **综合分** | 冷扫 | 热扫 | 均衡指数 | 峰值内存 | 大小误差 | 核验 | 有效平台 | 平台第一 |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: | :---: |
| 🥇 | **squirreldisk** | **86.8** | 82.8 | 84.9 | 93.1 | 12 MB | 2.02% | 大小 + 文件数 + 区域 | 9/9 | 3 |
| 🥈 | **gdu** | **72.2** | 66.9 | 75.5 | 74.6 | 26 MB | 0.10% | 大小 + 区域 | 11/14 | 5 |
| 🥉 | **diskus** | **61.3** | 74.2 | 52.0 | 59.6 | 11 MB | 0.15% | 大小 | 14/14 | 5 |
| 4 | **BSD du** | **60.5** | 57.2 | 51.6 | 75.2 | 71 MB | 2.78% | 大小 + 区域 | 2/2 | - |
| 5 | **pdu** | **54.6** | 57.5 | 49.4 | 57.3 | 9 MB | 0.15% | 大小 + 区域 | 14/14 | - |
| 6 | **spaceknife-backend** | **53.9** | 54.2 | 44.3 | 65.3 | 71 MB | 0.04% | 大小 + 文件数 + 区域 | 14/14 | - |
| 7 | **dua-cli** | **49.6** | 63.8 | 37.2 | 51.4 | 6 MB | 0.00% | 大小 + 区域 | 14/14 | 1 |
| 8 | **WinDirStat** | **48.3** | 92.3 | 24.8 | 49.2 | 71 MB | 0.31% | 大小 + 文件数 + 区域 | 4/4 | - |
| 9 | **WizTree64** | **46.0** | 66.3 | 28.6 | 51.5 | 95 MB | 0.31% | 大小 + 文件数 + 区域 | 3/3 | - |
| 10 | **GNU du** | **42.7** | 24.6 | 45.5 | 69.5 | 5 MB | 0.00% | 大小 + 区域 | 8/8 | - |
| 11 | **ncdu** | **41.4** | 25.3 | 43.3 | 64.5 | 3 MB | 0.00% | 大小 + 文件数 + 区域 | 10/10 | - |
| 12 | **dust** | **35.3** | 48.8 | 24.0 | 37.7 | 41 MB | 0.77% | 大小 + 区域 | 14/14 | - |
| 13 | **erdtree** | **29.2** | 40.4 | 20.1 | 30.6 | 90 MB | 0.04% | 大小 + 文件数 + 区域 | 10/13 | - |
| 14 | **SpaceSniffer** | **23.3** | 39.4 | 9.8 | 33.1 | 86 MB | 未核验 | 仅 I/O | 3/3 | - |
| 15 | **Sysinternals du** | **12.0** | 19.9 | 5.2 | 16.9 | 13 MB | 0.33% | 大小 + 文件数 + 区域 | 4/4 | - |

单项第一：**冷扫** WinDirStat（92.3） · **热扫** squirreldisk（84.9） · **均衡** squirreldisk（93.1） · **最省内存** ncdu（3 MB） · **最准** dua-cli（误差 0.00%）

**各平台名次（冷扫 / 热扫 秒）**

| 扫描器 | Linux x64 (ext4) | Linux ARM64 (ext4) | Linux x64 (Btrfs) | Linux ARM64 (Btrfs) | Linux x64 (XFS) | Linux ARM64 (XFS) | Linux x64 (ZFS) | Linux ARM64 (ZFS) | macOS x64 (APFS) | macOS ARM64 (APFS) | Win x64 (NTFS) | Win ARM64 (NTFS) | Win x64 (Btrfs) | Win x64 (ReFS) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **squirreldisk** | 🥇 1.07 / 0.15 | — | 🥇 0.78 / 0.15 | — | 🥈 1.13 / 0.15 | — | 🥈 1.82 / 0.46 | — | 🥇 0.50 / 0.35 | 🥈 0.27 / 0.36 | #4 2.32 / 0.38 | — | 🥈 1.57 / 0.53 | 🥈 1.72 / 0.22 |
| **gdu** | 🥈 1.00 / 0.24 | 🥉 0.85 / 0.13 | 🥈 0.67 / 0.17 | ⚠️ 无效 | 🥇 1.01 / 0.16 | 🥉 0.52 / 0.12 | ⚠️ 无效 | ⚠️ 无效 | #6 0.78 / 0.84 | #10 1.53 / 0.63 | 🥇 1.73 / 0.20 | 🥇 5.00 / 0.23 | 🥇 1.60 / 0.36 | 🥇 1.74 / 0.16 |
| **diskus** | 🥉 0.79 / 0.31 | 🥇 0.56 / 0.09 | 🥉 0.57 / 0.26 | 🥇 0.38 / 0.09 | 🥉 0.81 / 0.24 | 🥇 0.32 / 0.07 | 🥇 1.45 / 0.48 | 🥇 0.78 / 0.16 | 🥈 0.43 / 0.38 | 🥉 0.39 / 0.32 | #7 3.94 / 1.08 | #5 12.1 / 2.08 | #7 4.10 / 0.77 | #11 3.06 / 2.26 |
| **BSD du** | — | — | — | — | — | — | — | — | #4 0.74 / 0.65 | #6 0.48 / 0.62 | — | — | — | — |
| **pdu** | #4 1.09 / 0.31 | 🥈 1.22 / 0.09 | #4 0.74 / 0.31 | 🥈 0.58 / 0.10 | #4 1.16 / 0.28 | 🥈 0.52 / 0.09 | 🥉 2.04 / 0.50 | 🥈 1.31 / 0.17 | 🥉 0.49 / 0.40 | #4 0.46 / 0.41 | #8 4.21 / 1.21 | #6 12.0 / 2.23 | #8 4.43 / 0.76 | #7 2.25 / 1.22 |
| **spaceknife-backend** | #5 1.40 / 0.41 | #4 1.57 / 0.32 | #7 1.08 / 0.40 | #5 0.95 / 0.31 | #7 1.60 / 0.34 | #4 0.81 / 0.28 | #4 2.26 / 0.57 | 🥉 1.72 / 0.36 | #7 1.15 / 0.81 | #7 0.61 / 0.42 | 🥉 1.77 / 0.39 | 🥈 5.11 / 0.46 | 🥉 1.82 / 0.59 | #4 1.82 / 0.33 |
| **dua-cli** | #7 1.33 / 0.48 | #8 1.44 / 0.50 | #8 0.92 / 0.51 | #7 0.92 / 0.53 | #8 1.25 / 0.50 | #8 0.72 / 0.50 | #5 2.13 / 0.67 | #5 1.56 / 0.55 | #5 0.70 / 0.71 | 🥇 0.27 / 0.30 | 🥈 1.67 / 0.35 | #4 4.89 / 0.54 | #4 2.01 / 0.70 | 🥉 1.66 / 0.26 |
| **WinDirStat** | — | — | — | — | — | — | — | — | — | — | #5 1.92 / 0.71 | 🥉 3.17 / 0.68 | #5 1.74 / 1.30 | #6 1.78 / 1.10 |
| **WizTree64** | — | — | — | — | — | — | — | — | — | — | #6 2.26 / 0.77 | — | #6 2.92 / 0.98 | #5 2.25 / 0.66 |
| **GNU du** | #9 3.41 / 0.40 | #6 3.27 / 0.21 | #5 1.64 / 0.26 | #4 1.51 / 0.22 | #5 2.40 / 0.21 | #5 1.67 / 0.18 | #8 5.57 / 0.93 | #7 3.39 / 0.45 | — | — | — | — | — | — |
| **ncdu** | #10 3.44 / 0.40 | #5 3.16 / 0.21 | #6 1.68 / 0.26 | 🥉 1.53 / 0.21 | #6 2.56 / 0.23 | #6 1.65 / 0.18 | #7 5.52 / 0.92 | #6 3.46 / 0.44 | #10 1.32 / 1.08 | #8 1.01 / 0.76 | — | — | — | — |
| **dust** | #8 1.26 / 0.57 | #7 1.36 / 0.49 | #9 0.90 / 0.56 | #6 0.84 / 0.50 | #10 1.52 / 0.54 | #7 0.67 / 0.51 | #6 2.13 / 0.70 | #4 1.63 / 0.52 | #8 0.75 / 1.07 | #5 0.44 / 0.44 | #9 4.34 / 1.39 | #7 13.3 / 2.53 | #9 4.81 / 1.09 | #8 2.39 / 1.39 |
| **erdtree** | #6 1.35 / 0.43 | #9 1.60 / 0.53 | #10 1.24 / 0.45 | #8 1.07 / 0.54 | #9 1.77 / 0.43 | #9 1.14 / 0.55 | ⚠️ 无效 | ⚠️ 无效 | #9 0.85 / 1.08 | #9 0.79 / 0.87 | #11 5.62 / 2.95 | — | ⚠️ 无效 | #10 3.11 / 1.84 |
| **SpaceSniffer** | — | — | — | — | — | — | — | — | — | — | #10 4.88 / 2.50 | — | #10 3.83 / 2.63 | #9 3.79 / 1.91 |
| **Sysinternals du** | — | — | — | — | — | — | — | — | — | — | #12 9.05 / 4.61 | #8 22.0 / 6.52 | #11 7.62 / 3.67 | #12 5.82 / 3.37 |

<sub>
计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。
缺平台不扣分、也不加分：每个工具只在它能运行的平台上算分，相当于把它没参加的平台按它自己的平均分补上。所以平台多的工具不会因为参赛平台多而更容易刷高分，只有 Windows 版的工具也不会因为缺 Linux、macOS 被扣分。要注意的是，平台少的工具只和别人比了它能跑的那几个平台，它在其他系统上表现如何，榜单反映不出来；覆盖面看「有效平台」列。
Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。
</sub>

</details>

### NTFS MFT 专栏

直接读取 NTFS `$MFT` 的扫描模式单独比较（冷热两次耗时应接近，因为每次都要读完整个 MFT）。这里的成绩不和上面的普通遍历混排。

| 扫描器 | very-lite | lite | low | 徽章 |
| :--- | :---: | :---: | :---: | :---: |
| **WinDirStat** | 🥇 0.75 / 0.72 s | 🥈 2.95 / 2.88 s | 🥇 5.22 / 5.42 s | ![WinDirStat MFT](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat-mft-low.json) |
| **WizTree64** | 🥈 0.88 / 0.86 s | 🥇 2.55 / 2.74 s | 🥈 4.99 / 4.94 s | ![WizTree64 MFT](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwiztree-mft-low.json) |

<sub>单元格：名次 冷扫 / 热扫 秒。</sub>

### 在你的 README 里显示成绩

徽章由 CI 在每次发布时更新，内容是该扫描器的最新名次和综合分。把下面一行贴进任何 Markdown：

```markdown
[![spaceknife-backend](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![squirreldisk](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsquirreldisk.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![dua-cli](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdua.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![gdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![WizTree64](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwiztree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![WinDirStat](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![BSD du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fbsd-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![GNU du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgnu-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![diskus](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdiskus.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![pdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fpdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![ncdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fncdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![dust](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdust.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![erdtree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Ferdtree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![SpaceSniffer](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspacesniffer.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![Sysinternals du](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsysinternals-du.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
```

只看某个体量：把文件名换成 `<扫描器>-<体量>.json`（例如 `gdu-low.json`）；MFT 专栏用 `<扫描器>-mft-<体量>.json`。也可以用 `python scripts/readme_board.py --snippet <扫描器> [--preset low]` 生成。

<!-- LEADERBOARD:END -->

<!-- COMMUNITY:START -->

## 🖥️ 社区真实盘成绩

_还没有社区提交。_ 用 [本地基准套件](docs/LOCAL_SUITE.md) 在自己的硬盘上跑一遍，再提交成绩，就会出现在这里。

<!-- COMMUNITY:END -->

---

## 1. 核心架构与目录结构

```text
disk-scanner-bench/
├── Cargo.toml                      # Rust Workspace 根配置
├── crates/
│   ├── fs-mirage/                  # 核心模块1：跨平台确定性拟真文件树生成器
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── main.rs             # CLI 入口（支持 --root, --files, --logical-gb, --max-physical-mb, --seed, --manifest-out）
│   │       ├── topology.rs         # 平台无关的 ChaCha8Rng 确定性目录树与文件大小分布生成
│   │       └── materializer/       # 平台相关的底层稀疏文件与 4KB 脏块锚点落盘实现
│   │           ├── mod.rs
│   │           ├── unix.rs         # Linux (ext4) & macOS (APFS) 实现
│   │           └── windows.rs      # Windows (NTFS FSCTL_SET_SPARSE + Non-Resident Runlist) 实现
│   └── hw-probe/                   # 核心模块2：Runner 硬件天花板基线探针与归一化计算器
│       ├── Cargo.toml
│       └── src/
│           ├── main.rs             # 输出 baseline.json 并支持与实测结果合并计算归一化得分
│           ├── io_meta.rs          # B_meta：原生多线程目录遍历极限测试 (read_dir / FindFirstFileExW)
│           ├── io_seq.rs           # B_seq：顺序读取极限带宽测试
│           └── cpu_tree.rs         # B_cpu：纯内存数百万节点构建与排序算力基准
├── scripts/
│   ├── disk-mgr/                   # 核心模块3：虚拟磁盘镜像创建、挂载与冷缓存清除脚本
│   │   ├── linux_loop.sh           # ext4 稀疏镜像创建 (-N 高 inode) 与 /dev/shm RAMDisk 挂载
│   │   ├── windows_vhd.ps1         # NTFS/ReFS 动态 VHDX 创建、挂载为独立盘符 X: 及卸载清缓存
│   │   └── macos_dmg.sh            # APFS sparseimage 创建与挂载
│   ├── wrappers/                   # 核心模块4：待测软件注册表、适配调度与 GUI 自动化监控包装器
│   │   ├── scanners_registry.json  # 待测程序声明式注册表与版本锁定配置
│   │   ├── run_cli_scanners.py     # 统一调度 gdu, dua, dust, ncdu, WizTree, SpaceSniffer, WinDirStat
│   │   └── win_gui_monitor.ps1     # 针对 SpaceSniffer / WinDirStat 的无头计时器 (监控 I/O 与 CPU 归零)
│   └── report_gen.py               # 汇总 Ground Truth 准确度校验、归一化指标，生成 Markdown 报表
└── .github/
    └── workflows/
        └── benchmark.yml           # GitHub Actions 跨平台手动触发 (workflow_dispatch) 自动化流水线
```

---

## 2. 预设规模挡位与自定义测试规模（Scale Presets & Adjustable Scale）

`fs-mirage` 与 GitHub Actions `workflow_dispatch` 内置了 6 个标准化规模挡位（同时支持 `custom` 自定义任意项数与逻辑体积）：

| 挡位 (`--preset`) | 总文件项数 (`--files`) | 逻辑总体积 (`--logical-gb`) | 物理脏块上限 (`--max-physical-mb`) | 适用场景 |
| :--- | ---: | ---: | ---: | :--- |
| **`very-lite`** | `100,000` (10 万项) | `100 GiB` | `< 1.5 GiB` | 快速全平台回归与冒烟验证（当前触发） |
| **`lite`** | `400,000` (40 万项) | `350 GiB` | `< 1.5 GiB` | 轻量级日常开发构建与主干回归 |
| **`low`** | `1,000,000` (100 万项) | `500 GiB` | `< 1.5 GiB` | 标准百万节点基准测试（当前触发） |
| **`mid`** | `3,000,000` (300 万项) | `1 TiB` (`1024 GiB`) | `< 1.5 GiB` | 中高负载目录索引与内存树压测 |
| **`high`** | `5,000,000` (500 万项) | `2 TiB` (`2048 GiB`) | `< 1.5 GiB` | 重度五百万节点并发遍历压测 |
| **`very-high`** | `9,000,000` (900 万项) | `3 TiB` (`3072 GiB`) | `< 1.5 GiB` | 极限九百万节点天花板压测 |

```bash
# 使用预设挡位（如 low: 100万项 / 500GB）
cargo run --release --bin fs-mirage -- \
  --root /mnt/bench \
  --preset low \
  --seed 42 \
  --manifest-out ground_truth.json

# 或使用 custom 自定义任意文件项数与逻辑 GB 数
cargo run --release --bin fs-mirage -- \
  --root /mnt/bench \
  --preset custom \
  --files 1000000 \
  --logical-gb 500 \
  --max-physical-mb 1500 \
  --seed 42 \
  --manifest-out ground_truth.json
```

---

## 3. 新增待测软件规则与版本固定（Scanner Addition Rules & Version Pinning）

所有待测软件均在 [`scripts/wrappers/scanners_registry.json`](scripts/wrappers/scanners_registry.json) 中通过声明式规则管理，无需修改核心调度代码即可扩展新软件并锁定版本。

### 3.1 当前参加测试的扫描器

下表由 CI 根据 [`scanners_registry.json`](scripts/wrappers/scanners_registry.json) 自动生成。

<!-- SCANNERS:START -->

| 扫描器 | 锁定版本 | 平台 | 架构 | 大小口径 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **gdu** | `5.38.0` | Linux, macOS, Windows | `x86_64`, `aarch64` | allocated（Windows 上为 apparent） | 命令行 |
| **dua-cli** | `2.46.0` | Linux, macOS, Windows | `x86_64`, `aarch64` | allocated | 命令行 |
| **dust** | `1.2.6` | Linux, macOS, Windows | `x86_64`, `aarch64` | allocated（Windows 上为 apparent） | 命令行 |
| **ncdu** | `2.9.2` | Linux, macOS | `x86_64`, `aarch64` | allocated | 命令行 |
| **WizTree64** | `4.33` | Windows | `x86_64` | apparent | 命令行，参加 MFT 专栏 |
| **SpaceSniffer** | `2.2.0.27` | Windows | `x86_64` | apparent | 图形界面 |
| **WinDirStat** | `2.9.3` | Windows | `x86_64`, `aarch64` | apparent | 命令行，参加 MFT 专栏 |
| **spaceknife-backend** | `0.3.3 dev-38c3b73 (runs 40188287823, 40188287831)` | Linux, macOS, Windows | `x86_64`, `aarch64` | allocated | 命令行，参加 MFT 专栏 |
| **squirreldisk** | `2.6.1` | Linux, macOS, Windows | `x86_64`, `aarch64` | allocated | 命令行 |
| **GNU du** | `coreutils 9.4 (ubuntu-24.04 image)` | Linux | `x86_64`, `aarch64` | allocated | 命令行；系统基线：单线程，硬链接只算一次，计入目录块 |
| **BSD du** | `macOS system /usr/bin/du` | macOS | `x86_64`, `aarch64` | allocated | 命令行；系统基线：单线程，硬链接只算一次，精度为 KiB |
| **Sysinternals du** | `1.62` | Windows | `x86_64`, `aarch64` | allocated | 命令行；微软 Sysinternals 出品；单线程；CSV 同时给出大小和实际占用 |
| **pdu** | `0.24.0` | Linux, macOS, Windows | `x86_64`, `aarch64` | allocated（Windows 上为 apparent） | 命令行；parallel-disk-usage；用 --threads=max，因为默认的 auto 把虚拟盘误判成机械盘时会降到 1 线程；硬链接去重（-H）和块大小只在 Unix 上有 |
| **diskus** | `0.9.0` | Linux, macOS, Windows | `x86_64`, `aarch64` | allocated（Windows 上为 apparent） | 命令行；只输出总大小；默认线程数为核数 × 3；Windows 版只报逻辑大小 |
| **erdtree** | `3.1.2` | Linux, macOS, Windows | `x86_64`, `aarch64` | allocated | 命令行；加 -. 和 -i 才会计入隐藏文件和被 .gitignore 忽略的文件；整棵树常驻内存 |

<sub>未参加：TreeSizeFree（原因见注册表）。</sub>

<!-- SCANNERS:END -->


### 3.2 新增待测程序规范
在 [`scripts/wrappers/scanners_registry.json`](scripts/wrappers/scanners_registry.json) 的 `"scanners"` 数组中添加如下结构的对象即可自动纳入安装与评测流水线：

```json
{
  "id": "my_scanner",
  "name": "MyScanner",
  "version": "1.0.0",
  "enabled": true,
  "runner_type": "cli",
  "platforms": ["linux", "macos", "windows"],
  "architectures": ["x86_64", "aarch64"],
  "size_metric": "allocated",
  "command_template": ["{bin}", "--no-ui", "{path}"],
  "output_parser": "human_last_line",
  "install": {
    "linux_x86_64": "https://example.com/releases/download/v1.0.0/my_scanner-linux-amd64.tar.gz",
    "linux_aarch64": "https://example.com/releases/download/v1.0.0/my_scanner-linux-arm64.tar.gz",
    "macos_x86_64": "https://example.com/releases/download/v1.0.0/my_scanner-darwin-amd64.tar.gz",
    "macos_aarch64": "https://example.com/releases/download/v1.0.0/my_scanner-darwin-arm64.tar.gz",
    "windows_x86_64": "https://example.com/releases/download/v1.0.0/my_scanner-windows-amd64.zip"
  }
}
```

---

## 4. 归一化数学模型

1. **系统调用压榨率（Cold Cache I/O Efficiency）**：
   $$\eta_{\text{io}} = \frac{\text{Scanner Cold Speed (files/sec)}}{B_{\text{meta}}} \times 100\%$$
   - 标准系统调用扫描器介于 `0% ~ 100%` 之间；绕过文件 API 直接解析 `$MFT` 的工具（如 `WizTree`）可超过 `500%`。
2. **热缓存归一化算力开销（Warm Cache Normalized CPU Cost）**：
   $$\text{CPU Cost Ratio} = \frac{T_{\text{scanner-warm}}}{T_{\text{baseline-cpu}}}$$

---

## 5. 平台与文件系统

| 平台 | Runner | 文件系统 | 说明 |
| :--- | :--- | :--- | :--- |
| Linux x64 | `ubuntu-24.04` | ext4 | 直接 I/O 的 loop 设备 |
| Linux ARM64 | `ubuntu-24.04-arm` | ext4 | 同上 |
| macOS x64 | `macos-15-intel` | APFS | 磁盘镜像 |
| macOS ARM64 | `macos-15` | APFS | 磁盘镜像 |
| Windows x64 | `windows-latest` | NTFS、ReFS | 动态 VHDX；NTFS/ReFS 交叉核查 MFT 逃逸 |
| Windows ARM64 | `windows-11-arm` | NTFS | 只跑有原生 ARM64 版本的扫描器；Defender 因篡改防护无法关闭 |
| Windows x64（MFT 专栏） | `windows-latest` | NTFS | 单独的工作流 `benchmark-mft.yml`，只比较直接读 `$MFT` 的模式 |
