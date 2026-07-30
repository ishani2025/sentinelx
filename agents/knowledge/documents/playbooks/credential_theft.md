---
source_type: playbook
attack_type: credential_theft
mitre_technique: T1552.005
asset_type: iam_user
severity: high
department: any
title: Cloud Credential Theft Response Playbook
---
# Cloud Credential Theft Response Playbook
Incident Description: AWS IAM/STS credentials stolen and used from an external location.
Recommended Investigation Steps:
- Identify the compromised principal and all sessions in CloudTrail.
- Determine whether credentials were exfiltrated from EC2 instance metadata (IMDS).
- Correlate with identity provider (Okta/Entra) sign-in anomalies.
Recommended Remediation Steps:
- Rotate the IAM credentials/access keys.
- Invalidate active STS sessions (revoke temporary session tokens).
- Enforce IMDSv2 on the affected instances.
- Notify the Identity team and force re-authentication with MFA.
Enterprise Notes: Rotating keys alone is insufficient — active STS tokens remain valid until explicitly revoked. Always pair rotation with STS session invalidation and Identity-team notification.
