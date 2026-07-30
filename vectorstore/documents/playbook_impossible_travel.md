# Incident Playbook — Anomalous Login / Impossible Travel

**Scope:** Applies when an identity provider (e.g. Okta) flags a login as
high risk due to impossible travel, a new/unrecognized device, or an
anonymizing proxy/hosting provider ASN.

## Containment

1. Treat the flagged session as hostile: terminate it immediately rather
   than waiting for user confirmation.
2. Cross-reference the account's recent endpoint activity — if a credential
   theft or malware alert preceded the anomalous login on the user's normal
   device, treat both as the same incident (compromised credentials used
   from a new location), not two unrelated events.
3. Lock the account pending verification if the risk score is HIGH and the
   login originated from a geography inconsistent with the user's normal
   pattern within an implausible time window of their last known-good
   session.

## Investigation

4. Determine what the anomalous session accessed before termination
   (application access, OAuth grants, data exports).
5. Check whether the account has standing access to CRITICAL or
   RESTRICTED-data applications; if so, treat this as high business impact
   regardless of the identity provider's own risk score, since the
   blast radius extends beyond the identity system itself.

## Recovery

6. Re-enable the account only after password reset, MFA re-enrollment, and
   endpoint remediation (if the root cause was endpoint credential theft)
   are complete.
7. Notify the account owner's manager and the application owners whose
   systems the account can reach.
