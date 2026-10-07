#!/usr/bin/env bash

set -euo pipefail

# Benchmark size: 200 groups x 50 keys = 10,000 values per layer.
GROUP_COUNT=200
KEYS_PER_GROUP=50
VALUES_PER_LAYER=$((GROUP_COUNT * KEYS_PER_GROUP))

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCHMARK_DIR="$ROOT_DIR/target/benchmark"

BASE_FILE="$BENCHMARK_DIR/base.json"
OVERLAY_FILE="$BENCHMARK_DIR/overlay.json"
OUTPUT_FILE="$BENCHMARK_DIR/merged.json"
RESULT_FILE="$ROOT_DIR/docs/BENCHMARKS.md"

mkdir -p "$BENCHMARK_DIR"

generate_layer() {
    local output_file="$1"
    local port="$2"
    local suffix="$3"

    awk \
        -v groups="$GROUP_COUNT" \
        -v keys="$KEYS_PER_GROUP" \
        -v port="$port" \
        -v suffix="$suffix" '
        BEGIN {
            print "{"
            print "  \"app\": {"
            print "    \"name\": \"configmaster-benchmark\","
            print "    \"port\": " port
            print "  },"
            print "  \"benchmark\": {"

            for (g = 1; g <= groups; g++) {
                printf "    \"group%d\": {\n", g

                for (k = 1; k <= keys; k++) {
                    printf "      \"key%d\": \"value-%d-%d-%s\"", \
                        k, g, k, suffix

                    if (k < keys) {
                        printf ","
                    }

                    printf "\n"
                }

                printf "    }"

                if (g < groups) {
                    printf ","
                }

                printf "\n"
            }

            print "  }"
            print "}"
        }
    ' > "$output_file"
}

echo "Generating benchmark JSON..."
generate_layer "$BASE_FILE" 8080 "base"
generate_layer "$OVERLAY_FILE" 9090 "overlay"

echo "Generated $VALUES_PER_LAYER benchmark values per layer."

echo "Compiling ConfigMaster..."
(
    cd "$ROOT_DIR"
    mvn -q -DskipTests compile
)

echo "Running ConfigMaster merge benchmark..."

start_ns=$(date +%s%N)

(
    cd "$ROOT_DIR"
    mvn -q exec:java \
        -Dexec.args="merge target/benchmark/base.json target/benchmark/overlay.json" \
        > target/benchmark/merged.json
)

end_ns=$(date +%s%N)

elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))

if [[ ! -s "$OUTPUT_FILE" ]]; then
    echo "Benchmark failed: merged output was not created." >&2
    exit 1
fi

echo "Merge completed in ${elapsed_ms} ms."

if [[ ! -f "$RESULT_FILE" ]]; then
    cat > "$RESULT_FILE" <<'EOF'
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
EOF
fi

printf '| %-19s | %6s | %14s | %16s | %9s |\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" \
    "$GROUP_COUNT" \
    "$KEYS_PER_GROUP" \
    "$VALUES_PER_LAYER" \
    "${elapsed_ms} ms" \
    >> "$RESULT_FILE"

echo "Benchmark result recorded in docs/BENCHMARKS.md."