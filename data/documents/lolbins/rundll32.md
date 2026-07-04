# rundll32.exe — Windows Rundll32

## Description
Microsoft-signed binary that executes a specified function within a DLL. Part of the Windows operating system, used by both legitimate applications and attackers.

## Abused For
- **Executing DLL functions:** `rundll32.exe <dll>,<function>`
- **JavaScript/HTML execution:** `rundll32.exe javascript:"\..\mshtml,RunHTMLApplication"`
- **COM activation:** Execute arbitrary COM objects
- **DLL sideloading:** Placing malicious DLLs next to legitimate executables

## Suspicious Usage
```
rundll32.exe javascript:"\..\mshtml,RunHTMLApplication";<script code>
rundll32.exe comsvcs.dll,MiniDump <PID> lsass.dmp full
rundll32.exe c:\users\public\malicious.dll,EntryPoint
```

## Normal Usage
```
rundll32.exe shell32.dll,Control_RunDLL
rundll32.exe url.dll,FileProtocolHandler http://example.com
rundll32.exe printui.dll,PrintUIEntry
```

## Detection Flags
- Executing JavaScript or HTML via rundll32
- Loading DLLs from user-writable directories
- Using `comsvcs.dll,MiniDump` (credential dumping indicator)
