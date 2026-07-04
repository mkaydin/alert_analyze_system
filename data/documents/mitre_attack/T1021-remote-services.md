# T1021: Remote Services

## Description
Adversaries may use remote services to interact with systems that are accessible over a network in order to move laterally. This includes RDP, SMB/Windows Admin Shares, WinRM, SSH, VNC, and other remote access protocols.

## Sub-techniques

### T1021.001: Remote Desktop Protocol
Adversaries may use RDP to access remote systems. RDP is a common lateral movement technique that provides interactive desktop access.
- **Detection:** Event ID 4624 with LogonType 10 (RemoteInteractive), Event ID 1149 (RDP auth success)
- **Hunting:** Look for RDP connections from unusual source IPs or machines

### T1021.002: SMB/Windows Admin Shares
Adversaries may use administrative shares (ADMIN$, C$) for remote access and file transfer.
- **Examples:** `net use Z: \\TARGET\C$`, PsExec service creation over ADMIN$
- **Detection:** Event ID 5140 (network share access), 5145 (detailed share access)

### T1021.003: Distributed Component Object Model
Adversaries may use DCOM objects for lateral movement. DCOM allows remote code execution through COM interfaces.
- **Examples:** `[System.Activator]::CreateInstance([type]::GetTypeFromProgID("MMC20.Application", "TARGET"))`
- **Detection:** DCOM activity monitoring, network connections on RPC ports

### T1021.004: SSH
Adversaries may use SSH for remote access and file transfer on Linux/Unix and modern Windows (OpenSSH).
- **Detection:** SSH authentication logs on Linux, Event ID 4624 with LogonType 3 from SSH

### T1021.006: Windows Remote Management
Adversaries may use WinRM for remote PowerShell execution (Invoke-Command, Enter-PSSession).
- **Detection:** Event ID 91 (WinRM session created), 169 (WinRM auth success)
- **Note:** WinRM traffic flows over HTTP/HTTPS (ports 5985/5986)

## Detection Approach
- Correlate authentication events across systems (Event ID 4624)
- Monitor service creation events (Event ID 7045) from PsExec-style lateral movement
- Track RDP connection events (Event ID 1149, 4624 LogonType 10)
- Look for network authentication followed by process creation on target
- Hunt for anomalous remote service enumeration (net view, nltest)

## MITRE Mapping
- **Tactic:** Lateral Movement
- **Platform:** Windows, macOS, Linux
