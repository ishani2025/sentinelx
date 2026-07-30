---
source_type: threat_intel
attack_type: credential_theft
mitre_technique: T1078.004
asset_type: iam_user
severity: high
department: any
title: Threat Actor - Scattered Spider
---
# Threat Actor: Scattered Spider (UNC3944)
Campaign: Identity-first intrusions via help-desk social engineering and MFA fatigue.
IOCs: use of legitimate remote-access tools; anomalous Okta/Entra sign-ins; impossible travel.
MITRE Techniques: T1566 (Phishing), T1078.004 (Valid Cloud Accounts), T1621 (MFA Request Generation).
Notes: Attacks begin in identity systems before touching cloud infrastructure. Prioritize session revocation and MFA reset.
