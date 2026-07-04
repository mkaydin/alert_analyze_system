# T1204: User Execution

## Description
An adversary may rely upon a user to execute a payload in order to gain access or execution. Users may be manipulated into executing a malicious file via social engineering, such as opening a malicious email attachment or clicking a link that downloads and opens a malicious file.

## Sub-techniques

### T1204.001: Malicious Link
Adversaries may send users a link to a malicious file or website that, when clicked, triggers execution. Links may be sent via email, social media, or instant messaging. Users may also be redirected to malicious sites via drive-by compromises.

### T1204.002: Malicious File
Adversaries may send a malicious file to a user via email attachment, direct download, or physical media. The user executes the file (e.g., opens a PDF, runs an .exe, enables macros in a document), which triggers malicious code execution.

## Detection
- Monitor email attachments and link clicks in security-aware organizations
- Event ID 4688 / Sysmon 1 for process creation with parent-child relationship analysis
- Office application spawning unusual child processes (e.g., winword.exe spawning cmd.exe)
- Macro execution events in Microsoft Office (Event ID 3003 for Trust Center)
- Analyze email headers and attachment metadata
- User awareness training and phishing simulation results

## Common Examples
- Office document with malicious macros (VBA downloader)
- PDF with embedded JavaScript or exploit
- LNK file in a zip archive pointing to remote payload
- ISO/VHD file containing disguised executable
- Double-clicking a malicious .scr or .exe file

## MITRE Mapping
- **Tactic:** Execution
- **Platform:** Windows, macOS, Linux
- **Permissions Required:** User
