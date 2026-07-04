# wmic.exe — Windows Management Instrumentation Command-Line

## Description
Legitimate Microsoft tool for querying WMI (Windows Management Instrumentation). Provides deep system information access and can execute processes remotely. Frequently abused by attackers for execution and lateral movement.

## Abused For
- **Remote process execution:** `wmic.exe /node:<target> process call create "<command>"`
- **Local process execution:** `wmic.exe process call create "<command>"`
- **Data exfiltration:** Query system information, user lists, process lists
- **Lateral movement:** Execute commands on remote systems without psexec

## Suspicious Usage
```
wmic.exe process call create "powershell.exe -nop -w hidden -c IEX(...)"
wmic.exe /node:192.168.1.100 /user:admin process call create "cmd.exe /c whoami"
wmic.exe process call create "rundll32.exe javascript:\..\mshtml,..."
```

## Normal Usage
```
wmic.exe process list brief
wmic.exe /node:SRV-APP service where "name like 'sql%'" get name,state
```

## Detection Flags
- `process call create` used with uncommon binaries
- Remote node execution (`/node:` parameter)
- Child process spawning from wmic.exe
- Scheduled task or service creation via wmic
