"""
SafeDrop Configuration
Central configuration constants for the SafeDrop application.
"""

import os
from pathlib import Path

# ─── Storage Paths ────────────────────────────────────────────────────────────
BASE_DIR = Path.home() / ".safedrop"
STORAGE_DIR = BASE_DIR / "storage"
METADATA_FILE = BASE_DIR / "metadata.json"
LOG_FILE = BASE_DIR / "safedrop.log"

# ─── Limits ───────────────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ─── Expiry ───────────────────────────────────────────────────────────────────
DEFAULT_EXPIRY_DAYS = 7
MAX_EXPIRY_DAYS = 365

# ─── ID Settings ──────────────────────────────────────────────────────────────
ID_LENGTH = 12

# ─── Dangerous File Extensions ────────────────────────────────────────────────
DANGEROUS_EXTENSIONS = {
    # Windows executables & scripts
    ".exe", ".bat", ".cmd", ".com", ".scr", ".pif",
    ".msi", ".msp", ".mst", ".vbs", ".vbe", ".js",
    ".jse", ".wsf", ".wsh", ".ps1", ".ps1xml", ".ps2",
    ".ps2xml", ".psc1", ".psc2", ".msh", ".msh1", ".msh2",
    ".mshxml", ".msh1xml", ".msh2xml", ".reg", ".inf",
    # Linux/Mac executables & scripts
    ".sh", ".bash", ".zsh", ".ksh", ".csh", ".fish",
    ".elf", ".out", ".run",
    # Compiled code / libraries
    ".dll", ".so", ".dylib", ".sys", ".drv",
    # Java
    ".jar", ".jnlp", ".class",
    # Office macros
    ".xlsm", ".xlsb", ".xltm", ".docm", ".dotm",
    ".pptm", ".potm", ".ppam", ".ppsm", ".sldm",
    # Other
    ".hta", ".cpl", ".gadget", ".application",
    ".appref-ms", ".lnk", ".url",
}

# ─── Dangerous Magic Bytes (file signatures) ──────────────────────────────────
# Format: (offset, bytes, description)
DANGEROUS_SIGNATURES = [
    (0, b"MZ",                       "Windows PE executable (MZ header)"),
    (0, b"\x7fELF",                  "Linux ELF executable"),
    (0, b"\xca\xfe\xba\xbe",         "Java class file / Mach-O fat binary"),
    (0, b"\xfe\xed\xfa\xce",         "Mach-O 32-bit executable"),
    (0, b"\xfe\xed\xfa\xcf",         "Mach-O 64-bit executable"),
    (0, b"\xce\xfa\xed\xfe",         "Mach-O 32-bit (reversed)"),
    (0, b"\xcf\xfa\xed\xfe",         "Mach-O 64-bit (reversed)"),
    (0, b"#!/",                       "Unix shebang script"),
    (0, b"#!",                        "Unix shebang script"),
    (0, b"PK\x03\x04",               "ZIP/JAR archive (may contain executables)"),
    (0, b"\xd0\xcf\x11\xe0",         "Microsoft Office OLE2 compound document"),
]

# ─── Suspicious Script Patterns ───────────────────────────────────────────────
SUSPICIOUS_PATTERNS = [
    # PowerShell download cradles
    b"Invoke-WebRequest",
    b"IEX(",
    b"Invoke-Expression",
    b"DownloadString",
    b"DownloadFile",
    b"Net.WebClient",
    b"Start-Process",
    b"powershell -enc",
    b"powershell -e ",
    # Python/shell execution
    b"__import__('os')",
    b"subprocess.call",
    b"subprocess.Popen",
    b"os.system(",
    b"eval(base64",
    b"exec(base64",
    b"exec(compile",
    # Shell commands
    b"curl | bash",
    b"wget | bash",
    b"curl|bash",
    b"wget|bash",
    b"bash -i >& /dev/tcp",
    b"/bin/sh -i",
    b"nc -e /bin/sh",
    # Obfuscation
    b"base64_decode",
    b"fromCharCode",
    b"String.fromCharCode",
    b"unescape(",
    b"ActiveXObject",
    b"WScript.Shell",
    b"Shell.Application",
]

# ─── Entropy Threshold ────────────────────────────────────────────────────────
# Files with entropy > this value may be packed/encrypted malware
ENTROPY_THRESHOLD = 7.5
ENTROPY_SAMPLE_SIZE = 65536  # 64 KB sample

# ─── App Info ─────────────────────────────────────────────────────────────────
APP_NAME = "SafeDrop"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Vision KC"
APP_TAGLINE = "Secure. Simple. Shareable."
