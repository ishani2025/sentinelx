---
source_type: playbook
attack_type: data_exfiltration
mitre_technique: T1530
asset_type: s3
severity: high
department: any
title: S3 Data Exfiltration Response Playbook
---
# S3 Data Exfiltration Response Playbook
Incident Description: Large-volume object retrieval from a sensitive S3 bucket via compromised credentials.
Recommended Investigation Steps:
- Enable/inspect S3 data events in CloudTrail for GetObject volume.
- Use Macie to confirm data classification (PII/PCI) of exfiltrated objects.
- Identify the principal and source IP; check for prior credential theft.
Recommended Remediation Steps:
- Revoke the offending principal's access and rotate its credentials.
- Re-enable S3 Block Public Access; tighten the bucket policy.
- Preserve object versions for forensics; notify the Data Protection Officer.
Enterprise Notes: For PII buckets, engage Legal/DPO immediately and start the breach-notification clock. Blocking the IP alone does not stop a valid-credential exfiltration.
