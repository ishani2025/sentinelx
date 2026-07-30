# Enterprise Information Security & Cyber Incident Management Policy

*Companion document: Enterprise Incident Response Playbook. See the Alignment Matrix in the Playbook for step-by-step binding.*

---

# DOCUMENT 2 — ENTERPRISE INFORMATION SECURITY & INCIDENT MANAGEMENT POLICY

## 1. Policy Information

| Field | Value |
|---|---|
| Policy Name | Enterprise Information Security & Cyber Incident Management Policy |
| Version | 1.0 |
| Owner | Chief Information Security Officer (CISO) |
| Effective Date | On approval by Executive Management |
| Review Cycle | Annual, or upon material change / major incident |
| Classification | Internal — Confidential |

## 2. Purpose

Establish mandatory requirements to prevent, detect, respond to, and recover from cyber incidents across all major attack classes, ensuring protection of confidentiality, integrity, and availability of enterprise information assets and compliance with legal and regulatory obligations.

## 3. Scope

Applies to all employees, contractors, and third parties; all information assets, endpoints, servers, networks, applications, data, and cloud environments (AWS/Azure/GCP); all corporate and production systems and DevSecOps pipelines; on-premises, cloud, and hybrid.

## 4. Objectives

Reduce likelihood and impact of incidents; ensure rapid, consistent, auditable response; enforce Zero Trust and least-privilege; maintain regulatory compliance; preserve evidence; enable continuous improvement.

## 5. Definitions

**Incident** — a violation or imminent threat of violation of security policies. **Event** — an observable occurrence. **Crown-jewel asset** — asset whose compromise causes severe business impact. **Regulated data** — PII/PHI/PCI/other legally protected data. **Severity** — Sev1–Sev4 impact classification. **HITL** — human-in-the-loop approval. **WORM** — write-once-read-many immutable storage. **Zero Trust** — never trust, always verify; least privilege; assume breach.

## 6. Roles and Responsibilities

| Role | Responsibilities |
|---|---|
| SOC Analyst | 24×7 monitoring, triage, initial investigation, escalation per matrix |
| Incident Responder | Deep investigation, containment/eradication execution, evidence handling |
| Security Engineer | Detections, tooling, automation, control implementation & hardening |
| Cloud Administrator | Cloud config, IAM, guardrails, executes approved cloud remediation |
| System Owner | Accountable for asset; approves impactful actions on their systems |
| IT Operations | Patching, backups, restoration support, network changes |
| Legal | Regulatory/breach notification, evidence admissibility, contracts |
| HR | Insider cases, disciplinary process, employee communications |
| Communications | Internal/external messaging, PR, customer/regulator statements |
| Executive Management | Governance, risk acceptance, funding, major-incident decisions |

## 7. Policy Statements (mandatory — "shall")

**Prevention.** The organization *shall* implement layered, Zero-Trust-aligned preventive controls and secure-by-default configurations. **Detection.** The SOC *shall* maintain 24×7 detection across endpoint, network, identity, cloud, and application layers. **Logging.** All security-relevant systems *shall* generate logs, forwarded to central, tamper-evident storage retained per §9; cloud audit logging (e.g., CloudTrail) *shall* be enabled org-wide and *shall not* be disabled outside change control. **Monitoring.** Detections *shall* map to MITRE ATT&CK and *shall* be reviewed quarterly. **Access Control.** Access *shall* follow least privilege and be reviewed at least quarterly. **MFA.** Phishing-resistant MFA *shall* be enforced for all users, all remote access, and all privileged and cloud console access. **Privileged Access.** Privileged access *shall* be just-in-time, brokered, session-recorded, and require approval. **Credential Management.** Secrets *shall* be centrally vaulted, rotated, and never hardcoded; exposed credentials *shall* be revoked/rotated immediately. **Asset Management.** A current inventory of assets and data classification *shall* be maintained. **Patch Management.** Critical vulnerabilities *shall* be remediated within defined SLAs (e.g., critical ≤ 7 days, actively-exploited ≤ 48 h). **Backup & Recovery.** Backups *shall* be encrypted, immutable/offline, and restore-tested; RTO/RPO *shall* be defined per system. **Cloud Security.** Cloud environments *shall* enforce CSPM guardrails, block public exposure of sensitive resources, require IMDSv2, and encrypt data at rest/in transit. **Endpoint Protection.** EDR *shall* be deployed and tamper-protected on all endpoints/servers. **Network Security.** Networks *shall* be segmented; egress *shall* be controlled and monitored. **Threat Intelligence.** IOCs *shall* be enriched and operationalized into detection/blocking. **Incident Reporting.** Suspected incidents *shall* be reported immediately per the escalation matrix. **Evidence Preservation.** Evidence *shall* be collected with integrity hashing, chain-of-custody, and WORM retention; legal holds *shall* be honored. **Communication.** External communications *shall* occur only through approved spokespeople and Legal. **Third-Party Management.** Third parties *shall* meet security requirements and be monitored; their incidents *shall* be reportable. **Business Continuity / Disaster Recovery.** BC/DR plans *shall* exist, define RTO/RPO, and be tested at least annually. **Regulatory Compliance.** Applicable regulations *shall* be met, including breach-notification timelines.

## 8. Technical Security Controls (mapping)

| Control Area | CIS v8 | NIST CSF 2.0 | MITRE D3FEND | ISO 27001:2022 Annex A |
|---|---|---|---|---|
| Inventory & Asset Mgmt | 1, 2 | ID.AM | — | A.5.9 |
| Access Control / Least Priv | 5, 6 | PR.AA | Account Locking | A.5.15–A.5.18 |
| MFA / Identity | 6 | PR.AA | Multi-factor Auth | A.5.17 |
| Logging & Monitoring | 8 | DE.CM | Platform Monitoring | A.8.15, A.8.16 |
| Vulnerability/Patch | 7 | ID.RA/PR.PS | — | A.8.8 |
| Malware/Endpoint | 10 | DE.CM/PR.PS | Process Termination | A.8.7 |
| Data Protection | 3 | PR.DS | Encryption | A.8.10–A.8.12 |
| Network Defense | 4, 12, 13 | PR.IR/DE.CM | Network Isolation | A.8.20–A.8.22 |
| Backup/Recovery | 11 | RC.RP | Restore | A.8.13 |
| Incident Response | 17 | RS/RC | Credential Eviction | A.5.24–A.5.28 |
| Threat Intel | 7, 13 | ID.RA | — | A.5.7 |
| Secure DevOps/App | 16 | PR.PS | — | A.8.25–A.8.28 |

## 9. Incident Response Requirements

| Severity | Definition | Response Start | Containment | Notification |
|---|---|---|---|---|
| Sev1 Critical | Active breach of regulated/crown-jewel data; org-wide; ransomware; root/domain compromise | ≤ 15 min | ≤ 30 min | Exec+Legal ≤ 1 h; regulator per law (e.g., ≤ 72 h) |
| Sev2 High | Confirmed compromise, bounded | ≤ 30 min | ≤ 2 h | Exec brief ≤ 4 h |
| Sev3 Medium | Suspected/limited | ≤ 2 h | ≤ 8 h | System Owner |
| Sev4 Low | Policy/config, no compromise | ≤ 1 business day | Per plan | Ticket |

**Escalation criteria:** confirmed compromise, regulated-data involvement, crown-jewel impact, active spread, or SLA breach *shall* escalate. **Evidence retention:** incident records and evidence *shall* be retained a minimum of 12 months (longer where law/contract requires; indefinite under legal hold). **Documentation:** every incident *shall* have a case record, timeline, actions/approvals, and a final report.

## 10. Exceptions Process

Exceptions *shall* be formally requested, risk-assessed, time-bound, compensating-controlled, approved by the CISO (or delegate), logged in the exception register, and reviewed at expiry. No exception may violate a legal/regulatory requirement.

## 11. Enforcement

Non-compliance may result in disciplinary action up to termination and, where applicable, legal action. Technical enforcement (guardrails, SCPs, conditional access) *shall* be applied where feasible.

## 12. Compliance Verification

Continuous control monitoring (CSPM/SIEM/GRC tooling) *shall* verify enforcement; automated evidence collection *shall* feed compliance dashboards; deviations *shall* generate findings with owners and due dates.

## 13. Audit Requirements

Internal audits *shall* occur at least annually and external/independent assessments per regulatory need; audit trails *shall* be immutable and cover who/what/when for security-relevant actions; audit findings *shall* be tracked to closure.

## 14. Policy Review Process

The CISO *shall* review this policy annually and after any Sev1/Sev2 incident or material change; changes *shall* be version-controlled, approved by Executive Management, and communicated to affected parties.

## 15. Appendices

A. Severity classification matrix. B. Data classification scheme. C. Escalation & contact directory. D. Regulatory obligations register. E. Control-to-standard crosswalk (extended). F. Exception register template. G. Definitions glossary.

---
