#!/usr/bin/env python3
"""
QuietCache — stealth local tool combining:
- Encrypted deniable offline knowledge cache
- On-device claim/document verifier
- Quiet local search & pattern tools
- Shareable encrypted blobs for private transfer (USB/sneakernet/existing channels)

Runs fully offline. No accounts, no telemetry, no external calls.
Looks like a normal notes/search utility.
"""

import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from getpass import getpass

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from rich.console import Console
from rich.table import Table

console = Console()
DEFAULT_STORE = Path.home() / ".local" / "share" / "notes" / "cache.dat"
SALT_SIZE = 16
ITERATIONS = 480_000

class QuietCache:
    def __init__(self, store_path: Path, passphrase: str):
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.key = self._derive_key(passphrase)
        self.fernet = Fernet(self.key)
        self.data = {"entries": {}, "meta": {"created": datetime.utcnow().isoformat()}}
        self._load()

    def _derive_key(self, passphrase: str) -> bytes:
        if self.store_path.exists():
            with open(self.store_path, "rb") as f:
                salt = f.read(SALT_SIZE)
        else:
            salt = os.urandom(SALT_SIZE)
            with open(self.store_path, "wb") as f:
                f.write(salt)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

    def _load(self):
        if not self.store_path.exists() or self.store_path.stat().st_size <= SALT_SIZE:
            return
        try:
            with open(self.store_path, "rb") as f:
                salt = f.read(SALT_SIZE)
                encrypted = f.read()
            if encrypted:
                decrypted = self.fernet.decrypt(encrypted)
                self.data = json.loads(decrypted.decode())
        except Exception:
            console.print("[red]Failed to decrypt. Wrong passphrase or corrupted store.[/red]")
            sys.exit(1)

    def _save(self):
        encrypted = self.fernet.encrypt(json.dumps(self.data).encode())
        with open(self.store_path, "wb") as f:
            salt = open(self.store_path, "rb").read(SALT_SIZE) if self.store_path.exists() else os.urandom(SALT_SIZE)
            f.write(salt)
            f.write(encrypted)

    def add_entry(self, title: str, content: str, tags: list = None):
        eid = hashlib.sha256(f"{title}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
        self.data["entries"][eid] = {
            "title": title,
            "content": content,
            "tags": tags or [],
            "added": datetime.utcnow().isoformat(),
            "hash": hashlib.sha256(content.encode()).hexdigest()
        }
        self._save()
        return eid

    def add_file(self, title: str, file_path: Path, tags: list = None):
        content = file_path.read_bytes()
        text = content.decode(errors="replace")
        file_hash = hashlib.sha256(content).hexdigest()
        eid = hashlib.sha256(f"{title}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
        self.data["entries"][eid] = {
            "title": title,
            "content": text[:50000],
            "full_hash": file_hash,
            "tags": tags or [],
            "added": datetime.utcnow().isoformat(),
            "source_mtime": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "is_file": True
        }
        self._save()
        return eid, file_hash

    def search(self, query: str):
        q = query.lower()
        results = []
        for eid, entry in self.data["entries"].items():
            if q in entry["title"].lower() or q in entry["content"].lower() or any(q in t.lower() for t in entry.get("tags", [])):
                results.append((eid, entry))
        return results

    def verify(self, claim: str, source_id: str = None):
        claim_hash = hashlib.sha256(claim.encode()).hexdigest()
        matches = []
        for eid, entry in self.data["entries"].items():
            if source_id and eid != source_id:
                continue
            if claim_hash == entry.get("hash") or claim.lower() in entry.get("content", "").lower():
                matches.append({"id": eid, "title": entry["title"], "match": "exact" if claim_hash == entry.get("hash") else "text"})
        return matches

    def verify_document(self, file_path: Path, source_id: str = None):
        content = file_path.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()
        text = content.decode(errors="replace")
        matches = []
        for eid, entry in self.data["entries"].items():
            if source_id and eid != source_id:
                continue
            if entry.get("full_hash") == file_hash:
                matches.append({"id": eid, "title": entry["title"], "match": "exact hash", "added": entry["added"]})
            elif text and text[:200].lower() in entry.get("content", "").lower():
                matches.append({"id": eid, "title": entry["title"], "match": "text overlap", "added": entry["added"]})
        return matches, file_hash

    def export_stealth_blob(self, entry_ids: list, out_path: Path):
        payload = {eid: self.data["entries"][eid] for eid in entry_ids if eid in self.data["entries"]}
        blob = self.fernet.encrypt(json.dumps(payload).encode())
        header = f"# Local notes backup - {datetime.utcnow().date()}\n# Do not edit\n".encode()
        out_path.write_bytes(header + b"\n---\n" + base64.b64encode(blob))
        return out_path

    def import_stealth_blob(self, blob_path: Path):
        raw = blob_path.read_bytes()
        try:
            if b"---\n" in raw:
                _, b64part = raw.split(b"---\n", 1)
                encrypted = base64.b64decode(b64part)
            else:
                encrypted = raw
            decrypted = self.fernet.decrypt(encrypted)
            payload = json.loads(decrypted.decode())
            for eid, entry in payload.items():
                self.data["entries"][eid] = entry
            self._save()
            return len(payload)
        except Exception as e:
            console.print(f"[red]Import failed: {e}[/red]")
            return 0

    def list_entries(self):
        return self.data["entries"]

def main():
    parser = argparse.ArgumentParser(description="QuietCache — stealth local cache, verifier, and private transfer")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init")
    p_add = sub.add_parser("add")
    p_add.add_argument("title")
    p_add.add_argument("content")
    p_add.add_argument("--tags", nargs="*", default=[])

    p_search = sub.add_parser("search")
    p_search.add_argument("query")

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("claim")

    p_export = sub.add_parser("export")
    p_export.add_argument("ids", nargs="+")
    p_export.add_argument("-o", "--out", type=Path, required=True)

    p_import = sub.add_parser("import")
    p_import.add_argument("blob", type=Path)

    sub.add_parser("list")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    passphrase = getpass("Passphrase: ")
    if args.cmd == "init" or not args.store.exists():
        confirm = getpass("Confirm passphrase: ")
        if passphrase != confirm:
            console.print("[red]Passphrases do not match.[/red]")
            return

    qc = QuietCache(args.store, passphrase)

    if args.cmd == "add":
        eid = qc.add_entry(args.title, args.content, args.tags)
        console.print(f"[green]Added entry[/green] {eid}")
    elif args.cmd == "search":
        results = qc.search(args.query)
        if not results:
            console.print("No matches.")
            return
        table = Table(title="Search results")
        table.add_column("ID")
        table.add_column("Title")
        table.add_column("Tags")
        for eid, e in results:
            table.add_row(eid, e["title"], ", ".join(e.get("tags", [])))
        console.print(table)
    elif args.cmd == "verify":
        matches = qc.verify(args.claim)
        if matches:
            console.print("[green]Matches found:[/green]")
            for m in matches:
                console.print(f"  {m['id']} — {m['title']} ({m['match']})")
        else:
            console.print("[yellow]No local matches.[/yellow]")
    elif args.cmd == "export":
        path = qc.export_stealth_blob(args.ids, args.out)
        console.print(f"[green]Exported to[/green] {path}")
    elif args.cmd == "import":
        n = qc.import_stealth_blob(args.blob)
        console.print(f"[green]Imported {n} entries.[/green]")
    elif args.cmd == "list":
        entries = qc.list_entries()
        if not entries:
            console.print("Empty cache.")
            return
        table = Table(title="Local cache")
        table.add_column("ID")
        table.add_column("Title")
        table.add_column("Added")
        for eid, e in entries.items():
            table.add_row(eid, e["title"], e["added"][:19])
        console.print(table)

if __name__ == "__main__":
    main()
