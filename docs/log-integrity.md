### HMAC
- HMAC (Hash-based Message Authentication Code) is a cryptographic technique used to attach a tamper-proof "*proof of identity"* to a message.

## HMAC CHAIN
 Each new entry into the audit log contains a fingerprint (HMAC) of the previous entry thus forming a linked list of logs. This matters because you cannot compute a valid HMAC for a new entry without knowing the HMAC of the previous one,which would also indicate that there has been some tampering. Likewise,if the HMAC key leaks, an attacker can forge a new,valid HMAC chain.

## GENESIS_HMAC
  This is a string of 64 zeros. Since the very first log entry has no previous enrty to link to, we use this zero-string as a fake previous log. When a verifier reads the log and sees this zero-string at the start, it knows that its officially the beginning of the chain and not a missing or corrupted record.

## ENTRIES
   If any entry in the audit log is altered, all subsequent of previous log are considered invalid and will fail the verification process. This is because the HMAC of one log is used to make the HMAC of the other, anything besides this would render then chain invalid or false. The entire audit log will therefore no longer be trusted if any discrepancies arrive during the verification process.

## VERIFICATION USING CLI
- Open a terminal and navigate to the project root path (eg. desktop/GENKEY/lidas-internship/...)

- Run the verify command; (**python -m lidas.cli verify data/audit.log**). The default path (data/hmac.key). If your key is stored somewhere else, use the (--key) option; (python -m lidas.cli verify data/audit.log --key /path/to/my.key)

- Read the Output; If the audit log chain is intact, (OK: audit log chain is intact) will appear on the screen. If it is broken, (TAMPER DETECTED: chain broken at line X) will appear.

- To test the tamper detection manually, you can intentionally modify the audit log; Open data/audit.log in a text editor. Change one character in any line (e.g., alter an IP address) and then save the file.Run the verify command again, you should now see a tamper‑detected message, pointing to the line you modified.

## LIMITATIONS
 If the HMAC key was to be lost or  potentially leaked, the security of the entire system would be compromised. An attacker would be able create a whole new, valid and consistent HMAC chain and can rewrite the entire audit log. THe key should be treated like a password.