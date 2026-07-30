# Threat Intelligence — Commodity Infostealer Ecosystem Trends

**Report ref:** TI-2026-Q2-021
**Confidence:** High

## Summary

Commodity infostealer malware-as-a-service families continue to be the most
common precursor to enterprise account takeover, largely displacing manual
phishing-only credential theft. These families specialize in browser
credential store extraction, session-cookie theft (enabling MFA bypass via
session hijacking, not just password reuse), and rapid resale of harvested
credential logs on criminal marketplaces within hours of collection.

## Relevance to identity provider monitoring

Because session-cookie theft can bypass MFA entirely, an anomalous login
following a confirmed infostealer detection should be treated as
higher-confidence account takeover even if MFA shows as satisfied on the
new session — the MFA satisfaction may reflect a replayed/stolen session
token rather than a fresh factor challenge.

## Recommendation

Prioritize speed of session revocation over waiting for MFA-based signals
when an infostealer detection and an anomalous login for the same user
occur close together in time.
