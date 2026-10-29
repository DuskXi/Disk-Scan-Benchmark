//! Access-time reset for the timed scans, which run with the platform's daily-use access-time setting on.
//!
//! Every cold scan must meet access times two days old on every file and folder, so every daily-use policy (Linux
//! relatime: older than a day; Windows: more than an hour off) updates whatever the scan touches, and no scanner
//! inherits fresh access times from the one before it. Files are created with old access times
//! (materializer::set_old_atime). On Windows the CI sets the rest back once while last-access updates are still off (a
//! listing then changes nothing, so only what moved is set) and gives each scanner a fresh copy of that volume
//! (scripts/disk-mgr/windows_vhd.ps1 freeze). On Linux and macOS this runs before every cold scan: the scans there
//! update the folders they list, while reading a file's metadata leaves its access time alone.

use rayon::prelude::*;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime};

/// Which files to set back.
#[derive(Clone, Copy, PartialEq, Eq, Debug, clap::ValueEnum)]
pub enum Files {
    /// Those whose access time moved (read from the listing)
    Moved,
    /// Every file
    All,
    /// None: the scans on this platform leave files' access times alone (macOS: each reset otherwise reads every
    /// file's metadata, which on a high tree took 40-60 minutes per scanner)
    None,
}

/// Which folders to set back.
#[derive(Clone, Copy, PartialEq, Eq, Debug, clap::ValueEnum)]
pub enum Dirs {
    /// Every folder: listing a folder updates its access time when updates are on, so each must be set after
    All,
    /// Those whose access time moved: only right while last-access updates are off (Windows before the scans)
    Moved,
}

/// What a reset did: entries set, entries that failed, entries skipped because their access time was still old.
pub struct Reset {
    pub set: usize,
    pub failed: usize,
    pub unchanged: usize,
}

/// Sets access times under `root` (symlinks skipped, modification times kept) to `age` ago: the folders and files
/// `dirs` and `files` select. With `dir_list` (only with `Files::None` and `Dirs::All`) the folders are read from that
/// file when it exists instead of walking the tree, and saved there when it does not.
pub fn reset_access_times(
    root: &Path,
    age: Duration,
    files: Files,
    dirs: Dirs,
    dir_list: Option<&Path>,
) -> Reset {
    let when = SystemTime::now() - age;
    // an entry whose access time is older than this was not accessed since an earlier reset (or is old anyway)
    let stale = when + Duration::from_secs(3600);
    let cached = dir_list.filter(|_| files == Files::None && dirs == Dirs::All);
    if let Some(saved) = cached.and_then(|p| fs::read_to_string(p).ok()) {
        let mut paths: Vec<PathBuf> = saved.lines().map(PathBuf::from).collect();
        paths.reverse(); // saved shallow first: deeper folders before their parents
        let set = paths.par_iter().filter(|p| set_accessed(p, when)).count();
        return Reset {
            set,
            failed: paths.len() - set,
            unchanged: 0,
        };
    }

    // List everything first, one folder level at a time: listing a folder may update its access time, so no folder
    // may be listed after its time is set.
    let mut levels: Vec<Vec<PathBuf>> = vec![vec![root.to_path_buf()]];
    let mut set_dirs: Vec<Vec<PathBuf>> = vec![vec![root.to_path_buf()]];
    let mut set_files: Vec<PathBuf> = Vec::new();
    let mut unchanged = 0;
    loop {
        let listed: Vec<Listing> = levels
            .last()
            .expect("at least the root level")
            .par_iter()
            .map(|d| list(d, stale, files, dirs))
            .collect();
        let mut next = Vec::new();
        let mut next_set = Vec::new();
        for l in listed {
            next.extend(l.dirs);
            next_set.extend(l.set_dirs);
            set_files.extend(l.files);
            unchanged += l.unchanged;
        }
        if next.is_empty() {
            break;
        }
        levels.push(next);
        set_dirs.push(next_set);
    }
    if let Some(p) = cached {
        if let Ok(mut f) = fs::File::create(p) {
            for d in set_dirs.iter().flatten() {
                let _ = writeln!(f, "{}", d.display());
            }
        }
    }

    // Files before folders, deeper folders before their parents: on NTFS setting an entry's times updates its
    // folder's index, which counts as an access to that folder.
    let mut set = set_files
        .par_iter()
        .filter(|p| set_accessed(p, when))
        .count();
    for level in set_dirs.iter().rev() {
        set += level.par_iter().filter(|p| set_accessed(p, when)).count();
    }
    let total = set_files.len() + set_dirs.iter().map(Vec::len).sum::<usize>();
    Reset {
        set,
        failed: total - set,
        unchanged,
    }
}

struct Listing {
    dirs: Vec<PathBuf>,
    set_dirs: Vec<PathBuf>,
    files: Vec<PathBuf>,
    unchanged: usize,
}

fn list(dir: &Path, stale: SystemTime, files: Files, dirs: Dirs) -> Listing {
    let mut out = Listing {
        dirs: Vec::new(),
        set_dirs: Vec::new(),
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
                if dirs == Dirs::Moved && still_stale(&e, stale) {
                    out.unchanged += 1;
                } else {
                    out.set_dirs.push(e.path());
                }
                out.dirs.push(e.path());
            } else {
                match files {
                    Files::None => {}
                    Files::Moved if still_stale(&e, stale) => out.unchanged += 1,
                    _ => out.files.push(e.path()),
                }
            }
        }
    }
    out
}

/// Unix: lstat, which leaves the access time alone. Windows: the folder index's copy of the times, which the
/// listing returns; it follows times set explicitly at once, but may lag behind the updates scans make (hence
/// Files::All there while the scans run on the same volume).
fn still_stale(e: &fs::DirEntry, stale: SystemTime) -> bool {
    e.metadata()
        .and_then(|m| m.accessed())
        .is_ok_and(|t| t <= stale)
}

/// Only the access time changes; the modification time is left alone.
#[cfg(unix)]
pub fn set_accessed(path: &Path, when: SystemTime) -> bool {
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
pub fn set_accessed(path: &Path, when: SystemTime) -> bool {
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
