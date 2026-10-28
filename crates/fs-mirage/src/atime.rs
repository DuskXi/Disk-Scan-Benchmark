//! Access-time reset for the timed scans, which run with the platform's daily-use access-time setting on.
//!
//! Before each scanner's cold scan every file and folder under the root gets an access time two days back, so every
//! daily-use policy (Linux relatime: older than a day; Windows NTFS: more than an hour off) updates whatever the scan
//! touches, and no scanner inherits fresh access times from the one before it.

use rayon::prelude::*;
use std::fs::{self, File, FileTimes};
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime};

/// Sets the access time of every file and folder under `root` (symlinks skipped, modification times kept) to `age`
/// ago. Returns (entries set, entries that failed).
pub fn reset_access_times(root: &Path, age: Duration) -> (usize, usize) {
    // List everything first, one folder level at a time: listing a folder updates its access time, so no folder may
    // be listed after its time is set.
    let mut levels: Vec<Vec<PathBuf>> = vec![vec![root.to_path_buf()]];
    let mut files: Vec<PathBuf> = Vec::new();
    loop {
        let listed: Vec<(Vec<PathBuf>, Vec<PathBuf>)> = levels
            .last()
            .expect("at least the root level")
            .par_iter()
            .map(|d| list(d))
            .collect();
        let mut next = Vec::new();
        for (dirs, fs_) in listed {
            next.extend(dirs);
            files.extend(fs_);
        }
        if next.is_empty() {
            break;
        }
        levels.push(next);
    }

    let when = SystemTime::now() - age;
    // Files before folders, deeper folders before their parents: on NTFS setting an entry's times updates its
    // folder's index, which counts as an access to that folder.
    let mut ok = files.par_iter().filter(|p| set_accessed(p, when)).count();
    for level in levels.iter().rev() {
        ok += level.par_iter().filter(|p| set_accessed(p, when)).count();
    }
    let total = files.len() + levels.iter().map(Vec::len).sum::<usize>();
    (ok, total - ok)
}

fn list(dir: &Path) -> (Vec<PathBuf>, Vec<PathBuf>) {
    let mut dirs = Vec::new();
    let mut files = Vec::new();
    if let Ok(rd) = fs::read_dir(dir) {
        for e in rd.flatten() {
            let Ok(ft) = e.file_type() else { continue };
            if ft.is_symlink() {
                continue;
            }
            if ft.is_dir() {
                dirs.push(e.path());
            } else {
                files.push(e.path());
            }
        }
    }
    (dirs, files)
}

/// Only the access time changes: an unset FileTimes field is left alone (UTIME_OMIT / a NULL pointer to SetFileTime).
fn set_accessed(path: &Path, when: SystemTime) -> bool {
    match open_for_times(path) {
        Ok(f) => f.set_times(FileTimes::new().set_accessed(when)).is_ok(),
        Err(_) => false,
    }
}

#[cfg(unix)]
fn open_for_times(path: &Path) -> std::io::Result<File> {
    // opening (without reading) never updates the access time; futimens on the handle needs no write access
    File::open(path)
}

#[cfg(windows)]
fn open_for_times(path: &Path) -> std::io::Result<File> {
    use std::fs::OpenOptions;
    use std::os::windows::fs::OpenOptionsExt;
    const FILE_WRITE_ATTRIBUTES: u32 = 0x0100;
    const FILE_FLAG_BACKUP_SEMANTICS: u32 = 0x0200_0000; // folders can be opened
    const FILE_FLAG_OPEN_REPARSE_POINT: u32 = 0x0020_0000;
    OpenOptions::new()
        .access_mode(FILE_WRITE_ATTRIBUTES)
        .share_mode(0x7) // read, write, delete
        .custom_flags(FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT)
        .open(path)
}
