mod materializer;
mod topology;

use anyhow::{Context, Result};
use clap::{Parser, ValueEnum};
use std::fs;
use std::path::PathBuf;
use std::time::Instant;
use topology::{ScalePreset, TopologyConfig, TopologyPlan};

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

    /// Benchmark scale preset tier (very-lite, lite, low, mid, high, very-high, custom)
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

    /// Output path for the Ground Truth manifest JSON
    #[arg(long, default_value = "ground_truth.json")]
    manifest_out: PathBuf,
}

fn main() -> Result<()> {
    let args = Args::parse();
    let t0 = Instant::now();

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

    let plan = TopologyPlan::generate(&cfg);
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
