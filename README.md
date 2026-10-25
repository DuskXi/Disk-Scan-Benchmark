# `disk-scanner-bench`

跨平台硬盘空间扫描工具基准测试框架（Cross-Platform Disk Space Scanner Benchmark Framework）。

本框架在 GitHub Actions 的免费 Runner（Linux / macOS / Windows，x86_64 与 ARM64）上，用确定性生成的合成文件树（最多 900 万文件、逻辑上数 TB、物理上只占几 GB）对主流磁盘空间扫描工具做冷扫 / 热扫计时，核对扫描结果是否正确，并按平台归一化后排出跨平台、跨体量的总榜。合成数据会模拟多年使用后的磁盘布局（老化），设计理由与公平性说明见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。

<!-- LEADERBOARD:START -->

## 🏆 排行榜 Leaderboard

![最近更新](https://img.shields.io/badge/%E6%9C%80%E8%BF%91%E6%9B%B4%E6%96%B0-2026--10--25-4c8eda) ![已测体量](https://img.shields.io/badge/%E5%B7%B2%E6%B5%8B%E4%BD%93%E9%87%8F-1%2F6-dbab09) ![扫描器](https://img.shields.io/badge/%E6%89%AB%E6%8F%8F%E5%99%A8-12-6f42c1) ![平台](https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-7-0969da) ![MFT 专栏](https://img.shields.io/badge/MFT%20%E4%B8%93%E6%A0%8F-0%20%E4%B8%AA%E4%BD%93%E9%87%8F-8250df)

> 每个体量单独运行、单独更新：哪个体量跑完就刷新哪一列，其余保持上次的结果。`very-lite` / `lite` 体量过小，计时以进程启动等固定开销为主，只作参考，不计入跨体量综合分。评分方法与数据生成原理见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。

### 跨体量总榜

| 名次 | 扫描器 | **综合分**（low 及以上） | very-lite* | 徽章 |
| :---: | :--- | ---: | :---: | :---: |
| 🥇 | **squirreldisk** | **73.5 *** | 🥇 73.5 | ![squirreldisk](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsquirreldisk.json) |
| 🥈 | **gdu** | **73.0 *** | 🥈 73.0 | ![gdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgdu.json) |
| 🥉 | **dua-cli** | **58.6 *** | 🥉 58.6 | ![dua-cli](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdua.json) |
| 4 | **spaceknife-backend** | **54.3 *** | #4 54.3 | ![spaceknife-backend](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife.json) |
| 5 | **diskus** | **52.9 *** | #5 52.9 | ![diskus](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdiskus.json) |
| 6 | **WinDirStat** | **52.0 *** | #6 52.0 | ![WinDirStat](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat.json) |
| 7 | **WizTree64** | **48.2 *** | #7 48.2 | ![WizTree64](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwiztree.json) |
| 8 | **pdu** | **43.5 *** | #8 43.5 | ![pdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fpdu.json) |
| 9 | **ncdu** | **41.7 *** | #9 41.7 | ![ncdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fncdu.json) |
| 10 | **erdtree** | **36.0 *** | #10 36.0 | ![erdtree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Ferdtree.json) |
| 11 | **dust** | **31.9 *** | #11 31.9 | ![dust](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdust.json) |
| 12 | **SpaceSniffer** | **17.2 *** | #12 17.2 | ![SpaceSniffer](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspacesniffer.json) |

<sub>* 仅供参考的小体量；综合分带 * 的扫描器只有小体量成绩。综合分 = 各体量综合分的几何平均。</sub>

### 各体量详情

<details open>
<summary><b>very-lite</b> · 10 万文件 · 2026-10-25 · <a href="https://github.com/DuskXi/Disk-Scan-Benchmark/actions/runs/40207918748">run 40207918748</a> · commit <code>36e418b</code> · 仅供参考</summary>

| 名次 | 扫描器 | **综合分** | 冷扫 | 热扫 | 均衡指数 | 峰值内存 | 大小误差 | 有效平台 | 平台第一 |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 🥇 | **squirreldisk** | **73.5** | 58.3 | 80.1 | 84.9 | 11 MB | 0.45% | 5/5 | 2 |
| 🥈 | **gdu** | **73.0** | 69.7 | 73.1 | 76.5 | 25 MB | 0.27% | 7/7 | 3 |
| 🥉 | **dua-cli** | **58.6** | 75.7 | 43.0 | 61.8 | 15 MB | 0.00% | 7/7 | 1 |
| 4 | **spaceknife-backend** | **54.3** | 55.6 | 43.3 | 66.3 | 72 MB | 0.06% | 7/7 | - |
| 5 | **diskus** | **52.9** | 71.4 | 39.3 | 52.8 | 14 MB | 0.15% | 6/6 | 1 |
| 6 | **WinDirStat** | **52.0** | 98.1 | 25.8 | 55.4 | 71 MB | 0.31% | 3/3 | - |
| 7 | **WizTree64** | **48.2** | 70.1 | 28.6 | 55.8 | 94 MB | 0.31% | 2/2 | - |
| 8 | **pdu** | **43.5** | 66.2 | 28.0 | 44.4 | 8 MB | 0.15% | 4/4 | - |
| 9 | **ncdu** | **41.7** | 31.4 | 36.8 | 62.7 | 29 MB | 0.00% | 4/4 | - |
| 10 | **erdtree** | **36.0** | 45.5 | 26.4 | 38.9 | 108 MB | 0.05% | 4/4 | - |
| 11 | **dust** | **31.9** | 47.1 | 20.1 | 34.4 | 49 MB | 0.82% | 7/7 | - |
| 12 | **SpaceSniffer** | **17.2** | 30.1 | 6.0 | 28.0 | 86 MB | - | 2/2 | - |

单项第一：**冷扫** WinDirStat（98.1） · **热扫** squirreldisk（80.1） · **均衡** squirreldisk（84.9） · **最省内存** pdu（8 MB） · **最准** dua-cli（误差 0.00%）

**各平台名次（冷扫 / 热扫 秒）**

| 扫描器 | Linux x64 (ext4) | Linux ARM64 (ext4) | macOS x64 (APFS) | macOS ARM64 (APFS) | Win x64 (NTFS) | Win ARM64 (NTFS) | Win x64 (ReFS) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **squirreldisk** | 🥇 0.91 / 0.15 | — | 🥇 0.71 / 0.20 | #4 0.96 / 0.36 | #4 4.13 / 0.38 | — | 🥈 2.17 / 0.37 |
| **gdu** | 🥈 0.86 / 0.18 | 🥈 0.92 / 0.13 | #4 0.50 / 0.40 | #7 0.89 / 0.61 | 🥇 2.78 / 0.32 | 🥇 3.46 / 0.20 | 🥇 2.13 / 0.22 |
| **dua-cli** | #7 0.89 / 0.43 | #6 1.51 / 0.53 | #5 0.54 / 0.59 | 🥇 0.27 / 0.23 | 🥉 2.74 / 0.53 | #4 3.72 / 0.53 | 🥉 2.06 / 0.37 |
| **spaceknife-backend** | #5 1.08 / 0.34 | 🥉 1.69 / 0.30 | #8 0.94 / 0.64 | #5 0.80 / 0.45 | 🥈 2.99 / 0.54 | 🥈 3.89 / 0.47 | #4 2.19 / 0.42 |
| **diskus** | 🥉 0.74 / 0.24 | 🥇 0.64 / 0.09 | 🥈 0.43 / 0.29 | 🥈 0.35 / 0.36 | #7 6.75 / 1.75 | — | #10 3.80 / 3.27 |
| **WinDirStat** | — | — | — | — | #5 2.22 / 0.95 | 🥉 2.42 / 0.69 | #6 2.18 / 1.24 |
| **WizTree64** | — | — | — | — | #6 3.50 / 1.05 | — | #5 2.66 / 0.80 |
| **pdu** | #4 0.82 / 0.28 | — | 🥉 0.42 / 0.36 | — | #8 7.28 / 1.88 | — | #7 2.93 / 1.84 |
| **ncdu** | #6 2.40 / 0.23 | #4 3.82 / 0.21 | #9 0.84 / 1.00 | #6 0.70 / 0.71 | — | — | — |
| **erdtree** | #8 1.04 / 0.39 | #7 1.68 / 0.51 | #7 0.71 / 0.68 | #8 0.99 / 0.96 | — | — | — |
| **dust** | #9 0.93 / 0.50 | #5 1.36 / 0.50 | #6 0.65 / 0.61 | 🥉 0.63 / 0.41 | #9 7.59 / 2.26 | #5 8.89 / 2.40 | #8 3.16 / 2.00 |
| **SpaceSniffer** | — | — | — | — | #10 8.93 / 7.00 | — | #9 5.64 / 2.76 |

<sub>
计分：每个平台内先算相对分，冷扫/热扫 = 该平台最快用时 ÷ 本扫描器用时 × 100，均衡指数 = 本扫描器均衡指数 ÷ 该平台最高 × 100（冷热两次取几何平均）。跨平台取几何平均，各平台硬件快慢在平台内就约掉了。综合分 = 冷扫、热扫、均衡指数三项的几何平均。峰值内存和大小误差取各有效平台的中位数（误差取绝对值）。只计有效成绩：违规、无效、无法运行的平台不计入，但在名次表里标出；—表示该平台不支持或没有原生版本。名次表按该平台三项相对分的几何平均排名。综合分只按扫描器跑过的平台计算，覆盖面看「有效平台」列。
Win ARM64 没有 ReFS 对照任务，那一列的成绩没有经过 NTFS/ReFS 跨文件系统（MFT 逃逸）核查。
</sub>

</details>

### NTFS MFT 专栏

_还没有已发布的 MFT 运行结果（工作流 `benchmark-mft.yml`）。_

### 在你的 README 里显示成绩

徽章由 CI 在每次发布时更新，内容是该扫描器的最新名次和综合分。把下面一行贴进任何 Markdown：

```markdown
[![squirreldisk](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fsquirreldisk.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![gdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fgdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![dua-cli](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdua.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![spaceknife-backend](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspaceknife.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![diskus](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdiskus.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![WinDirStat](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwindirstat.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![WizTree64](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fwiztree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![pdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fpdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![ncdu](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fncdu.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![erdtree](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Ferdtree.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![dust](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fdust.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
[![SpaceSniffer](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FDuskXi%2FDisk-Scan-Benchmark%2Fmain%2Fleaderboard%2Fbadges%2Fspacesniffer.json)](https://github.com/DuskXi/Disk-Scan-Benchmark#-排行榜-leaderboard)
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
