### Security Policy

## Reporting a vulnerability

*The security of LIDAS is taken seriously. If you believe that you have encountered a security risk, please report it to us privately*

**Please do not report security vulnerabilities through the public GIthub issues**.*Instead, please send an email to **'moyosorelonge24@gmail.com'**. Feedback will be given between 24-48 hours after your initial report has been submitted. We will keep you updated on our progress towards the fix.

*We appretiate your help in keeping LIDAS and its users safe*

## HMAC key handling

*LIDAS usses a secret HMAC key to sign each audit log entry, ensuring the log's integrity and tamper-evidence. This key is loaded from the path specified by the (LIDAS_KEY_PATH) environment variable. If this varriable is not set, the default path is (data/hmac.key).*

**NOTICE**
*Never commit the HMAC key to version control. Ensure (data/hmac.key) or custom path, is listed in your (.gitignore) file to prevent accidental exposure.*
 
*The key file should have strict permissions. On Unix-like systems, use (chmod 0600) to ensure only the owning user can read and write the file.*

*The HMAC key is essential for verifying the audit log. If the key is lost, you will not be able to validate the integrity of existing logs. Back up the key securely and store it separately from the audit logs themselves.*

*If the HMAC key is lost or compromised, the integrity of the entire audit log cannot be verified. In the event of key compromise, you must consider all existing logs untrustworthy and rotate to a new key, which will invalidate all previous HMAC signatures.*

## Audit log immutability

*The audit log is designed to be an append-only, tamper-evident record of events. LIDAS writes audit entries to the path specified by the (LIDAS_AUDIT_LOG_PATH) environment variable, which defaults to (data/audit.log).*

*The audit log is strictly append-only. New entries are added to the end of the file, and existing entries are never modified.*

*Manually editing the audit log file with a text editor will break the HMAC integrity checks and corrupt the log. The log is not meant to be human-readable or manually modified.*

*To check the integrity of the audit log, use the built-in (lidas verify) command. This tool will read the log file, recompute the HMAC for each entry using the secret key, and report any entries that have been tampered with. This is the only supported way to interact with the log's integrity features.*

## Scope limitations

[**LIDAS is a lightweight, focused tool designed to provide tamper-evident audit logging for specific applications. It is not a replacement for a full-featured Security Information and Event Management (SIEM) system or a production-grade enterprise logging solution.**

*LIDAS does not provide log aggregation, real-time alerting, advanced querying, or correlation across multiple data sources. It is intended to be a building block for integrity, not a complete monitoring platform.*

*LIDAS is designed for single-host audit logging. It does not natively support distributed logging or clustering across multiple machines.*

*LIDAS relies on the operating system's file permissions for access control to the audit log and key file. It does not manage user authentication or authorization for log access.*

*For extremely high-volume logging, you may need to tune the log rotation or consider the performance impact of HMAC computation on every entry.*