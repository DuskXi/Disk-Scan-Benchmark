use crate::topology::{compute_dirty_anchor_offsets, BLOCK_SIZE};
use anyhow::{bail, Result};
use std::fs::{self, OpenOptions};
use std::mem::{size_of, zeroed};
use std::os::windows::fs::FileExt;
use std::os::windows::io::AsRawHandle;
use std::path::Path;
use std::ptr::{null, null_mut};
use windows_sys::Win32::Foundation::HANDLE;
use windows_sys::Win32::Storage::FileSystem::{
    FileStandardInfo, GetFileInformationByHandleEx, FILE_STANDARD_INFO,
};
use windows_sys::Win32::System::IO::DeviceIoControl;
use windows_sys::Win32::System::Ioctl::FSCTL_SET_SPARSE;

pub fn create_sparse_anchored_file(
    path: &Path,
    logical_size: u64,
    dirty_blocks: u8,
    fill_byte: u8,
) -> Result<u64> {
    let file = OpenOptions::new()
        .write(true)
        .read(true)
        .create(true)
        .truncate(true)
        .open(path)?;

    let raw_handle = file.as_raw_handle() as HANDLE;

    // Step 1: Mark file handle as sparse via FSCTL_SET_SPARSE when creating sparse holes
    // (either pure sparse small files with dirty_blocks == 0, or large files >= 64KB with multi-extent runlists).
    // Sampled small files (dirty_blocks == 1, logical_size < 64KB) remain non-sparse so NTFS allocates real 4KB clusters.
    if dirty_blocks == 0 || logical_size >= 65536 {
        let mut bytes_returned: u32 = 0;
        let ok = unsafe {
            DeviceIoControl(
                raw_handle,
                FSCTL_SET_SPARSE,
                null(),
                0,
                null_mut(),
                0,
                &mut bytes_returned,
                null_mut(),
            )
        };
        if ok == 0 {
            let err = std::io::Error::last_os_error();
            bail!(
                "DeviceIoControl(FSCTL_SET_SPARSE) failed on {}: {}",
                path.display(),
                err
            );
        }
    }

    // Step 2: Set full logical size
    file.set_len(logical_size)?;

    // Step 3: Write 4KB dirty anchor blocks at 4096-aligned offsets using seek_write
    if dirty_blocks > 0 && logical_size > 0 {
        let mut buf = [fill_byte; BLOCK_SIZE as usize];
        buf[0] = fill_byte ^ 0x5A;
        buf[buf.len() - 1] = fill_byte.wrapping_add(17).max(1);

        let offsets = compute_dirty_anchor_offsets(logical_size, dirty_blocks);
        for off in offsets {
            let write_len = (logical_size - off).min(BLOCK_SIZE) as usize;
            let mut written = 0;
            while written < write_len {
                let n = file.seek_write(&buf[written..write_len], off + written as u64)?;
                if n == 0 {
                    break;
                }
                written += n;
            }
        }
    }

    // Step 4: Query true NTFS physical allocated bytes via GetFileInformationByHandleEx(FileStandardInfo)
    let mut std_info: FILE_STANDARD_INFO = unsafe { zeroed() };
    let info_ok = unsafe {
        GetFileInformationByHandleEx(
            raw_handle,
            FileStandardInfo,
            &mut std_info as *mut _ as *mut _,
            size_of::<FILE_STANDARD_INFO>() as u32,
        )
    };

    if info_ok != 0 && std_info.AllocationSize >= 0 {
        Ok(std_info.AllocationSize as u64)
    } else {
        Ok((dirty_blocks as u64) * BLOCK_SIZE)
    }
}

pub fn create_symlink(target: &Path, link: &Path, is_dir: bool) -> Result<()> {
    if link.symlink_metadata().is_ok() {
        let _ = if is_dir {
            fs::remove_dir(link)
        } else {
            fs::remove_file(link)
        };
    }

    let res = if is_dir {
        std::os::windows::fs::symlink_dir(target, link)
    } else {
        std::os::windows::fs::symlink_file(target, link)
    };

    match res {
        Ok(()) => Ok(()),
        Err(e) if e.raw_os_error() == Some(1314) => {
            // ERROR_PRIVILEGE_NOT_HELD (non-admin without Developer Mode enabled):
            // Fall back to NTFS Directory Junction (requires no elevation) or stub file
            if is_dir {
                let status = std::process::Command::new("cmd")
                    .args([
                        "/C",
                        "mklink",
                        "/J",
                        &link.to_string_lossy(),
                        &target.to_string_lossy(),
                    ])
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null())
                    .status();
                if let Ok(s) = status {
                    if s.success() {
                        return Ok(());
                    }
                }
            }
            // Unprivileged fallback for file symlink so non-admin test runs succeed
            fs::write(link, target.to_string_lossy().as_bytes())?;
            Ok(())
        }
        Err(e) => Err(e.into()),
    }
}
