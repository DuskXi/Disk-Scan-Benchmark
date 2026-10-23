# `disk-scanner-bench`

跨平台硬盘空间扫描工具基准测试框架（Cross-Platform Disk Space Scanner Benchmark Framework）。

本框架专为 GitHub Actions 公共免费 Runner（Linux / Windows / macOS，含 x86_64 与 ARM64）设计，在 **实际物理磁盘占用 < 1.5 GB** 的条件下，通过确定性拓扑与 **稀疏文件 + 4KB 脏块锚点算法（Dirty-Extent Anchoring）** 无损拟真出包含 **数百万文件节点、20 TB+ 逻辑体积、真实长尾分布与非驻留碎片运行列表（Non-Resident Runlist）** 的复杂文件系统，并借助 **硬件极限基线探针（`hw-probe`）** 对各工具实测耗时进行科学归一化。

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
│   │   ├── windows_vhd.ps1         # NTFS 动态 VHDX 创建、挂载为独立盘符 X: 及卸载清缓存
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

## 2. 可调测试规模（Adjustable Scale）

`fs-mirage` 与 GitHub Actions `workflow_dispatch` 均支持按需调整测试规模（文件数与数据量）：

```bash
cargo run --release --bin fs-mirage -- \
  --root /mnt/bench \
  --files 1000000 \
  --logical-gb 20480 \
  --max-physical-mb 1500 \
  --seed 42 \
  --manifest-out ground_truth.json
```

- `--files`：总生成文件节点数（例如 `10000`、`1000000`、`3000000`）。
- `--logical-gb`：目标逻辑总体积（单位 GiB，例如 `500` 表示 500 GiB，`20480` 表示 20 TiB；若省略则按自然重尾分布生成）。
- `--max-physical-mb`：实际落盘脏块物理空间上限（默认 `1500` MiB，确保适配 GitHub Runner 磁盘配额）。
- `--seed`：确定性 `ChaCha8Rng` 随机种子（相同参数在 Linux / Windows / macOS 下生成 100% 一致的目录拓扑与逻辑大小）。

---

## 3. 新增待测软件规则与版本固定（Scanner Addition Rules & Version Pinning）

所有待测软件均在 [`scripts/wrappers/scanners_registry.json`](scripts/wrappers/scanners_registry.json) 中通过声明式规则管理，无需修改核心调度代码即可扩展新软件并锁定版本。

### 3.1 当前内置软件列表（已锁定近期稳定版 / 多线程版）
| ID | 名称 | 锁定版本 | 支持平台 | 支持架构 | 运行模式 | 校验口径 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `gdu` | `gdu` | `5.38.0` | Linux, macOS, Windows | `x86_64`, `aarch64` | CLI | `allocated` |
| `dua` | `dua-cli` | `2.46.0` | Linux, macOS, Windows | `x86_64`, `aarch64` | CLI | `allocated` |
| `dust` | `dust` | `1.2.6` | Linux, macOS, Windows | `x86_64`, `aarch64` | CLI | `allocated` |
| `ncdu` | `ncdu` | `2.9.2` | Linux, macOS | `x86_64`, `aarch64` | CLI | `allocated` |
| `wiztree` | `WizTree64` | `4.33` | Windows | `x86_64` | CLI (`/export`) | `apparent` |
| `spacesniffer` | `SpaceSniffer` | `2.2.0.27` | Windows | `x86_64` | `win_gui` (原生 x64) | `apparent` |
| `windirstat` | `WinDirStat` | `2.9.3` | Windows | `x86_64` | `win_gui` (2.x 多线程引擎) | `apparent` |

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
   $$\text{CPU Cost Ratio} = \frac{T_{\text{scanner\_warm}}}{T_{\text{baseline\_cpu}}}$$

---

## 5. 跨平台与架构支持矩阵（含 TODO）

- [x] **Linux `x86_64`** (`ubuntu-24.04`)
- [x] **Linux `aarch64` (ARM64)** (`ubuntu-24.04-arm`)
- [x] **macOS `x86_64` (Intel)** (`macos-13`)
- [x] **macOS `aarch64` (Apple Silicon ARM64)** (`macos-14`)
- [x] **Windows `x86_64`** (`windows-latest`)
- [ ] **TODO: Windows `aarch64` (ARM64 Windows)**
  - 待 GitHub Actions 公共 `windows-11-arm` Runner 稳定支持管理员态动态 VHDX 挂载，且 `WizTree` / `SpaceSniffer` / `WinDirStat` 提供统一 ARM64 原生可固定版本分发包后，在 `.github/workflows/benchmark.yml` 与 `scripts/wrappers/scanners_registry.json` 中启用 `windows_aarch64`。
