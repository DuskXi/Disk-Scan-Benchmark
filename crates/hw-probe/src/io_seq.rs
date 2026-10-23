use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::alloc::{alloc, dealloc, Layout};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::Path;
use std::slice;
use std::time::Instant;

const CHUNK_SIZE: usize = 1024 * 1024; // 1 MiB page-aligned chunk

struct AlignedHeapBuffer {
    ptr: *mut u8,
    layout: Layout,
}

impl AlignedHeapBuffer {
    fn new(size: usize, align: usize) -> Self {
        let layout = Layout::from_size_align(size, align).expect("Invalid alignment layout");
        let ptr = unsafe { alloc(layout) };
        if ptr.is_null() {
            std::alloc::handle_alloc_error(layout);
        }
        unsafe {
            std::ptr::write_bytes(ptr, 0xA5, size);
        }
        Self { ptr, layout }
    }

    fn as_mut_slice(&mut self) -> &mut [u8] {
        unsafe { slice::from_raw_parts_mut(self.ptr, self.layout.size()) }
    }

    fn as_slice(&self) -> &[u8] {
        unsafe { slice::from_raw_parts(self.ptr, self.layout.size()) }
    }
}

impl Drop for AlignedHeapBuffer {
    fn drop(&mut self) {
        unsafe {
            dealloc(self.ptr, self.layout);
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SeqProbeResult {
    pub test_size_mb: usize,
    pub elapsed_ms: f64,
    pub b_seq_mb_per_sec: f64,
}

pub fn run_seq_probe(root: &Path, size_mb: usize) -> Result<SeqProbeResult> {
    let size_mb = size_mb.max(16);
    let temp_path = root.join(".hw_probe_seq_test.bin");

    // Clean up any stale file first
    let _ = fs::remove_file(&temp_path);

    let result = measure_seq_read(&temp_path, size_mb);

    // Always remove the temporary probe file so it does not pollute the benchmark tree
    let _ = fs::remove_file(&temp_path);

    result
}

fn measure_seq_read(temp_path: &Path, size_mb: usize) -> Result<SeqProbeResult> {
    let mut chunk = AlignedHeapBuffer::new(CHUNK_SIZE, 4096);
    for (idx, b) in chunk.as_mut_slice().iter_mut().enumerate().step_by(4096) {
        *b = ((idx / 4096) & 0xFF) as u8 ^ 0x5A;
    }

    // 1. Write the test file and flush to storage
    {
        let mut wf = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(temp_path)?;
        for _ in 0..size_mb {
            wf.write_all(chunk.as_slice())?;
        }
        wf.sync_all()?;
    }

    // Advise OS kernel to evict cache for this file before reading
    evict_file_cache(temp_path);

    // 2. Sequentially read the file (using unbuffered/direct I/O where supported)
    let mut rf = open_for_unbuffered_seq_read(temp_path)?;
    let t0 = Instant::now();
    let mut total_read: usize = 0;
    let buf = chunk.as_mut_slice();
    loop {
        let n = rf.read(buf)?;
        if n == 0 {
            break;
        }
        total_read += n;
        std::hint::black_box(buf[0]);
    }
    let elapsed = t0.elapsed();
    let elapsed_secs = elapsed.as_secs_f64().max(1e-6);
    let actual_mb = (total_read as f64) / (1024.0 * 1024.0);
    let b_seq_mb_per_sec = actual_mb / elapsed_secs;

    Ok(SeqProbeResult {
        test_size_mb: size_mb,
        elapsed_ms: elapsed_secs * 1000.0,
        b_seq_mb_per_sec,
    })
}

#[cfg(windows)]
fn open_for_unbuffered_seq_read(path: &Path) -> Result<File> {
    use std::os::windows::fs::OpenOptionsExt;
    use windows_sys::Win32::Storage::FileSystem::{
        FILE_FLAG_NO_BUFFERING, FILE_FLAG_SEQUENTIAL_SCAN,
    };

    if let Ok(f) = OpenOptions::new()
        .read(true)
        .custom_flags(FILE_FLAG_NO_BUFFERING | FILE_FLAG_SEQUENTIAL_SCAN)
        .open(path)
    {
        return Ok(f);
    }

    Ok(OpenOptions::new()
        .read(true)
        .custom_flags(FILE_FLAG_SEQUENTIAL_SCAN)
        .open(path)?)
}

#[cfg(target_os = "linux")]
fn open_for_unbuffered_seq_read(path: &Path) -> Result<File> {
    use std::os::unix::fs::OpenOptionsExt;
    if let Ok(f) = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_DIRECT)
        .open(path)
    {
        return Ok(f);
    }
    Ok(OpenOptions::new().read(true).open(path)?)
}

#[cfg(target_os = "macos")]
fn open_for_unbuffered_seq_read(path: &Path) -> Result<File> {
    use std::os::unix::io::AsRawFd;
    let f = OpenOptions::new().read(true).open(path)?;
    unsafe {
        libc::fcntl(f.as_raw_fd(), libc::F_NOCACHE, 1);
    }
    Ok(f)
}

#[cfg(all(unix, not(target_os = "linux"), not(target_os = "macos")))]
fn open_for_unbuffered_seq_read(path: &Path) -> Result<File> {
    Ok(OpenOptions::new().read(true).open(path)?)
}

#[cfg(target_os = "linux")]
fn evict_file_cache(path: &Path) {
    use std::os::unix::io::AsRawFd;
    if let Ok(f) = OpenOptions::new().read(true).open(path) {
        unsafe {
            libc::posix_fadvise(f.as_raw_fd(), 0, 0, libc::POSIX_FADV_DONTNEED);
        }
    }
}

#[cfg(not(target_os = "linux"))]
fn evict_file_cache(_path: &Path) {}
