# MITRE ATT&CK Enterprise Tactics Overview

## Overview
The MITRE ATT&CK Enterprise framework catalogs 14 tactics that describe the "why" behind each step of an attack. Tactics represent the adversary's technical objectives.

## The 14 Enterprise Tactics

### TA0043: Reconnaissance
The adversary is gathering information to plan future operations. This includes active and passive scanning, OSINT gathering, and target identification.
- **Techniques:** 10
- **Examples:** Active Scanning, Search Open Websites/Domains, Gather Victim Identity Information

### TA0042: Resource Development
The adversary is acquiring resources to support operations. This includes infrastructure, accounts, and capabilities.
- **Techniques:** 8
- **Examples:** Acquire Infrastructure, Develop Capabilities, Obtain Capabilities, Stage Capabilities

### TA0001: Initial Access
The adversary is trying to get into your network. Includes entry vectors like phishing, exploitation, and valid accounts.
- **Techniques:** 9
- **Examples:** Drive-by Compromise, Exploit Public-Facing Application, External Remote Services, Phishing, Valid Accounts

### TA0002: Execution
The adversary is trying to run malicious code. Includes techniques for running payloads on target systems.
- **Techniques:** 14
- **Examples:** Command and Scripting Interpreter, Native API, Scheduled Task/Job, User Execution, Windows Management Instrumentation

### TA0003: Persistence
The adversary is trying to maintain their foothold. Includes mechanisms that ensure continued access across reboots and credential changes.
- **Techniques:** 19
- **Examples:** Account Manipulation, Boot or Logon Autostart Execution, Create Account, Create or Modify System Process, Scheduled Task/Job, Valid Accounts

### TA0004: Privilege Escalation
The adversary is trying to gain higher-level permissions. Includes techniques for obtaining SYSTEM/root or domain admin access.
- **Techniques:** 13
- **Examples:** Abuse Elevation Control Mechanism, Access Token Manipulation, Boot or Logon Autostart Execution, Create or Modify System Process, Process Injection

### TA0005: Defense Evasion
The adversary is trying to avoid being detected. Includes techniques for bypassing security controls, obfuscation, and hiding malicious activity.
- **Techniques:** 42
- **Examples:** Abuse Elevation Control Mechanism, Deobfuscate/Decode Files or Information, Indicator Removal, Masquerading, Modify Registry, Process Injection, Signed Binary Proxy Execution

### TA0006: Credential Access
The adversary is trying to steal account names and passwords. Includes techniques for obtaining credentials from systems.
- **Techniques:** 17
- **Examples:** Brute Force, Credential Dumping, Credentials from Password Stores, Input Capture, OS Credential Dumping, Steal Web Session Cookie

### TA0007: Discovery
The adversary is trying to figure out your environment. Includes techniques for system and network information gathering.
- **Techniques:** 30
- **Examples:** Account Discovery, Application Window Discovery, File and Directory Discovery, Network Service Scanning, Process Discovery, System Information Discovery

### TA0008: Lateral Movement
The adversary is trying to move through your network. Includes techniques for pivoting from compromised systems to others.
- **Techniques:** 9
- **Examples:** Exploitation of Remote Services, Internal Spearphishing, Remote Service Session Hijacking, Remote Services, Taint Shared Content, Use Alternate Authentication Material

### TA0009: Collection
The adversary is trying to gather data of interest. Includes techniques for identifying and collecting sensitive data.
- **Techniques:** 17
- **Examples:** Archive Collected Data, Audio Capture, Automated Collection, Clipboard Data, Data from Information Repositories, Email Collection, Input Capture, Screen Capture

### TA0011: Command and Control
The adversary is trying to communicate with compromised systems to control them. Includes various C2 protocols and techniques.
- **Techniques:** 16
- **Examples:** Application Layer Protocol, Data Encoding, Data Obfuscation, Dynamic Resolution, Encrypted Channel, Ingress Tool Transfer, Non-Application Layer Protocol, Non-Standard Port, Protocol Tunneling, Remote Access Software

### TA0010: Exfiltration
The adversary is trying to steal data. Includes techniques for removing data from the target network.
- **Techniques:** 9
- **Examples:** Automated Exfiltration, Data Transfer Size Limits, Exfiltration Over Alternative Protocol, Exfiltration Over C2 Channel, Exfiltration Over Physical Medium, Scheduled Transfer

### TA0040: Impact
The adversary is trying to manipulate, interrupt, or destroy systems and data. Includes techniques for damaging or disrupting operations.
- **Techniques:** 13
- **Examples:** Data Destruction, Data Manipulation, Defacement, Disk Wipe, Endpoint Denial of Service, Firmware Corruption, Inhibit System Recovery, Network Denial of Service, Resource Hijacking, Service Stop, System Shutdown/Reboot

## MITRE ATT&CK Navigator
The ATT&CK Navigator is a web-based tool for visualizing and heat-mapping ATT&CK techniques. It allows analysts to layer threat intelligence, detection coverage, and gap analysis onto the ATT&CK matrix.
