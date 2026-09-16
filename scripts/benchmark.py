from datetime import timedelta
import time
import random
from lidas.parser import parse_line
from lidas.rules import RuleEngine, SSHBruteForceRule, DEFAULT_RULES

def generate_ssh_line(ip, failed=True):
    result = 'Failed' if failed else 'Accepted'
    return f'Jun 30 09:14:01 host sshd[1]: {result} password for user test from {ip} port 22 ssh2'

# Baseline: use the default rules (5 rules)
engine = RuleEngine()
# For the 100‑rule test, we'll create a separate engine with 100 copies
def create_engine_with_100_rules():
    # Start with the default rules (5)
    rules = list(DEFAULT_RULES)
    # Add 95 more SSH brute‑force rules (each tracks its own state)
    for i in range(95):
        rules.append(SSHBruteForceRule(threshold=5, window=timedelta(seconds=60)))
    return RuleEngine(rules)

N = 10_000
# Generate lines using random IPs (all failed attempts)
lines = [generate_ssh_line(f'10.0.{random.randint(0,255)}.{random.randint(1,254)}') for _ in range(N)]

# ---- Baseline (5 rules) ----
engine = RuleEngine()  # uses DEFAULT_RULES
start = time.perf_counter()
for line in lines:
    event = parse_line(line)
    engine.process_event(event)
elapsed = time.perf_counter() - start
print(f'Baseline (5 rules): {N} events in {elapsed:.3f}s — {N/elapsed:.0f} events/sec')

# ---- 100 rules ----
engine100 = create_engine_with_100_rules()
start = time.perf_counter()
for line in lines:
    event = parse_line(line)
    engine100.process_event(event)
elapsed = time.perf_counter() - start
print(f'100 rules: {N} events in {elapsed:.3f}s — {N/elapsed:.0f} events/sec')