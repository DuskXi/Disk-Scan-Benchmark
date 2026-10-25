mod cpu_tree;
mod io_meta;
mod io_rand;
mod io_seq;

use anyhow::{Context, Result};
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(
    name = "hw-probe",
    about = "Hardware ceiling baseline probe (B_meta, B_seq, B_cpu) & normalization calculator"
)]
struct Args {
    /// Root path of the mounted benchmark volume / test directory
    #[arg(long)]
    root: PathBuf,

    /// Output path for baseline.json
    #[arg(long, default_value = "baseline.json")]
    out: PathBuf,

    /// Sequential I/O probe test size in MiB (default: 512 MiB)
    #[arg(long, default_value_t = 512)]
    seq_mb: usize,

    /// Random 4 KiB read probe: test file size in MiB (default: 1024 MiB)
    #[arg(long, default_value_t = 1024)]
    rand_mb: usize,

    /// Random read probe: reader threads, i.e. reads kept in flight (default: 32)
    #[arg(long, default_value_t = 32)]
    rand_threads: usize,

    /// Random read probe: duration in seconds (default: 3)
    #[arg(long, default_value_t = 3.0)]
    rand_secs: f64,

    /// Number of virtual nodes for pure-memory CPU tree benchmark (default: 1,000,000)
    #[arg(long, default_value_t = 1_000_000)]
    cpu_nodes: usize,

    /// Optional: raw scanner results JSON to merge and normalize against this baseline
    #[arg(long)]
    merge_results: Option<PathBuf>,

    /// Optional: output path when --merge-results is used
    #[arg(long, default_value = "normalized_results.json")]
    merged_out: PathBuf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardwareBaseline {
    pub os: String,
    pub arch: String,
    pub logical_cores: usize,
    pub b_meta_files_per_sec: f64,
    pub b_seq_mb_per_sec: f64,
    pub b_cpu_ms: f64,
    /// Random 4 KiB read requests per second with `rand_detail.threads` in flight (S_IOPS of the balanced index)
    pub b_rand_read_iops: f64,
    pub meta_detail: io_meta::MetaProbeResult,
    pub seq_detail: io_seq::SeqProbeResult,
    pub rand_detail: io_rand::RandProbeResult,
    pub cpu_detail: cpu_tree::CpuProbeResult,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawScannerEntry {
    pub scanner: String,
    #[serde(default)]
    pub version: String,
    pub cold_time_ms: f64,
    pub warm_time_ms: f64,
    pub peak_rss_mb: f64,
    pub scanned_files: u64,
    pub scanned_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NormalizedScannerEntry {
    pub scanner: String,
    pub version: String,
    pub cold_time_ms: f64,
    pub warm_time_ms: f64,
    pub cold_files_per_sec: f64,
    pub eta_io_percent: f64,
    pub cpu_cost_ratio: f64,
    pub peak_rss_mb: f64,
    pub scanned_files: u64,
    pub scanned_bytes: u64,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let logical_cores = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1);

    println!(
        "[hw-probe] Starting Hardware Ceiling Probe on {} (os={}, arch={}, cores={})...",
        args.root.display(),
        std::env::consts::OS,
        std::env::consts::ARCH,
        logical_cores
    );

    // 1. B_meta: Native concurrent metadata traversal ceiling
    let meta_detail = io_meta::run_meta_probe(&args.root)
        .with_context(|| format!("Failed to run B_meta probe on {}", args.root.display()))?;
    println!(
        "[hw-probe] B_meta: {:.0} files/sec ({} files, {} dirs in {:.2} ms)",
        meta_detail.b_meta_files_per_sec,
        meta_detail.files_scanned,
        meta_detail.dirs_scanned,
        meta_detail.elapsed_ms
    );

    // 2. B_seq: Sequential read bandwidth ceiling
    let seq_detail = io_seq::run_seq_probe(&args.root, args.seq_mb)
        .with_context(|| format!("Failed to run B_seq probe on {}", args.root.display()))?;
    println!(
        "[hw-probe] B_seq : {:.2} MB/s ({} MiB in {:.2} ms)",
        seq_detail.b_seq_mb_per_sec, seq_detail.test_size_mb, seq_detail.elapsed_ms
    );

    // 2b. S_IOPS: Random 4 KiB read ceiling with many reads in flight
    let rand_detail =
        io_rand::run_rand_probe(&args.root, args.rand_mb, args.rand_threads, args.rand_secs)
            .with_context(|| {
                format!("Failed to run random read probe on {}", args.root.display())
            })?;
    println!(
        "[hw-probe] S_iops: {:.0} random 4 KiB reads/s ({} threads, {} reads in {:.0} ms)",
        rand_detail.b_rand_read_iops,
        rand_detail.threads,
        rand_detail.reads,
        rand_detail.elapsed_ms
    );

    // 3. B_cpu: Pure-memory tree construction & descending sort baseline
    let cpu_detail = cpu_tree::run_cpu_tree_probe(args.cpu_nodes);
    println!(
        "[hw-probe] B_cpu : {:.2} ms ({} virtual tree nodes)",
        cpu_detail.b_cpu_ms, cpu_detail.node_count
    );

    let baseline = HardwareBaseline {
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        logical_cores,
        b_meta_files_per_sec: meta_detail.b_meta_files_per_sec,
        b_seq_mb_per_sec: seq_detail.b_seq_mb_per_sec,
        b_cpu_ms: cpu_detail.b_cpu_ms,
        b_rand_read_iops: rand_detail.b_rand_read_iops,
        meta_detail,
        seq_detail,
        rand_detail,
        cpu_detail,
    };

    if let Some(parent) = args.out.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)?;
        }
    }
    let json_str = serde_json::to_string_pretty(&baseline)?;
    fs::write(&args.out, json_str)
        .with_context(|| format!("Failed to write baseline to {}", args.out.display()))?;
    println!("[hw-probe] Baseline saved to {}", args.out.display());

    // Optional: Merge & compute normalized scores if --merge-results was provided
    if let Some(raw_path) = args.merge_results {
        let raw_content = fs::read_to_string(&raw_path)
            .with_context(|| format!("Failed to read {}", raw_path.display()))?;
        let raw_entries: Vec<RawScannerEntry> = serde_json::from_str(&raw_content)?;
        let normalized: Vec<NormalizedScannerEntry> = raw_entries
            .into_iter()
            .map(|entry| {
                let cold_secs = (entry.cold_time_ms / 1000.0).max(1e-6);
                let cold_files_per_sec = (entry.scanned_files as f64) / cold_secs;
                let eta_io_percent = if baseline.b_meta_files_per_sec > 0.0 {
                    (cold_files_per_sec / baseline.b_meta_files_per_sec) * 100.0
                } else {
                    0.0
                };
                let cpu_cost_ratio = if baseline.b_cpu_ms > 0.0 {
                    entry.warm_time_ms / baseline.b_cpu_ms
                } else {
                    0.0
                };
                NormalizedScannerEntry {
                    scanner: entry.scanner,
                    version: entry.version,
                    cold_time_ms: entry.cold_time_ms,
                    warm_time_ms: entry.warm_time_ms,
                    cold_files_per_sec,
                    eta_io_percent,
                    cpu_cost_ratio,
                    peak_rss_mb: entry.peak_rss_mb,
                    scanned_files: entry.scanned_files,
                    scanned_bytes: entry.scanned_bytes,
                }
            })
            .collect();

        let norm_json = serde_json::to_string_pretty(&normalized)?;
        fs::write(&args.merged_out, norm_json)?;
        println!(
            "[hw-probe] Normalized results saved to {}",
            args.merged_out.display()
        );
    }

    Ok(())
}
