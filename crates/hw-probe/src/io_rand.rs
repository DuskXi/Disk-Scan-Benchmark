use anyhow::Result;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};
use std::alloc::{alloc, dealloc, Layout};
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::path::Path;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::time::{Duration, Instant};

const BLOCK: usize = 4096;

/// Random 4 KiB read ceiling of the benchmark volume (the `S_IOPS` of the balanced resource index): a test file
/// read with unbuffered I/O at random aligned offsets by many threads at once, like a scanner keeping a queue of
/// metadata reads in flight.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RandProbeResult {
    pub file_mb: usize,
    pub threads: usize,
    pub block_bytes: usize,
    pub elapsed_ms: f64,
    pub reads: u64,
    pub b_rand_read_iops: f64,
}

struct Aligned {
    ptr: *mut u8,
    layout: Layout,
}

impl Aligned {
    fn new(size: usize) -> Self {
        let layout = Layout::from_size_align(size, BLOCK).expect("layout");
        let ptr = unsafe { alloc(layout) };
        if ptr.is_null() {
            std::alloc::handle_alloc_error(layout);
        }
        unsafe { std::ptr::write_bytes(ptr, 0x5A, size) };
        Self { ptr, layout }
    }
    fn as_mut_slice(&mut self) -> &mut [u8] {
        unsafe { std::slice::from_raw_parts_mut(self.ptr, self.layout.size()) }
    }
    fn as_slice(&self) -> &[u8] {
        unsafe { std::slice::from_raw_parts(self.ptr, self.layout.size()) }
    }
}

impl Drop for Aligned {
    fn drop(&mut self) {
        unsafe { dealloc(self.ptr, self.layout) }
    }
}

pub fn run_rand_probe(
    root: &Path,
    file_mb: usize,
    threads: usize,
    seconds: f64,
) -> Result<RandProbeResult> {
    let file_mb = file_mb.max(64);
    let path = root.join(".hw_probe_rand_test.bin");
    let _ = fs::remove_file(&path);
    let result = measure(&path, file_mb, threads.max(1), seconds.max(0.5));
    let _ = fs::remove_file(&path);
    result
}

fn measure(path: &Path, file_mb: usize, threads: usize, seconds: f64) -> Result<RandProbeResult> {
    // Real data, so every read hits allocated, written blocks (not a hole the filesystem answers from metadata)
    {
        let chunk = Aligned::new(1024 * 1024);
        let mut f = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(path)?;
        // macOS: written pages would stay in the unified buffer cache and serve the "unbuffered" reads from memory
        // (F_NOCACHE on the reader does not evict them), so the writer bypasses the cache too
        #[cfg(target_os = "macos")]
        unsafe {
            use std::os::unix::io::AsRawFd;
            libc::fcntl(f.as_raw_fd(), libc::F_NOCACHE, 1);
        }
        for _ in 0..file_mb {
            f.write_all(chunk.as_slice())?;
        }
        f.sync_all()?;
    }
    let blocks = (file_mb * 1024 * 1024 / BLOCK) as u64;
    let reads = AtomicU64::new(0);
    let stop = AtomicBool::new(false);
    let t0 = Instant::now();
    std::thread::scope(|s| -> Result<()> {
        let mut workers = Vec::with_capacity(threads);
        for i in 0..threads {
            let (reads, stop) = (&reads, &stop);
            workers.push(s.spawn(move || -> Result<()> {
                let f = open_unbuffered(path)?;
                let mut buf = Aligned::new(BLOCK);
                let mut rng = ChaCha8Rng::seed_from_u64(0x10_95 + i as u64);
                let mut local = 0u64;
                while !stop.load(Ordering::Relaxed) {
                    let off = rng.gen_range(0..blocks) * BLOCK as u64;
                    read_at(&f, buf.as_mut_slice(), off)?;
                    local += 1;
                }
                reads.fetch_add(local, Ordering::Relaxed);
                Ok(())
            }));
        }
        std::thread::sleep(Duration::from_secs_f64(seconds));
        stop.store(true, Ordering::Relaxed);
        for w in workers {
            w.join().expect("rand probe worker panicked")?;
        }
        Ok(())
    })?;
    let elapsed = t0.elapsed().as_secs_f64().max(1e-6);
    let total = reads.load(Ordering::Relaxed);
    Ok(RandProbeResult {
        file_mb,
        threads,
        block_bytes: BLOCK,
        elapsed_ms: elapsed * 1000.0,
        reads: total,
        b_rand_read_iops: total as f64 / elapsed,
    })
}

#[cfg(windows)]
fn open_unbuffered(path: &Path) -> Result<File> {
    use std::os::windows::fs::OpenOptionsExt;
    use windows_sys::Win32::Storage::FileSystem::{
        FILE_FLAG_NO_BUFFERING, FILE_FLAG_RANDOM_ACCESS,
    };
    Ok(OpenOptions::new()
        .read(true)
        .custom_flags(FILE_FLAG_NO_BUFFERING | FILE_FLAG_RANDOM_ACCESS)
        .open(path)?)
}

#[cfg(target_os = "linux")]
fn open_unbuffered(path: &Path) -> Result<File> {
    use std::os::unix::fs::OpenOptionsExt;
    match OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_DIRECT)
        .open(path)
    {
        Ok(f) => Ok(f),
        Err(_) => Ok(OpenOptions::new().read(true).open(path)?),
    }
}

#[cfg(target_os = "macos")]
fn open_unbuffered(path: &Path) -> Result<File> {
    use std::os::unix::io::AsRawFd;
    let f = OpenOptions::new().read(true).open(path)?;
    unsafe {
        libc::fcntl(f.as_raw_fd(), libc::F_NOCACHE, 1);
    }
    Ok(f)
}

#[cfg(all(unix, not(target_os = "linux"), not(target_os = "macos")))]
fn open_unbuffered(path: &Path) -> Result<File> {
    Ok(OpenOptions::new().read(true).open(path)?)
}

#[cfg(windows)]
fn read_at(f: &File, buf: &mut [u8], off: u64) -> Result<()> {
    use std::os::windows::fs::FileExt;
    f.seek_read(buf, off)?;
    Ok(())
}

#[cfg(unix)]
fn read_at(f: &File, buf: &mut [u8], off: u64) -> Result<()> {
    use std::os::unix::fs::FileExt;
    f.read_at(buf, off)?;
    Ok(())
}
