use crate::topology::{EntryKind, FileEntry, GroundTruthManifest, TopologyPlan};
use anyhow::{Context, Result};
use rayon::prelude::*;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;

#[cfg(unix)]
mod unix;
#[cfg(windows)]
mod windows;

pub fn to_os_path(root: &Path, rel_path: &str) -> PathBuf {
    let mut p = root.to_path_buf();
    for seg in rel_path.split('/').filter(|s| !s.is_empty()) {
        p.push(seg);
    }
    p
}

pub fn materialize_tree(root: &Path, mut plan: TopologyPlan) -> Result<GroundTruthManifest> {
    fs::create_dir_all(root)
        .with_context(|| format!("Failed to create root directory: {}", root.display()))?;

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
        level_dirs.par_iter().try_for_each(|rel_dir| -> Result<()> {
            let full_dir = to_os_path(root, rel_dir);
            match fs::create_dir(&full_dir) {
                Ok(()) => Ok(()),
                Err(e) if e.kind() == io::ErrorKind::AlreadyExists => Ok(()),
                Err(_) => fs::create_dir_all(&full_dir)
                    .with_context(|| format!("Failed to create directory: {}", full_dir.display())),
            }
        })?;
    }

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
    let hl_alloc_map: Mutex<HashMap<&str, u64>> = Mutex::new(HashMap::with_capacity(hardlink_targets.len().min(65536)));

    // 2. Group regular files by parent directory to minimize per-directory B-Tree lock contention on NTFS / APFS
    let mut dir_groups: HashMap<&str, Vec<&FileEntry>> = HashMap::with_capacity(plan.directories.len().max(64));
    for entry in &plan.regular_files {
        let parent = entry.rel_path.rsplit_once('/').map(|(p, _)| p).unwrap_or("");
        dir_groups.entry(parent).or_default().push(entry);
    }

    // Split very large flat directories into coarse batches (25,000 files) so work balances across cores
    // without 8 threads hammering the exact same directory inode on every single file.
    let mut work_batches: Vec<(&str, Vec<&FileEntry>)> = Vec::with_capacity(dir_groups.len() + 16);
    for (parent, entries) in dir_groups {
        if entries.len() <= 25_000 {
            work_batches.push((parent, entries));
        } else {
            for chunk in entries.chunks(25_000) {
                work_batches.push((parent, chunk.to_vec()));
            }
        }
    }

    let total_allocated = AtomicU64::new(0);
    work_batches
        .par_iter()
        .try_for_each(|(parent_rel, entries)| -> Result<()> {
            let parent_dir = to_os_path(root, parent_rel);
            let mut local_alloc_sum: u64 = 0;
            let mut local_hl_hits: Vec<(&str, u64)> = Vec::new();

            for entry in entries {
                let file_name = entry
                    .rel_path
                    .rsplit_once('/')
                    .map(|(_, f)| f)
                    .unwrap_or(entry.rel_path.as_str());
                let full_path = parent_dir.join(file_name);
                let alloc = match entry.kind {
                    EntryKind::RegularFile {
                        logical_size,
                        dirty_blocks,
                        fill_byte,
                    } => create_sparse_anchored_file(&full_path, logical_size, dirty_blocks, fill_byte)
                        .with_context(|| format!("Failed to materialize file {}", full_path.display()))?,
                    _ => 0,
                };
                local_alloc_sum += alloc;
                if alloc > 0 && hardlink_targets.contains(entry.rel_path.as_str()) {
                    local_hl_hits.push((entry.rel_path.as_str(), alloc));
                }
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
        })?;

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
                if dst_path.exists() {
                    let _ = fs::remove_file(&dst_path);
                }
                fs::hard_link(&src_path, &dst_path).with_context(|| {
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

    // 4. Materialize symlinks / junctions
    plan.symlinks.par_iter().try_for_each(|entry| -> Result<()> {
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

    let allocated_bytes = total_allocated.load(Ordering::Relaxed);
    let extra_hl_alloc = hardlink_extra_alloc.load(Ordering::Relaxed);

    plan.manifest.allocated_size_bytes = allocated_bytes;
    plan.manifest.allocated_size_with_hardlinks_bytes = allocated_bytes + extra_hl_alloc;

    Ok(plan.manifest)
}

#[cfg(unix)]
fn create_sparse_anchored_file(
    path: &Path,
    logical_size: u64,
    dirty_blocks: u8,
    fill_byte: u8,
) -> Result<u64> {
    unix::create_sparse_anchored_file(path, logical_size, dirty_blocks, fill_byte)
}

#[cfg(windows)]
fn create_sparse_anchored_file(
    path: &Path,
    logical_size: u64,
    dirty_blocks: u8,
    fill_byte: u8,
) -> Result<u64> {
    windows::create_sparse_anchored_file(path, logical_size, dirty_blocks, fill_byte)
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
