# Incident Playbook — Credential Compromise

**Scope:** Applies when an endpoint detection alert indicates credential
theft (e.g. infostealer accessing browser credential stores) and/or an
identity provider reports anomalous authentication for the same user.

## Containment

1. Revoke all active sessions for the affected identity provider account.
2. Force a password reset on next login; invalidate the current password
   immediately.
3. Isolate the source endpoint from the network to stop further credential
   harvesting and prevent lateral movement.
4. If the account has access to financial, HR, or other restricted-data
   systems, notify the system owner so downstream access can be reviewed.

## Investigation

5. Review authentication logs for the account across all connected
   applications (SSO, OAuth token grants) for the period between the
   suspected compromise and containment.
6. Identify the process/file responsible for credential theft on the
   endpoint and capture its hash for threat-intel correlation.
7. Check for persistence mechanisms (scheduled tasks, new services, browser
   extensions) created on the same host after the initial alert.

## Recovery

8. Reissue MFA factors if there is any indication the attacker enrolled a
   new device/factor.
9. Re-image the endpoint if persistence or further compromise is confirmed;
   otherwise a targeted malware removal plus credential rotation is
   sufficient.
10. Restore endpoint to the network only after containment actions are
    verified.

## Notes

- Approval requirements for containment/remediation actions on
  finance/HR-owned assets are governed by organizational policy, not this
  playbook — the Policy node determines those separately.
