# Playbook: Persistence Detection — Scheduled Tasks / Services / Run Keys

## Objective
Investigate persistence mechanisms discovered on endpoints and systematically eliminate attacker footholds.

## Initial Triage
1. **Identify the type:**
   - Service (`services.msc`, `sc query`)
   - Scheduled task (`schtasks /query`)
   - Registry Run key (`reg query HKLM\...\Run`)
   - Startup folder (`shell:startup`)
2. **Check the binary path** — is it in a user-writable directory?
3. **Review digital signature** — is the binary signed by a trusted publisher?
4. **Check creation time** — was it created around the same time as the alert?

## Containment Steps
- **Disable** the service/task (do not delete yet — preserve for forensics)
- **Block** the binary hash via Defender/AV
- **Kill** any running instances of the malicious binary
- **Identify** how the persistence was installed (parent process, user account)

## Investigation
- Trace the origin: which user created it, from which machine
- Look for related IOC matches (file hashes, IPs, domains)
- Check if the persistence spreads to other parts of the registry/filesystem
- Review timeline: first activity vs. persistence creation time

## Remediation
1. Remove the persistence mechanism (service, task, registry key)
2. Run full antimalware scan on affected hosts
3. Check for additional persistence mechanisms (attackers often install multiple)
4. Review and rotate credentials for affected user accounts
5. Apply principle of least privilege to service accounts

## Post-Incident
- Create detection rule for similar persistence patterns
- Add binary hashes to blocklist
- Document the TTPs mapped to MITRE ATT&CK
