---
source_type: playbook
attack_type: ransomware
mitre_technique: T1486
asset_type: ec2
severity: critical
department: any
title: Ransomware Response Playbook
---
# Ransomware Response Playbook
Incident Description: Rapid encryption of files/objects with extortion demand.
Recommended Investigation Steps:
- Identify patient-zero host and encryption process lineage (EDR).
- Determine scope/blast radius and whether backups were targeted.
Recommended Remediation Steps:
- Isolate affected hosts from the network immediately.
- Restore from validated immutable/offline backups.
- Rotate credentials that may have been exposed; engage IR retainer.
Enterprise Notes: Never pay before scoping. Verify backup integrity before restore; assume credential theft occurred.
