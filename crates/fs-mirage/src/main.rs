mod materializer;
mod topology;

use anyhow::{Context, Result};
use clap::Parser;
use std::fs;
use std::path::PathBuf;
use std::time::Instant;
use topology::{TopologyConfig, TopologyPlan};

#[derive(Parser, Debug)]
#[command(
    name = "fs-mirage",
    about = "Cross-platform deterministic realistic file tree generator with dirty-extent sparse anchoring"
)]
struct Args {
    /// Root directory where the synthetic file tree will be materialized
    #[arg(long)]
    root: PathBuf,

    /// Total number of file items to generate (e.g. 10000, 1000000, 3000000)
    #[arg(long, default_value_t = 100_000)]
    files: usize,

    /// Deterministic PRNG seed (ChaCha8Rng)
    #[arg(long, default_value_t = 42)]
    seed: u64,

    /// Target total logical size in GiB (e.g. 500, 20480). If omitted, uses natural 1GB..100GB distribution
    #[arg(long)]
    logical_gb: Option<f64>,

    /// Maximum physical disk budget in MiB (default: 1500 MiB)
    #[arg(long, default_value_t = 1500)]
    max_physical_mb: u64,

    /// Output path for the Ground Truth manifest JSON
    #[arg(long, default_value = "ground_truth.json")]
    manifest_out: PathBuf,
}

fn main() -> Result<()> {
    let args = Args::parse();
    let t0 = Instant::now();

    println!(
        "[fs-mirage] Generating deterministic topology (files={}, seed={}, logical_gb={:?}, max_physical_mb={})...",
        args.files, args.seed, args.logical_gb, args.max_physical_mb
    );

    let cfg = TopologyConfig {
        total_files: args.files,
        seed: args.seed,
        target_logical_gb: args.logical_gb,
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
    let manifest = materializer::materialize_tree(&args.root, plan)?;
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
    fs::write(&args.manifest_out, json_str)
        .with_context(|| format!("Failed to write manifest to {}", args.manifest_out.display()))?;

    println!(
        "[fs-mirage] Ground truth saved to {}",
        args.manifest_out.display()
    );
    Ok(())
}
