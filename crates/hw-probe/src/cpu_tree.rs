use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};
use std::time::Instant;

#[derive(Debug, Clone)]
struct VNode {
    id: u32,
    own_size: u64,
    total_size: u64,
    children: Vec<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CpuProbeResult {
    pub node_count: usize,
    pub root_total_bytes: u64,
    pub b_cpu_ms: f64,
}

pub fn run_cpu_tree_probe(node_count: usize) -> CpuProbeResult {
    let n = node_count.max(1000);
    let mut rng = ChaCha8Rng::seed_from_u64(0xDEC0_DED1_2026);

    let t0 = Instant::now();

    // 1. Construct `n` virtual tree nodes in memory (approx 10% directories, 90% files)
    let dir_count = (n / 10).max(16);
    let mut nodes: Vec<VNode> = Vec::with_capacity(n);

    for i in 0..n {
        let is_dir = i < dir_count;
        let own_size = if is_dir {
            0
        } else {
            rng.gen_range(64..=1_048_576)
        };
        nodes.push(VNode {
            id: i as u32,
            own_size,
            total_size: own_size,
            children: Vec::new(),
        });
    }

    // Attach every node i >= 1 to a parent directory in `0..min(i, dir_count)`
    // Guaranteeing a strict DAG / tree topological order (parent index < child index)
    for i in 1..n {
        let max_parent = i.min(dir_count);
        let parent_idx = rng.gen_range(0..max_parent);
        nodes[parent_idx].children.push(i as u32);
    }

    // 2. Bottom-up depth-first aggregation and per-directory descending size sort
    for idx in (0..dir_count).rev() {
        let mut children = std::mem::take(&mut nodes[idx].children);
        let mut sum = nodes[idx].own_size;
        for &child_id in &children {
            sum = sum.wrapping_add(nodes[child_id as usize].total_size);
        }
        // Sort directory children in descending order of total_size
        children.sort_unstable_by(|&a, &b| {
            nodes[b as usize]
                .total_size
                .cmp(&nodes[a as usize].total_size)
                .then_with(|| a.cmp(&b))
        });
        nodes[idx].total_size = sum;
        nodes[idx].children = children;
    }

    let root_total_bytes = std::hint::black_box(nodes[0].total_size);
    let _ = std::hint::black_box(nodes[0].id);
    let elapsed_ms = t0.elapsed().as_secs_f64() * 1000.0;

    CpuProbeResult {
        node_count: n,
        root_total_bytes,
        b_cpu_ms: elapsed_ms,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cpu_tree_probe() {
        let res = run_cpu_tree_probe(10_000);
        assert_eq!(res.node_count, 10_000);
        assert!(res.root_total_bytes > 0);
        assert!(res.b_cpu_ms >= 0.0);
    }
}
