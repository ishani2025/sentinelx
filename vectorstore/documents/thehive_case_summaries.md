# TheHive Case Summaries — Identity & Endpoint Cases (Last 12 Months)

## Case #TH-1183 — Credential theft, Engineering contractor laptop

Infostealer detected via EDR on a contractor laptop; browser credentials for
a CI/CD service account were harvested. No anomalous login was observed
before containment (endpoint isolated within 12 minutes). Closed as
contained/no-impact. Reinforced the value of fast EDR-to-isolation response
time for non-production-adjacent accounts.

## Case #TH-1201 — Anomalous Okta login, Sales account

A Sales account logged in from an unrecognized ASN flagged as a hosting
provider (consistent with proxy/VPN abuse). No preceding endpoint alert.
Investigation concluded it was a false positive caused by the employee using
a personal VPN service; risk-based policy was tuned to reduce noise for
known consumer VPN ASNs while keeping hosting-provider ASNs flagged as high
risk.

## Case #TH-1240 — Scheduled task persistence, Domain Controller

An unsigned driver and a suspicious scheduled task were observed on a domain
controller shortly after a phishing-driven credential compromise elsewhere
in the environment. Treated as a confirmed lateral-movement/persistence
attempt against Tier-0 infrastructure; CISO-level escalation invoked
immediately given the domain controller's CRITICAL criticality rating.
Closed after credential rotation for all domain admin accounts and DC
rebuild.

## Case #TH-1266 — Finance credential compromise + impossible travel

Directly analogous precedent case: browser-credential infostealer on a
Finance analyst's laptop, followed within an hour by a high-risk Okta login
from an unrecognized geography using a hosting-provider IP. CFO approval was
required and obtained for payroll-adjacent containment actions per POL-001.
Session was terminated, password reset, and the endpoint was re-imaged after
persistence (scheduled task) was confirmed on the host.
