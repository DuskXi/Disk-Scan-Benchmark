use crate::topology::{compute_dirty_anchor_offsets, BLOCK_SIZE};
use anyhow::Result;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::mem::{size_of, zeroed};
use std::os::windows::ffi::OsStrExt;
use std::os::windows::fs::FileExt;
use std::os::windows::io::{AsRawHandle, FromRawHandle};
use std::path::Path;
use std::ptr::{null, null_mut};
use windows_sys::Wdk::Foundation::OBJECT_ATTRIBUTES;
use windows_sys::Wdk::Storage::FileSystem::NtCreateFile;
use windows_sys::Win32::Foundation::{
    CloseHandle, GENERIC_WRITE, HANDLE, INVALID_HANDLE_VALUE, UNICODE_STRING,
};
use windows_sys::Win32::Storage::FileSystem::{
    CreateFileW, FileStandardInfo, GetFileInformationByHandleEx, SetFileAttributesW, WriteFile,
    CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, FILE_FLAG_BACKUP_SEMANTICS, FILE_LIST_DIRECTORY,
    FILE_READ_ATTRIBUTES, FILE_SHARE_DELETE, FILE_SHARE_READ, FILE_SHARE_WRITE, FILE_STANDARD_INFO,
    OPEN_EXISTING, SYNCHRONIZE,
};
use windows_sys::Win32::System::Ioctl::{FSCTL_SET_COMPRESSION, FSCTL_SET_SPARSE};
use windows_sys::Win32::System::IO::{DeviceIoControl, IO_STATUS_BLOCK};

/// Directory handle used as the RootDirectory of relative NtCreateFile opens, the Windows counterpart of the
/// `openat(dir_fd, name)` fast path on Unix: it skips re-resolving (and re-ACL-checking) 8..25 path components
/// for every one of the million files created below the same directory.
pub struct DirHandle(HANDLE);

// A directory HANDLE may be used from any thread; it is only read by NtCreateFile.
unsafe impl Send for DirHandle {}
unsafe impl Sync for DirHandle {}

impl Drop for DirHandle {
    fn drop(&mut self) {
        unsafe {
            CloseHandle(self.0);
        }
    }
}

pub fn open_dir_handle(dir: &Path) -> Option<DirHandle> {
    let mut wide: Vec<u16> = Vec::with_capacity(dir.as_os_str().len() + 1);
    wide.extend(dir.as_os_str().encode_wide());
    wide.push(0);
    let h = unsafe {
        CreateFileW(
            wide.as_ptr(),
            FILE_LIST_DIRECTORY | SYNCHRONIZE,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            null(),
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS,
            0 as HANDLE,
        )
    };
    if h == INVALID_HANDLE_VALUE {
        None
    } else {
        Some(DirHandle(h))
    }
}

/// Allocated bytes of a directory (its `$INDEX_ALLOCATION` runs, roughly 150-500 bytes per entry on NTFS).
/// Scanners such as SpaceKnife include this in "size on disk"; the Unix materializer adds `st_blocks` of directories
/// for the same reason.
pub fn dir_allocation_bytes(dir: &Path) -> u64 {
    let mut wide: Vec<u16> = Vec::with_capacity(dir.as_os_str().len() + 1);
    wide.extend(dir.as_os_str().encode_wide());
    wide.push(0);
    let h = unsafe {
        CreateFileW(
            wide.as_ptr(),
            FILE_READ_ATTRIBUTES,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            null(),
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS,
            0 as HANDLE,
        )
    };
    if h == INVALID_HANDLE_VALUE {
        return 0;
    }
    let mut info: FILE_STANDARD_INFO = unsafe { zeroed() };
    let ok = unsafe {
        GetFileInformationByHandleEx(
            h,
            FileStandardInfo,
            &mut info as *mut _ as *mut _,
            size_of::<FILE_STANDARD_INFO>() as u32,
        )
    };
    unsafe {
        CloseHandle(h);
    }
    if ok != 0 && info.AllocationSize > 0 {
        info.AllocationSize as u64
    } else {
        0
    }
}

const FILE_OVERWRITE_IF: u32 = 5;
const FILE_NON_DIRECTORY_FILE: u32 = 0x40;
const FILE_SYNCHRONOUS_IO_NONALERT: u32 = 0x20;
const OBJ_CASE_INSENSITIVE: u32 = 0x40;

/// Creates (or truncates) `name` inside `dir` with a single relative NtCreateFile call.
fn nt_create_relative(dir: &DirHandle, name: &str) -> Option<HANDLE> {
    let wide: Vec<u16> = name.encode_utf16().collect();
    if wide.is_empty() || wide.len() > 255 {
        return None;
    }
    let byte_len = (wide.len() * 2) as u16;
    let us = UNICODE_STRING {
        Length: byte_len,
        MaximumLength: byte_len,
        Buffer: wide.as_ptr() as *mut u16,
    };
    let oa = OBJECT_ATTRIBUTES {
        Length: size_of::<OBJECT_ATTRIBUTES>() as u32,
        RootDirectory: dir.0,
        ObjectName: &us,
        Attributes: OBJ_CASE_INSENSITIVE,
        SecurityDescriptor: null(),
        SecurityQualityOfService: null(),
    };
    let mut iosb: IO_STATUS_BLOCK = unsafe { zeroed() };
    let mut handle: HANDLE = 0 as HANDLE;
    let status = unsafe {
        NtCreateFile(
            &mut handle,
            GENERIC_WRITE | SYNCHRONIZE,
            &oa,
            &mut iosb,
            null(),
            FILE_ATTRIBUTE_NORMAL,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            FILE_OVERWRITE_IF,
            FILE_NON_DIRECTORY_FILE | FILE_SYNCHRONOUS_IO_NONALERT,
            null(),
            0,
        )
    };
    if status >= 0 {
        Some(handle)
    } else {
        None
    }
}

/// Marks a directory as compressed so files created below it inherit the attribute.
pub fn compress_dir(dir: &Path) {
    let mut wide: Vec<u16> = Vec::with_capacity(dir.as_os_str().len() + 1);
    wide.extend(dir.as_os_str().encode_wide());
    wide.push(0);
    let h = unsafe {
        CreateFileW(
            wide.as_ptr(),
            0x8000_0000 | GENERIC_WRITE, // GENERIC_READ | GENERIC_WRITE
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            null(),
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS,
            0 as HANDLE,
        )
    };
    if h == INVALID_HANDLE_VALUE {
        return;
    }
    let format: u16 = 1; // COMPRESSION_FORMAT_DEFAULT
    let mut returned: u32 = 0;
    unsafe {
        DeviceIoControl(
            h,
            FSCTL_SET_COMPRESSION,
            &format as *const u16 as *const _,
            2,
            null_mut(),
            0,
            &mut returned,
            null_mut(),
        );
        CloseHandle(h);
    }
}

/// Adds the NTFS metadata a lived-in volume has: ~4% of files carry a `Zone.Identifier` alternate data stream
/// (downloaded files), ~2% are hidden+system and ~3% are read-only. `h` is a deterministic hash of the file.
pub fn decorate(path: &Path, h: u64) {
    let bucket = h % 100;
    if bucket >= 9 {
        return;
    }
    let mut wide: Vec<u16> = Vec::with_capacity(path.as_os_str().len() + 24);
    wide.extend(path.as_os_str().encode_wide());
    if bucket < 4 {
        let mut ads = wide.clone();
        ads.extend(":Zone.Identifier".encode_utf16());
        ads.push(0);
        let handle = unsafe {
            CreateFileW(
                ads.as_ptr(),
                GENERIC_WRITE,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                null(),
                CREATE_ALWAYS,
                FILE_ATTRIBUTE_NORMAL,
                0 as HANDLE,
            )
        };
        if handle != INVALID_HANDLE_VALUE {
            let data = b"[ZoneTransfer]\r\nZoneId=3\r\n";
            let mut written: u32 = 0;
            unsafe {
                WriteFile(
                    handle,
                    data.as_ptr(),
                    data.len() as u32,
                    &mut written,
                    null_mut(),
                );
                CloseHandle(handle);
            }
        }
    } else {
        wide.push(0);
        // 0x2 hidden | 0x4 system for buckets 4..6, 0x1 read-only for buckets 6..9
        let attrs: u32 = if bucket < 6 { 0x6 } else { 0x1 };
        unsafe {
            SetFileAttributesW(wide.as_ptr(), attrs);
        }
    }
}

pub fn create_sparse_anchored_file(
    dir: Option<&DirHandle>,
    file_name: &str,
    path: &Path,
    logical_size: u64,
    dirty_blocks: u8,
    fill_byte: u8,
    preallocate: bool,
) -> Result<u64> {
    use super::prof;
    let t = prof::start();
    let r = create_inner(
        dir,
        file_name,
        path,
        logical_size,
        dirty_blocks,
        fill_byte,
        preallocate,
    );
    if t.is_some() {
        let cat = if preallocate && logical_size > 0 {
            3
        } else if dirty_blocks == 0 && logical_size == 0 {
            0
        } else if dirty_blocks == 0 && logical_size <= 680 {
            1
        } else if dirty_blocks == 1 && logical_size <= BLOCK_SIZE {
            4
        } else {
            2
        };
        prof::stop(cat, t);
    }
    r
}

fn create_inner(
    dir: Option<&DirHandle>,
    file_name: &str,
    path: &Path,
    logical_size: u64,
    dirty_blocks: u8,
    fill_byte: u8,
    preallocate: bool,
) -> Result<u64> {
    // Relative open through the parent directory handle; falls back to the full-path open if it is refused.
    let rel_handle = dir.and_then(|d| nt_create_relative(d, file_name));

    // Ultra-fast path for 0-byte clean files: a single create + close.
    if dirty_blocks == 0 && logical_size == 0 {
        if let Some(h) = rel_handle {
            unsafe {
                CloseHandle(h);
            }
            return Ok(0);
        }
        // Relative open unavailable: single full-path CreateFileW + CloseHandle.
        let mut wide: Vec<u16> = Vec::with_capacity(path.as_os_str().len() + 1);
        wide.extend(path.as_os_str().encode_wide());
        wide.push(0);
        let h = unsafe {
            CreateFileW(
                wide.as_ptr(),
                GENERIC_WRITE,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                null(),
                CREATE_ALWAYS,
                FILE_ATTRIBUTE_NORMAL,
                0 as HANDLE,
            )
        };
        if h != INVALID_HANDLE_VALUE {
            unsafe {
                CloseHandle(h);
            }
            return Ok(0);
        }
    }

    let mut file = match rel_handle {
        Some(h) => unsafe { std::fs::File::from_raw_handle(h as _) },
        None => OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(path)?,
    };

    // Preallocated media: a plain (non-sparse) SetEndOfFile makes NTFS allocate every cluster immediately while the
    // valid data length stays 0, so a multi-hundred-GiB file costs a few metadata writes instead of real I/O.
    if preallocate && logical_size > 0 {
        file.set_len(logical_size)?;
        let alloc = query_allocation(file.as_raw_handle() as HANDLE);
        return Ok(alloc.unwrap_or(logical_size));
    }

    // Fast path 1: Tiny files <= 680B with dirty_blocks == 0 fit directly inside the 1KB NTFS $MFT record
    // as Resident $DATA (AllocationSize == 0 naturally without requiring FSCTL_SET_SPARSE).
    if dirty_blocks == 0 && logical_size <= 680 {
        if logical_size > 0 {
            file.set_len(logical_size)?;
        }
        return Ok(0);
    }

    // Fast path 2: Sampled 4KB dirty small files (dirty_blocks == 1, logical_size <= 4096)
    // A single sequential write sets both EndOfFile and allocates exactly one 4KB NTFS cluster.
    if dirty_blocks == 1 && logical_size > 0 && logical_size <= BLOCK_SIZE {
        let mut buf = [fill_byte; BLOCK_SIZE as usize];
        buf[0] = fill_byte ^ 0x5A;
        buf[buf.len() - 1] = fill_byte.wrapping_add(17).max(1);
        file.write_all(&buf[..logical_size as usize])?;
        return Ok(BLOCK_SIZE);
    }

    let raw_handle = file.as_raw_handle() as HANDLE;

    // Step 1: Mark file handle as sparse via FSCTL_SET_SPARSE when creating sparse holes
    // (either pure sparse files > 680B with dirty_blocks == 0, or large files >= 64KB with multi-extent runlists).
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
        // Compressed directories reject FSCTL_SET_SPARSE; the file then simply stays a normal (compressed) file.
        let _ = ok;
    }

    // Step 2: Set full logical size
    file.set_len(logical_size)?;

    if dirty_blocks == 0 {
        return Ok(0);
    }

    // Step 3: Write 4KB dirty anchor blocks at 4096-aligned offsets using seek_write
    if logical_size > 0 {
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
    Ok(query_allocation(raw_handle).unwrap_or((dirty_blocks as u64) * BLOCK_SIZE))
}

fn query_allocation(handle: HANDLE) -> Option<u64> {
    let mut std_info: FILE_STANDARD_INFO = unsafe { zeroed() };
    let info_ok = unsafe {
        GetFileInformationByHandleEx(
            handle,
            FileStandardInfo,
            &mut std_info as *mut _ as *mut _,
            size_of::<FILE_STANDARD_INFO>() as u32,
        )
    };
    if info_ok != 0 && std_info.AllocationSize >= 0 {
        Some(std_info.AllocationSize as u64)
    } else {
        None
    }
}

pub fn create_symlink(target: &Path, link: &Path, is_dir: bool) -> Result<()> {
    let norm_target = std::path::PathBuf::from(target.to_string_lossy().replace('/', "\\"));
    let norm_link = std::path::PathBuf::from(link.to_string_lossy().replace('/', "\\"));

    if norm_link.symlink_metadata().is_ok() {
        let _ = if is_dir {
            fs::remove_dir(&norm_link)
        } else {
            fs::remove_file(&norm_link)
        };
    }

    let res = if is_dir {
        std::os::windows::fs::symlink_dir(&norm_target, &norm_link)
    } else {
        std::os::windows::fs::symlink_file(&norm_target, &norm_link)
    };

    match res {
        Ok(()) => Ok(()),
        Err(_) => {
            // Fall back to NTFS Directory Junction (for dirs) or reference stub file
            // if CreateSymbolicLinkW is rejected by policy or volume reparse constraints
            if is_dir {
                let status = std::process::Command::new("cmd")
                    .args([
                        "/C",
                        "mklink",
                        "/J",
                        &norm_link.to_string_lossy(),
                        &norm_target.to_string_lossy(),
                    ])
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null())
                    .status();
                if let Ok(s) = status {
                    if s.success() {
                        return Ok(());
                    }
                }
                let _ = fs::create_dir_all(&norm_link);
                return Ok(());
            }
            fs::write(&norm_link, norm_target.to_string_lossy().as_bytes())?;
            Ok(())
        }
    }
}
