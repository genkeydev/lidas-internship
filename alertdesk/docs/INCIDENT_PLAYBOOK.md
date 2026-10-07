# AlertDesk Incident Playbook

## Purpose and scope

Use this playbook when the AlertDesk internship service has a suspected
credential exposure, unauthorized ticket change, unexpected outage, or possible
loss or disclosure of ticket data. It supports the lab service only. AlertDesk
uses shared stub bearer tokens and is not a production incident-response or
SOAR platform. Do not use it to manage real security incidents or sensitive
production data.

## Roles and escalation

- **Responder:** the person on call for the development or lab environment.
  Coordinate with the project maintainer before changing access or stored data.
- **Maintainer:** controls deployment access, credentials, backups, and the
  decision to restore service.
- **Affected users:** report the time, affected environment, observed behavior,
  and ticket identifiers through the team's approved private channel. Do not
  send bearer tokens or sensitive ticket contents in public issues or chat.

If the event involves real credentials, personal data, or a production system,
stop using this playbook alone and follow the responsible organization's
security and privacy escalation process.

## 1. Triage

1. Record when the report arrived, who is responding, the environment, symptoms,
   and the first known affected time. Use UTC and avoid copying secrets or
   unnecessary ticket contents into the incident record.
2. Check service availability at `/health` and review the process or container
   logs for request paths, response codes, and timing around the report.
3. Review relevant rows in the SQLite `audit_events` table for create, assign,
   and transition actions. Audit rows identify a configured role, not an
   individual user. Preserve the original database before investigating.
4. Decide whether the event is an outage, suspected unauthorized access or
   change, data exposure, or data integrity issue. Record the decision and
   notify the maintainer.

Application request logs deliberately omit authorization headers, request
bodies, query strings, and ticket data. Audit event details can contain ticket
titles, assignees, and status changes; handle the database and logs as
potentially sensitive evidence.

## 2. Contain

For suspected token exposure or unauthorized changes, ask the maintainer to
restrict access to the affected environment. If the exposure cannot be bounded,
stop the service while preserving its database and logs. The current stub-token
setup has no per-token revocation or expiry; changing token mappings requires a
controlled configuration change and service restart. Never paste tokens into
the incident record.

For an outage, avoid repeated restarts or database edits until a copy of the
database and relevant logs has been preserved. Do not run destructive Compose
commands such as `docker compose down -v` when the named data volume may contain
evidence or required tickets.

## 3. Investigate and recover

1. Preserve a timestamped copy of the database and relevant deployment logs in
   access-controlled storage. Record who collected each copy and where it is
   stored. Do not alter the original evidence.
2. Compare observed activity with deployment and configuration changes. The
   audit table records application actions but is not tamper-proof and does not
   identify an individual beyond the configured role.
3. For suspected compromise, rebuild from the reviewed source and deployment
   configuration after the maintainer approves recovery. Replace any exposed
   credentials through the controlled configuration process; the sample tokens
   must never be reused outside the lab.
4. Restore ticket data only from a known-good backup after checking its
   integrity. The SQLite file path is configurable with `ALERTDESK_DB`; the
   Compose deployment uses its named `alertdesk-data` volume. Confirm the
   intended database before restarting the service.
5. Verify `/health`, authorized and unauthorized access behavior, and ticket
   read/write behavior against the lab data before reopening access.

## 4. Communicate and close

The maintainer should tell affected lab users what service is unavailable, what
action they should take, and when the next update will arrive. Share only
information they need to respond; do not disclose tokens or unrelated ticket
details. Keep a timeline of decisions, containment, recovery, and notifications.

After recovery, record the cause if known, impact, evidence locations, data
restored or lost, and follow-up owners and dates. Update this playbook or the
deployment/security documentation when the response reveals a gap. Retain or
delete evidence according to the organization's policy.

## Handoff checklist

- Confirm the recipient maintainer and the lab environment to which the work is
  being handed off.
- Share the deployment instructions, database backup location, and any open
  operational risks through the approved private channel.
- Confirm the recipient can restore the service and understands that the
  configured bearer tokens are lab-only.
- For the Week 8 code handoff, submit the isolated `week-8-submission` branch
  for review against the cumulative `interns/Evelyn-Banin` branch. The internship
  guide's final milestone target is `intern/Evelyn-Banin` on the upstream
  repository; prepare that handoff only after the weekly change is reviewed.
