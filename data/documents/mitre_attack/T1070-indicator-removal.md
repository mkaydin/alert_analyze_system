# T1070: Indicator Removal

## Description
Adversaries may delete or modify artifacts generated within a system to remove evidence of their presence. This includes clearing logs, deleting files, wiping event logs, and removing evidence of tool execution.

## Sub-techniques

### T1070.001: Clear Windows Event Logs
Adversaries may clear Windows Event Logs to hide traces of their activity. Event logs are cleared via `wevtutil cl System`, `wevtutil cl Security`, `wevtutil cl Application`, or PowerShell's `Clear-EventLog`.
- **Detection:** Event ID 1102 (Security log cleared), Event ID 104 (System log cleared)
- **ATT&CK:** High confidence indicator of malicious activity

### T1070.004: File Deletion
Adversaries may delete files left behind by their tools. This includes droppers, scripts, archives, and configuration files. Tools like `del`, `rm`, PowerShell `Remove-Item`, or built-in tool cleaner scripts.
- **Detection:** Sysmon Event ID 23 (File Delete), EDR file deletion events
- **Context:** Often paired with T1059 for cleanup after execution

### T1070.006: Timestomp
Adversaries may modify file timestamps (creation, modification, access) to hide file creation times. Tools like `SetMace` or PowerShell `(Get-Item file).CreationTime = $date` are used.
- **Detection:** MACE timestamp inconsistencies via Sysmon Event ID 2 (File creation time changed)
- **Forensic analysis:** Compare timestamps across MACE attributes for anomalies

### T1070.007: Clear Network Connection History
Adversaries may clear ARP cache, DNS cache, or NetBIOS name cache to remove evidence of network connections.
- **Detection:** `arp -d`, `ipconfig /flushdns` execution events

## MITRE Mapping
- **Tactic:** Defense Evasion
- **Platform:** Windows, macOS, Linux
- **Detection:** Log clearing events, Sysmon file deletion logs, MACE timestamp analysis
