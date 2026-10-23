use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};

pub const BLOCK_SIZE: u64 = 4096;
const GB: u64 = 1024 * 1024 * 1024;
const MB: u64 = 1024 * 1024;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FileZone {
    DeepSource,
    FlatCache,
    SparseMedia,
    EdgeLongName,
    EdgeHardLink,
    EdgeSymlink,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EntryKind {
    /// Regular or sparse file
    RegularFile {
        logical_size: u64,
        /// Number of 4KB dirty blocks to write (0 = sparse metadata-only, 1..=8 = dirty extent anchors)
        dirty_blocks: u8,
        /// Deterministic seed byte for filling the 4KB dirty block(s)
        fill_byte: u8,
    },
    /// Hard link pointing to another relative path in the generated tree
    HardLink {
        target_rel_path: String,
        logical_size: u64,
    },
    /// Symbolic link (or directory junction on Windows fallback)
    Symlink {
        target_rel_path: String,
        is_dir_cycle: bool,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileEntry {
    /// Forward-slash normalized relative path from root
    pub rel_path: String,
    pub zone: FileZone,
    pub kind: EntryKind,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ScalePreset {
    VeryLite,
    Lite,
    Low,
    Mid,
    High,
    VeryHigh,
    Custom,
}

impl ScalePreset {
    pub fn as_str(&self) -> &'static str {
        match self {
            ScalePreset::VeryLite => "very-lite",
            ScalePreset::Lite => "lite",
            ScalePreset::Low => "low",
            ScalePreset::Mid => "mid",
            ScalePreset::High => "high",
            ScalePreset::VeryHigh => "very-high",
            ScalePreset::Custom => "custom",
        }
    }

    /// Returns (total_files, logical_gb) for each standard tier:
    /// - very-lite: 100,000 items, 100 GB
    /// - lite:      400,000 items, 350 GB
    /// - low:     1,000,000 items, 500 GB
    /// - mid:     3,000,000 items, 1024 GB (1 TB)
    /// - high:    5,000,000 items, 2048 GB (2 TB)
    /// - very-high: 9,000,000 items, 3072 GB (3 TB)
    pub fn spec(&self) -> Option<(usize, f64)> {
        match self {
            ScalePreset::VeryLite => Some((100_000, 100.0)),
            ScalePreset::Lite => Some((400_000, 350.0)),
            ScalePreset::Low => Some((1_000_000, 500.0)),
            ScalePreset::Mid => Some((3_000_000, 1024.0)),
            ScalePreset::High => Some((5_000_000, 2048.0)),
            ScalePreset::VeryHigh => Some((9_000_000, 3072.0)),
            ScalePreset::Custom => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TopologyConfig {
    pub preset: String,
    pub total_files: usize,
    pub seed: u64,
    /// Optional target total logical size in GiB. If None, uses natural 1GB..100GB distribution.
    pub target_logical_gb: Option<f64>,
    /// Maximum physical data blocks budget in MiB (default: 1500 MiB = 1.5 GiB)
    pub max_physical_mb: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GroundTruthManifest {
    pub preset: String,
    pub seed: u64,
    pub total_files: usize,
    pub total_regular_files: usize,
    pub total_dirs: usize,
    pub total_hardlinks: usize,
    pub total_symlinks: usize,
    pub media_files_count: usize,
    /// True logical size deduplicating hardlinks (Apparent Size)
    pub apparent_size_bytes: u64,
    /// Sum of logical sizes if hardlinks are counted multiple times
    pub apparent_size_with_hardlinks_bytes: u64,
    /// Planned dirty blocks bytes written by materializer
    pub planned_dirty_bytes: u64,
    /// Actual OS-reported allocated physical bytes on disk (deduplicating hardlinks)
    pub allocated_size_bytes: u64,
    /// Actual OS-reported allocated physical bytes on disk (counting hardlinks multiple times)
    pub allocated_size_with_hardlinks_bytes: u64,
}

#[derive(Debug)]
pub struct TopologyPlan {
    /// All directories in topological order (parents before children), relative paths with `/`
    pub directories: Vec<String>,
    /// Regular files (materialized first so hardlinks/symlinks can reference them)
    pub regular_files: Vec<FileEntry>,
    /// Hardlink entries (materialized after regular files)
    pub hardlinks: Vec<FileEntry>,
    /// Symlink entries (materialized last)
    pub symlinks: Vec<FileEntry>,
    /// Initial ground truth statistics before OS allocation measurement
    pub manifest: GroundTruthManifest,
}

impl TopologyPlan {
    pub fn generate(cfg: &TopologyConfig) -> Self {
        let mut rng = ChaCha8Rng::seed_from_u64(cfg.seed);
        let total = cfg.total_files.max(10);

        // Proportions from engineering spec 2.1:
        // - 50% Deep source/dependency zone (depth 8..=25, size 64B..=16KB)
        // - 35% Flat high-density log/cache zone (50k..150k per dir, size 128B..=16KB)
        // - 0.1% Sparse media/image zone (1GB..=100GB, >=1 file)
        // - Remaining (~14.9%) Edge cases: HardLinks (~5%), Symlinks (~0.4% capped at 500), LongFilenames (~9.5%)
        let count_deep = total * 50 / 100;
        let count_flat = total * 35 / 100;
        let count_media = (total / 1000).max(1);
        let remaining = total.saturating_sub(count_deep + count_flat + count_media);
        let count_hardlinks = (total * 5 / 100).min(remaining / 2);
        let count_symlinks = (total / 250).clamp(2, 500).min(remaining.saturating_sub(count_hardlinks));
        let count_long = remaining.saturating_sub(count_hardlinks + count_symlinks);

        let mut dir_set = std::collections::BTreeSet::new();
        let add_dir_with_ancestors = |dir_path: &str, set: &mut std::collections::BTreeSet<String>| {
            let mut current = String::new();
            for part in dir_path.split('/').filter(|s| !s.is_empty()) {
                if !current.is_empty() {
                    current.push('/');
                }
                current.push_str(part);
                set.insert(current.clone());
            }
        };

        // Physical block budget calculation:
        // Reserve physical budget for media files first (up to 8 * 4KB = 32KB each).
        // Each NTFS sparse extent may allocate up to 64KB (16 clusters), so we budget conservatively.
        let max_phys_bytes = cfg.max_physical_mb.saturating_mul(MB);
        let media_reserved_bytes = (count_media as u64) * 8 * 65536;
        let small_budget_bytes = max_phys_bytes.saturating_sub(media_reserved_bytes);
        // Cap sampled dirty small files at 12,000 (~48 MB physical blocks) so million-file tiers
        // do not bottleneck virtualized VHDX / APFS sparseimage on 180k random 4KB writes.
        let max_small_dirty_files = (small_budget_bytes / BLOCK_SIZE).min(12_000) as usize;
        let total_small_regular = count_deep + count_flat + count_long;
        // Deterministic sampling rate (in parts per 10,000) for small files to receive a 4KB dirty block
        let small_dirty_rate_bp: u32 = if total_small_regular == 0 {
            0
        } else {
            let raw_bp = ((max_small_dirty_files as u64) * 10_000 / (total_small_regular as u64)).min(2000);
            raw_bp.max(100) as u32
        };

        let mut regular_files = Vec::with_capacity(total_small_regular + count_media);
        let mut small_dirty_allocated: usize = 0;
        let mut planned_dirty_bytes: u64 = 0;

        // 1. Generate Deep Source / Dependency Zone (50%)
        // Create realistic deep hierarchies where each step adds exactly 1 directory level (depth 8..=25)
        let num_deep_chains = (count_deep / 80).clamp(8, 1200);
        let mut deep_leaf_dirs = Vec::with_capacity(num_deep_chains * 4);
        let pkg_names = ["core", "runtime", "compiler", "serde", "tokio", "syn", "libc", "vfs", "index", "cache"];
        for chain_idx in 0..num_deep_chains {
            let target_depth = rng.gen_range(8..=25);
            let mut path = format!("zone_deep/ws_{:03}", chain_idx / 16);
            for d in 3..=target_depth {
                let seg = match d % 4 {
                    0 => format!("nm_{}_{}", pkg_names[rng.gen_range(0..pkg_names.len())], d),
                    1 => format!("deps_{}", d),
                    2 => format!("mod_{}", pkg_names[rng.gen_range(0..pkg_names.len())]),
                    _ => format!("s_{:02}", rng.gen_range(0..32)),
                };
                path.push('/');
                path.push_str(&seg);
                if d >= 8 {
                    deep_leaf_dirs.push(path.clone());
                }
            }
            add_dir_with_ancestors(&path, &mut dir_set);
        }

        let extensions = ["rs", "ts", "js", "json", "rlib", "d", "o", "toml", "h", "c"];
        for i in 0..count_deep {
            let dir = &deep_leaf_dirs[rng.gen_range(0..deep_leaf_dirs.len())];
            let ext = extensions[rng.gen_range(0..extensions.len())];
            let rel_path = format!("{}/f_{:07}.{}", dir, i, ext);
            let write_dirty = small_dirty_allocated < max_small_dirty_files
                && rng.gen_range(0..10_000) < small_dirty_rate_bp;
            let logical_size = if write_dirty {
                BLOCK_SIZE
            } else if rng.gen_bool(0.90) {
                // 90% of clean small files use 0-byte logical size (created via single openat/CreateFileW
                // without a second ftruncate/SetFileInformationByHandle metadata transaction;
                // zone_sparse_media absorbs the remaining logical volume so total apparent_size is exact).
                0
            } else {
                // Remaining 10% <= 680B (fits in NTFS Resident $MFT record without requiring FSCTL_SET_SPARSE)
                rng.gen_range(64..=680)
            };
            let dirty_blocks = if write_dirty {
                small_dirty_allocated += 1;
                planned_dirty_bytes += BLOCK_SIZE;
                1
            } else {
                0
            };
            let fill_byte = rng.gen_range(1..=254);
            regular_files.push(FileEntry {
                rel_path,
                zone: FileZone::DeepSource,
                kind: EntryKind::RegularFile {
                    logical_size,
                    dirty_blocks,
                    fill_byte,
                },
            });
        }

        // 2. Generate Flat High-Density Log / Cache Zone (35%)
        // Each flat bucket holds 10,000 ~ 20,000 files so all worker threads can populate distinct
        // flat buckets in parallel without single-directory B-Tree mutex contention on APFS / NTFS.
        let mut flat_remaining = count_flat;
        let mut bucket_id = 0usize;
        let mut flat_file_idx = 0usize;
        while flat_remaining > 0 {
            let bucket_cap = rng.gen_range(10_000..=20_000);
            let count_in_bucket = flat_remaining.min(bucket_cap);
            let bucket_dir = format!("zone_flat_cache/bucket_{:03}", bucket_id);
            add_dir_with_ancestors(&bucket_dir, &mut dir_set);

            for _ in 0..count_in_bucket {
                let rel_path = format!("{}/cache_{:08}.log", bucket_dir, flat_file_idx);
                flat_file_idx += 1;
                let write_dirty = small_dirty_allocated < max_small_dirty_files
                    && rng.gen_range(0..10_000) < small_dirty_rate_bp;
                let logical_size = if write_dirty {
                    BLOCK_SIZE
                } else if rng.gen_bool(0.90) {
                    0
                } else {
                    rng.gen_range(128..=680)
                };
                let dirty_blocks = if write_dirty {
                    small_dirty_allocated += 1;
                    planned_dirty_bytes += BLOCK_SIZE;
                    1
                } else {
                    0
                };
                let fill_byte = rng.gen_range(1..=254);
                regular_files.push(FileEntry {
                    rel_path,
                    zone: FileZone::FlatCache,
                    kind: EntryKind::RegularFile {
                        logical_size,
                        dirty_blocks,
                        fill_byte,
                    },
                });
            }
            flat_remaining -= count_in_bucket;
            bucket_id += 1;
        }

        // 3. Generate Edge Long Filenames Zone
        let long_base_dir = "zone_edge/long_paths/nested_container/subcomponent";
        add_dir_with_ancestors(long_base_dir, &mut dir_set);
        for i in 0..count_long {
            let sub_bucket = format!("{}/shard_{:03}", long_base_dir, i / 500);
            add_dir_with_ancestors(&sub_bucket, &mut dir_set);
            let pad_len = rng.gen_range(100..=140);
            let pad: String = (0..pad_len)
                .map(|k| (b'a' + ((i + k) % 26) as u8) as char)
                .collect();
            let rel_path = format!("{}/long_{:07}_{}.dat", sub_bucket, i, pad);
            let write_dirty = small_dirty_allocated < max_small_dirty_files
                && rng.gen_range(0..10_000) < small_dirty_rate_bp;
            let logical_size = if write_dirty {
                BLOCK_SIZE
            } else if rng.gen_bool(0.90) {
                0
            } else {
                rng.gen_range(256..=680)
            };
            let dirty_blocks = if write_dirty {
                small_dirty_allocated += 1;
                planned_dirty_bytes += BLOCK_SIZE;
                1
            } else {
                0
            };
            let fill_byte = rng.gen_range(1..=254);
            regular_files.push(FileEntry {
                rel_path,
                zone: FileZone::EdgeLongName,
                kind: EntryKind::RegularFile {
                    logical_size,
                    dirty_blocks,
                    fill_byte,
                },
            });
        }

        // Calculate small files logical sum so far
        let small_logical_sum: u64 = regular_files
            .iter()
            .map(|e| match e.kind {
                EntryKind::RegularFile { logical_size, .. } => logical_size,
                _ => 0,
            })
            .sum();

        // 4. Generate Ultra-Large Sparse Media / Image Zone (0.1% of files, >90% logical volume)
        let media_dir = "zone_sparse_media/images";
        add_dir_with_ancestors(media_dir, &mut dir_set);

        let mut raw_media_sizes: Vec<u64> = Vec::with_capacity(count_media);
        for _ in 0..count_media {
            // Log-uniform / heavy-tail between 1 GB and 100 GB, averaging ~20 GB
            let size_gb: f64 = if rng.gen_bool(0.75) {
                rng.gen_range(1.0..=25.0)
            } else {
                rng.gen_range(25.0..=100.0)
            };
            let bytes = ((size_gb * (GB as f64)) as u64) & !(BLOCK_SIZE - 1);
            raw_media_sizes.push(bytes.max(GB));
        }

        // If user specified --logical-gb, scale media sizes so total logical volume hits target_logical_gb
        if let Some(target_gb) = cfg.target_logical_gb {
            let target_bytes = (target_gb * (GB as f64)) as u64;
            let desired_media_sum = target_bytes.saturating_sub(small_logical_sum).max(count_media as u64 * MB * 16);
            let current_media_sum: u64 = raw_media_sizes.iter().sum::<u64>().max(1);
            for sz in &mut raw_media_sizes {
                let scaled = ((*sz as u128) * (desired_media_sum as u128) / (current_media_sum as u128)) as u64;
                *sz = (scaled & !(BLOCK_SIZE - 1)).max(16 * MB);
            }
        }

        for (i, logical_size) in raw_media_sizes.into_iter().enumerate() {
            let sub = format!("{}/vol_{:02}", media_dir, i % 16);
            add_dir_with_ancestors(&sub, &mut dir_set);
            let ext = if i % 2 == 0 { "img" } else { "vhdx.raw" };
            let rel_path = format!("{}/sparse_blob_{:05}.{}", sub, i, ext);

            // Number of 4KB dirty anchor blocks (1..=8) proportional to log2 of size in GB
            let size_gb = (logical_size as f64 / GB as f64).max(1.0);
            let dirty_blocks = (size_gb.log2().ceil() as u8 + 2).clamp(2, 8);
            planned_dirty_bytes += (dirty_blocks as u64) * BLOCK_SIZE;
            let fill_byte = rng.gen_range(1..=254);

            regular_files.push(FileEntry {
                rel_path,
                zone: FileZone::SparseMedia,
                kind: EntryKind::RegularFile {
                    logical_size,
                    dirty_blocks,
                    fill_byte,
                },
            });
        }

        // 5. Generate Edge HardLinks (pointing to existing regular small/medium files)
        let hardlink_dir = "zone_edge/hardlinks";
        add_dir_with_ancestors(hardlink_dir, &mut dir_set);
        let candidate_regular_count = regular_files.len().saturating_sub(count_media).max(1);
        let mut hardlinks = Vec::with_capacity(count_hardlinks);
        let mut hardlink_extra_logical: u64 = 0;

        for i in 0..count_hardlinks {
            let sub = format!("{}/group_{:03}", hardlink_dir, i / 1000);
            add_dir_with_ancestors(&sub, &mut dir_set);
            let target_idx = rng.gen_range(0..candidate_regular_count);
            let target_entry = &regular_files[target_idx];
            let target_size = match target_entry.kind {
                EntryKind::RegularFile { logical_size, .. } => logical_size,
                _ => 0,
            };
            hardlink_extra_logical += target_size;
            hardlinks.push(FileEntry {
                rel_path: format!("{}/hl_{:07}.lnk", sub, i),
                zone: FileZone::EdgeHardLink,
                kind: EntryKind::HardLink {
                    target_rel_path: target_entry.rel_path.clone(),
                    logical_size: target_size,
                },
            });
        }

        // 6. Generate Edge Symlinks (including cyclic directory symlinks pointing to ancestors)
        let symlink_dir = "zone_edge/symlinks";
        add_dir_with_ancestors(symlink_dir, &mut dir_set);
        let mut symlinks = Vec::with_capacity(count_symlinks);
        for i in 0..count_symlinks {
            let is_dir_cycle = i < 4; // First up to 4 symlinks are ancestor directory loop traps
            if is_dir_cycle {
                symlinks.push(FileEntry {
                    rel_path: format!("{}/cycle_loop_{:02}", symlink_dir, i),
                    zone: FileZone::EdgeSymlink,
                    kind: EntryKind::Symlink {
                        target_rel_path: "zone_edge".to_string(),
                        is_dir_cycle: true,
                    },
                });
            } else {
                let target_idx = rng.gen_range(0..candidate_regular_count);
                let target_rel = regular_files[target_idx].rel_path.clone();
                symlinks.push(FileEntry {
                    rel_path: format!("{}/sym_{:05}.ref", symlink_dir, i),
                    zone: FileZone::EdgeSymlink,
                    kind: EntryKind::Symlink {
                        target_rel_path: target_rel,
                        is_dir_cycle: false,
                    },
                });
            }
        }

        let apparent_size_bytes: u64 = regular_files
            .iter()
            .map(|e| match e.kind {
                EntryKind::RegularFile { logical_size, .. } => logical_size,
                _ => 0,
            })
            .sum();

        // Sort directories by depth (and lexicographically) so parents are always created before children
        let mut directories: Vec<String> = dir_set.into_iter().collect();
        directories.sort_by(|a, b| {
            let depth_a = a.bytes().filter(|&c| c == b'/').count();
            let depth_b = b.bytes().filter(|&c| c == b'/').count();
            depth_a.cmp(&depth_b).then_with(|| a.cmp(b))
        });

        let total_regular_files = regular_files.len();
        let total_hardlinks = hardlinks.len();
        let total_symlinks = symlinks.len();
        let actual_total_files = total_regular_files + total_hardlinks + total_symlinks;

        let manifest = GroundTruthManifest {
            preset: cfg.preset.clone(),
            seed: cfg.seed,
            total_files: actual_total_files,
            total_regular_files,
            total_dirs: directories.len(),
            total_hardlinks,
            total_symlinks,
            media_files_count: count_media,
            apparent_size_bytes,
            apparent_size_with_hardlinks_bytes: apparent_size_bytes + hardlink_extra_logical,
            planned_dirty_bytes,
            allocated_size_bytes: 0,
            allocated_size_with_hardlinks_bytes: 0,
        };

        TopologyPlan {
            directories,
            regular_files,
            hardlinks,
            symlinks,
            manifest,
        }
    }
}

/// Computes `dirty_blocks` 4096-aligned byte offsets across `[0, logical_size)`
/// covering start (offset 0), end, and evenly-spaced interior anchors.
pub fn compute_dirty_anchor_offsets(logical_size: u64, dirty_blocks: u8) -> Vec<u64> {
    if dirty_blocks == 0 || logical_size == 0 {
        return Vec::new();
    }
    if logical_size <= BLOCK_SIZE || dirty_blocks == 1 {
        return vec![0];
    }

    let last_aligned = ((logical_size - 1) / BLOCK_SIZE) * BLOCK_SIZE;
    if last_aligned == 0 {
        return vec![0];
    }

    let n = dirty_blocks as u64;
    let mut offsets = Vec::with_capacity(dirty_blocks as usize);
    for i in 0..n {
        let raw = if i == 0 {
            0
        } else if i + 1 == n {
            last_aligned
        } else {
            ((last_aligned as u128 * i as u128) / (n as u128 - 1)) as u64
        };
        let aligned = (raw / BLOCK_SIZE) * BLOCK_SIZE;
        if offsets.last().copied() != Some(aligned) {
            offsets.push(aligned);
        }
    }
    offsets
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deterministic_topology() {
        let cfg = TopologyConfig {
            preset: "custom".to_string(),
            total_files: 1000,
            seed: 42,
            target_logical_gb: None,
            max_physical_mb: 1500,
        };
        let plan1 = TopologyPlan::generate(&cfg);
        let plan2 = TopologyPlan::generate(&cfg);

        assert_eq!(plan1.manifest.total_files, 1000);
        assert_eq!(plan1.manifest.apparent_size_bytes, plan2.manifest.apparent_size_bytes);
        assert_eq!(plan1.regular_files.len(), plan2.regular_files.len());
        assert_eq!(plan1.directories, plan2.directories);
        for (a, b) in plan1.regular_files.iter().zip(plan2.regular_files.iter()) {
            assert_eq!(a.rel_path, b.rel_path);
        }
    }

    #[test]
    fn test_dirty_anchor_offsets_alignment() {
        let size = 10 * GB;
        let offsets = compute_dirty_anchor_offsets(size, 6);
        assert_eq!(offsets.len(), 6);
        assert_eq!(offsets[0], 0);
        for &off in &offsets {
            assert_eq!(off % BLOCK_SIZE, 0);
            assert!(off + BLOCK_SIZE <= size);
        }
    }
}
