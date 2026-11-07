# 本地基准套件：在自己的硬盘上跑分并提交成绩

CI 上的榜单用的是合成数据和云端磁盘。真实硬盘（尤其是用了多年的系统盘、NAS、机械盘）上的表现可能不一样，
本地套件就是用来收集这类成绩的：在你自己的电脑上，用和 CI 完全相同的扫描器版本扫你指定的盘，
生成一份**不含任何个人信息**的成绩，你检查过后可以提交给本项目，进入 README 的「社区真实盘成绩」。

---

## 1. 运行

需要 Python 3.10+ 和 Git。测 IOPS 需要 Rust（`cargo`，用来编译 `hw-probe`）；ARM64 的 Linux / macOS 上部分扫描器没有预编译版本，也会用 `cargo install` 编译。

```bash
git clone https://github.com/DuskXi/Disk-Scan-Benchmark.git
cd Disk-Scan-Benchmark
```

**Windows**（在**管理员**终端里运行，冷扫需要清空系统文件缓存）：

```powershell
python scripts/local_suite/run_local.py --target D:\ --target E:\
```

**Linux / macOS**（`sudo` 用于清缓存：Linux 写 `/proc/sys/vm/drop_caches`，macOS 运行 `purge`）：

```bash
sudo python3 scripts/local_suite/run_local.py --target /home --target /mnt/data
```

常用参数：

| 参数 | 作用 |
| :--- | :--- |
| `--target <路径>` | 要扫的盘或文件夹，可以写多个 |
| `--scanners gdu,dua,pdu` | 只跑这些扫描器（默认跑本平台所有可用的） |
| `--no-cold` | 不清缓存，只测热扫 |
| `--no-iops` | 不测 IOPS（不往盘里写测试文件） |
| `--warm-runs 3` | 热扫次数 |
| `--timeout 3600` | 单次扫描的超时秒数 |
| `--drive-years 1 --drive-years 3-4` | 每块盘大约用了几年，按 `--target` 的顺序，可以写范围（可选；榜单会注明每块盘的年头） |
| `--by-author` | 仅限本基准作者：把成绩标为作者自己的电脑（作者的 SpaceKnife 也在榜上，见 README 的利益声明） |
| `--submit` | 跑完、你确认后，直接提交成 GitHub Issue |
| `--yes` | 跳过所有确认（声明和提交） |

扫描器会被下载到仓库的 `bin/` 目录，版本和 CI 锁定的完全一样。扫描只读取目录信息，不会修改你的文件。
大盘（几百万个文件）全部扫完可能要几十分钟，期间尽量不要做大量读写。

> 没有管理员 / root 权限时套件照样能跑，但这块盘会被标记为「未能清缓存」，它的冷扫成绩实际上是热扫，
> 社区榜单只会使用它的热扫成绩。

---

## 2. 运行前的准备

套件开始前会把下面这份清单和数据声明打印出来，你输入 `yes` 才会开始：

1. **关掉一直在读写硬盘的软件**，否则冷扫和 IOPS 都会被拖慢：
   - 文件索引（Everything、Windows 搜索索引、正在建索引的 Spotlight）
   - 网盘与同步（OneDrive、Dropbox、坚果云、Syncthing……）
   - 下载与做种（BT / PT 客户端、游戏平台的更新下载）
   - 备份与快照（文件历史、Time Machine、Veeam……）
   - 杀毒软件的全盘扫描（实时防护可以保留，但不要正在全盘扫描）
   - 虚拟机、数据库、编译任务等
2. 笔记本插上电源，用高性能电源模式。
3. 冷扫需要清空系统文件缓存：Windows 用**管理员**终端，Linux / macOS 用 `sudo`。
4. 跑分期间不要用这台电脑做别的事。
5. 每块被测的盘留出 2 GB 以上空闲空间（IOPS 测试用）。

**IOPS 测试会写盘**：每块盘写入一个 1 GB 的临时文件，用 32 个线程跳过系统缓存随机读 5 秒，然后删除。
需要 Rust（`cargo`）来编译 `hw-probe`；没有 Rust 或用了 `--no-iops` 时跳过，这块盘的 IOPS 记为未测。

---

## 3. 收集哪些信息、不收集哪些

成绩文件 `local-results/submission.json` 是按白名单逐个字段拼出来的，提交时工作流还会再按同一份白名单校验一次，
多出任何字段或者字段里出现不允许的字符，提交都会被拒绝。

**会收集：**

| 内容 | 例子 | 说明 |
| :--- | :--- | :--- |
| 操作系统和精确版本 | `Windows 11 25H2 (build 26100.2894)`、`Ubuntu 24.04.1 LTS, kernel 6.8.0-45-generic`、`macOS 15.1 (24B83)` | Windows 精确到 25H2 这一级加内部版本号，Linux 精确到完整内核版本号 |
| 架构 | `x86_64`、`aarch64` | |
| CPU 型号、物理核数、逻辑核数 | `Intel(R) Core(TM) i9-14900K`、`24`、`32` | |
| 内存总量 | `64` | 按 GB 取整 |
| 每块盘的硬盘类型 | `NVMe SSD`、`SATA SSD`、`SATA HDD`、`SAS HDD`、`USB SSD` | |
| 每块盘的连接方式和速度 | `PCIe 4.0 x4`、`SATA 6 Gb/s`、`SAS 12 Gb/s` | Windows 读不到 SATA / SAS 的协商速率，只标 `SATA` / `SAS` |
| 每块盘的随机 4 KiB 读 IOPS | `412345` | 32 路并发、跳过系统缓存测得；见下方说明 |
| 每块盘的文件系统和硬盘型号 | `ntfs`、`TOPMORE Aquarius` | 只有型号，没有序列号 |
| 每块盘的容量和已用空间 | `2050`、`930` | 按 GB 取整（100 GB 以上取整到 10 GB） |
| 每块盘的大致项数 | `1609`（千项） | 各扫描器报告的文件数的中位数 |
| 每块盘是不是系统盘 | `true` / `false` | 只记是或否，自动判断 |
| 每块盘大约用了几年 | `1`、`[3, 4]` | 只有用了 `--drive-years` 才有 |
| 每个扫描器的成绩 | 冷扫 / 热扫毫秒数、峰值内存、CPU 时间、读盘次数、报告的总大小和文件数 | |
| 套件版本和日期 | `36e418b`、`2026-10-25` | |

**绝不收集：** 任何路径或文件名、盘符、卷标、计算机名、用户名、IP、序列号或其他硬件唯一标识、文件内容。

具体做法：

- 扫描时只把盘的路径交给扫描器，成绩里只保留数字；
- 读硬件信息时，CPU 和硬盘型号会过一遍字符白名单（只允许字母、数字、空格和少量标点，最长 64 个字符），
  路径分隔符、冒号、`@` 之类的字符根本放不进去；
- 校验器拒绝任何未知字段，扫描器名必须在注册表里，数字必须在合理范围内；
- 写出成绩之前套件还会自查一遍：成绩里的任何文字只要含有本机的用户名、计算机名、被扫文件夹的名字，
  或者像路径的写法（盘符、网络共享 `\\`、`/home/`、`/Users/`、`/mnt/` 等），就直接停下，不写文件，也不提交。

提交前请自己打开 `local-results/submission.json` 看一遍。用了 `--submit` 时，套件会先显示要提交的内容，你输入 `yes` 才会提交。

---

## 4. 提交

两种方式任选：

1. **Issue（推荐）**：运行时加 `--submit`。装了并登录了 [GitHub CLI](https://cli.github.com/) 的话会直接创建 issue；
   否则套件会告诉你打开 [提交表单](https://github.com/DuskXi/Disk-Scan-Benchmark/issues/new?template=benchmark-submission.yml)，
   把 `submission.json` 的内容粘贴进去。
2. **Pull Request**：把 `submission.json` 改名为 `community/submissions/<你起的名字>.json` 提交 PR。

提交之后：

1. 工作流自动校验，并在 issue 下回复结果（通过 / 不通过以及原因）；
2. 维护者核对后打上 `accepted` 标签；
3. 工作流把成绩存进 `community/submissions/`，刷新 README 的社区榜单和 [community/README.md](../community/README.md)，然后关闭 issue。
   README 里是所有真实盘的综合排名；community/README.md 列出每一份提交、每一块盘的全部成绩和分数。

---

## 5. 分数怎么算

套件跑完生成的 `local-results/submission.md` 和社区榜单用同一套分数（代码在 `scripts/local_suite/scoring.py`），
和 CI 一样只做"同一块盘内"的比较，不同电脑、不同硬盘之间的快慢不会混在一起：

| 分数 | 每块盘上怎么算 |
| :--- | :--- |
| 冷扫分 | 这块盘上最快的冷扫用时 ÷ 自己的 × 100 |
| 热扫分 | 这块盘上最快的热扫用时 ÷ 自己的 × 100 |
| 均衡分 | 和 CI 的均衡指数同一个公式：均衡时间 = 墙钟时间^0.5 ×（CPU 时间 ÷ 逻辑核数 + 读盘次数 ÷ 这块盘的 IOPS）^0.5，这块盘上最好的均衡时间 ÷ 自己的 × 100。跑得快但把 CPU 或硬盘压得更满的工具占不到便宜。成绩里只记了冷扫这一次的 CPU 时间和读盘次数，所以只用冷扫算 |
| 综合分 | 冷扫分、热扫分、均衡分的几何平均 |

多块盘时，每一项先在各块盘之间取几何平均，再合成综合分；每块盘的分量一样，不管它多大、多快。
没能清缓存的盘只算热扫分。一次跑了几块盘，`submission.md` 会先给出这几块盘的综合排名，再列出每块盘的明细。
