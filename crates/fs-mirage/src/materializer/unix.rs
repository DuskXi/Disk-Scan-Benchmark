use crate::topology::{compute_dirty_anchor_offsets, BLOCK_SIZE};
use anyhow::Result;
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::os::unix::fs::{FileExt, MetadataExt};
use std::os::unix::io::{AsRawFd, RawFd};
use std::path::Path;

/// The access time of an open file (super::set_old_atime), the modification time left alone.
fn stamp_fd(fd: RawFd) {
    if let Some(secs) = super::old_atime() {
        let times = [
            libc::timespec {
                tv_sec: secs as libc::time_t,
                tv_nsec: 0,
            },
            libc::timespec {
                tv_sec: 0,
                tv_nsec: libc::UTIME_OMIT as _,
            },
        ];
        unsafe {
            libc::futimens(fd, times.as_ptr());
        }
    }
}

/// Stamps the file when dropped, i.e. after everything was written to it and before it is closed.
struct Stamp(RawFd);

impl Drop for Stamp {
    fn drop(&mut self) {
        stamp_fd(self.0);
    }
}

pub fn open_dir_fd(dir: &Path) -> Option<File> {
    File::open(dir).ok()
}

pub fn create_sparse_anchored_file(
    dir_fd: Option<&File>,
    file_name: &str,
    path: &Path,
    logical_size: u64,
    dirty_blocks: u8,
    fill_byte: u8,
    preallocate: bool,
) -> Result<u64> {
    // Ultra-fast path for 0-byte clean files using openat(dir_fd, file_name) with stack buffer:
    // bypasses 8..25 levels of VFS namei() path resolution and skips ftruncate().
    if dirty_blocks == 0 && logical_size == 0 {
        if let Some(dfd) = dir_fd {
            let name_bytes = file_name.as_bytes();
            if !name_bytes.is_empty() && name_bytes.len() < 255 && !name_bytes.contains(&0) {
                let mut stack_buf = [0u8; 256];
                stack_buf[..name_bytes.len()].copy_from_slice(name_bytes);
                let fd = unsafe {
                    libc::openat(
                        dfd.as_raw_fd(),
                        stack_buf.as_ptr() as *const libc::c_char,
                        libc::O_WRONLY | libc::O_CREAT | libc::O_TRUNC | libc::O_CLOEXEC,
                        0o644,
                    )
                };
                if fd >= 0 {
                    stamp_fd(fd);
                    unsafe {
                        libc::close(fd);
                    }
                    return Ok(0);
                }
            }
        }
    }

    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(path)?;
    let _stamp = Stamp(file.as_raw_fd()); // dropped before `file`

    // Preallocated media: fallocate() reserves every block as an unwritten extent (st_blocks reports the full size)
    // without writing data. Other Unixes (macOS/APFS) cannot do this and fall through to the sparse path below.
    #[cfg(target_os = "linux")]
    if preallocate && logical_size > 0 {
        let rc = unsafe { libc::fallocate(file.as_raw_fd(), 0, 0, logical_size as libc::off_t) };
        if rc == 0 {
            return Ok(file.metadata()?.blocks().saturating_mul(512));
        }
        eprintln!(
            "[fs-mirage] fallocate({} bytes) failed for {}: {}; falling back to a sparse file",
            logical_size,
            path.display(),
            std::io::Error::last_os_error()
        );
    }
    #[cfg(not(target_os = "linux"))]
    let _ = preallocate;

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
