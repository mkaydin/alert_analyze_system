# Windows Event IDs for Incident Response — Comprehensive Reference

## Authentication and Logon (Security Log)

| ID | Description | Investigation |
|----|------------|---------------|
| 4624 | Successful logon. Check LogonType (2=Interactive, 3=Network, 10=RDP) | Who authenticated, from where, using what method |
| 4625 | Failed logon. Check Status/SubStatus codes | Brute-force detection, password spray hunting |
| 4634 | Logon session ended | Session duration calculation |
| 4647 | User-initiated logoff | Eplicit user action |
| 4648 | Explicit credential use (runas, remote auth) | Lateral movement detection |
| 4672 | Special privileges assigned (SeDebugPrivilege) | Privilege escalation indicator |
| 4778/4779 | RDP session reconnected/disconnected | RDP session tracking |
| 4800/4801 | Workstation locked/unlocked | User session timeline |

## Domain Authentication (Domain Controllers)

| ID | Description | Investigation |
|----|------------|---------------|
| 4768 | Kerberos TGT request (AS-REQ) | Golden ticket detection, unusual encryption |
| 4769 | Kerberos service ticket request (TGS-REQ) | Kerberoasting detection |
| 4771 | Kerberos pre-auth failed | Password spraying indicator |
| 4776 | NTLM credential validation | NTLM abuse detection |

## Account and Group Management

| ID | Description | Investigation |
|----|------------|---------------|
| 4720 | User account created | Persistence indicator (Subject = attacker) |
| 4722 | User account enabled | Suspicious account activation |
| 4723/4724 | Password change/reset | Account takeover detection |
| 4726 | User account deleted | Covering tracks |
| 4740 | Account locked out | Attacker brute-force or user mistake |
| 4732 | Member added to security-enabled local group | Privilege escalation (especially Administrators) |
| 4756 | Member added to universal group | Domain privilege escalation |

## Process Execution

| ID | Log | Description |
|----|-----|-------------|
| 4688 | Security | Process creation (enable command-line auditing!) |
| 4689 | Security | Process termination |
| 1 | Sysmon | Process create with hashes, parent info |
| 3 | Sysmon | Network connection per process |
| 7 | Sysmon | Image (DLL) loaded |
| 8 | Sysmon | CreateRemoteThread (process injection indicator) |
| 10 | Sysmon | ProcessAccess (LSASS access detection) |
| 11 | Sysmon | FileCreate (malware dropper detection) |
| 22 | Sysmon | DNSEvent (DNS queries per process) |
| 25 | Sysmon | ProcessTampering (process hollowing) |

## PowerShell Activity

| ID | Log | Description |
|----|-----|-------------|
| 4103 | PowerShell/Operational | Module/pipeline logging |
| 4104 | PowerShell/Operational | **Script block logging** (captures decoded scripts) |
| 4105/4106 | PowerShell/Operational | Script block invocation start/stop |
| 400 | Windows PowerShell | Engine started |
| 800 | Windows PowerShell | Pipeline execution |

## Services and Drivers

| ID | Log | Description |
|----|-----|-------------|
| 7045 | System | **Service installed** (Cobalt Strike detection) |
| 7036 | System | Service state change |
| 7034 | System | Service terminated unexpectedly |
| 7040 | System | Service start type changed |
| 4697 | Security | Service installed (requires audit policy) |
| 6 | Sysmon | Driver loaded (BYOVD detection) |

## Scheduled Tasks

| ID | Log | Description |
|----|-----|-------------|
| 4698 | Security | Scheduled task created |
| 4699 | Security | Scheduled task deleted |
| 4702 | Security | Scheduled task updated |
| 106 | TaskScheduler/Operational | Task registered |
| 140 | TaskScheduler/Operational | Task updated |
| 141 | TaskScheduler/Operational | Task deleted |
| 200 | TaskScheduler/Operational | Task action started |
| 129 | TaskScheduler/Operational | Task launched new process (has PID) |

## Remote Access and Lateral Movement

| ID | Log | Description |
|----|-----|-------------|
| 1149 | RemoteConnectionManager | User authenticated to RDP listener |
| 21 | LocalSessionManager | RDP session logon |
| 22 | LocalSessionManager | Shell start |
| 23 | LocalSessionManager | Session logoff |
| 24 | LocalSessionManager | Session disconnected |
| 40 | LocalSessionManager | Session disconnection reason |
| 5140 | Security | Network share accessed |
| 5145 | Security | File share detailed access check |
| 91 | WinRM/Operational | Session created |
| 169 | WinRM/Operational | User authenticated successfully |

## Defense Evasion and Log Tampering

| ID | Log | Description |
|----|-----|-------------|
| 1102 | Security | **Security log cleared** (HIGH priority alert) |
| 104 | System | System log cleared |
| 1100 | Security | Event log service shutdown |
| 4719 | Security | System audit policy changed |
| 4739 | Security | Domain policy changed |

## Microsoft Defender Events

| ID | Log | Description |
|----|-----|-------------|
| 1116 | Defender/Operational | Malware detected |
| 1117 | Defender/Operational | Action taken against malware |
| 1121 | Defender/Operational | Blocked by ASR rule |
| 5001 | Defender/Operational | Real-time protection disabled |
| 5007 | Defender/Operational | Defender configuration changed |
| 5010 | Defender/Operational | Scanning for malware disabled |
| 5013 | Defender/Operational | Tamper protection blocked change |

## Windows Firewall

| ID | Log | Description |
|----|-----|-------------|
| 2003 | Firewall | Profile changed |
| 2004/2097 | Firewall | Rule added to exception list |
| 2006/2099 | Firewall | Rule deleted |
| 2009 | Firewall | Firewall disabled for profile |
| 4946/4947/4948 | Security | Rule added/modified/deleted |

## AppLocker

| ID | Log | Description |
|----|-----|-------------|
| 8002 | AppLocker | EXE allowed |
| 8003 | AppLocker | EXE would be blocked (audit mode) |
| 8004 | AppLocker | EXE blocked |
| 8006 | AppLocker | Script would be blocked |
| 8007 | AppLocker | Script blocked |

## LogonType Reference (Event 4624/4625)
- **2:** Interactive (console)
- **3:** Network (SMB, WMI, RPC)
- **4:** Batch (scheduled task)
- **5:** Service
- **7:** Unlock
- **8:** NetworkCleartext (IIS Basic Auth)
- **9:** NewCredentials (runas /netonly)
- **10:** RemoteInteractive (RDP)
- **11:** CachedInteractive (offline DC logon)
