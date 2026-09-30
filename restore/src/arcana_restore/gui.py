"""Desktop window for Arcana Restore (tkinter; no extra dependencies).

Three tabs: Seal evidence, Open vault, Verify ledger. All work runs on a background
thread; the passphrase fields are cleared after every operation. The logic functions
(`seal_files`, `open_vault`, `check_ledger`) are UI-free and unit tested.
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__, pipeline, vault
from .imaging import RepairConfig
from .ledger import Ledger

try:  # optional native drag-and-drop
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:  # pragma: no cover - depends on platform package
    DND_FILES = TkinterDnD = None

BG, PANEL, BORDER, TEXT, MUTED, ACCENT = "#0b0f14", "#121821", "#1f2a38", "#e6edf3", "#93a4b8", "#4fb0ff"
DEFAULT_VAULT = os.path.join(os.path.expanduser("~"), "Arcana Vault")
DEFAULT_OUT = os.path.join(os.path.expanduser("~"), "Arcana Recovered")


# ---- UI-free logic (unit tested) -------------------------------------------------

def check_passphrase(pw: str, confirm: str | None = None) -> str | None:
    """Return an error message, or None if the passphrase is acceptable."""
    if len(pw) < vault.MIN_PASSPHRASE_CHARS:
        return f"Passphrase must be at least {vault.MIN_PASSPHRASE_CHARS} characters."
    if confirm is not None and pw != confirm:
        return "Passphrases do not match."
    return None


def seal_files(paths, vault_dir, passphrase, repair=True, on_result=None, kdf=None, workers=None):
    files = pipeline.collect(list(paths))
    if not files:
        raise ValueError("No supported image files (PNG, JPEG, TIFF, BMP) were selected.")
    return pipeline.process_batch(files, vault_dir, passphrase, workers or min(4, os.cpu_count() or 1),
                                  RepairConfig(repair=repair), kdf, on_result)


def open_vault(vault_file, passphrase, out_dir):
    return pipeline.extract(vault_file, passphrase, out_dir)


def check_ledger(vault_dir, expect_head=None):
    return Ledger(os.path.join(vault_dir, pipeline.LEDGER_NAME)).verify(expect_head or None)


def reveal(path: str) -> None:
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except OSError:
        pass


# ---- window ----------------------------------------------------------------------

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(f"Arcana Restore {__version__}")
        root.geometry("760x640")
        root.minsize(680, 560)
        root.configure(bg=BG)
        self._style()
        self.events: queue.Queue = queue.Queue()
        self.busy = False

        head = ttk.Label(root, text="Arcana Restore", style="H1.TLabel")
        head.pack(anchor="w", padx=20, pady=(16, 0))
        ttk.Label(root, text="Repair, seal and verify evidence images. Everything stays on this computer.",
                  style="Muted.TLabel").pack(anchor="w", padx=20, pady=(0, 10))
        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=20, pady=(0, 6))
        self.seal_tab, self.open_tab, self.ledger_tab = (ttk.Frame(nb, padding=14) for _ in range(3))
        nb.add(self.seal_tab, text="Seal evidence")
        nb.add(self.open_tab, text="Open vault")
        nb.add(self.ledger_tab, text="Verify ledger")
        self._build_seal()
        self._build_open()
        self._build_ledger()

        self.log = tk.Text(root, height=7, bg=PANEL, fg=TEXT, relief="flat", state="disabled",
                           highlightthickness=1, highlightbackground=BORDER, font=("TkFixedFont", 9))
        self.log.pack(fill="x", padx=20, pady=(0, 6))
        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill="x", padx=20, pady=(0, 14))
        self.root.after(100, self._drain)

    # -- styling / helpers
    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, fieldbackground=PANEL, bordercolor=BORDER)
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=TEXT)
        s.configure("Muted.TLabel", foreground=MUTED)
        s.configure("H1.TLabel", font=("TkDefaultFont", 18, "bold"))
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(14, 6))
        s.map("TNotebook.Tab", foreground=[("selected", TEXT)], background=[("selected", BG)])
        s.configure("TButton", background=PANEL, foreground=TEXT, padding=(12, 6), borderwidth=1)
        s.map("TButton", bordercolor=[("active", "#2c6690")])
        s.configure("Accent.TButton", background=ACCENT, foreground="#04141f", font=("TkDefaultFont", 10, "bold"))
        s.map("Accent.TButton", background=[("active", "#6cbeff"), ("disabled", BORDER)])
        s.configure("TCheckbutton", background=BG, foreground=TEXT)
        s.configure("TEntry", insertcolor=TEXT, foreground=TEXT, fieldbackground=PANEL)
        s.map("TEntry", fieldbackground=[("readonly", PANEL), ("disabled", PANEL), ("!disabled", PANEL)],
              foreground=[("!disabled", TEXT)], bordercolor=[("focus", ACCENT)])
        s.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=PANEL, bordercolor=BORDER)

    def say(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _row(self, parent, label, var, browse=None, secret=False):
        ttk.Label(parent, text=label).grid(sticky="w", pady=(8, 2), columnspan=2)
        row = ttk.Frame(parent)
        row.grid(sticky="ew", columnspan=2)
        row.columnconfigure(0, weight=1)
        e = ttk.Entry(row, textvariable=var, show="•" if secret else "")
        e.grid(row=0, column=0, sticky="ew")
        if browse:
            ttk.Button(row, text="Browse…", command=browse).grid(row=0, column=1, padx=(8, 0))
        return e

    def _set_busy(self, busy: bool):
        self.busy = busy
        state = "disabled" if busy else "normal"
        for b in (self.seal_btn, self.open_btn, self.ledger_btn):
            b.configure(state=state)

    def _run(self, work):
        """Run ``work()`` on a thread; it reports via self.events (thread-safe)."""
        if self.busy:
            return
        self._set_busy(True)
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)

        def target():
            try:
                work()
            except Exception as exc:  # shown to the user, never silently dropped
                self.events.put(("error", str(exc)))
            self.events.put(("done", None))
        threading.Thread(target=target, daemon=True).start()

    def _drain(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "log":
                    self.say(payload)
                elif kind == "error":
                    self.say(f"ERROR: {payload}")
                    messagebox.showerror("Arcana Restore", payload)
                elif kind == "progress":
                    self.progress.stop()
                    self.progress.configure(mode="determinate", maximum=payload[1], value=payload[0])
                elif kind == "reveal":
                    self.reveal_path = payload
                    self.reveal_btn.configure(state="normal")
                elif kind == "done":
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                    self._set_busy(False)
        except queue.Empty:
            pass
        self.root.after(100, self._drain)

    # -- Seal tab
    def _build_seal(self):
        t = self.seal_tab
        t.columnconfigure(0, weight=1)
        ttk.Label(t, text="1. Add images (or drop them here)").grid(sticky="w", columnspan=2)
        box = ttk.Frame(t)
        box.grid(sticky="nsew", columnspan=2, pady=(4, 0))
        box.columnconfigure(0, weight=1)
        self.files = tk.Listbox(box, height=6, bg=PANEL, fg=TEXT, selectbackground="#2c6690", relief="flat",
                                highlightthickness=1, highlightbackground=BORDER)
        self.files.grid(row=0, column=0, sticky="nsew")
        btns = ttk.Frame(box)
        btns.grid(row=0, column=1, padx=(8, 0), sticky="n")
        ttk.Button(btns, text="Add files…", command=self._add_files).pack(fill="x")
        ttk.Button(btns, text="Add folder…", command=self._add_folder).pack(fill="x", pady=4)
        ttk.Button(btns, text="Remove", command=self._remove_files).pack(fill="x")
        if TkinterDnD is not None:
            try:
                self.files.drop_target_register(DND_FILES)
                self.files.dnd_bind("<<Drop>>", lambda e: self._add_paths(self.root.tk.splitlist(e.data)))
            except Exception:
                pass
        self.vault_dir = tk.StringVar(value=DEFAULT_VAULT)
        self._row(t, "2. Vault folder (sealed files and ledger are saved here)", self.vault_dir,
                  lambda: self._pick_dir(self.vault_dir))
        self.pw1, self.pw2 = tk.StringVar(), tk.StringVar()
        self._row(t, "3. Passphrase (12+ characters)", self.pw1, secret=True)
        self._row(t, "Confirm passphrase", self.pw2, secret=True)
        self.repair = tk.BooleanVar(value=True)
        ttk.Checkbutton(t, text="Repair glare and shadow (the untouched original is always sealed too)",
                        variable=self.repair).grid(sticky="w", columnspan=2, pady=(10, 0))
        self.ack = tk.BooleanVar(value=False)
        ttk.Checkbutton(t, text="I understand a lost passphrase cannot be recovered by anyone",
                        variable=self.ack).grid(sticky="w", columnspan=2)
        self.seal_btn = ttk.Button(t, text="Seal evidence", style="Accent.TButton", command=self._seal)
        self.seal_btn.grid(sticky="e", columnspan=2, pady=(12, 0))

    def _add_paths(self, paths):
        have = set(self.files.get(0, "end"))
        for p in paths:
            if p not in have:
                self.files.insert("end", p)
                have.add(p)

    def _add_files(self):
        self._add_paths(filedialog.askopenfilenames(title="Choose images",
                        filetypes=[("Images", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp"), ("All files", "*.*")]))

    def _add_folder(self):
        d = filedialog.askdirectory(title="Choose a folder of images")
        if d:
            self._add_paths([d])

    def _remove_files(self):
        for i in reversed(self.files.curselection()):
            self.files.delete(i)

    def _pick_dir(self, var):
        d = filedialog.askdirectory(initialdir=var.get() or os.path.expanduser("~"))
        if d:
            var.set(d)

    def _seal(self):
        paths = list(self.files.get(0, "end"))
        if not paths:
            return messagebox.showwarning("Arcana Restore", "Add at least one image first.")
        err = check_passphrase(self.pw1.get(), self.pw2.get())
        if err:
            return messagebox.showwarning("Arcana Restore", err)
        if not self.ack.get():
            return messagebox.showwarning("Arcana Restore", "Please confirm you understand the passphrase cannot be recovered.")
        pw, vdir, repair = self.pw1.get(), self.vault_dir.get(), self.repair.get()
        self.pw1.set(""), self.pw2.set("")
        self.say(f"Sealing into {vdir} …")

        def work():
            done = []

            def cb(r):
                done.append(r)
                name = os.path.basename(r.source)
                self.events.put(("log", f"[ok]   {name} ({r.report.get('status')})" if r.ok else f"[fail] {name}: {r.error}"))
            seal_files(paths, vdir, pw, repair, cb)
            ok = sum(r.ok for r in done)
            _, n, head, _ = check_ledger(vdir)
            self.events.put(("log", f"{ok}/{len(done)} sealed. Ledger head ({n} entries):\n{head}\nKeep a copy of this head to prove nothing was removed later."))
            self.events.put(("reveal", vdir))
        self._run(work)

    # -- Open tab
    def _build_open(self):
        t = self.open_tab
        t.columnconfigure(0, weight=1)
        self.vfile, self.opw, self.outdir = tk.StringVar(), tk.StringVar(), tk.StringVar(value=DEFAULT_OUT)
        self._row(t, "Sealed file (.arcr)", self.vfile, self._pick_vault)
        self._row(t, "Passphrase", self.opw, secret=True)
        self._row(t, "Save recovered files to", self.outdir, lambda: self._pick_dir(self.outdir))
        ttk.Label(t, text="Saves the original, the restored image, the repair mask and a manifest. "
                  "Existing files are never overwritten.", style="Muted.TLabel", wraplength=640).grid(sticky="w", columnspan=2, pady=(10, 0))
        row = ttk.Frame(t)
        row.grid(sticky="e", columnspan=2, pady=(12, 0))
        self.reveal_path = None
        self.reveal_btn = ttk.Button(row, text="Show folder", state="disabled", command=lambda: self.reveal_path and reveal(self.reveal_path))
        self.reveal_btn.pack(side="left", padx=(0, 8))
        self.open_btn = ttk.Button(row, text="Open vault", style="Accent.TButton", command=self._open)
        self.open_btn.pack(side="left")

    def _pick_vault(self):
        f = filedialog.askopenfilename(title="Choose a sealed file", filetypes=[("Arcana vault", "*.arcr"), ("All files", "*.*")])
        if f:
            self.vfile.set(f)

    def _open(self):
        if not self.vfile.get():
            return messagebox.showwarning("Arcana Restore", "Choose a sealed file first.")
        pw, vf, out = self.opw.get(), self.vfile.get(), self.outdir.get()
        self.opw.set("")

        def work():
            try:
                for p in open_vault(vf, pw, out):
                    self.events.put(("log", f"wrote {p}"))
                self.events.put(("reveal", out))
            except vault.AuthError:
                self.events.put(("error", "Wrong passphrase, or the file was modified."))
            except FileExistsError:
                self.events.put(("error", "Files from this vault already exist in that folder. Choose another folder."))
        self._run(work)

    # -- Ledger tab
    def _build_ledger(self):
        t = self.ledger_tab
        t.columnconfigure(0, weight=1)
        self.lvault, self.lhead = tk.StringVar(value=DEFAULT_VAULT), tk.StringVar()
        self._row(t, "Vault folder", self.lvault, lambda: self._pick_dir(self.lvault))
        self._row(t, "Expected head (optional: the value you saved when you sealed)", self.lhead)
        ttk.Label(t, text="Checks that no ledger entry was edited, reordered or deleted. "
                  "To also catch removed final entries, enter the head you saved earlier.", style="Muted.TLabel",
                  wraplength=640).grid(sticky="w", columnspan=2, pady=(10, 0))
        self.ledger_btn = ttk.Button(t, text="Verify", style="Accent.TButton", command=self._verify)
        self.ledger_btn.grid(sticky="e", columnspan=2, pady=(12, 0))

    def _verify(self):
        vdir, head = self.lvault.get(), self.lhead.get().strip()

        def work():
            ok, n, h, msg = check_ledger(vdir, head)
            self.events.put(("log", f"{'VERIFIED' if ok else 'FAILED'}: {msg}; entries={n}; head={h}"))
        self._run(work)


def main() -> int:
    root = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    try:
        icon = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(__file__)), "icon.png")
        if os.path.exists(icon):
            root.iconphoto(True, tk.PhotoImage(file=icon))
    except tk.TclError:
        pass
    App(root)
    root.mainloop()
    return 0
