#!/usr/bin/env python3
"""
QuietCache GUI — local window for the stealth cache/verifier/transfer tool.
Uses only standard library Tkinter + the existing QuietCache class.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from quietcache import QuietCache, DEFAULT_STORE

class QuietCacheGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Notes")
        self.root.geometry("720x520")
        self.root.minsize(600, 400)
        self.qc = None
        self.store_path = DEFAULT_STORE
        self.dark_mode = tk.BooleanVar(value=False)
        self.style = ttk.Style()
        self._apply_theme()
        self._build_login()

    def _apply_theme(self):
        if self.dark_mode.get():
            bg = "#1e1e1e"
            fg = "#e0e0e0"
            entry_bg = "#2d2d2d"
            self.style.theme_use("clam")
            self.style.configure(".", background=bg, foreground=fg, fieldbackground=entry_bg)
            self.style.configure("TFrame", background=bg)
            self.style.configure("TLabel", background=bg, foreground=fg)
            self.style.configure("TButton", background="#333333", foreground=fg)
            self.style.configure("TEntry", fieldbackground=entry_bg, foreground=fg)
            self.style.configure("TNotebook", background=bg)
            self.style.configure("TNotebook.Tab", background="#2d2d2d", foreground=fg)
            self.style.map("TNotebook.Tab", background=[("selected", "#3a3a3a")])
            self.root.configure(bg=bg)
            self.text_bg = entry_bg
            self.text_fg = fg
        else:
            self.style.theme_use("default")
            self.root.configure(bg="SystemButtonFace")
            self.text_bg = "white"
            self.text_fg = "black"

    def _style_text(self, widget):
        widget.configure(bg=self.text_bg, fg=self.text_fg, insertbackground=self.text_fg)

    def toggle_dark(self):
        self._apply_theme()
        if self.qc:
            self._build_main()
        else:
            self._build_login()

    def _build_login(self):
        self.clear()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)
        ttk.Label(frame, text="Local Notes", font=("", 14)).pack(pady=10)
        ttk.Label(frame, text="Passphrase").pack()
        self.pass_entry = ttk.Entry(frame, show="*", width=30)
        self.pass_entry.pack(pady=5)
        self.pass_entry.focus()
        ttk.Button(frame, text="Open", command=self.open_store).pack(pady=10)
        ttk.Button(frame, text="Choose store file…", command=self.choose_store).pack()
        self.dark_cb = ttk.Checkbutton(frame, text="Dark mode", variable=self.dark_mode, command=self.toggle_dark)
        self.dark_cb.pack(pady=5)
        self.status = ttk.Label(frame, text=f"Store: {self.store_path}")
        self.status.pack(pady=10)
        self.root.bind("<Return>", lambda e: self.open_store())

    def choose_store(self):
        path = filedialog.asksaveasfilename(title="Store location", defaultextension=".dat", filetypes=[("Data", "*.dat"), ("All", "*.*")])
        if path:
            self.store_path = Path(path)
            self.status.config(text=f"Store: {self.store_path}")

    def open_store(self):
        pw = self.pass_entry.get()
        if not pw:
            messagebox.showwarning("Notes", "Enter a passphrase.")
            return
        try:
            self.qc = QuietCache(self.store_path, pw)
            self._build_main()
        except Exception as e:
            messagebox.showerror("Notes", f"Error: {e}")

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def _build_main(self):
        self.clear()
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=5, pady=5)

        add_f = ttk.Frame(nb, padding=10)
        nb.add(add_f, text="Add")
        ttk.Label(add_f, text="Title").pack(anchor="w")
        self.title_e = ttk.Entry(add_f)
        self.title_e.pack(fill="x", pady=2)
        ttk.Label(add_f, text="Content").pack(anchor="w")
        self.content_t = scrolledtext.ScrolledText(add_f, height=12)
        self.content_t.pack(fill="both", expand=True, pady=2)
        self._style_text(self.content_t)
        ttk.Label(add_f, text="Tags (space separated)").pack(anchor="w")
        self.tags_e = ttk.Entry(add_f)
        self.tags_e.pack(fill="x", pady=2)
        ttk.Button(add_f, text="Save entry", command=self.do_add).pack(pady=5)

        search_f = ttk.Frame(nb, padding=10)
        nb.add(search_f, text="Search")
        top = ttk.Frame(search_f)
        top.pack(fill="x")
        self.query_e = ttk.Entry(top)
        self.query_e.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(top, text="Search", command=self.do_search).pack(side="left")
        ttk.Button(top, text="List all", command=self.do_list).pack(side="left", padx=5)
        self.results = scrolledtext.ScrolledText(search_f, height=18, state="disabled")
        self.results.pack(fill="both", expand=True, pady=5)
        self._style_text(self.results)

        ver_f = ttk.Frame(nb, padding=10)
        nb.add(ver_f, text="Verify")
        ttk.Label(ver_f, text="Claim or text to check (or drop a document)").pack(anchor="w")
        self.claim_t = scrolledtext.ScrolledText(ver_f, height=5)
        self.claim_t.pack(fill="x", pady=2)
        self._style_text(self.claim_t)
        btn_row = ttk.Frame(ver_f)
        btn_row.pack(fill="x", pady=4)
        ttk.Button(btn_row, text="Check text", command=self.do_verify).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Check file…", command=self.do_verify_file).pack(side="left", padx=2)
        self.verify_out = scrolledtext.ScrolledText(ver_f, height=12, state="disabled")
        self.verify_out.pack(fill="both", expand=True, pady=4)
        self._style_text(self.verify_out)

        xfer_f = ttk.Frame(nb, padding=10)
        nb.add(xfer_f, text="Transfer")
        ttk.Label(xfer_f, text="Export selected IDs (space separated)").pack(anchor="w")
        self.export_ids = ttk.Entry(xfer_f)
        self.export_ids.pack(fill="x", pady=2)
        ttk.Button(xfer_f, text="Export stealth notes file…", command=self.do_export).pack(pady=5)
        ttk.Separator(xfer_f).pack(fill="x", pady=10)
        ttk.Button(xfer_f, text="Import stealth notes / blob…", command=self.do_import).pack(pady=5)
        self.xfer_status = ttk.Label(xfer_f, text="Offline transfer only — USB, existing channels, or sneakernet. No servers, no IDs.")
        self.xfer_status.pack(pady=10)

        bar = ttk.Frame(self.root)
        bar.pack(fill="x", padx=5, pady=2)
        ttk.Checkbutton(bar, text="Dark mode", variable=self.dark_mode, command=self.toggle_dark).pack(side="left", padx=5)
        ttk.Button(bar, text="Lock", command=self._build_login).pack(side="right")
        ttk.Label(bar, text=f"Store: {self.store_path.name}").pack(side="left")

    def _set_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def do_add(self):
        title = self.title_e.get().strip()
        content = self.content_t.get("1.0", "end").strip()
        tags = self.tags_e.get().split()
        if not title or not content:
            messagebox.showwarning("Notes", "Title and content required.")
            return
        eid = self.qc.add_entry(title, content, tags)
        messagebox.showinfo("Notes", f"Saved: {eid}")
        self.title_e.delete(0, "end")
        self.content_t.delete("1.0", "end")
        self.tags_e.delete(0, "end")

    def do_search(self):
        q = self.query_e.get().strip()
        if not q:
            return
        results = self.qc.search(q)
        lines = [f"{eid}  |  {e['title']}\n  tags: {', '.join(e.get('tags', []))}\n" for eid, e in results]
        self._set_text(self.results, "\n".join(lines) if lines else "No matches.")

    def do_list(self):
        entries = self.qc.list_entries()
        lines = [f"{eid}  |  {e['title']}  ({e['added'][:19]})" for eid, e in entries.items()]
        self._set_text(self.results, "\n".join(lines) if lines else "Empty.")

    def do_verify(self):
        claim = self.claim_t.get("1.0", "end").strip()
        if not claim:
            return
        matches = self.qc.verify(claim)
        text = "Matches:\n" + "\n".join(f"{m['id']} — {m['title']} ({m['match']})" for m in matches) if matches else "No local matches."
        self._set_text(self.verify_out, text)

    def do_verify_file(self):
        path = filedialog.askopenfilename(title="Select document to verify")
        if not path:
            return
        matches, fhash = self.qc.verify_document(Path(path))
        if matches:
            text = f"File hash: {fhash[:16]}…\nMatches:\n" + "\n".join(f"{m['id']} — {m['title']} ({m['match']})" for m in matches)
        else:
            text = f"File hash: {fhash[:16]}…\nNo local matches."
        self._set_text(self.verify_out, text)

    def do_export(self):
        ids = self.export_ids.get().split()
        if not ids:
            messagebox.showwarning("Notes", "Enter one or more entry IDs.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Notes", "*.txt")], title="Save as ordinary notes file")
        if path:
            self.qc.export_stealth_blob(ids, Path(path))
            self.xfer_status.config(text=f"Exported stealth notes to {Path(path).name}")

    def do_import(self):
        path = filedialog.askopenfilename(title="Import stealth notes or blob", filetypes=[("Notes / Blob", "*.txt *.blob"), ("All", "*.*")])
        if path:
            n = self.qc.import_stealth_blob(Path(path))
            self.xfer_status.config(text=f"Imported {n} entries")
            messagebox.showinfo("Notes", f"Imported {n} entries.")

def main():
    root = tk.Tk()
    QuietCacheGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
