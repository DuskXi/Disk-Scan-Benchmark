use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetaProbeResult {
    pub files_scanned: u64,
    pub dirs_scanned: u64,
    pub total_logical_bytes: u64,
    pub elapsed_ms: f64,
    pub b_meta_files_per_sec: f64,
}

pub fn run_meta_probe(root: &Path) -> Result<MetaProbeResult> {
    let files_count = AtomicU64::new(0);
    let dirs_count = AtomicU64::new(0);
    let bytes_count = AtomicU64::new(0);

    // On Windows, canonicalize returns the `\\?\` extended-length path prefix
    // so FindFirstFileExW can traverse deep directories exceeding MAX_PATH (260 chars).
    let scan_root = std::fs::canonicalize(root).unwrap_or_else(|_| root.to_path_buf());

    let t0 = Instant::now();

    rayon::scope(|s| {
        traverse_dir(&scan_root, s, &files_count, &dirs_count, &bytes_count);
    });

    let elapsed = t0.elapsed();
    let elapsed_secs = elapsed.as_secs_f64().max(1e-6);
    let elapsed_ms = elapsed_secs * 1000.0;
    let files = files_count.load(Ordering::Relaxed);
    let dirs = dirs_count.load(Ordering::Relaxed);
    let total_bytes = bytes_count.load(Ordering::Relaxed);

    let b_meta_files_per_sec = (files as f64) / elapsed_secs;

    Ok(MetaProbeResult {
        files_scanned: files,
        dirs_scanned: dirs,
        total_logical_bytes: total_bytes,
        elapsed_ms,
        b_meta_files_per_sec,
    })
}

#[cfg(unix)]
fn traverse_dir<'s>(
    dir: &Path,
    scope: &rayon::Scope<'s>,
    files_count: &'s AtomicU64,
    dirs_count: &'s AtomicU64,
    bytes_count: &'s AtomicU64,
) {
    let read_dir = match std::fs::read_dir(dir) {
        Ok(rd) => rd,
        Err(_) => return,
    };

    let mut local_dirs = 0u64;
    let mut file_batch: Vec<std::path::PathBuf> = Vec::new();

    for entry in read_dir.flatten() {
        let ft = match entry.file_type() {
            Ok(ft) => ft,
            Err(_) => continue,
        };
        if ft.is_dir() && !ft.is_symlink() {
            local_dirs += 1;
            let child_path = entry.path();
            scope.spawn(move |s| {
                traverse_dir(&child_path, s, files_count, dirs_count, bytes_count);
            });
        } else {
            file_batch.push(entry.path());
            if file_batch.len() >= 512 {
                let chunk = std::mem::take(&mut file_batch);
                scope.spawn(move |_| {
                    stat_file_chunk(&chunk, files_count, bytes_count);
                });
            }
        }
    }

    if !file_batch.is_empty() {
        stat_file_chunk(&file_batch, files_count, bytes_count);
    }
    if local_dirs > 0 {
        dirs_count.fetch_add(local_dirs, Ordering::Relaxed);
    }
}

#[cfg(unix)]
fn stat_file_chunk(
    paths: &[std::path::PathBuf],
    files_count: &AtomicU64,
    bytes_count: &AtomicU64,
) {
    let mut local_files = 0u64;
    let mut local_bytes = 0u64;
    for p in paths {
        local_files += 1;
        if let Ok(meta) = std::fs::symlink_metadata(p) {
            if meta.is_file() {
                local_bytes += meta.len();
            }
        }
    }
    if local_files > 0 {
        files_count.fetch_add(local_files, Ordering::Relaxed);
    }
    if local_bytes > 0 {
        bytes_count.fetch_add(local_bytes, Ordering::Relaxed);
    }
}

#[cfg(windows)]
fn traverse_dir<'s>(
    dir: &Path,
    scope: &rayon::Scope<'s>,
    files_count: &'s AtomicU64,
    dirs_count: &'s AtomicU64,
    bytes_count: &'s AtomicU64,
) {
    use std::ffi::OsString;
    use std::mem::zeroed;
    use std::os::windows::ffi::{OsStrExt, OsStringExt};
    use std::ptr::null_mut;
    use windows_sys::Win32::Foundation::INVALID_HANDLE_VALUE;
    use windows_sys::Win32::Storage::FileSystem::{
        FindClose, FindExInfoBasic, FindExSearchNameMatch, FindFirstFileExW, FindNextFileW,
        FILE_ATTRIBUTE_DIRECTORY, FILE_ATTRIBUTE_REPARSE_POINT, FIND_FIRST_EX_LARGE_FETCH,
        WIN32_FIND_DATAW,
    };

    let mut search_pattern = dir.as_os_str().to_os_string();
    let bytes = search_pattern.as_encoded_bytes();
    if !bytes.ends_with(b"\\") && !bytes.ends_with(b"/") {
        search_pattern.push("\\*");
    } else {
        search_pattern.push("*");
    }
    let wide_pattern: Vec<u16> = search_pattern.encode_wide().chain(std::iter::once(0)).collect();

    let mut find_data: WIN32_FIND_DATAW = unsafe { zeroed() };
    let handle = unsafe {
        FindFirstFileExW(
            wide_pattern.as_ptr(),
            FindExInfoBasic,
            &mut find_data as *mut _ as *mut _,
            FindExSearchNameMatch,
            null_mut(),
            FIND_FIRST_EX_LARGE_FETCH,
        )
    };

    if handle == INVALID_HANDLE_VALUE {
        return;
    }

    let mut local_files = 0u64;
    let mut local_dirs = 0u64;
    let mut local_bytes = 0u64;

    loop {
        let name_slice = &find_data.cFileName;
        let len = name_slice.iter().position(|&c| c == 0).unwrap_or(name_slice.len());
        let is_dot = (len == 1 && name_slice[0] == b'.' as u16)
            || (len == 2 && name_slice[0] == b'.' as u16 && name_slice[1] == b'.' as u16);

        if !is_dot {
            let attrs = find_data.dwFileAttributes;
            let is_dir = (attrs & FILE_ATTRIBUTE_DIRECTORY) != 0;
            let is_reparse = (attrs & FILE_ATTRIBUTE_REPARSE_POINT) != 0;

            if is_dir && !is_reparse {
                local_dirs += 1;
                let child_name = OsString::from_wide(&name_slice[..len]);
                let child_path = dir.join(child_name);
                scope.spawn(move |s| {
                    traverse_dir(&child_path, s, files_count, dirs_count, bytes_count);
                });
            } else {
                local_files += 1;
                if !is_dir {
                    let size = ((find_data.nFileSizeHigh as u64) << 32) | (find_data.nFileSizeLow as u64);
                    local_bytes += size;
                }
            }
        }

        let has_next = unsafe { FindNextFileW(handle, &mut find_data) };
        if has_next == 0 {
            break;
        }
    }

    unsafe {
        FindClose(handle);
    }

    if local_files > 0 {
        files_count.fetch_add(local_files, Ordering::Relaxed);
    }
    if local_dirs > 0 {
        dirs_count.fetch_add(local_dirs, Ordering::Relaxed);
    }
    if local_bytes > 0 {
        bytes_count.fetch_add(local_bytes, Ordering::Relaxed);
    }
}
