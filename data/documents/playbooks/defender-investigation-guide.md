# Microsoft Defender for Endpoint — Alert Investigation Guide

## Alert Triage Workflow

### Step 1: Review Alert Details
- Open the alert in Defender portal
- Review the alert title, description, severity (informational/low/medium/high)
- Note the detection source (EDR, AV, custom detection, ASR)
- Check MITRE ATT&CK mapping if available

### Step 2: Examine Affected Assets
- Identify the device(s) involved
- Check device risk level, OS platform, onboarding status
- Review logged-on users during the incident time window
- Check if device is isolated or needs isolation

### Step 3: Analyze the Alert Story (Process Tree)
- Review the process tree in the Defender alert page
- Identify:
  - Initial process (parent) — how did execution start?
  - Child processes — what was spawned?
  - Command lines — are they suspicious?
  - File hashes — check reputation
  - Network connections — where did it connect to?
  - Registry modifications — what was changed?

### Step 4: Investigate Related Signals
- **Process creation timeline:** Review Event 4688 for related processes
- **Network connections:** Check for C2 beaconing patterns
- **File modifications:** Look for dropped files, DLL sideloading
- **Registry changes:** Check persistence mechanisms
- **Scheduled tasks/services:** Review for new persistence

### Step 5: Determine Scope
- Check if the same indicator (hash, IP, domain) appears on other devices
- Run Advanced Hunting queries for related activity
- Review authentication logs for lateral movement
- Check email logs if phishing is suspected

## Key Advanced Hunting Queries

### Find process creation by a specific binary on all devices
```
DeviceProcessEvents
| where FileName == "regsvr32.exe"
| where Timestamp > ago(7d)
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName
```

### Find network connections from suspicious processes
```
DeviceNetworkEvents
| where InitiatingProcessFileName in~ ("regsvr32.exe", "rundll32.exe", "mshta.exe")
| where Timestamp > ago(7d)
| project Timestamp, DeviceName, InitiatingProcessFileName, RemoteIP, RemotePort, RemoteUrl
```

### Detect service creation events
```
DeviceEvents
| where ActionType == "ServiceCreated"
| where Timestamp > ago(7d)
| project Timestamp, DeviceName, FileName, FolderPath, ServiceName, ServiceStartType
```

## Common Defender Alert Categories
- **Initial Access:** Phishing emails, exploit kits, compromised credentials
- **Execution:** Office apps spawning processes, WMI execution, script execution
- **Persistence:** Registry Run keys, scheduled tasks, services, startup folder
- **Privilege Escalation:** UAC bypass, token manipulation, service creation
- **Defense Evasion:** Disabling security tools, log clearing, process injection
- **Credential Access:** LSASS dumping, credential theft tools
- **Discovery:** Network scanning, account enumeration
- **Lateral Movement:** RDP connections, SMB/PsExec, WinRM
