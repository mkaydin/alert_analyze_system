# Playbook: LOLBin Execution — regsvr32 / rundll32 / mshta

## Objective
Investigate and contain suspicious execution of living-off-the-land binaries (LOLBins) used for code execution.

## Triage Steps
1. **Identify the parent process** — what spawned the LOLBin?
   - Suspicious: Office apps, browser, WMI, scheduled tasks
   - Benign: Windows installer, system processes
2. **Inspect command line** — look for `/s` (silent), remote URLs, encoded scripts
3. **Check network connections** — did the LOLBin reach out to external IPs?
4. **Review child processes** — did it spawn cmd, powershell, or other executables?

## Containment
- Block the parent process binary if unsigned
- Add remote IP/domain to blocklist
- Kill malicious process tree
- Remove startup persistence (Run keys, scheduled tasks, services)

## Deep Investigation
- Extract and analyze any downloaded payload (.sct, .hta, .dll)
- Check for DLL sideloading: look for unsigned DLLs in the LOLBin's directory
- Review Event ID 4688 (process creation) with command-line auditing
- Cross-reference with Threat Intelligence for known IOCs

## Escalation Criteria
- Credential dumping detected in child processes
- Lateral movement attempted
- Multiple hosts affected
- Persistence mechanism identified

## Recommended Actions
1. Quarantine affected endpoints
2. Collect full process memory dumps
3. Review logs for lateral movement
4. Reset credentials for affected accounts
5. Escalate to incident response team
