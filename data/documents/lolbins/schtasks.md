# schtasks.exe — Task Scheduler

## Description
Built-in Windows utility for creating, querying, and managing scheduled tasks. Adversaries abuse scheduled tasks for persistence and privilege escalation.

## Abused For
- **Persistence:** Create tasks that trigger at logon, system startup, or on a schedule
- **Privilege escalation:** Tasks run as SYSTEM even if created by a lower-privileged user
- **Execution:** Trigger malicious code at specific times or events
- **Lateral movement:** Create remote scheduled tasks via `schtasks /s <target>`
- **Cleanup:** Delete tasks after execution to cover tracks

## Suspicious Usage
```
schtasks.exe /create /tn "WindowsUpdateTask" /tr "C:\temp\malicious.exe" /sc onlogon /ru SYSTEM
schtasks.exe /create /tn "Updater" /tr "powershell -nop -w hidden -e <base64>" /sc daily /st 09:00
schtasks.exe /run /tn "EvilTask"
schtasks.exe /delete /tn "EvilTask" /f
```

## Normal Usage
```
schtasks.exe /create /tn "BackupScript" /tr "C:\scripts\backup.bat" /sc daily /st 02:00
schtasks.exe /query /fo LIST
```

## Detection Flags
- Tasks pointing to executables in user-writable paths
- Tasks configured to run as SYSTEM from non-standard paths
- OnLogon or OnStart triggers with suspicious task names
- Very short or unusual schedule intervals
- Immediate deletion of tasks after creation
