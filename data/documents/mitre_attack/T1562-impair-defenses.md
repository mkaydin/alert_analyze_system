# T1562: Impair Defenses

## Description
Adversaries may maliciously modify components of a victim environment in order to hinder or disable defensive mechanisms. This includes disabling security tools, modifying firewall rules, stopping logging services, and tampering with security configurations.

## Sub-techniques

### T1562.001: Disable or Modify Tools
Adversaries may disable security tools to avoid detection. Common targets include antivirus/EDR, Sysmon, logging services, and endpoint detection agents.
- **Examples:** Stop Windows Defender (`Stop-Service WinDefend`), uninstall security agents, modify registry to disable real-time protection
- **Detection:** Event ID 5004 (Defender real-time protection changed), 7036 (service stopped)
- **Registry paths:** `HKLM\Software\Policies\Microsoft\Windows Defender\DisableAntiSpyware`

### T1562.002: Disable Windows Event Logging
Adversaries may stop or disable event logging services to prevent detection.
- **Examples:** `wevtutil set-log Security /enabled:false`, `sc stop EventLog`
- **Detection:** Event ID 1100 (Event log service shutdown)
- **Note:** Services requiring admin privileges to disable

### T1562.004: Disable or Modify System Firewall
Adversaries may disable or modify firewall rules to allow C2 traffic or lateral movement.
- **Examples:** `netsh advfirewall set allprofiles state off`, `netsh advfirewall firewall add rule name="Allow" dir=in action=allow protocol=tcp localport=445`
- **Detection:** Event ID 2003 (Firewall profile changed), 4946/4947/4948 (rule added/modified/deleted)

### T1562.006: Disable or Modify Cloud Defenses
Adversaries may disable or modify cloud logging and defenses (applicable for hybrid environments).
- **Examples:** Disable AWS CloudTrail, modify Azure NSG rules, disable GCP VPC Flow Logs

### T1562.010: Downgrade Attack
Adversaries may downgrate or disable system features to evade detection.
- **Examples:** PowerShell v2 downgrade attack (bypasses script block logging)
- **Detection:** Monitor for PowerShell v2 engine usage (`powershell -version 2`)

## MITRE Mapping
- **Tactic:** Defense Evasion
- **Platform:** Windows, macOS, Linux, Cloud
- **Detection:** Service state changes, registry modification events, firewall rule changes, security tool configuration changes
