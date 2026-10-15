# QuietCache

Stealth local tool combining:
- Encrypted deniable offline knowledge cache
- On-device claim/document verifier
- Quiet local search
- Shareable encrypted blobs for private transfer (USB, existing channels, sneakernet)

Fully offline. No accounts, no telemetry, no network calls by default.
Store defaults to `~/.local/share/notes/cache.dat` (looks like ordinary notes).

## Usage

```bash
python3 quietcache.py init
python3 quietcache.py add "Title" "Content here" --tags source ref
python3 quietcache.py search "keyword"
python3 quietcache.py verify "exact claim text"
python3 quietcache.py list
python3 quietcache.py export abc123 -o share.txt
python3 quietcache.py import share.txt
```

## GUI

```bash
python3 quietcache_gui.py
```

Opens a local window (title shows as “Notes”). Tabs for Add, Search, Verify (text or file), and Transfer. Dark mode toggle included.

## Features

- **Stealth local verifier** — Drop in a claim or document. Checks against local primary sources using hashes, timestamps, and text. Fully on-device, no network.
- **Ambient private channel** — Export/import as ordinary-looking notes files. Transfer via USB, existing channels, or sneakernet. No servers, no persistent identifiers.
- Encrypted deniable offline knowledge cache
- Quiet local search over your own data

Dependencies: Python 3 + `cryptography` and `rich` (and `python3-tk` for GUI).

Install on Kali:
```bash
sudo apt install python3 python3-pip python3-tk
pip3 install --user cryptography rich
```
