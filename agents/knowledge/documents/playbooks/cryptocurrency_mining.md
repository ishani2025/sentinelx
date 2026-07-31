---
source_type: playbook
attack_type: cryptocurrency_mining
mitre_technique: T1496
asset_type: ec2
severity: high
department: any
title: EC2 Cryptocurrency Mining Response Playbook
---
# EC2 Cryptocurrency Mining Response Playbook
Incident Description: A compromised EC2 instance establishes outbound connections to a known cryptocurrency mining pool, consuming compute resources for unauthorized mining (cryptojacking).
Recommended Investigation Steps:
- Correlate the GuardDuty finding with VPC Flow Logs for the mining pool IP/domain and connection volume.
- Inspect the instance for unexpected high CPU utilization and unfamiliar mining processes or binaries.
- Review CloudTrail and the instance's IAM role for signs of initial access via a vulnerable public-facing app.
Recommended Remediation Steps:
- Isolate the instance (quarantine security group; remove from load balancer / auto-scaling group).
- Snapshot the EBS volume for forensics prior to any termination.
- Block outbound access to the mining pool IP/domain at the security group / WAF layer.
- Revoke and rotate the instance's IAM role credentials/STS sessions; rebuild from a known-good AMI.
Enterprise Notes: Cryptojacking is often a symptom of a broader compromise, not the root cause — identify and patch the initial access vector, don't just kill the miner process. Snapshot before terminating.
