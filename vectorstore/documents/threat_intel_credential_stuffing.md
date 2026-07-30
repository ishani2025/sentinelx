# Threat Intelligence — Credential Stuffing & Infostealer Campaigns Targeting Finance Staff

**Report ref:** TI-2026-Q2-014
**Confidence:** Medium-High

## Summary

Multiple threat intelligence vendors report an ongoing campaign targeting
finance and accounting staff at mid-size enterprises with invoice-themed
phishing lures that deliver commodity infostealer malware (browser
credential harvesting). Harvested credentials are typically reused within
1-3 hours from infrastructure hosted on bulletproof/anonymizing hosting
providers, consistent with automated credential-stuffing tooling rather than
manual operator activity.

## Indicators associated with this campaign

- Infostealer binaries frequently disguised as "update_helper", "invoice_viewer",
  or similarly named utility executables.
- Command-and-control and credential-reuse infrastructure has been observed
  on ASNs flagged as "unknown-hosting" / bulletproof hosting.
- Logins following this pattern frequently originate from Eastern Europe
  (including Russia-geolocated infrastructure) even when the victim
  organization has no legitimate business presence there.

## Assessment

Organizations with Finance-department staff holding standing access to
payroll or general-ledger systems should treat any infostealer detection on
a Finance endpoint, followed by an anomalous login for the same user, as
consistent with this active campaign rather than an isolated incident, and
respond with the full credential-compromise containment playbook.
