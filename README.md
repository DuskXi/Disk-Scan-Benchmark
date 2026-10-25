# `disk-scanner-bench`

跨平台硬盘空间扫描工具基准测试框架（Cross-Platform Disk Space Scanner Benchmark Framework）。

本框架在 GitHub Actions 的免费 Runner（Linux / macOS / Windows，x86_64 与 ARM64）上，用确定性生成的合成文件树（最多 900 万文件、逻辑上数 TB、物理上只占几 GB）对主流磁盘空间扫描工具做冷扫 / 热扫计时，核对扫描结果是否正确，并按平台归一化后排出跨平台、跨体量的总榜。合成数据会模拟多年使用后的磁盘布局（老化），设计理由与公平性说明见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。

<!-- LEADERBOARD:START -->

## 🏆 排行榜 Leaderboard

![最近更新](https://img.shields.io/badge/%E6%9C%80%E8%BF%91%E6%9B%B4%E6%96%B0-%E2%80%94-4c8eda) ![已测体量](https://img.shields.io/badge/%E5%B7%B2%E6%B5%8B%E4%BD%93%E9%87%8F-0%2F6-dbab09) ![扫描器](https://img.shields.io/badge/%E6%89%AB%E6%8F%8F%E5%99%A8-0-6f42c1) ![平台](https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-0-0969da) ![MFT 专栏](https://img.shields.io/badge/MFT%20%E4%B8%93%E6%A0%8F-0%20%E4%B8%AA%E4%BD%93%E9%87%8F-8250df)

> 每个体量单独运行、单独更新：哪个体量跑完就刷新哪一列，其余保持上次的结果。`very-lite` / `lite` 体量过小，计时以进程启动等固定开销为主，只作参考，不计入跨体量综合分。评分方法与数据生成原理见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md)。

_还没有已发布的运行结果。_

<!-- LEADERBOARD:END -->

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
