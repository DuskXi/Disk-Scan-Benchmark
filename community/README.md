# 社区真实盘成绩 · Community results on real drives

由 `scripts/local_suite/community.py render` 生成，请勿手改。[返回 README](../README.md) · [怎样提交](../docs/LOCAL_SUITE.md)

大家用[本地基准套件](../docs/LOCAL_SUITE.md)在自己的硬盘上跑出的成绩，经维护者核对后收录在这里。提交里只有数字、扫描器版本、系统版本、CPU 和硬盘型号、文件系统与盘的类型，没有路径、文件夹名、文件名、盘符、卷标、计算机名或用户名：套件只复制白名单里的字段并在提交前自查，收录前工作流再按同一份白名单校验。

Results from the [local suite](../docs/LOCAL_SUITE.md) on contributors' own drives, accepted after a maintainer's check. A submission holds numbers, versions, the OS version, CPU and drive models, filesystem and drive type, and nothing else: no paths, folder or file names, drive letters, volume labels, computer or user names.

> ⚖️ **利益声明**：SpaceKnife 和 SpaceKnife (Rust) 属于本基准作者的项目，作者从它们的排名中直接受益，详见[利益声明](../README.md#利益声明--conflict-of-interest)。<br>
> ⚖️ **Conflict of interest**: SpaceKnife and SpaceKnife (Rust) belong to a project of this benchmark's author, who benefits directly from how they rank; see [Conflict of interest](../README.md#利益声明--conflict-of-interest).

> ⚖️ 目前收录的成绩全部来自本基准作者自己的电脑：1 块 NTFS 系统盘（已使用约 1 年）、2 块 ReFS 数据盘（已使用约 3–4 年），都是日常在用的盘。<br>
> ⚖️ Both submissions so far come from this benchmark's author's own machine: 1 NTFS system drive in use for about 1 year, 2 ReFS data drives in use for about 3–4 years, all of them in daily use.

## 综合排名 · Overall（2 份提交、3 块盘）

| 名次 | 扫描器 | 综合分 | 冷扫分 | 热扫分 | 均衡分 | 盘数 |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 🥇 | **SpaceKnife** | <mark>**87.4**</mark> | 90.4 | <mark>**85.1**</mark> | <mark>**86.6**</mark> | 3 |
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

## 所有盘 · All drives

| 提交 | CPU | 用途 | 文件系统 | 类型 | 型号 | 随机读 IOPS | 项数 | 本盘第一 |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | ---: | :--- |
| [#2](https://github.com/DuskXi/Disk-Scan-Benchmark/issues/2) 盘 1 | Intel(R) Core(TM) i9-14900K | 数据盘，已使用约 3–4 年 | refs | NVMe SSD | TOPMORE Aquarius | 33,085 | 2,892k | SpaceKnife |
| [#2](https://github.com/DuskXi/Disk-Scan-Benchmark/issues/2) 盘 2 | Intel(R) Core(TM) i9-14900K | 数据盘，已使用约 3–4 年 | refs | NVMe SSD | TOPMORE Aquarius | 47,539 | 1,114k | SpaceKnife |
| [#1](https://github.com/DuskXi/Disk-Scan-Benchmark/issues/1) 盘 1 | Intel(R) Core(TM) i9-14900K | 系统盘，已使用约 1 年 | ntfs | NVMe SSD | ZHITAI TiPro9000 4TB | 479,609 | 8,050k | SpaceKnife |

## [#2](https://github.com/DuskXi/Disk-Scan-Benchmark/issues/2) · Intel(R) Core(TM) i9-14900K · 24 核 / 32 线程 · 64 GB · Windows 11 26H2 (build 26300.9711)

提交日期 2026-10-27，套件版本 `d6be58b`，2 块盘。

> ⚖️ 这份成绩来自本基准作者自己的电脑：2 块 ReFS 数据盘（已使用约 3–4 年）。作者也是 SpaceKnife 的作者，见[利益声明](../README.md#利益声明--conflict-of-interest)。<br>
> ⚖️ These results come from this benchmark's author's own machine: 2 ReFS data drives in use for about 3–4 years. The author also wrote SpaceKnife: see [Conflict of interest](../README.md#利益声明--conflict-of-interest).

**这份提交的综合**

| 名次 | 扫描器 | 综合分 | 冷扫分 | 热扫分 | 均衡分 | 盘数 |
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

**盘 1**（数据盘，已使用约 3–4 年）：refs · NVMe SSD · PCIe 4.0 x4 · TOPMORE Aquarius · 33,085 IOPS · 3500.0/4100.0 GB · 约 2892k 项

| 名次 | 扫描器 | 版本 | 综合分 | 冷扫分 | 热扫分 | 均衡分 | 冷扫 (s) | 热扫 (s) | 峰值内存 (MB) | 冷扫 CPU (s) | 冷扫读盘次数 | 报告大小 (GB) |
| :---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 🥇 | SpaceKnife | `0.3.4` | <mark>**87.1**</mark> | 75.2 | <mark>**100.0**</mark> | 87.9 | 23.03 | 2.65 | 516 | 43 | 380,729 | 3408.5 |
| 🥈 | dua-cli | `2.46.0` | 83.4 | 99.3 | 58.3 | <mark>**100.0**</mark> | 17.43 | 4.55 | 167 | 50 | 381,891 | 3452.5 |
| 🥉 | gdu | `5.38.0` | 74.7 | <mark>**100.0**</mark> | 47.7 | 87.3 | 17.31 | 5.56 | 67 | 58 | 512,995 | 3427.6 |
| 4 | SquirrelDisk | `2.6.1` | 29.3 | 19.3 | 31.0 | 42.3 | 89.77 | 8.57 | 95 | 36 | 432,753 | 3502.3 |
| 5 | WizTree | `4.33` | 21.0 | 16.0 | 15.9 | 36.5 | 108.08 | 16.71 | 1403 | 122 | 399,650 | 3449.1 |
| 6 | pdu | `0.24.0` | 18.1 | 30.1 | 4.8 | 40.5 | 57.47 | 54.76 | 21 | 365 | 425,866 | 3449.1 |
| 7 | diskus | `0.9.0` | 16.7 | 27.5 | 4.5 | 38.0 | 62.90 | 59.58 | 67 | 430 | 388,402 | 3449.1 |
| 8 | dust | `1.2.6` | 16.4 | 26.7 | 4.3 | 38.1 | 64.96 | 61.23 | 973 | 395 | 390,935 | 3408.5 |
| 9 | WinDirStat | `2.9.3` | 13.2 | 9.7 | 8.1 | 29.5 | 179.33 | 32.82 | 682 | 100 | 380,447 | 3449.1 |
| 10 | erdtree | `3.1.2` | 6.6 | 9.0 | 1.5 | 20.6 | 191.56 | 173.86 | 2423 | 526 | 389,803 | 3448.6 |

**盘 2**（数据盘，已使用约 3–4 年）：refs · NVMe SSD · PCIe 4.0 x4 · TOPMORE Aquarius · 47,539 IOPS · 3010.0/4100.0 GB · 约 1114k 项

| 名次 | 扫描器 | 版本 | 综合分 | 冷扫分 | 热扫分 | 均衡分 | 冷扫 (s) | 热扫 (s) | 峰值内存 (MB) | 冷扫 CPU (s) | 冷扫读盘次数 | 报告大小 (GB) |
| :---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 🥇 | SpaceKnife | `0.3.4` | <mark>**94.8**</mark> | 98.3 | 86.8 | <mark>**100.0**</mark> | 2.46 | 0.45 | 234 | 7 | 99,715 | 3078.6 |
| 🥈 | dua-cli | `2.46.0` | 84.5 | <mark>**100.0**</mark> | 61.9 | 97.5 | 2.42 | 0.62 | 91 | 12 | 99,914 | 3023.7 |
| 🥉 | SquirrelDisk | `2.6.1` | 69.1 | 37.7 | <mark>**100.0**</mark> | 87.4 | 6.42 | 0.39 | 31 | 5 | 47,812 | 3023.9 |
| 4 | gdu | `5.38.0` | 66.7 | 97.5 | 32.4 | 93.7 | 2.48 | 1.19 | 85 | 17 | 100,021 | 3057.8 |
| 5 | WizTree | `4.33` | 31.4 | 28.9 | 15.6 | 68.3 | 8.36 | 2.47 | 556 | 16 | 45,929 | 3021.9 |
| 6 | WinDirStat | `2.9.3` | 14.2 | 10.5 | 6.8 | 40.0 | 23.02 | 5.67 | 306 | 16 | 50,509 | 3021.9 |
| 7 | dust | `1.2.6` | 3.6 | 3.4 | 1.3 | 10.0 | 70.62 | 29.38 | 503 | 112 | 214,744 | 2968.7 |
| 8 | pdu | `0.24.0` | 3.4 | 2.8 | 1.5 | 9.3 | 85.77 | 25.86 | 30 | 110 | 198,832 | 3021.9 |
| 9 | diskus | `0.9.0` | 2.7 | 2.1 | 1.1 | 8.0 | 113.24 | 33.75 | 121 | 158 | 136,338 | 3021.9 |
| 10 | erdtree | `3.1.2` | 1.7 | 1.6 | 0.5 | 6.4 | 154.80 | 78.86 | 1236 | 197 | 136,433 | 3021.8 |

## [#1](https://github.com/DuskXi/Disk-Scan-Benchmark/issues/1) · Intel(R) Core(TM) i9-14900K · 24 核 / 32 线程 · 64 GB · Windows 11 26H2 (build 26300.9711)

提交日期 2026-10-27，套件版本 `3a0708e`，1 块盘。

> ⚖️ 这份成绩来自本基准作者自己的电脑：1 块 NTFS 系统盘（已使用约 1 年）。作者也是 SpaceKnife 的作者，见[利益声明](../README.md#利益声明--conflict-of-interest)。<br>
> ⚖️ These results come from this benchmark's author's own machine: 1 NTFS system drive in use for about 1 year. The author also wrote SpaceKnife: see [Conflict of interest](../README.md#利益声明--conflict-of-interest).

**盘 1**（系统盘，已使用约 1 年）：ntfs · NVMe SSD · PCIe 4.0 x4 · ZHITAI TiPro9000 4TB · 479,609 IOPS · 3040.0/4100.0 GB · 约 8050k 项

| 名次 | 扫描器 | 版本 | 综合分 | 冷扫分 | 热扫分 | 均衡分 | 冷扫 (s) | 热扫 (s) | 峰值内存 (MB) | 冷扫 CPU (s) | 冷扫读盘次数 | 报告大小 (GB) |
| :---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 🥇 | SpaceKnife | `0.3.4` | <mark>**80.7**</mark> | <mark>**100.0**</mark> | 71.1 | 74.0 | 23.76 | 26.42 | 1291 | 276 | 1,067,847 | 3188.6 |
| 🥈 | dua-cli | `2.46.0` | 74.8 | 78.5 | 93.1 | 57.3 | 30.29 | 20.17 | 325 | 355 | 1,482,772 | 3012.7 |
| 🥉 | WizTree | `4.33` | 60.3 | 45.1 | 48.6 | <mark>**100.0**</mark> | 52.64 | 38.63 | 4324 | 58 | 408,467 | 3178.1 |
| 4 | SquirrelDisk | `2.6.1` | 60.3 | 62.9 | 54.6 | 63.8 | 37.81 | 34.42 | 202 | 192 | 1,512,428 | 3150.8 |
| 5 | gdu | `5.38.0` | 38.8 | 21.1 | <mark>**100.0**</mark> | 27.6 | 112.65 | 18.79 | 83 | 402 | 1,857,687 | 3093.2 |
| 6 | WinDirStat | `2.9.3` | 20.0 | 15.1 | 20.2 | 26.1 | 157.76 | 93.17 | 2058 | 334 | 1,272,865 | 3169.5 |
| 7 | dust | `1.2.6` | 5.6 | 7.3 | 4.3 | 5.7 | 326.06 | 435.94 | 3072 | 4037 | 2,864,885 | 3188.6 |
| 8 | pdu | `0.24.0` | 4.4 | 5.0 | 3.1 | 5.6 | 479.47 | 604.45 | 27 | 2770 | 2,888,142 | 3175.3 |
| 9 | diskus | `0.9.0` | 4.3 | 4.8 | 3.7 | 4.6 | 494.55 | 507.89 | 163 | 4172 | 2,812,783 | 3173.6 |
| 10 | erdtree | `3.1.2` | 3.0 | 3.4 | 2.6 | 3.0 | 696.01 | 731.02 | 9955 | 6854 | 3,232,407 | 3546.4 |

