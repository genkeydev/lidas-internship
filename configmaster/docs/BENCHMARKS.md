# ConfigMaster Benchmarks

This document records wall-clock benchmark results for ConfigMaster when merging large generated JSON configuration trees.

## Benchmark configuration

The benchmark generates two JSON configuration layers. Each layer contains 200 groups with 50 values per group, giving 10,000 values per layer.

Both layers include the required `app.name` and `app.port` fields so the merged configuration is valid against the current client specification.

The script generates the test files and compiles ConfigMaster before timing starts. Only the `merge` command is included in the recorded wall time.

Generated benchmark files are stored under `target/benchmark/` and are not committed.

## Results

| Date                | Groups | Keys per group | Values per layer | Wall time |
|---------------------|-------:|---------------:|-----------------:|----------:|
| 2026-10-06 16:17:37 |    200 |             50 |            10000 |   3086 ms |
