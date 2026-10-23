use crate::topology::{compute_dirty_anchor_offsets, BLOCK_SIZE};
use anyhow::Result;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::os::unix::fs::{FileExt, MetadataExt};
use std::path::Path;

pub fn create_sparse_anchored_file(
    path: &Path,
    logical_size: u64,
    dirty_blocks: u8,
    fill_byte: u8,
) -> Result<u64> {
    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(path)?;

    if dirty_blocks == 0 || logical_size == 0 {
        if logical_size > 0 {
            file.set_len(logical_size)?;
        }
        return Ok(0);
    }

    let mut buf = [fill_byte; BLOCK_SIZE as usize];
    // Mix deterministic non-zero header/footer inside block to defeat inline zero-page dedup
    buf[0] = fill_byte ^ 0x5A;
    buf[buf.len() - 1] = fill_byte.wrapping_add(17).max(1);

    // Fast path for single-block sampled small files: single write_all sets both size and 4KB block
    if dirty_blocks == 1 && logical_size <= BLOCK_SIZE {
        file.write_all(&buf[..logical_size as usize])?;
        return Ok(BLOCK_SIZE);
    }

    // Establish full logical size (creates implicit sparse hole on ext4 / APFS / XFS)
    file.set_len(logical_size)?;

    let offsets = compute_dirty_anchor_offsets(logical_size, dirty_blocks);
    for off in offsets {
        let write_len = (logical_size - off).min(BLOCK_SIZE) as usize;
        file.write_all_at(&buf[..write_len], off)?;
    }

    let meta = file.metadata()?;
    Ok(meta.blocks().saturating_mul(512))
}

pub fn create_symlink(target: &Path, link: &Path, _is_dir: bool) -> Result<()> {
    if link.symlink_metadata().is_ok() {
        let _ = fs::remove_file(link);
    }
    std::os::unix::fs::symlink(target, link)?;
    Ok(())
}
