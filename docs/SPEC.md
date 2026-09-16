# PROJECT LIDAS

## PURPOSE
**Project LIDAS is a lightweight intrusion detection system designed to provide real-time network intrusion detection on resource-constrained devices without exceeding a specific amount of RAM, idealy between 500MB to 1GB of RAM, and on a single CPU core while monitoring a 100Mbps link.**

## SCOPE
**Log formats supported by Project LIDAS include:**
- JSON
- CSV
- Syslog

*The following are operations that are out-of-scope for Project LIDAS;*
- **Active Traffic Prevention (IPS)**: *Active mitigation turns the IDS into an IPS (Intrusion Prevention System) which is resource-intensive.*

- **Deep Application-Layer Parsing**: *A lightweight IDS stops at protocol header and raw payload level; it does not try to reconstruct or execute file objects*

- **Full Packet Capture**: *A lightweight system logs alerts only, removing the raw packet data immediately after evaluation*

- **Advanced Behavioral Anomaly Detection**:*Lightweight systems strictly use predetermined, rule-based signature matching to avoid using massive, resource-intensive memory pools.*

- **Centralized Log Management and Visualization**:*Graphical tools and databases consume far more RAM than the packet engine itself. A lightweight IDS strictly outputs raw text files e.g. standard JSON or Syslog format, relieving the visualization task to an entirely separate server.*

## DETECTION RULES

- SSH-001:*Detects SSH brute force attacks* (HIGH)
- HTTP-001:*Detects possible SQL injections* (CRITICAL)
- HTTP-002:*Detects suspicious user agents* (MEDIUM)
- CANARY-001:*Detects access to Canary token* (CRITICAL)
- HTTP-003:*Detects possible directory/path scans* (MEDIUM)
- HTTP-004:*Detects credential stuffing agaainst web logins* (HIGH)

## Acceptance Criteria
**Triggered**
- SSH-001:*When ≥5 failed SSH logins from one IP in 60s*
- HTTP-001:*When SQLi signatures in the HTTP request path*
- HTTP-002:*When known scanner tools in User-Agent string*
- HTTP-003:*When ≥10 HTTP 404s from one IP in 30s*
- CANARY-001:*When there is access to decoy paths or canary SSH users*
- HTTP_004:*When ≥10 401 HTTP responses from the same IP in 60s*

**Not Triggered**
- SSH-001:*if <= 4 failed SSH logins from one IP in 60s OR if 5 or more failed SSH logins from the same IP spans longer than 60s OR if SSH login is successful(repeated) OR if network-level connection attempts do not reach the SSH authentication stage*

- HTTP-001:*if SQLi signatures only appear in the HTTP headers or the HTTP request body OR if a request where the signature is part of a legitimate, static resource name*

- HTTP-002:*if User-Agent string belongs to a legitimate web browser OR where there are standard search engine crawlers (Googlebot, Bingbot, DuckDuckBot) OR if a request that has no User-Agent header at all*

- HTTP-003:*if 9 or fewer 404 responses from one IP in 30s OR 10 or more 404 responses from the same IP spans longer than 30s OR if a request returns a HTTP status other than 404, even if they are for weird paths OR if there is legitimate traffic to a REST API that returns "404 Not Found" for valid,exsisting resource IDs that have been deleted.*

- HTTP-004:*if 9 or fewer 401 responsses from one IP in 60 seconds OR 10 or more 401 responses from the same IP spans longer than the 60s window OR if a request returns a HTTP status other than 401 OR DDoS attacks.* 

- CANARY-001:*if access to any path or user is not explicitly configured as a decoy the canary definition OR if when internal health checks or security scanners on the whitelist are operating OR if a 404 status response for a path that resembles a decoy but was never configured as one.*