# T1053: Scheduled Task/Job

## Description
Adversaries may use scheduled tasks or jobs to execute programs at specific times or in response to events. Scheduled tasks are a common persistence mechanism and can be abused for execution, privilege escalation, and lateral movement.

## Sub-techniques

### T1053.002: At (Windows)
Adversaries may use the `at.exe` utility to schedule tasks on legacy Windows systems.
- **Suspicious:** `at.exe 09:00 /interactive cmd.exe`
- **Detection:** Event ID 4688 for at.exe execution

### T1053.005: Scheduled Task (Windows)
Adversaries use `schtasks.exe` or PowerShell `New-ScheduledTask` for task creation.
- **Suspicious:**
  - Tasks executing from user-writable paths
  - Tasks running as SYSTEM with suspicious binary paths
  - Tasks with names mimicking legitimate Windows tasks
  - Tasks triggered by logon or startup events
- **Examples:**
  - `schtasks /create /tn "WindowsUpdate" /tr "C:\temp\malware.exe" /sc onlogon /ru SYSTEM`
  - `schtasks /create /tn "Updater" /tr "powershell -nop -w hidden -e <base64>" /sc hourly`

## Detection
- Event ID 4698 (Scheduled task created)
- Event ID 4702 (Scheduled task updated)
- TaskScheduler/Operational Event 106 (Task registered), 200 (Task action started)
- Sysmon Event 1 for process execution following task registration
- Registry: `HKLM\Software\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tasks`
- Filesystem: `C:\Windows\System32\Tasks\`

## MITRE Mapping
- **Tactic:** Execution, Persistence, Privilege Escalation
- **Platform:** Windows, macOS, Linux
