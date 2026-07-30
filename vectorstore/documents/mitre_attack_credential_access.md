# MITRE ATT&CK — Credential Access & Initial Access Reference

## T1555.003 — Credentials from Password Stores: Credentials from Web Browsers

Adversaries deploy infostealer malware that reads browser credential stores
(saved passwords, session cookies, autofill data) from Chrome, Edge, and
Firefox profile directories. Once harvested, credentials are typically
exfiltrated to an attacker-controlled endpoint within minutes and reused for
account takeover before the victim notices anything unusual. This technique
is frequently the first stage of a broader account-takeover chain: steal
credentials on the endpoint, then use them from a different location to
authenticate to SaaS/identity providers such as Okta.

Detection signals: a process (often disguised as a legitimate updater or
helper binary) accessing browser `Login Data` / `Cookies` SQLite files,
followed shortly after by outbound network connections to unfamiliar
external IPs from the same host.

## T1078 — Valid Accounts

Once credentials are stolen, adversaries authenticate using legitimate,
valid account credentials rather than exploiting a vulnerability. This makes
the activity blend in with normal user behavior and is why identity
providers score logins for anomalies (new device, impossible travel,
anonymizing proxy/VPN) rather than relying on credential validity alone.

## T1110 — Brute Force

Adversaries may systematically guess or replay credentials (including
password-spraying reused/leaked credentials against many accounts) to gain
initial access. Distinguished from T1078 by the presence of many failed
authentication attempts prior to a success.

## Mitigations

- Enforce MFA on all identity provider logins, especially for accounts with
  access to financial or HR systems.
- Immediately revoke active sessions and force a password reset for any
  account flagged for credential compromise.
- Isolate the source endpoint to prevent further credential harvesting or
  lateral movement while the account is being secured.
