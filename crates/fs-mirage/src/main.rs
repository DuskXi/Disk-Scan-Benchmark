mod atime;
mod materializer;
mod profile;
mod topology;

use anyhow::{Context, Result};
use clap::{Parser, ValueEnum};
use std::fs;
use std::path::PathBuf;
use std::time::Instant;
#[cfg(unix)]
use topology::GroundTruthManifest;
use topology::{EntryKind, ScalePreset, TopologyConfig, TopologyPlan};

#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, ValueEnum, Debug)]
enum CliPreset {
    /// 100,000 items (10万项), 100 GB logical size
    #[value(name = "very-lite")]
    VeryLite,
    /// 400,000 items (40万项), 350 GB logical size
    #[value(name = "lite")]
    Lite,
    /// 1,000,000 items (100万项), 500 GB logical size
    #[value(name = "low")]
    Low,
    /// 3,000,000 items (300万项), 1 TB (1024 GB) logical size
    #[value(name = "mid")]
    Mid,
    /// 5,000,000 items (500万项), 2 TB (2048 GB) logical size
    #[value(name = "high")]
    High,
    /// 9,000,000 items (900万项), 3 TB (3072 GB) logical size
    #[value(name = "very-high")]
    VeryHigh,
    /// 14,000,000 items (1400万项), 3.60 TB (3686.4 GB) logical size: a mainstream 4 TB NVMe drive (about 3.63 TB
    /// as the OS shows it) about 99% full
    #[value(name = "before-death")]
    BeforeDeath,
    /// Custom scale via --files and --logical-gb
    #[value(name = "custom")]
    Custom,
}

impl From<CliPreset> for ScalePreset {
    fn from(val: CliPreset) -> Self {
        match val {
            CliPreset::VeryLite => ScalePreset::VeryLite,
            CliPreset::Lite => ScalePreset::Lite,
            CliPreset::Low => ScalePreset::Low,
            CliPreset::Mid => ScalePreset::Mid,
            CliPreset::High => ScalePreset::High,
            CliPreset::VeryHigh => ScalePreset::VeryHigh,
            CliPreset::BeforeDeath => ScalePreset::BeforeDeath,
            CliPreset::Custom => ScalePreset::Custom,
        }
    }
}

#[derive(Parser, Debug)]
#[command(
    name = "fs-mirage",
    about = "Cross-platform deterministic realistic file tree generator with dirty-extent sparse anchoring"
)]
struct Args {
    /// Root directory where the synthetic file tree will be materialized
    #[arg(long)]
    root: PathBuf,

    /// Benchmark scale preset tier (very-lite, lite, low, mid, high, very-high, before-death, custom)
    #[arg(long, value_enum)]
    preset: Option<CliPreset>,

    /// Total number of file items to generate (overrides preset if specified)
    #[arg(long)]
    files: Option<usize>,

    /// Target total logical size in GiB (overrides preset if specified)
    #[arg(long)]
    logical_gb: Option<f64>,

    /// Deterministic PRNG seed (ChaCha8Rng)
    #[arg(long, default_value_t = 42)]
    seed: u64,

    /// Maximum physical disk budget in MiB (default: 1500 MiB)
    #[arg(long, default_value_t = 1500)]
    max_physical_mb: u64,

    /// Do not preallocate the large media files (keep them sparse). Use on filesystems where preallocation would
    /// really write zeros (e.g. ReFS) or where the volume is smaller than the logical size (tmpfs RAM disks).
    #[arg(long)]
    no_prealloc: bool,

    /// Skip the lived-in volume extras (compressed dirs, alternate streams, attributes) on Windows.
    #[arg(long)]
    no_realism: bool,

    /// Only plan the topology and print its statistics (no files are written).
    #[arg(long)]
    plan_only: bool,

    /// Unix: re-read the allocation of an already generated tree (same --root, --preset/--profile, --seed and size
    /// options) and update the allocation fields of the existing --manifest-out. Used after a remount on Btrfs, XFS
    /// and ZFS, whose block counts settle only after the data is flushed.
    #[arg(long)]
    recount_alloc: bool,

    /// Generate a tree with the shape and name style of a real tree, from a profile written by scripts/profile/fs_profile.py.
    #[arg(long)]
    profile: Option<PathBuf>,

    /// Output path for the Ground Truth manifest JSON
    #[arg(long, default_value = "ground_truth.json")]
    manifest_out: PathBuf,

    /// Also create this many "ballast" files on the same volume, outside --root, before the benchmark tree. They are
    /// never scanned and not in the manifest. A real tree is scanned inside a volume that holds millions of other
    /// files, and that can make directory enumeration more expensive than on a volume that holds nothing but the
    /// benchmark tree.
    #[arg(long, default_value_t = 0)]
    ballast_files: usize,

    /// Where the ballast tree goes (default: a "ballast" folder next to --root, e.g. X:\ballast for X:\bench).
    #[arg(long)]
    ballast_root: Option<PathBuf>,

    /// Make every ballast file empty: same names and folder shape, no allocation, much faster to create.
    #[arg(long)]
    ballast_empty: bool,

    /// Set access times under --root two days back (modification times kept) and exit, without generating anything:
    /// every folder, and every file whose access time moved since the last reset (Linux, macOS; Windows: every file).
    /// For the timed scans, which run with access-time updates on.
    #[arg(long)]
    reset_atime: bool,

    /// With --reset-atime: set every file back too, not only those whose access time moved. For volumes where the
    /// listing's copy of a file's times may lag behind the file's own (Windows, while scans update access times).
    #[arg(long)]
    reset_atime_all: bool,
}

/// Ballast plan: the same generator as the benchmark tree (other seed), optionally with every file emptied.
#[cfg(unix)]
fn recount(args: &Args, plan: &TopologyPlan) -> Result<()> {
    let text = fs::read_to_string(&args.manifest_out).with_context(|| {
        format!(
            "--recount-alloc needs the manifest of the generated tree at {}",
            args.manifest_out.display()
        )
    })?;
    let mut manifest: GroundTruthManifest =
        serde_json::from_str(&text).context("parsing the existing manifest")?;
    let before = manifest.allocated_size_bytes;
    let counts = materializer::recount_allocation(&args.root, plan);
    manifest.allocated_size_bytes = counts.total;
    manifest.allocated_files_only_bytes = counts.files_only;
    manifest.allocated_size_with_hardlinks_bytes = counts.total + counts.hardlink_extra;
    for (name, zone) in manifest.zones.iter_mut() {
        zone.allocated_size_bytes = counts.zones.get(name).copied().unwrap_or(0);
        zone.allocated_files_only_bytes = counts.zone_files.get(name).copied().unwrap_or(0);
    }
    fs::write(&args.manifest_out, serde_json::to_string_pretty(&manifest)?)?;
    println!(
        "[fs-mirage] Allocation recounted: {:.2} MiB -> {:.2} MiB ({})",
        before as f64 / (1024.0 * 1024.0),
        counts.total as f64 / (1024.0 * 1024.0),
        args.manifest_out.display()
    );
    Ok(())
}

#[cfg(not(unix))]
fn recount(_args: &Args, _plan: &TopologyPlan) -> Result<()> {
    anyhow::bail!("--recount-alloc is only needed (and supported) on Unix filesystems")
}

fn ballast_plan(
    args: &Args,
    cfg: &TopologyConfig,
    prof: Option<&profile::Profile>,
) -> TopologyPlan {
    let bcfg = TopologyConfig {
        total_files: args.ballast_files,
        seed: cfg.seed ^ 0x00BA_11A5_7BA1_1A57,
        ..cfg.clone()
    };
    let mut plan = match prof {
        Some(p) => profile::generate_from_profile(&bcfg, p),
        None => TopologyPlan::generate(&bcfg),
    };
    if args.ballast_empty {
        for entry in &mut plan.regular_files {
            if let EntryKind::RegularFile {
                logical_size,
                dirty_blocks,
                preallocate,
                ..
            } = &mut entry.kind
            {
                *logical_size = 0;
                *dirty_blocks = 0;
                *preallocate = false;
            }
        }
    }
    plan
}

fn main() -> Result<()> {
    let args = Args::parse();
    let t0 = Instant::now();

    if args.reset_atime {
        let r = atime::reset_access_times(
            &args.root,
            std::time::Duration::from_secs(2 * 86_400),
            args.reset_atime_all,
        );
        println!(
            "[fs-mirage] access times of {} entries under {} set two days back in {:.2?} ({} failed, {} files untouched since the last reset)",
            r.set,
            args.root.display(),
            t0.elapsed(),
            r.failed,
            r.unchanged
        );
        return Ok(());
    }

    let scale_preset: ScalePreset = match args.preset {
        Some(p) => p.into(),
        None => {
            if args.files.is_some() {
                ScalePreset::Custom
            } else {
                ScalePreset::VeryLite
            }
        }
    };

    let (default_files, _) = scale_preset.spec().unwrap_or((100_000, 100.0));
    let total_files = args.files.unwrap_or(default_files);
    let target_logical_gb = match args.logical_gb {
        Some(gb) => Some(gb),
        None => scale_preset.spec().map(|(_, gb)| gb),
    };

    println!(
        "[fs-mirage] Generating deterministic topology (preset={}, files={}, seed={}, logical_gb={:?}, max_physical_mb={})...",
        scale_preset.as_str(),
        total_files,
        args.seed,
        target_logical_gb,
        args.max_physical_mb
    );

    let cfg = TopologyConfig {
        preset: scale_preset.as_str().to_string(),
        total_files,
        seed: args.seed,
        target_logical_gb,
        max_physical_mb: args.max_physical_mb,
    };

    let prof: Option<profile::Profile> = match &args.profile {
        Some(path) => {
            let text = fs::read_to_string(path)
                .with_context(|| format!("reading profile {}", path.display()))?;
            Some(serde_json::from_str(&text).context("parsing profile JSON")?)
        }
        None => None,
    };
    let plan = match &prof {
        Some(p) => profile::generate_from_profile(&cfg, p),
        None => TopologyPlan::generate(&cfg),
    };
    let topo_elapsed = t0.elapsed();
    println!(
        "[fs-mirage] Topology planned in {:.2?}: {} dirs, {} regular files, {} hardlinks, {} symlinks, apparent_size={:.2} GiB",
        topo_elapsed,
        plan.manifest.total_dirs,
        plan.manifest.total_regular_files,
        plan.manifest.total_hardlinks,
        plan.manifest.total_symlinks,
        plan.manifest.apparent_size_bytes as f64 / (1024.0 * 1024.0 * 1024.0)
    );

    if args.plan_only {
        let m = &plan.manifest;
        println!(
            "[fs-mirage] plan-only: files={} dirs={} files_per_dir={:.1} folder_share={:.1}% hardlinks={} symlinks={} apparent_gib={:.1}",
            m.total_files,
            m.total_dirs,
            m.total_files as f64 / m.total_dirs.max(1) as f64,
            100.0 * m.total_dirs as f64 / (m.total_files + m.total_dirs).max(1) as f64,
            m.total_hardlinks,
            m.total_symlinks,
            m.apparent_size_bytes as f64 / (1024.0 * 1024.0 * 1024.0)
        );
        return Ok(());
    }

    if args.recount_alloc {
        return recount(&args, &plan);
    }

    // Timed scans with access-time updates on (the CI sets BENCH_ATIME=daily): files are created with access times two
    // days back, so the reset before the scans only has to set the folders back
    if std::env::var("BENCH_ATIME").is_ok_and(|v| v == "daily") {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs() as i64)
            .unwrap_or(0);
        materializer::set_old_atime(now - 2 * 86_400);
    }

    if args.ballast_files > 0 {
        let ballast_root = match &args.ballast_root {
            Some(p) => p.clone(),
            None => args
                .root
                .parent()
                .filter(|p| !p.as_os_str().is_empty())
                .map(|p| p.join("ballast"))
                .context("--root has no parent folder for the ballast; pass --ballast-root")?,
        };
        let tb = Instant::now();
        let bplan = ballast_plan(&args, &cfg, prof.as_ref());
        let (bdirs, bfiles) = (bplan.manifest.total_dirs, bplan.manifest.total_files);
        materializer::materialize_tree(&ballast_root, bplan, !args.no_prealloc, !args.no_realism)?;
        println!(
            "[fs-mirage] Ballast ({}) materialized in {:.2?}: {} files, {} dirs under {}",
            if args.ballast_empty {
                "empty files"
            } else {
                "sized like the tree"
            },
            tb.elapsed(),
            bfiles,
            bdirs,
            ballast_root.display()
        );
    }

    let t1 = Instant::now();
    let manifest =
        materializer::materialize_tree(&args.root, plan, !args.no_prealloc, !args.no_realism)?;
    let mat_elapsed = t1.elapsed();

    println!(
        "[fs-mirage] Materialized in {:.2?}: apparent={:.2} GiB, allocated={:.2} MiB",
        mat_elapsed,
        manifest.apparent_size_bytes as f64 / (1024.0 * 1024.0 * 1024.0),
        manifest.allocated_size_bytes as f64 / (1024.0 * 1024.0)
    );

    if let Some(parent) = args.manifest_out.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)?;
        }
    }
    let json_str = serde_json::to_string_pretty(&manifest)
        .context("Failed to serialize ground_truth manifest")?;
    fs::write(&args.manifest_out, json_str).with_context(|| {
        format!(
            "Failed to write manifest to {}",
            args.manifest_out.display()
        )
    })?;

    println!(
        "[fs-mirage] Ground truth saved to {}",
        args.manifest_out.display()
    );
    Ok(())
}
