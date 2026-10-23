use crate::topology::{EntryKind, FileEntry, GroundTruthManifest, TopologyPlan};
use anyhow::{Context, Result};
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

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

    // 1. Group directories by depth so each depth level can be created in parallel safely
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
            fs::create_dir_all(&full_dir)
                .with_context(|| format!("Failed to create directory: {}", full_dir.display()))?;
            Ok(())
        })?;
    }

    // 2. Materialize regular & sparse files concurrently using rayon
    let total_allocated = AtomicU64::new(0);
    let per_file_alloc: Vec<(String, u64)> = plan
        .regular_files
        .par_iter()
        .map(|entry| -> Result<(String, u64)> {
            let full_path = to_os_path(root, &entry.rel_path);
            let alloc = match entry.kind {
                EntryKind::RegularFile {
                    logical_size,
                    dirty_blocks,
                    fill_byte,
                } => create_sparse_anchored_file(&full_path, logical_size, dirty_blocks, fill_byte)
                    .with_context(|| format!("Failed to materialize file {}", full_path.display()))?,
                _ => 0,
            };
            total_allocated.fetch_add(alloc, Ordering::Relaxed);
            Ok((entry.rel_path.clone(), alloc))
        })
        .collect::<Result<Vec<_>>>()?;

    let alloc_map: HashMap<String, u64> = per_file_alloc.into_iter().collect();

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
                if let Some(&target_alloc) = alloc_map.get(target_rel_path) {
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
