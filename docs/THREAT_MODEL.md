# PROJECT LIDAS THREAT MODEL
**Version: 1.0.0**
**Date: 2026-08-23**
**Approach**:*STRIDE(Spoofing, Tampering, Information Disclosure, Denial of Service, Elevation of Privilege)*


# DATA FLOW
   *Project LIDAS is a log-based Intrusion Detection System that reads application logs (SSH/HTTP), parses them, runs them through detection rules, and then emits alerts to the console and an HMAC-chained audit log.*


      [Raw Log File]
            |
            |
            |
           \ /
         [Parser]
            |
            |(Log Event)
            |
           \ /
       [Rule Engine]
            |
            |(Alert)
            |
           \ /
        [Emitter]
            |
            |(Screen, Audit Log)
            |
           \ /
       [Audit Log/Verifier/CLI]


# STRIDE THREAT ANALYSIS
- **Spoofing**
   * Parser (HIGH [*IP/UA Spoof*])
   * Rule Engine (LOW)
   * Emitter (LOW)
   * Audit Log (NONE)
   * CLI/Verifier (NONE)

- **Tampering**
   * Parser (HIGH [*Log Injection*])
   * Rule Engine (MEDIUM [*Memory Bloat*])
   * Emitter (MEDIUM [*Disable Logging*])
   * Audit Log (HIGH [*Key Theft*])
   * CLI/Verifier (HIGH [*Wrong Key*])

- **Repudiation**
   * Parser (LOW)
   * Rule Engine (NONE)
   * Emitter (CRITICAL [*Provides & breaks HMAC chain*])
   * Audit Log (HIGH [*HMAC chain*])
   * CLI/Verifier (NONE)

- **Information Disclosure**
   * Parser (HIGH [*Raw Secrets like admin passwords*])
   * Rule Engine (LOW)
   * Emitter (CRITICAL [*Secrets in plain text*])
   * Audit Log (HIGH [*Plain text logs*])
   * CLI/Verifier (LOW)

- **Denial Of Service**
   * Parser (HIGH [*ReDoS*])
   * Rule Engine (HIGH [*State Bloat*])
   * Emitter (MEDIUM [*Blocking I/O*])
   * Audit Log (MEDIUM [*Disk Full*])
   * CLI/Verifier (LOW)

- **Elevation of Privilege**
   * Parser (MEDIUM [*If it has root access*])
   * Rule Engine (LOW)
   * Emitter (LOW)
   * Audit Log (HIGH [*Key Controls*])
   * CLI/Verifier (HIGH [*Root Access*])


### Spoofing
- **Can an attacker fake a log source to avoid detection ?**
   YES. LIDAS reads text files and has no network-level authority to verify that the source IP actually belongs to the client making the request. For LIDAS, there is no mitigation for IP spoofing, but for User-Agents, the confidence is set to 0.7 to reduce noise, and behavioral rules (SSH/404) act as a backup.

### Tampering
- **Can an attacker modify the log file before LIDAS reads it and what happens to the audit log?**
      YES. If an attacker has write access to the original log files before LIDAS scans it, they can cover their tracks or insert junk. LIDAS has no protection against this because it trusts the source file without doubt. If an attacker tries to modify a line in the audit log, the entry HMAC of that line becomes invalid and will be caught by the Verifier. However, if the attacker is able to steal the HMAC key, they can recompute entry HMAC values and rewrite the entire file, even the verifier will approve it. Thus, the key file permissions are set to (0o600) which means only the owner of the system can read/write to the file to prevent casual theft.

### Repudiation
- **Can an attacker deny that an attack happened and what does the HMAC chain protect against?**
      NO (for alerts), YES (for raw logs). An operator cannot deny that LIDAS generated an alert at specific time, because the chain cryptographically proves the existence and sequence of that alert thus, if they try to delete it, the chain breaks. However, if the HMAC key was to leak, the attacker can forge a new chain which breaks all repudiation guarantees.

### Information Disclosure
- **Does the audit log leak sensitive information?**
     YES. The (LogEvent) structure in LIDAS stores the full "raw" log line. This raw string is written to the audit log in plaintext. SSH logs do not contain passwords but HTTP logs frequently contain session tokens, API keys, and PII in query strings or POST bodies. The code preserves the raw line for forensic detail (evidence).

## Denial Of Service
- **Can a malformed log line crash the IDS and stop detection?**
    NO (for basic malformed lines), YES (for complex attacks). The (parse_line) has a top-level catch-all thus, if a line is garbage, it returns a (LogEvent) with (source="unknown"), it never raises an exception. If the SQL rule crashes, the SSH rule keeps running. Simple malformed text will not crash the IDS, however, complex DoS vectors such as ReDos and Memory exhaustion caused by DDoS can crash LIDAS.

## Elevation of Priviledge 
- **If LIDAS runs as root, what happens if an attacker exploits a bug in it?**
    FULL SYSTEM COMPROMISE. To read system logs, operators will run LIDAS as root. If an attacker manages to inject a payload into the log file that exploits a hyothetical bug in the Python parser, because LIDAS has root access, the attacker's payload executes with root permissions and they can do anything to or with LIDAS. There are no mitigations in the code.

## ACCEPTED RISKS
- Spoofing of log sources is accepted at the host level, since LIDAS trusts the OS (Operating System)
- Denial of Service through DDoS attacks is accepted, requiring external rate-limiting alongside LIDAS. 