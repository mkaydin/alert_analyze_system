# Playbook: Credential Access — LSASS Dumping Investigation

## Objective
Detect and respond to attempts to extract credentials from LSASS process memory, which indicates an adversary with privileged access seeking to escalate or move laterally.

## Detection Signals
- **Process access to lsass.exe** with suspicious access flags (Event ID 4656)
- **Procdump** running against lsass.exe: `procdump.exe -ma lsass.exe`
- **comsvcs.dll** usage: `rundll32.exe comsvcs.dll,MiniDump`
- **Task Manager** creating lsass.dmp files
- **Mimikatz** in process memory (event ID 4104 script block logging)
- **Volume shadow copy** access to SAM, SYSTEM, SECURITY hives

## Immediate Actions
1. **Isolate** the affected host from the network
2. **Identify** the tool/technique used (Mimikatz, procdump, comsvcs)
3. **Check** dump file creation in: `%TEMP%`, `%SYSTEMROOT%\Temp`, user profile
4. **Determine** which accounts are affected (domain admin, service accounts, local users)

## Investigation
- Review authentication logs for pass-the-hash or pass-the-ticket activity
- Check if dumped credentials were used against other systems (Event ID 4624, 4648)
- Look for lateral movement originating from the affected host
- Identify initial access vector — how did the attacker get admin rights?

## Containment
- **Reset credentials** for all accounts that were active on the affected host
- **Rotate** KRBTGT password twice if domain controller was affected (Golden Ticket)
- **Disable** compromised service accounts
- **Enforce** LSASS protection (RunAsPPL) on all endpoints

## Remediation
1. Deploy Credential Guard on all Windows endpoints
2. Enable Windows Defender Credential Guard via group policy
3. Restrict SeDebugPrivilege to Administrators only
4. Enable additional logging: PowerShell Script Block Logging, Command Line Auditing
5. Deploy ASR rules to block LSASS dumping via Office apps, PSExec, and WMI
