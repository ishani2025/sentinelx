# Incident Playbook — Ransomware / Data Encrypted for Impact (T1486)

**Scope:** Applies when file encryption activity, ransom notes, or mass file
modification consistent with ransomware is observed.

## Containment

1. Immediately isolate affected hosts from the network — do not power off
   (preserves memory forensics).
2. Disable affected service/user accounts identified as the encryption
   process owner.
3. Identify and isolate any additional hosts showing early-stage indicators
   (mass file renames, shadow copy deletion attempts) before full encryption
   completes.

## Investigation

4. Identify the ransomware family via file extension pattern / ransom note
   artifacts and correlate with threat intelligence.
5. Determine initial access vector (phishing, exposed RDP, compromised
   credentials, supply chain).
6. Assess backup integrity for affected systems before considering recovery.

## Recovery

7. Recovery requires executive and legal sign-off before any ransom-related
   communication; SentinelX's remediation plan should never include ransom
   payment or negotiation actions.
8. Restore from verified clean backups; rebuild rather than clean-in-place
   for systems with confirmed encryption.
