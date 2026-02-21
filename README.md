# SafeDrop 🔒

> **Secure. Simple. Shareable.**  
> A command-line file sharing tool with built-in malware scanning and encryption.

Developed by **Vision KC**

---

## Features

| Feature | Description |
|---|---|
| 🔍 **Security Scanning** | Extension check, magic byte detection, entropy analysis, and script pattern matching |
| 🔐 **Encryption at Rest** | All files encrypted with Fernet (AES-128-CBC + HMAC-SHA256) before storage |
| 🆔 **Unique File IDs** | Cryptographically secure 12-character IDs (e.g. `ABCD-WXYZ-2345`) |
| ⏰ **File Expiry** | Set automatic expiry (1–365 days, or never) |
| 🗑️ **Auto-Delete** | Optionally delete a file after its first download |
| 📊 **Download Counter** | Track how many times a file has been downloaded |
| 📝 **Logging** | All uploads and downloads logged to `~/.safedrop/safedrop.log` |
| 🛡️ **Directory Traversal Prevention** | All file paths validated to stay within the storage directory |
| 💻 **Rich Terminal UI** | Clean, colorful interface powered by [Rich](https://github.com/Textualize/rich) |

---

## Installation

### Requirements

- Python 3.9 or higher
- pip

### Install from source

```bash
git clone https://github.com/VisionKC/safedrop.git
cd safedrop
pip install -e .
```

### Install dependencies only

```bash
pip install -r requirements.txt
```

---

## Usage

### Run SafeDrop

```bash
# If installed as a package:
safedrop

# Or run directly with Python:
python -m safedrop
```

### Main Menu

```
  ____         __       ____
 / __/__ _____/ /__ ___/ / /______  ___
_\ \/ _ `/ _  / -_) _  / __/ __/ \/ _ \
/___/\_,_/\_,_/\__/\_,_/\__/_/  /_/ .__/
                                  /_/

  Secure. Simple. Shareable.
  v1.0.0  ·  Developed by Vision KC

  ┌────────────────────────────────────────┐
  │  1   Upload File    Share a file       │
  │  2   Download File  Retrieve by ID     │
  │  3   Exit           Quit SafeDrop      │
  └────────────────────────────────────────┘
```

### Upload a File

1. Select **1** from the menu
2. Enter the full path to your file
3. SafeDrop scans the file for threats
4. Set expiry days (0 = never expires)
5. Choose auto-delete and add an optional note
6. Your unique **File ID** is displayed — share it with the recipient

### Download a File

1. Select **2** from the menu
2. Enter the File ID (e.g. `ABCD-WXYZ-2345`)
3. Choose a destination directory
4. The file is decrypted and restored to your chosen location

---

## Security

### Malware Detection

SafeDrop runs four layers of scanning before accepting any file:

1. **Extension Check** — Blocks 50+ dangerous file types (`.exe`, `.bat`, `.ps1`, `.sh`, `.dll`, `.jar`, etc.)
2. **Magic Byte Detection** — Reads file headers to detect executables regardless of extension (MZ, ELF, Mach-O, shebang, ZIP, OLE2)
3. **Entropy Analysis** — Calculates Shannon entropy; files with entropy > 7.5/8.0 are flagged as potentially packed/encrypted malware
4. **Script Pattern Matching** — Scans file content for known malicious patterns (PowerShell download cradles, reverse shells, obfuscation techniques)

### Encryption

- Files are encrypted with **Fernet** (symmetric authenticated encryption)
- Each file gets its own unique encryption key
- Keys are stored in the metadata file (`~/.safedrop/metadata.json`)
- The stored file format uses the `.sdf` (SafeDrop File) extension

### Storage Layout

```
~/.safedrop/
├── storage/          # Encrypted file storage (chmod 700)
│   ├── ABCDWXYZ2345.sdf
│   └── ...
├── metadata.json     # File records (IDs, keys, expiry, etc.)
└── safedrop.log      # Audit log
```

### Input Validation

- All file IDs are validated against the expected format before lookup
- Destination paths are sanitized to prevent directory traversal
- File size is limited to **500 MB** per upload
- Original filenames are stripped of directory components on restore

---

## Configuration

Edit `safedrop/config.py` to customize:

| Setting | Default | Description |
|---|---|---|
| `MAX_FILE_SIZE_MB` | `500` | Maximum upload size in MB |
| `DEFAULT_EXPIRY_DAYS` | `7` | Default file expiry |
| `ENTROPY_THRESHOLD` | `7.5` | Entropy threshold for malware detection |
| `STORAGE_DIR` | `~/.safedrop/storage/` | Where encrypted files are stored |

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Project Structure

```
SafeDrop/
├── safedrop/
│   ├── __init__.py       # Package metadata
│   ├── __main__.py       # Entry point & main loop
│   ├── config.py         # Configuration constants
│   ├── id_generator.py   # Secure ID generation
│   ├── logger.py         # Logging setup
│   ├── security.py       # Malware scanning
│   ├── crypto.py         # File encryption/decryption
│   ├── metadata.py       # File record management
│   ├── storage.py        # Secure file storage
│   ├── upload.py         # Upload flow
│   ├── download.py       # Download flow
│   └── cli.py            # Terminal UI
├── tests/
│   ├── test_id_generator.py
│   ├── test_security.py
│   ├── test_crypto.py
│   ├── test_metadata.py
│   └── test_storage.py
├── requirements.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Vision KC**  
[Github](https://github.com/vision-dev1)
[Portfolio](https://visionkc.com.np)

