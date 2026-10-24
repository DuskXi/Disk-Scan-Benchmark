use crate::topology::{EntryKind, FileEntry, GroundTruthManifest, TopologyPlan};
use anyhow::{Context, Result};
use rayon::prelude::*;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::Instant;

#[cfg(unix)]
mod unix;
#[cfg(windows)]
mod windows;

/// Optional cumulative per-operation timing (set `FSM_PROFILE=1`); thread-time sums, not wall time.
pub mod prof {
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::sync::OnceLock;
    use std::time::Instant;

    pub const NAMES: [&str; 10] = [
        "create 0B",
        "create <=680B (set_len)",
        "create sparse (>680B)",
        "create prealloc",
        "create dirty-write",
        "decorate (ADS/attrs)",
        "churn create",
        "churn delete",
        "open dir handle",
        "hardlink",
    ];
    static COUNT: [AtomicU64; 10] = [const { AtomicU64::new(0) }; 10];
    static NS: [AtomicU64; 10] = [const { AtomicU64::new(0) }; 10];

    pub fn enabled() -> bool {
        static E: OnceLock<bool> = OnceLock::new();
        *E.get_or_init(|| std::env::var("FSM_PROFILE").is_ok())
    }
    pub fn start() -> Option<Instant> {
        if enabled() {
            Some(Instant::now())
        } else {
            None
        }
    }
    pub fn stop(cat: usize, t: Option<Instant>) {
        if let Some(t) = t {
            COUNT[cat].fetch_add(1, Ordering::Relaxed);
            NS[cat].fetch_add(t.elapsed().as_nanos() as u64, Ordering::Relaxed);
        }
    }
    pub fn report() {
        if !enabled() {
            return;
        }
        for (i, name) in NAMES.iter().enumerate() {
            let n = COUNT[i].load(Ordering::Relaxed);
            let ns = NS[i].load(Ordering::Relaxed);
            if n > 0 {
                eprintln!(
                    "[prof] {:<26} n={:>9} total={:>8.1}s avg={:>7.1}us",
                    name,
                    n,
                    ns as f64 / 1e9,
                    ns as f64 / n as f64 / 1e3
                );
            }
        }
    }
}

/// One short-lived file is created next to every `CHURN_EVERY`-th regular file (about 12%) and deleted again.
/// The temporary files really allocate clusters, so deleting them fragments free space as well.
const CHURN_EVERY: usize = 8;
const CHURN_PHASE: usize = 5;

/// Deterministic Fisher-Yates shuffle seeded from the directory name (xorshift64*), so runs stay reproducible.
fn shuffle_deterministic<T>(items: &mut [T], seed_text: &str) {
    let mut state: u64 = 0xcbf2_9ce4_8422_2325;
    for b in seed_text.bytes() {
        state ^= b as u64;
        state = state.wrapping_mul(0x0100_0000_01b3);
    }
    state |= 1;
    for i in (1..items.len()).rev() {
        state ^= state >> 12;
        state ^= state << 25;
        state ^= state >> 27;
        let r = state.wrapping_mul(0x2545_f491_4f6c_dd1d);
        items.swap(i, (r % (i as u64 + 1)) as usize);
    }
}

/// FNV-1a hash used to pick deterministic subsets (compressed directories, files with alternate streams, ...).
fn fnv(text: &str) -> u64 {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for b in text.bytes() {
        h ^= b as u64;
        h = h.wrapping_mul(0x0100_0000_01b3);
    }
    h
}

pub fn to_os_path(root: &Path, rel_path: &str) -> PathBuf {
    let mut p = root.to_path_buf();
    for seg in rel_path.split('/').filter(|s| !s.is_empty()) {
        p.push(seg);
    }
    p
}

pub fn materialize_tree(
    root: &Path,
    mut plan: TopologyPlan,
    prealloc: bool,
    realism: bool,
) -> Result<GroundTruthManifest> {
    fs::create_dir_all(root)
        .with_context(|| format!("Failed to create root directory: {}", root.display()))?;

    let t_dirs = Instant::now();
    // 1. Group directories by depth so each depth level can be created in parallel with a single mkdir syscall
    let mut dirs_by_depth: Vec<Vec<&str>> = Vec::new();
    for dir in &plan.directories {
        let depth = dir.bytes().filter(|&b| b == b'/').count();
        if dirs_by_depth.len() <= depth {
            dirs_by_depth.resize_with(depth + 1, Vec::new);
        }
        dirs_by_depth[depth].push(dir.as_str());
    }

    for level_dirs in dirs_by_depth {
        level_dirs
            .par_iter()
            .try_for_each(|rel_dir| -> Result<()> {
                let full_dir = to_os_path(root, rel_dir);
                match fs::create_dir(&full_dir) {
                    Ok(()) => Ok(()),
                    Err(e) if e.kind() == io::ErrorKind::AlreadyExists => Ok(()),
                    Err(_) => fs::create_dir_all(&full_dir).with_context(|| {
                        format!("Failed to create directory: {}", full_dir.display())
                    }),
                }
            })?;
    }

    eprintln!(
        "[fs-mirage]   directories created in {:.2?}",
        t_dirs.elapsed()
    );
    let t_files = Instant::now();

    // NTFS-only realism: a small share of directories is compressed (new files inherit it), the way CompactOS /
    // WinSxS style trees look; scanners then take their compressed-size code paths for those files.
    #[cfg(windows)]
    if realism {
        plan.directories
            .par_iter()
            .filter(|d| fnv(d) % 40 == 0)
            .for_each(|rel_dir| windows::compress_dir(&to_os_path(root, rel_dir)));
    }
    #[cfg(not(windows))]
    let _ = realism;

    // Track only the subset of regular file paths referenced by hardlinks to avoid cloning millions of Strings
    let hardlink_targets: HashSet<&str> = plan
        .hardlinks
        .iter()
        .filter_map(|e| match &e.kind {
            EntryKind::HardLink {
                target_rel_path, ..
            } => Some(target_rel_path.as_str()),
            _ => None,
        })
        .collect();
    let hl_alloc_map: Mutex<HashMap<&str, u64>> =
        Mutex::new(HashMap::with_capacity(hardlink_targets.len().min(65536)));

    // 2. Group regular files by parent directory to minimize per-directory B-Tree lock contention on NTFS / APFS
    let mut dir_groups: HashMap<&str, Vec<&FileEntry>> =
        HashMap::with_capacity(plan.directories.len().max(64));
    for entry in &plan.regular_files {
        let parent = entry
            .rel_path
            .rsplit_once('/')
            .map(|(p, _)| p)
            .unwrap_or("");
        dir_groups.entry(parent).or_default().push(entry);
    }

    // Keep each directory (<= 20,000 files) as an exclusive batch owned by a single worker thread
    // so multiple threads never contend on the same parent directory B-Tree lock on APFS / NTFS.
    // Sort largest directories first so the ~25 flat buckets start immediately across worker threads.
    // On NTFS a single thread creating files in one huge directory tops out at roughly 1k files/s, which makes the
    // largest flat bucket the critical path of the whole run, so split big directories into chunks that are
    // created concurrently (NTFS only serializes the short directory-index insert, not MFT record setup / data writes).
    #[cfg(windows)]
    const MAX_FILES_PER_BATCH: usize = 256;
    #[cfg(not(windows))]
    const MAX_FILES_PER_BATCH: usize = usize::MAX;
    let mut work_batches: Vec<(&str, Vec<&FileEntry>)> = Vec::with_capacity(dir_groups.len());
    for (parent, mut entries) in dir_groups {
        // Insert names in a pseudo-random order instead of ascending: ascending inserts build perfectly packed
        // directory indexes, random order half-fills and splits index pages like a long-lived directory. Free to do.
        shuffle_deterministic(&mut entries, parent);
        for chunk in entries.chunks(MAX_FILES_PER_BATCH) {
            work_batches.push((parent, chunk.to_vec()));
        }
    }
    work_batches.sort_by(|a, b| b.1.len().cmp(&a.1.len()));

    eprintln!(
        "[fs-mirage]   {} directory batches, largest: {:?}",
        work_batches.len(),
        work_batches
            .iter()
            .take(8)
            .map(|b| b.1.len())
            .collect::<Vec<_>>()
    );

    let cores = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4);
    // NTFS file creation is latency-bound (MFT record setup, journal, filter drivers), so Windows keeps many more
    // requests in flight than the Unix filesystems need.
    #[cfg(windows)]
    let io_threads = (cores * 8).clamp(16, 64);
    #[cfg(not(windows))]
    let io_threads = (cores * 3).clamp(8, 24);
    let io_threads: usize = std::env::var("FSM_THREADS")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(io_threads);
    let io_pool = rayon::ThreadPoolBuilder::new()
        .num_threads(io_threads)
        .build()
        .unwrap_or_else(|_| rayon::ThreadPoolBuilder::new().build().unwrap());

    let total_allocated = AtomicU64::new(0);
    let churn_every: usize = std::env::var("FSM_CHURN_EVERY")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(CHURN_EVERY);
    io_pool.install(|| -> Result<()> {
        work_batches
            .par_iter()
            .try_for_each(|(parent_rel, entries)| -> Result<()> {
                let parent_dir = to_os_path(root, parent_rel);
                #[cfg(unix)]
                let dir_fd = unix::open_dir_fd(&parent_dir);
                #[cfg(windows)]
                let t_dir = prof::start();
                #[cfg(windows)]
                let dir_handle = windows::open_dir_handle(&parent_dir);
                #[cfg(windows)]
                prof::stop(8, t_dir);
                let mut local_alloc_sum: u64 = 0;
                let mut local_hl_hits: Vec<(&str, u64)> = Vec::new();

                let mut churn_paths: Vec<PathBuf> = Vec::new();
                for (entry_idx, entry) in entries.iter().enumerate() {
                    let file_name = entry
                        .rel_path
                        .rsplit_once('/')
                        .map(|(_, f)| f)
                        .unwrap_or(entry.rel_path.as_str());
                    let full_path = parent_dir.join(file_name);
                    // Churn: every few files a short-lived neighbour is created and removed after the batch. That
                    // leaves freed MFT records / directory-index slots / inodes between live files, which later
                    // creations from other threads reuse, so the on-disk layout is scattered like an aged volume.
                    if churn_every > 0 && (entry_idx + CHURN_PHASE) % churn_every == 0 {
                        let churn_name = format!(".churn_{}", entry_idx);
                        let churn_size = 4096 * (1 + (fnv(&churn_name) % 16));
                        let churn_path = parent_dir.join(&churn_name);
                        #[cfg(unix)]
                        let churn_ok = unix::create_sparse_anchored_file(
                            dir_fd.as_ref(),
                            &churn_name,
                            &churn_path,
                            churn_size,
                            0,
                            1,
                            prealloc,
                        )
                        .is_ok();
                        #[cfg(windows)]
                        let churn_ok = windows::create_sparse_anchored_file(
                            dir_handle.as_ref(),
                            &churn_name,
                            &churn_path,
                            churn_size,
                            0,
                            1,
                            prealloc,
                        )
                        .is_ok();
                        if churn_ok {
                            churn_paths.push(churn_path);
                        }
                    }
                    let alloc = match entry.kind {
                        EntryKind::RegularFile {
                            logical_size,
                            dirty_blocks,
                            fill_byte,
                            preallocate,
                        } => {
                            let preallocate = preallocate && prealloc;
                            #[cfg(unix)]
                            let res = unix::create_sparse_anchored_file(
                                dir_fd.as_ref(),
                                file_name,
                                &full_path,
                                logical_size,
                                dirty_blocks,
                                fill_byte,
                                preallocate,
                            );
                            #[cfg(windows)]
                            let res = windows::create_sparse_anchored_file(
                                dir_handle.as_ref(),
                                file_name,
                                &full_path,
                                logical_size,
                                dirty_blocks,
                                fill_byte,
                                preallocate,
                            );
                            res.with_context(|| {
                                format!("Failed to materialize file {}", full_path.display())
                            })?
                        }
                        _ => 0,
                    };
                    #[cfg(windows)]
                    if realism {
                        let t_dec = prof::start();
                        windows::decorate(&full_path, fnv(&entry.rel_path));
                        prof::stop(5, t_dec);
                    }
                    local_alloc_sum += alloc;
                    if alloc > 0 && hardlink_targets.contains(entry.rel_path.as_str()) {
                        local_hl_hits.push((entry.rel_path.as_str(), alloc));
                    }
                }

                for churn_path in churn_paths {
                    let t_del = prof::start();
                    let _ = fs::remove_file(churn_path);
                    prof::stop(7, t_del);
                }

                if local_alloc_sum > 0 {
                    total_allocated.fetch_add(local_alloc_sum, Ordering::Relaxed);
                }
                if !local_hl_hits.is_empty() {
                    if let Ok(mut guard) = hl_alloc_map.lock() {
                        for (k, v) in local_hl_hits {
                            guard.insert(k, v);
                        }
                    }
                }
                Ok(())
            })
    })?;

    eprintln!(
        "[fs-mirage]   regular files written in {:.2?}",
        t_files.elapsed()
    );
    let t_links = Instant::now();
    let alloc_map = hl_alloc_map.into_inner().unwrap_or_default();

    // 3. Materialize hard links concurrently
    let hardlink_extra_alloc = AtomicU64::new(0);
    plan.hardlinks
        .par_iter()
        .try_for_each(|entry| -> Result<()> {
            if let EntryKind::HardLink {
                ref target_rel_path,
                ..
            } = entry.kind
            {
                let src_path = to_os_path(root, target_rel_path);
                let dst_path = to_os_path(root, &entry.rel_path);
                // Create first and only clean up on AlreadyExists: an up-front exists() costs an extra
                // metadata syscall per link, which is expensive on NTFS.
                let t_hl = prof::start();
                let linked = match fs::hard_link(&src_path, &dst_path) {
                    Err(e) if e.kind() == io::ErrorKind::AlreadyExists => {
                        let _ = fs::remove_file(&dst_path);
                        fs::hard_link(&src_path, &dst_path)
                    }
                    other => other,
                };
                prof::stop(9, t_hl);
                linked.with_context(|| {
                    format!(
                        "Failed to create hard link {} -> {}",
                        dst_path.display(),
                        src_path.display()
                    )
                })?;
                if let Some(&target_alloc) = alloc_map.get(target_rel_path.as_str()) {
                    hardlink_extra_alloc.fetch_add(target_alloc, Ordering::Relaxed);
                }
            }
            Ok(())
        })?;

    eprintln!(
        "[fs-mirage]   hard links created in {:.2?}",
        t_links.elapsed()
    );
    let t_syms = Instant::now();

    // 4. Materialize symlinks / junctions
    plan.symlinks
        .par_iter()
        .try_for_each(|entry| -> Result<()> {
            if let EntryKind::Symlink {
                ref target_rel_path,
                is_dir_cycle,
            } = entry.kind
            {
                let target_path = to_os_path(root, target_rel_path);
                let link_path = to_os_path(root, &entry.rel_path);
                create_platform_symlink(&target_path, &link_path, is_dir_cycle)?;
            }
            Ok(())
        })?;

    eprintln!("[fs-mirage]   symlinks created in {:.2?}", t_syms.elapsed());

    let files_only_bytes = total_allocated.load(Ordering::Relaxed);

    // 5. On Unix (ext4 / XFS), directories themselves allocate 4KB+ physical blocks (st_blocks)
    // that CLI disk usage tools (gdu, dua, dust, ncdu) include in the volume total.
    #[cfg(unix)]
    {
        use std::os::unix::fs::MetadataExt;
        let dir_blocks_bytes: u64 = plan
            .directories
            .par_iter()
            .map(|rel_dir| {
                let p = to_os_path(root, rel_dir);
                fs::symlink_metadata(&p)
                    .map(|m| m.blocks().saturating_mul(512))
                    .unwrap_or(0)
            })
            .sum();
        let root_blocks_bytes = fs::symlink_metadata(root)
            .map(|m| m.blocks().saturating_mul(512))
            .unwrap_or(0);
        total_allocated.fetch_add(dir_blocks_bytes + root_blocks_bytes, Ordering::Relaxed);
    }

    // 5b. On Windows, directories own NTFS index allocation that scanners reading "size on disk" include
    #[cfg(windows)]
    {
        let dir_alloc_bytes: u64 = plan
            .directories
            .par_iter()
            .map(|rel_dir| windows::dir_allocation_bytes(&to_os_path(root, rel_dir)))
            .sum();
        total_allocated.fetch_add(
            dir_alloc_bytes + windows::dir_allocation_bytes(root),
            Ordering::Relaxed,
        );
    }

    prof::report();
    let allocated_bytes = total_allocated.load(Ordering::Relaxed);
    let extra_hl_alloc = hardlink_extra_alloc.load(Ordering::Relaxed);

    plan.manifest.allocated_size_bytes = allocated_bytes;
    plan.manifest.allocated_files_only_bytes = files_only_bytes;
    plan.manifest.allocated_size_with_hardlinks_bytes = allocated_bytes + extra_hl_alloc;

    Ok(plan.manifest)
}

#[cfg(unix)]
fn create_platform_symlink(target: &Path, link: &Path, is_dir: bool) -> Result<()> {
    unix::create_symlink(target, link, is_dir)
}

#[cfg(windows)]
fn create_platform_symlink(target: &Path, link: &Path, is_dir: bool) -> Result<()> {
    windows::create_symlink(target, link, is_dir)
}

#[allow(dead_code)]
pub fn verify_entry_count(entries: &[FileEntry]) -> usize {
    entries.len()
}
