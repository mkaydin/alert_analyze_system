# Edge / Teams / Browser-based LOLBins

## msedge.exe — Microsoft Edge

### Description
The Microsoft Edge browser is a signed Microsoft binary that can be abused for execution and C2 communication.

### Abused For
- **Download:** Edge can download files from the internet
- **Execute:** Edge can spawn child processes (CMD, PowerShell) via protocols
- **C2 communication:** Edge can be used for HTTPS-based C2 (blending with normal web traffic)
- **Detection evasion:** Edge is a trusted Microsoft-signed binary

## msedge_proxy.exe — Edge Proxy

### Description
Edge's proxy helper binary, can be used for code execution and download.

## Teams.exe — Microsoft Teams

### Description
Microsoft Teams is a signed Microsoft binary that can be abused for child process spawning and C2 communication. Teams can spawn cmd.exe, powershell.exe, or Node.js processes.

### Abused For
- **Child process spawning:** Teams.exe spawning cmd.exe or powershell.exe
- **C2 via Teams API:** Using Teams messaging API for C2 traffic
- **Data exfiltration:** Via Teams file upload

## Detection Flags for Browser/Teams LOLBins
- msedge.exe/Teams.exe spawning cmd.exe, powershell.exe, or wscript.exe
- msedge.exe/Teams.exe accessing internal resources or executing scripts
- Child processes of browsers not associated with browser functionality
- Suspicious command-line arguments passed via browser protocols

## MITRE Mapping
- **Tactic:** Execution, Defense Evasion
- **Platform:** Windows
- **Techniques:** T1218.015 (Signed Binary Proxy Execution: Trusted Browser/Application)
