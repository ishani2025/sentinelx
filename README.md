# SentinelX

**Autonomous, AI-native SOC platform that turns cloud security alerts into cross-platform, policy-governed incident response.**

SentinelX sits on top of AWS security services and correlates threats across AWS **and** non-AWS systems (identity, endpoint, network), reasons over them with a mesh of specialized AI agents, executes a governed response with human-in-the-loop approval, and documents every incident as an auditable case that feeds its long-term memory.

> Built for the FRONTIER 2026 AI & Agentic Product Challenge (AWS Student Builder Groups · VIT Chennai) — Track 02, Agentic Systems.

---

## The problem

Enterprise SOCs receive ~3,000 cloud-security alerts a day; ~46% are false positives, ~62% of alerts are never investigated, and there's a global shortage of ~4.8M security professionals. Real threats — stolen credentials, exposed data, privilege escalation — slip through because they span systems no single tool watches together, and attackers stay hidden a mean of ~181 days. Detection tools raise alerts but don't *investigate or respond* — that manual reasoning is what buries analysts.

## What SentinelX does

- **Consumes** AWS detection + the GuardDuty Investigation Agent instead of rebuilding them.
- **Correlates** the AWS finding with non-AWS signals (Okta/Azure AD, EDR, firewall) by shared identity, IP, and time — reconstructing the *whole* attack chain, not just the AWS half.
- **Reasons** with specialized agents that add business context, policy, historical incidents, and risk.
- **Responds** under governance — low-risk actions auto-run; high-impact actions require human approval.
- **Records & learns** — every incident becomes an audited TheHive case that feeds a RAG knowledge base.

## Differentiator

AWS's GuardDuty Investigation Agent investigates only *inside AWS*. SentinelX is the layer on top that adds cross-platform correlation, enterprise context and policy, and governed response — the part AWS deliberately leaves to the customer.

---

## Architecture

```
AWS sources (GuardDuty, Macie, Inspector, CloudTrail)          Non-AWS sources
        │                                            (Okta/Azure AD, EDR, Firewall)
   Security Hub ── EventBridge ──▶ SentinelX ◀── Universal Log Collector
                                      │
                     GuardDuty Investigation Agent (AWS-native investigation)
                                      │
                            ┌──── Supervisor Agent ────┐   (cross-platform correlation)
              Business Context · Policy · Historical · Risk Assessment
                                      │
                          Response Planning ──▶ Execution Agent
                        auto (low-risk) │ human approval (high-impact)
                                      │
                           boto3 / AWS + enterprise APIs
                                      │
                    TheHive case + Slack report ──▶ RAG knowledge base
```

Colour legend used in the deck: **blue = AWS (consumed)**, **violet = SentinelX (built)**.

---

## Repository structure

```
sentinelx/
├── README.md                     # this file
├── config/                       # settings, policies, assets, risk_matrix
├── ingestion/
│   ├── aws/                      # Security Hub, GuardDuty, CloudTrail, Macie clients
│   └── connectors/               # Enterprise Connector Layer (Okta, AD, EDR, firewall, syslog)
├── normalization/                # unified event model + normalizer
├── correlation/                  # correlate by identity · IP · time
├── agents/                       # supervisor + specialized agents (business/policy/historical/risk/response/execution/verification)
├── rag/                          # vector store, knowledge base, retriever
├── response/                     # governor, approval, executors (aws/enterprise)
├── integrations/                 # thehive, slack, jira, servicenow
├── reporting/                    # incident report assembly
├── orchestrator/                 # pipeline (the spine)
├── api/                          # FastAPI app
├── demo/
│   ├── sample_logs/              # matched cross-platform attack logs (Okta+EDR+FW+CloudTrail+GuardDuty+Macie+SecHub)
│   └── run_demo.py               # replays the attack end-to-end
├── tests/
└── docs/
    └── governance/
        ├── IR_Playbook.md        # enterprise incident response playbook (26 sections + artifacts)
        └── Security_Policy.md    # enterprise security policy (15 sections)
```

Related deliverables (kept outside this code repo):
- **`../sentinelx_playbooks/`** — library of 109 machine-readable YAML detection playbooks across 29 categories (schema-validated).
- **`../SentinelX_Design_Doc.md`** — full engineering design of the AI-native SOAR platform.

---

## Demo

A single cross-platform attack, told across 7 matched log sources (all share user `jsmith`, attacker IP `203.0.113.77`, timeline 09:00–09:22):

1. **EDR** — infostealer steals credentials on the laptop
2. **Okta** — login from Russia (impossible travel)
3. **Firewall/VPN** — same IP, impossible-travel alert
4. **CloudTrail** — console login (no MFA) → CreateAccessKey → mass GetObject on the PII bucket
5. **GuardDuty** — `Exfiltration:S3` finding
6. **Macie** — bucket holds PII (business context)
7. **Security Hub** — aggregated finding (the EventBridge trigger)

SentinelX correlates all seven into one incident, flags the PII exposure, and proposes a governed response (auto-notify + human-approved key disable).

```bash
python demo/run_demo.py        # replays demo/sample_logs end-to-end
```

---

## Tech stack

- **AWS:** GuardDuty (+ Investigation Agent), Security Hub, CloudTrail, Macie, Inspector, EventBridge, IAM, S3, Lambda, AWS SDK (boto3)
- **AI:** LLM (Amazon Bedrock or open model) orchestrated as a multi-agent system; RAG over a vector store (FAISS/OpenSearch)
- **Integrations:** Okta/Azure AD, EDR, firewalls (Enterprise Connector Layer); TheHive + Cortex; Slack/Jira/ServiceNow
- **Backend:** Python, FastAPI; event-driven (EventBridge); optional Step Functions orchestration

## Setup

```bash
git clone <repo> && cd sentinelx
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add AWS creds, TheHive/Slack tokens, model config
python demo/run_demo.py       # run the offline demo (no AWS account needed)
```

## Standards & compliance

Aligned to NIST SP 800-61, NIST CSF 2.0, MITRE ATT&CK, MITRE D3FEND, CIS Controls v8, ISO/IEC 27001/27002, Zero Trust (NIST 800-207), CSA CCM, and OWASP. See `docs/governance/`.

## Roadmap

Multi-cloud parity (Azure/GCP), real cross-system identity resolution, confidence-calibrated autonomy, predictive/pre-emptive playbooks, and formal audit certification. See the design doc for details.

## Team

FRONTIER 2026 · Track 02 (Agentic Systems) — *add team name + members here.*

## License

TBD.
