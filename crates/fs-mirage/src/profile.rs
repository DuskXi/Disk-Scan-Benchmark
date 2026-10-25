//! Profile-driven topology: generates a tree with the *shape and style* of a real directory tree, learned from the
//! aggregate histograms `scripts/profile/fs_profile.py` writes (no names or paths are ever part of a profile).
//!
//! Directories are produced level by level (the count per depth follows the profile), every directory samples how many
//! files and sub-directories it holds from the joint histogram of its depth bucket, names follow the recorded length and
//! character-class distributions, and file sizes follow the recorded log2 size histogram. Huge files (>= 1 GiB) are
//! handled like the regular generator's media files so the preset's total volume still holds.

use crate::topology::{
    EntryKind, FileEntry, FileZone, GroundTruthManifest, TopologyConfig, TopologyPlan,
    ZoneGroundTruth, BLOCK_SIZE, PREALLOC_MIN_BYTES,
};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::Deserialize;
use std::collections::{BTreeMap, HashMap, HashSet};

const MB: u64 = 1024 * 1024;
const GB: u64 = 1024 * MB;
/// Size bins at or above this hold files of at least ~1 GiB: those become "media" files.
const BIG_BIN: u32 = 31;
/// Extra apparent-only volume of the sparse hole files relative to the media volume.
const HOLE_EXTRA_RATIO: f64 = 0.4;

#[derive(Debug, Deserialize)]
pub struct Totals {
    pub files: u64,
    pub zero_size_files: u64,
}

#[derive(Debug, Deserialize)]
pub struct SizeBins {
    pub count: BTreeMap<String, u64>,
}

#[derive(Debug, Deserialize)]
pub struct Profile {
    pub totals: Totals,
    pub depth_buckets: Vec<[u32; 2]>,
    pub dirs_by_depth: BTreeMap<String, u64>,
    pub dir_shape: BTreeMap<String, Vec<[u64; 3]>>,
    pub stem_len: BTreeMap<String, u64>,
    pub ext_len: BTreeMap<String, u64>,
    pub dir_name_len: BTreeMap<String, u64>,
    pub size_bins: SizeBins,
    pub name_char_share: BTreeMap<String, f64>,
}

/// A histogram that can be sampled: `(value, cumulative weight)`.
struct Hist {
    items: Vec<(u64, u64)>,
    total: u64,
}

impl Hist {
    fn from_pairs(pairs: impl Iterator<Item = (u64, u64)>) -> Self {
        let mut acc = 0u64;
        let mut items = Vec::new();
        for (v, w) in pairs {
            if w > 0 {
                acc += w;
                items.push((v, acc));
            }
        }
        Hist { items, total: acc }
    }
    fn from_map(m: &BTreeMap<String, u64>) -> Self {
        Self::from_pairs(
            m.iter()
                .filter_map(|(k, v)| k.parse::<u64>().ok().map(|k| (k, *v))),
        )
    }
    fn sample(&self, rng: &mut ChaCha8Rng, default: u64) -> u64 {
        if self.total == 0 {
            return default;
        }
        let r = rng.gen_range(0..self.total);
        let idx = self.items.partition_point(|&(_, c)| c <= r);
        self.items[idx.min(self.items.len() - 1)].0
    }
}

/// log2 bin -> inclusive value range, mirroring `log2_bin` in the profiler (0 -> 0, 1 -> 1, b>=2 -> (2^(b-2), 2^(b-1)]).
fn bin_range(b: u64) -> (u64, u64) {
    match b {
        0 => (0, 0),
        1 => (1, 1),
        b => ((1u64 << (b - 2)) + 1, 1u64 << (b - 1)),
    }
}

fn sample_in_bin(rng: &mut ChaCha8Rng, b: u64) -> u64 {
    let (lo, hi) = bin_range(b);
    if lo >= hi {
        lo
    } else {
        rng.gen_range(lo..=hi)
    }
}

fn depth_bucket(p: &Profile, depth: usize) -> usize {
    p.depth_buckets
        .iter()
        .position(|[lo, hi]| (depth as u32) >= *lo && (depth as u32) <= *hi)
        .unwrap_or(p.depth_buckets.len() - 1)
}

struct Style {
    upper: f64,
    digit: f64,
    space: f64,
    non_ascii: f64,
    brackets: f64,
}

const EXT_BY_LEN: [&[&str]; 5] = [
    &[],
    &["h", "c", "d", "o", "a", "m", "r"],
    &["js", "py", "gz", "md", "ts", "rs", "sh", "7z", "db", "gl"],
    &[
        "jpg", "png", "txt", "dll", "exe", "pdf", "zip", "log", "xml", "bin", "dat", "cfg", "ini",
        "tmp", "mp3", "cpp",
    ],
    &[
        "json", "html", "woff", "webp", "jpeg", "yaml", "toml", "wasm", "lock", "java",
    ],
];
const NON_ASCII: [char; 5] = ['é', 'ä', 'ж', '日', 'ñ'];

fn rand_char(rng: &mut ChaCha8Rng, digits: bool) -> char {
    if digits && rng.gen_bool(0.25) {
        (b'0' + rng.gen_range(0..10u8)) as char
    } else {
        (b'a' + rng.gen_range(0..26u8)) as char
    }
}

fn gen_stem(rng: &mut ChaCha8Rng, len: usize, st: &Style) -> String {
    let len = len.max(1);
    let digits = rng.gen_bool(st.digit.clamp(0.0, 1.0));
    let mut chars: Vec<char> = (0..len).map(|_| rand_char(rng, digits)).collect();
    if len >= 2 && rng.gen_bool(st.upper.clamp(0.0, 1.0)) {
        let i = rng.gen_range(0..len);
        chars[i] = chars[i].to_ascii_uppercase();
    }
    if len >= 3 && rng.gen_bool(0.15) {
        let i = rng.gen_range(1..len - 1);
        chars[i] = ['-', '_', '.'][rng.gen_range(0..3)];
    }
    if len >= 4 && rng.gen_bool(st.space.clamp(0.0, 1.0)) {
        let i = rng.gen_range(1..len - 1);
        chars[i] = ' ';
    }
    if len >= 2 && rng.gen_bool(st.non_ascii.clamp(0.0, 1.0)) {
        let i = rng.gen_range(0..len);
        chars[i] = NON_ASCII[rng.gen_range(0..NON_ASCII.len())];
    }
    let mut s: String = chars.into_iter().collect();
    if rng.gen_bool(st.brackets.clamp(0.0, 1.0)) {
        s.push_str(&format!(" ({})", rng.gen_range(1..9)));
    }
    if is_win_reserved(&s) {
        s.push('x');
    }
    s
}

/// DOS device names (CON, NUL, COM1, ...) are rejected by Win32 with any extension; random 3-4 char stems hit them.
fn is_win_reserved(stem: &str) -> bool {
    let base = stem.split('.').next().unwrap_or("").to_ascii_lowercase();
    matches!(base.as_str(), "con" | "prn" | "aux" | "nul")
        || ((base.starts_with("com") || base.starts_with("lpt"))
            && base.len() == 4
            && base.as_bytes()[3].is_ascii_digit())
}

fn unique(used: &mut HashSet<String>, mut name: String, counter: &mut u64) -> String {
    if used.insert(name.to_lowercase()) {
        return name;
    }
    loop {
        *counter += 1;
        let tail = format!("{:x}", *counter);
        name = format!("{}{}", name, tail);
        if used.insert(name.to_lowercase()) {
            return name;
        }
    }
}

struct Node {
    depth: usize,
    rel: String,
}

pub fn generate_from_profile(cfg: &TopologyConfig, prof: &Profile) -> TopologyPlan {
    let mut rng = ChaCha8Rng::seed_from_u64(cfg.seed ^ 0x0050_524f_4649_4c45);
    let target_files = cfg.total_files.max(200);
    let scale = target_files as f64 / prof.totals.files.max(1) as f64;
    let share = |k: &str| prof.name_char_share.get(k).copied().unwrap_or(0.0);
    let style = Style {
        upper: share("has_upper"),
        digit: share("has_digit").min(0.6),
        space: share("space"),
        non_ascii: share("non_ascii"),
        brackets: share("has_brackets"),
    };
    let stem_h = Hist::from_map(&prof.stem_len);
    let dirname_h = Hist::from_map(&prof.dir_name_len);
    let ext_total: u64 = prof.ext_len.values().sum();
    let ext_h = Hist::from_map(&prof.ext_len);

    // --- directories, level by level -------------------------------------------------------------------------------
    let max_depth = prof
        .dirs_by_depth
        .iter()
        .filter(|(_, c)| **c > 0)
        .filter_map(|(k, _)| k.parse::<usize>().ok())
        .max()
        .unwrap_or(1)
        .max(1);
    let mut nodes: Vec<Node> = vec![Node {
        depth: 0,
        rel: String::new(),
    }];
    let mut level_range: Vec<(usize, usize)> = vec![(0, 1)];
    let mut used_names: HashMap<usize, HashSet<String>> = HashMap::new();
    let mut counter = 0u64;
    for d in 1..=max_depth {
        let orig = prof.dirs_by_depth.get(&d.to_string()).copied().unwrap_or(0);
        if orig == 0 {
            break;
        }
        let want = ((orig as f64 * scale).round() as usize).max(1);
        let (ps, pe) = level_range[d - 1];
        let bucket = depth_bucket(prof, d - 1).to_string();
        let shape: Vec<(u64, u64)> = prof
            .dir_shape
            .get(&bucket)
            .map(|rows| {
                rows.iter()
                    .map(|r| (r[1], r[2]))
                    .fold(BTreeMap::new(), |mut m: BTreeMap<u64, u64>, (sb, c)| {
                        *m.entry(sb).or_default() += c;
                        m
                    })
                    .into_iter()
                    .collect()
            })
            .unwrap_or_default();
        let sub_h = Hist::from_pairs(shape.into_iter());
        let mut cum: Vec<u64> = Vec::with_capacity(pe - ps);
        let mut acc = 0u64;
        for _ in ps..pe {
            let b = sub_h.sample(&mut rng, 0);
            acc += sample_in_bin(&mut rng, b);
            cum.push(acc);
        }
        let start = nodes.len();
        for _ in 0..want {
            let parent = if acc == 0 {
                ps + rng.gen_range(0..(pe - ps))
            } else {
                let r = rng.gen_range(0..acc);
                ps + cum.partition_point(|&c| c <= r).min(pe - ps - 1)
            };
            let len = dirname_h.sample(&mut rng, 8) as usize;
            let raw = gen_stem(&mut rng, len, &style);
            let used = used_names.entry(parent).or_default();
            let name = unique(used, raw, &mut counter);
            let rel = if nodes[parent].rel.is_empty() {
                name
            } else {
                format!("{}/{}", nodes[parent].rel, name)
            };
            nodes.push(Node { depth: d, rel });
        }
        level_range.push((start, nodes.len()));
    }

    // --- files per directory ------------------------------------------------------------------------------------------
    let mut raw_counts: Vec<u64> = vec![0; nodes.len()];
    let mut raw_sum = 0u64;
    let file_hists: Vec<Hist> = (0..prof.depth_buckets.len())
        .map(|b| {
            let mut m: BTreeMap<u64, u64> = BTreeMap::new();
            if let Some(rows) = prof.dir_shape.get(&b.to_string()) {
                for r in rows {
                    *m.entry(r[0]).or_default() += r[2];
                }
            }
            Hist::from_pairs(m.into_iter())
        })
        .collect();
    for (i, n) in nodes.iter().enumerate().skip(1) {
        let fb = file_hists[depth_bucket(prof, n.depth)].sample(&mut rng, 0);
        let c = sample_in_bin(&mut rng, fb);
        raw_counts[i] = c;
        raw_sum += c;
    }
    let factor = target_files as f64 / raw_sum.max(1) as f64;

    // --- file sizes ---------------------------------------------------------------------------------------------------
    let total_files_prof = prof.totals.files.max(1);
    let mut size_pairs: Vec<(u64, u64)> = vec![(0, prof.totals.zero_size_files)];
    let mut big_count = 0u64;
    for (k, v) in &prof.size_bins.count {
        if let Ok(b) = k.parse::<u64>() {
            if (b as u32) >= BIG_BIN {
                big_count += v;
            } else {
                size_pairs.push((b, *v));
            }
        }
    }
    let size_h = Hist::from_pairs(size_pairs.into_iter());

    let mut regular_files: Vec<FileEntry> = Vec::with_capacity(target_files + 64);
    let mut ext_counter = 0u64;
    for (i, n) in nodes.iter().enumerate().skip(1) {
        let cnt = (raw_counts[i] as f64 * factor + rng.gen::<f64>()).floor() as u64;
        if cnt == 0 {
            continue;
        }
        // seeded with the sub-directory names, so a file can never collide with a directory (case-insensitively)
        let mut used: HashSet<String> = used_names.remove(&i).unwrap_or_default();
        used.reserve(cnt as usize);
        for _ in 0..cnt {
            let ext_len = ext_h.sample(&mut rng, 3).min(4) as usize;
            let ext = if ext_len == 0 || ext_total == 0 {
                String::new()
            } else {
                let list = EXT_BY_LEN[ext_len.min(4)];
                format!(".{}", list[rng.gen_range(0..list.len())])
            };
            let stem_len = stem_h.sample(&mut rng, 10) as usize;
            let stem = gen_stem(&mut rng, stem_len, &style);
            let name = unique(&mut used, format!("{}{}", stem, ext), &mut ext_counter);
            let bin = size_h.sample(&mut rng, 0);
            let logical_size = sample_in_bin(&mut rng, bin);
            let fill_byte = rng.gen_range(1..=254);
            regular_files.push(FileEntry {
                rel_path: format!("{}/{}", n.rel, name),
                zone: FileZone::DeepSource,
                kind: EntryKind::RegularFile {
                    logical_size,
                    dirty_blocks: 0,
                    fill_byte,
                    preallocate: logical_size >= PREALLOC_MIN_BYTES,
                },
            });
        }
    }
    let small_logical_sum: u64 = regular_files
        .iter()
        .map(|e| match e.kind {
            EntryKind::RegularFile { logical_size, .. } => logical_size,
            _ => 0,
        })
        .sum();

    // --- media (>= 1 GiB) files and a few sparse hole files ------------------------------------------------------------
    let big_share = big_count as f64 / total_files_prof as f64;
    let count_media = ((regular_files.len() as f64 * big_share).round() as usize).clamp(8, 4000);
    let mut media_sizes: Vec<u64> = (0..count_media)
        .map(|_| {
            let e: f64 = rng.gen_range(30.0..37.5);
            (2f64.powf(e) as u64) & !(BLOCK_SIZE - 1)
        })
        .collect();
    if let Some(target_gb) = cfg.target_logical_gb {
        let target_bytes = (target_gb * GB as f64) as u64;
        let desired = target_bytes
            .saturating_sub(small_logical_sum)
            .max(count_media as u64 * 16 * MB);
        let current: u64 = media_sizes.iter().sum::<u64>().max(1);
        for s in &mut media_sizes {
            *s = (((*s as u128) * desired as u128 / current as u128) as u64 & !(BLOCK_SIZE - 1))
                .max(16 * MB);
        }
    }
    let media_total: u64 = media_sizes.iter().sum();
    let dir_count = nodes.len();
    let mut media_used: HashSet<String> = HashSet::new();
    for sz in &media_sizes {
        let n = &nodes[rng.gen_range(1..dir_count)];
        let ext = EXT_BY_LEN[3][rng.gen_range(0..EXT_BY_LEN[3].len())];
        let stem = gen_stem(&mut rng, 14, &style);
        let name = unique(
            &mut media_used,
            format!("{}.{}", stem, ext),
            &mut ext_counter,
        );
        let fill_byte = rng.gen_range(1..=254);
        regular_files.push(FileEntry {
            rel_path: format!("{}/{}", n.rel, name),
            zone: FileZone::SparseMedia,
            kind: EntryKind::RegularFile {
                logical_size: *sz,
                dirty_blocks: 2,
                fill_byte,
                preallocate: true,
            },
        });
    }
    let hole_total = (media_total as f64 * HOLE_EXTRA_RATIO) as u64;
    let hole_count = count_media.clamp(1, 6);
    let hole_dir = nodes[1..]
        .iter()
        .find(|n| n.depth == 1)
        .map(|n| n.rel.clone())
        .unwrap_or_default();
    for i in 0..hole_count {
        let sz = ((hole_total / hole_count as u64) & !(BLOCK_SIZE - 1)).max(MB);
        let fill_byte = rng.gen_range(1..=254);
        regular_files.push(FileEntry {
            rel_path: format!("{}/sparse_hole_{:02}.img", hole_dir, i),
            zone: FileZone::SparseMedia,
            kind: EntryKind::RegularFile {
                logical_size: sz,
                dirty_blocks: 4,
                fill_byte,
                preallocate: false,
            },
        });
    }

    // --- manifest -----------------------------------------------------------------------------------------------------
    let directories: Vec<String> = nodes.iter().skip(1).map(|n| n.rel.clone()).collect();
    let apparent: u64 = regular_files
        .iter()
        .map(|e| match e.kind {
            EntryKind::RegularFile { logical_size, .. } => logical_size,
            _ => 0,
        })
        .sum();
    let mut zones: BTreeMap<String, ZoneGroundTruth> = BTreeMap::new();
    for d in &directories {
        let top = d.split('/').next().unwrap_or("unknown");
        zones
            .entry(top.to_string())
            .or_insert(ZoneGroundTruth {
                files: 0,
                dirs: 0,
                apparent_size_bytes: 0,
                allocated_size_bytes: 0,
            })
            .dirs += 1;
    }
    for f in &regular_files {
        let top = f.rel_path.split('/').next().unwrap_or("unknown");
        let sz = match f.kind {
            EntryKind::RegularFile { logical_size, .. } => logical_size,
            _ => 0,
        };
        let z = zones.entry(top.to_string()).or_insert(ZoneGroundTruth {
            files: 0,
            dirs: 0,
            apparent_size_bytes: 0,
            allocated_size_bytes: 0,
        });
        z.files += 1;
        z.apparent_size_bytes += sz;
    }
    let manifest = GroundTruthManifest {
        preset: cfg.preset.clone(),
        seed: cfg.seed,
        total_files: regular_files.len(),
        total_regular_files: regular_files.len(),
        total_dirs: directories.len(),
        total_hardlinks: 0,
        total_symlinks: 0,
        media_files_count: count_media,
        apparent_size_bytes: apparent,
        apparent_size_with_hardlinks_bytes: apparent,
        planned_dirty_bytes: 0,
        allocated_size_bytes: 0,
        allocated_size_with_hardlinks_bytes: 0,
        allocated_files_only_bytes: 0,
        zones,
        aged_timeline: false,
    };
    TopologyPlan {
        directories,
        regular_files,
        hardlinks: Vec::new(),
        symlinks: Vec::new(),
        manifest,
    }
}
