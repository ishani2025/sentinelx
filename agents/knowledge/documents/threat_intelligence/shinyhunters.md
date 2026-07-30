---
source_type: threat_intel
attack_type: data_exfiltration
mitre_technique: T1530
asset_type: s3
severity: high
department: any
title: Threat Actor - ShinyHunters
---
# Threat Actor: ShinyHunters
Campaign: Harvesting exposed cloud credentials and env files to access and exfiltrate cloud data stores.
IOCs: access from hosting-provider ASNs; mass GetObject; credentials sourced from public code leaks.
MITRE Techniques: T1552.001 (Credentials in Files), T1530 (Data from Cloud Storage).
Notes: Rotate exposed credentials, scan repos, and monitor S3 data events.
