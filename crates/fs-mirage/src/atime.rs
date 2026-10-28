//! Access-time reset for the timed scans, which run with the platform's daily-use access-time setting on.
//!
//! Every cold scan must meet access times two days old on every file and folder, so every daily-use policy (Linux
//! relatime: older than a day; Windows: more than an hour off) updates whatever the scan touches, and no scanner
//! inherits fresh access times from the one before it. On Windows the CI sets them back once and then gives each
//! scanner a fresh copy of that volume (scripts/disk-mgr/windows_vhd.ps1 freeze). On Linux and
//! macOS this runs before every cold scan, so it only rewrites what moved: the scans there update the folders they
//! list, while reading a file's metadata leaves its access time alone.

use rayon::prelude::*;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime};

/// What a reset did: entries set, entries that failed, files skipped because their access time was still old.
pub struct Reset {
    pub set: usize,
    pub failed: usize,
    pub unchanged: usize,
}

/// Sets the access time of every folder, and of every file whose access time moved since the last reset, under
/// `root` (symlinks skipped, modification times kept) to `age` ago.
pub fn reset_access_times(root: &Path, age: Duration) -> Reset {
    let when = SystemTime::now() - age;
    // a file whose access time is older than this was not accessed since an earlier reset (or is old anyway)
    let stale = when + Duration::from_secs(3600);
    // List everything first, one folder level at a time: listing a folder updates its access time, so no folder may
    // be listed after its time is set, and every folder is set (this listing just touched it).
    let mut levels: Vec<Vec<PathBuf>> = vec![vec![root.to_path_buf()]];
    let mut files: Vec<PathBuf> = Vec::new();
    let mut unchanged = 0;
    loop {
        let listed: Vec<Listing> = levels
            .last()
            .expect("at least the root level")
            .par_iter()
            .map(|d| list(d, stale))
            .collect();
        let mut next = Vec::new();
        for l in listed {
            next.extend(l.dirs);
            files.extend(l.files);
            unchanged += l.unchanged;
        }
        if next.is_empty() {
            break;
        }
        levels.push(next);
    }

    // Files before folders, deeper folders before their parents: on NTFS setting an entry's times updates its
    // folder's index, which counts as an access to that folder.
    let mut set = files.par_iter().filter(|p| set_accessed(p, when)).count();
    for level in levels.iter().rev() {
        set += level.par_iter().filter(|p| set_accessed(p, when)).count();
    }
    let total = files.len() + levels.iter().map(Vec::len).sum::<usize>();
    Reset {
        set,
        failed: total - set,
        unchanged,
    }
}

struct Listing {
    dirs: Vec<PathBuf>,
    files: Vec<PathBuf>,
    unchanged: usize,
}

fn list(dir: &Path, stale: SystemTime) -> Listing {
    let mut out = Listing {
        dirs: Vec::new(),
        files: Vec::new(),
        unchanged: 0,
    };
    if let Ok(rd) = fs::read_dir(dir) {
        for e in rd.flatten() {
            let Ok(ft) = e.file_type() else { continue };
            if ft.is_symlink() {
                continue;
            }
            if ft.is_dir() {
                out.dirs.push(e.path());
            } else if still_stale(&e, stale) {
                out.unchanged += 1;
            } else {
                out.files.push(e.path());
            }
        }
    }
    out
}

/// Unix: lstat, which leaves the access time alone. Windows: always rewritten, since what a folder listing reports
/// there is the folder index's copy of the times, which NTFS may update later than the file's own.
#[cfg(unix)]
fn still_stale(e: &fs::DirEntry, stale: SystemTime) -> bool {
    e.metadata()
        .and_then(|m| m.accessed())
        .is_ok_and(|t| t <= stale)
}

#[cfg(windows)]
fn still_stale(_e: &fs::DirEntry, _stale: SystemTime) -> bool {
    false
}

/// Only the access time changes; the modification time is left alone.
#[cfg(unix)]
fn set_accessed(path: &Path, when: SystemTime) -> bool {
    use std::os::unix::ffi::OsStrExt;
    let Ok(c) = std::ffi::CString::new(path.as_os_str().as_bytes()) else {
        return false;
    };
    let secs = when
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
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
    // one call by path, no open and close per entry
    unsafe {
        libc::utimensat(
            libc::AT_FDCWD,
            c.as_ptr(),
            times.as_ptr(),
            libc::AT_SYMLINK_NOFOLLOW,
        ) == 0
    }
}

/// Only the access time changes: an unset FileTimes field is a NULL pointer to SetFileTime.
#[cfg(windows)]
fn set_accessed(path: &Path, when: SystemTime) -> bool {
    use std::fs::{FileTimes, OpenOptions};
    use std::os::windows::fs::OpenOptionsExt;
    const FILE_WRITE_ATTRIBUTES: u32 = 0x0100;
    const FILE_FLAG_BACKUP_SEMANTICS: u32 = 0x0200_0000; // folders can be opened
    const FILE_FLAG_OPEN_REPARSE_POINT: u32 = 0x0020_0000;
    OpenOptions::new()
        .access_mode(FILE_WRITE_ATTRIBUTES)
        .share_mode(0x7) // read, write, delete
        .custom_flags(FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT)
        .open(path)
        .and_then(|f| f.set_times(FileTimes::new().set_accessed(when)))
        .is_ok()
}
