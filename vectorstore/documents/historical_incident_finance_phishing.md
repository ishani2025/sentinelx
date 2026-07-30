# Historical Incident — INC-2025-0417: Finance Team Spear-Phishing

**Date:** 2025-04-17
**Department:** Finance
**Outcome:** Contained, no data loss confirmed

## Summary

A Finance team member received a spear-phishing email impersonating a
vendor invoice, opened a malicious attachment that executed an infostealer,
and had browser-stored credentials exfiltrated. Approximately 40 minutes
later, the compromised Okta account was used to log in from an IP address
geolocated outside the employee's normal working region. Security On-Call
isolated the endpoint and Finance leadership (CFO) approved an emergency
session revocation and password reset within the 15-minute CRITICAL
escalation SLA.

## Root cause

Attachment-based infostealer delivery; no MFA challenge on the anomalous
login because the account's MFA factor had a "remember this device" window
that had not yet expired.

## Lessons applied

- Reduced "remember this device" trust window for Finance-department
  accounts.
- Added automatic session termination (not just alerting) for HIGH-risk
  Okta login events tied to accounts with Payroll or GL access.
- This incident is the direct precedent for the current Credential
  Compromise Response Policy (POL-001) and Endpoint Isolation Policy
  (POL-004).
