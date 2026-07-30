# MITRE ATT&CK — Persistence & Defense Evasion Reference

## T1053.005 — Scheduled Task/Job: Scheduled Task

Adversaries commonly create a Windows scheduled task to establish
persistence after initial access, often chained directly off a
dropper/loader process so it survives a reboot or logoff. A scheduled task
created shortly after a credential-theft or malicious-execution alert on the
same host is a strong indicator the attacker is establishing a foothold
rather than a one-off, contained event.

## T1176 — Browser Extensions

Malicious or low-reputation browser extensions can be used for persistence
and passive data collection (browsing history, form data, session tokens).
Lower severity in isolation, but notable when it co-occurs with credential
theft indicators on the same host or user.

## T1215 — Kernel Modules and Extensions

Unsigned drivers loaded outside of normal software deployment channels are
a common defense-evasion and rootkit-persistence technique. Should be
triaged with software inventory context — an unsigned driver tied to a
known, benign hardware vendor is lower priority than one with no
attribution.

## Mitigations

- Audit newly created scheduled tasks for unfamiliar binaries or scripts
  executing from temp/user-writable directories.
- Require driver signing enforcement; alert on any successfully loaded
  unsigned kernel driver.
- Treat any persistence technique observed within the same session as a
  confirmed credential-theft alert as escalating the incident, not a
  separate low-severity item.
