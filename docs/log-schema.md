### OVERVIEW
 *The LIDAS audit log is an append‑only, tamper‑evident file that records every detection alert. Each line in the file is a single JSON object, and each object is cryptographically chained to the one before it using HMAC‑SHA256.*

 ## ENTRY STRUCTURE 
  Every audit logline is a JSON object with exactly 3 top-level keys;

- **prev_hmac** (STRING)
    HMAC (hex‑encoded) of the previous entry’s entry_hmac and its entire alert payload. The first entry uses a fixed GENESIS_HMAC.

- **alert** (OBJECT)
   The detection event itself. Contains all information about the rule that fired.

- **entry_hmac** (STRING)
   HMAC (hex‑encoded) of prev_hmac and alert (as a JSON string). This is the “seal” for this entry.

## THE (alert) OBJECT
  The (alert) field is a nested object with these keys:

- **rule_id** (STRING)
   Unique identifier for the rule (e.g., SSH-001, HTTP-003).

- **rule_name** (STRING)
   Human‑readable name of the rule (e.g., "SSH brute force").

- **severity** (STRING)
   One of LOW, MEDIUM, HIGH, CRITICAL.

- **timestamp** (STRING)
   ISO‑8601 timestamp with UTC offset (e.g., 2026-06-30T09:14:01+00:00). Always timezone‑aware.

- **source_ip** (STRING)
   The IP address that triggered the alert (if applicable; otherwise null).

- **confidence** (NUMBER(Float))
   A value between 0.0 and 1.0 indicating how certain the rule is that this is an attack.

- **summary** (STRING)
   A short, human‑readable summary of what the rule detected.

- **evidence** (ARRAY)
   A list of raw log lines that contributed to this alert (typically one or more).

## EXAMPLE JSON FORMAT

{
  "prev_hmac": "a7c3e8f9d1b2c4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9",
  "alert": {
    "rule_id": "SSH-001",
    "rule_name": "SSH brute force",
    "severity": "HIGH",
    "timestamp": "2026-06-30T09:14:01+00:00",
    "source_ip": "10.0.0.5",
    "confidence": 0.95,
    "summary": "5 failed SSH logins from 10.0.0.5 within 60 seconds",
    "evidence": [
      "Jun 30 09:13:01 webhost sshd[1234]: Failed password for invalid user admin from 10.0.0.5 port 51514 ssh2",
      "Jun 30 09:13:31 webhost sshd[1234]: Failed password for invalid user admin from 10.0.0.5 port 51515 ssh2",
      "Jun 30 09:14:01 webhost sshd[1234]: Failed password for invalid user admin from 10.0.0.5 port 51516 ssh2"
    ]
  },
  "entry_hmac": "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0"
}

## HMAC CALCULATION 

- **Genesis**: The prev_hmac of the first entry is always the hex‑encoded value of the constant GENESIS_HMAC (defined in lidas/audit_log.py). This gives the chain a fixed starting point.

**Entry HMAC**: For every entry after the first, prev_hmac is the hex‑encoded HMAC of the previous entry’s entry_hmac concatenated with the JSON representation of that previous entry’s alert object.

**Current entry HMAC**: The entry_hmac field is the hex‑encoded HMAC of the current entry’s prev_hmac (as a UTF‑8 string) plus the JSON string of the current alert object, all hashed with the HMAC key.

 
 *The HMAC key is a 32‑byte symmetric secret stored in a file (by default data/hmac.key). If the key is compromised, an attacker can forge a valid chain. Keep the key secure and never commit it to version control.*

## FILE FORMAT
 *The log file is a plain text file using UTF‑8 encoding. Each entry is written on its own line, terminated with a newline (\n). Lines are not pretty‑printed (no extra spaces or indentation) to keep the file compact. Empty lines are ignored by the verifier.*

## VERIFICATION
  The entire chain can be verified using the CLI:

(**python -m lidas.cli verify data/audit.log****)

The verifier will:
- Read each line.
- Compute the expected entry_hmac for each entry using the HMAC key.
- Compare it to the stored entry_hmac.
- Check that the next entry’s prev_hmac matches the previous entry’s entry_hmac.
- Report success or indicate the first line where the chain breaks.