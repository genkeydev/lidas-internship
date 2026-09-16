import time
import random
import sys
from datetime import timedelta

from lidas.parser import parse_line
from lidas.rules import (
    RuleEngine,
    SSHBruteForceRule,
    SQLInjectionRule,
    SuspiciousUserAgentRule,
    CanaryTokenRule,
    PortScanHintRule,
)

# --- Memory measurement (robust) ---
def deep_getsizeof(obj, seen=None):
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        for k, v in obj.items():
            size += deep_getsizeof(k, seen)
            size += deep_getsizeof(v, seen)
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            size += deep_getsizeof(item, seen)
    elif hasattr(obj, '__dict__'):
        size += deep_getsizeof(obj.__dict__, seen)
    return size

def get_engine_memory(engine):
    total = 0
    for attr in ['rules', '_rules']:
        if hasattr(engine, attr):
            rules_list = getattr(engine, attr)
            if rules_list:
                for rule in rules_list:
                    total += deep_getsizeof(rule)
            break
    return total

# --- Rules ---
def get_default_rules():
    return [
        SSHBruteForceRule(threshold=5, window=timedelta(seconds=60)),
        SQLInjectionRule(),
        SuspiciousUserAgentRule(),
        CanaryTokenRule(),
        PortScanHintRule(threshold=10, window=timedelta(seconds=30)),
    ]

def build_engine_with_rules(rules):
    try:
        return RuleEngine(rules)
    except TypeError:
        engine = RuleEngine()
        for rule in rules:
            engine.add_rule(rule)
        return engine

def create_engine_with_100_rules():
    rules = get_default_rules()
    for i in range(95):
        rules.append(SSHBruteForceRule(threshold=5, window=timedelta(seconds=60)))
    return build_engine_with_rules(rules)

# --- Log generator (FIXED) ---
def generate_ssh_line(ip, failed=True):
    """Generate an SSH log line in the exact format the parser expects."""
    if failed:
        result = "Failed password for invalid user test"
    else:
        result = "Accepted password for test"
    return f'Jun 30 09:14:01 webhost sshd[1]: {result} from {ip} port 22 ssh2'

# --- Benchmark ---
N = 10_000
lines = [generate_ssh_line(f'10.0.{random.randint(0,255)}.{random.randint(1,254)}') for _ in range(N)]

# Baseline (5 rules)
engine = build_engine_with_rules(get_default_rules())
start = time.perf_counter()
for line in lines:
    event = parse_line(line)
    engine.process_event(event)
elapsed = time.perf_counter() - start

mem_bytes = get_engine_memory(engine)
mem_mb = mem_bytes / (1024 * 1024)

print(f'Baseline (5 rules): {N} events in {elapsed:.3f}s — {N/elapsed:.0f} events/sec')
print(f'Memory: {mem_mb:.2f} MB')

# 100 rules
engine100 = create_engine_with_100_rules()
start = time.perf_counter()
for line in lines:
    event = parse_line(line)
    engine100.process_event(event)
elapsed = time.perf_counter() - start

mem_bytes = get_engine_memory(engine100)
mem_mb = mem_bytes / (1024 * 1024)

print(f'100 rules: {N} events in {elapsed:.3f}s — {N/elapsed:.0f} events/sec')
print(f'Memory: {mem_mb:.2f} MB')