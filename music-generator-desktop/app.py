"""
Original Music Generator - Desktop App (Full Band)
-----------------------------------------------------
100% algorithmic music generation. No samples, no loops, no third-party
recordings, and NO vocals - this generates instrumental backing tracks
only. Every note, chord stab, and drum hit is synthesized from scratch.
Use the output as a backing track and add your own vocals/lyrics on top.

Run with:  python app.py
Requires:  numpy, pygame  (pip install numpy pygame)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import tempfile
import os
import sys

import music_engine as me
import prompt_parser as pp
import restrictions


def _resource_path(*parts):
    """Resolve a bundled resource path, working both from source and from a
    PyInstaller-frozen executable (where files are unpacked to sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

try:
    import pygame
    pygame.mixer.init(frequency=me.SAMPLE_RATE, size=-16, channels=1)
    HAS_AUDIO = True
except Exception:
    HAS_AUDIO = False


class MusicGenApp:
    def __init__(self, root):
        self.root = root
        root.title("Original Music Generator - Full Band")
        root.geometry("560x760")
        root.resizable(False, False)
        self._set_window_icon()

        self.melody = None
        self.buffer = None
        self._disabled_features = set()

        self._show_eula_gate()

    def _set_window_icon(self):
        icon_path = _resource_path("assets", "icon.ico")
        try:
            if sys.platform.startswith("win"):
                self.root.iconbitmap(icon_path)
            else:
                self.root.iconphoto(True, tk.PhotoImage(file=_resource_path("assets", "icon.png")))
        except Exception:
            pass

    def _load_eula_text(self):
        with open(_resource_path("EULA.md"), "r", encoding="utf-8") as f:
            return f.read()

    _BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

    def _insert_markdown_lite(self, text_widget, md_text):
        """Render the handful of Markdown constructs EULA.md actually uses
        (# / ## headings, **bold**) instead of showing the raw symbols."""
        text_widget.tag_configure("h1", font=("Segoe UI", 13, "bold"), spacing3=8)
        text_widget.tag_configure("h2", font=("Segoe UI", 10, "bold"), spacing1=10, spacing3=4)
        text_widget.tag_configure("bold", font=("Segoe UI", 9, "bold"))

        for line in md_text.splitlines():
            if line.startswith("## "):
                text_widget.insert("end", line[3:] + "\n", "h2")
                continue
            if line.startswith("# "):
                text_widget.insert("end", line[2:] + "\n", "h1")
                continue

            pos = 0
            for m in self._BOLD_RE.finditer(line):
                text_widget.insert("end", line[pos:m.start()])
                text_widget.insert("end", m.group(1), "bold")
                pos = m.end()
            text_widget.insert("end", line[pos:] + "\n")

    def _show_eula_gate(self):
        """Blocking license-agreement screen shown before the app is usable.
        Continue stays disabled until the checkbox is ticked; Decline closes
        the app immediately without building the generator UI."""
        try:
            eula_text = self._load_eula_text()
        except OSError as e:
            messagebox.showerror(
                "Can't start",
                f"The license agreement couldn't be loaded, so the app can't start.\n\n{e}"
            )
            self.root.destroy()
            return

        self._gate_frame = ttk.Frame(self.root)
        self._gate_frame.pack(fill="both", expand=True, padx=16, pady=16)

        ttk.Label(self._gate_frame, text="Before You Use This App", font=("Segoe UI", 14, "bold")).pack(pady=(0, 6))
        ttk.Label(
            self._gate_frame,
            text="Please read this first - it explains what the app does and where "
                 "responsibility falls if you use it to try to copy someone else's work.",
            font=("Segoe UI", 9), foreground="#555", wraplength=500
        ).pack(pady=(0, 8))

        text_frame = ttk.Frame(self._gate_frame)
        text_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        text_widget = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Segoe UI", 9))
        self._insert_markdown_lite(text_widget, eula_text)
        text_widget.config(state="disabled")
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        self.eula_agree_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self._gate_frame, text="I agree to the conditions of the EULA",
            variable=self.eula_agree_var, command=self._update_eula_continue_state
        ).pack(anchor="w", pady=(10, 8))

        btn_row = ttk.Frame(self._gate_frame)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Decline", command=self._on_eula_decline).pack(side="right")
        self.eula_continue_btn = ttk.Button(
            btn_row, text="Continue", command=self._on_eula_agree, state="disabled"
        )
        self.eula_continue_btn.pack(side="right", padx=(0, 6))

    def _update_eula_continue_state(self):
        self.eula_continue_btn.config(state="normal" if self.eula_agree_var.get() else "disabled")

    def _on_eula_agree(self):
        if not self.eula_agree_var.get():
            return
        self._gate_frame.destroy()
        self._build_ui()
        self._apply_genre_defaults()

        disabled, locked_until = restrictions.active_restrictions()
        if disabled:
            self._apply_feature_restrictions(disabled)
            feature_list = ", ".join(restrictions.FEATURE_LABELS[f] for f in disabled)
            self.status.set(
                f"Restricted for {restrictions.remaining_time_str(locked_until)} "
                f"due to repeated attempts to reference real artists/songs: {feature_list}."
            )

    def _on_eula_decline(self):
        self.root.destroy()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}
        outer = ttk.Frame(self.root)
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Label(outer, text="Original Music Generator", font=("Segoe UI", 16, "bold")).pack(pady=(0, 2))
        ttk.Label(outer, text="Algorithmic full-band backing tracks - no samples, no vocals, no copyright risk.",
                  font=("Segoe UI", 9), foreground="#555").pack(pady=(0, 10))

        # --- Free text prompt ---
        prompt_box = ttk.LabelFrame(outer, text="Describe the track (optional)")
        prompt_box.pack(fill="x", **pad)
        self.prompt_var = tk.StringVar()
        self.prompt_entry = ttk.Entry(prompt_box, textvariable=self.prompt_var, width=58)
        self.prompt_entry.pack(side="left", padx=6, pady=8, fill="x", expand=True)
        self.prompt_apply_btn = ttk.Button(prompt_box, text="Apply", command=self.on_apply_prompt)
        self.prompt_apply_btn.pack(side="left", padx=6)
        self.prompt_hint_label = ttk.Label(
            outer, text="Describe style/instruments only - no artist, band, or song names "
                        "(and no vocals - this app is instrumental-only).",
            font=("Segoe UI", 8), foreground="#777", wraplength=520
        )
        self.prompt_hint_label.pack(pady=(0, 8))

        # --- Genre ---
        row = ttk.Frame(outer); row.pack(fill="x", **pad)
        ttk.Label(row, text="Genre:", width=14).pack(side="left")
        self.genre_var = tk.StringVar(value="Heavy Metal")
        genre_combo = ttk.Combobox(row, textvariable=self.genre_var, values=list(me.GENRE_PRESETS.keys()),
                                    width=20, state="readonly")
        genre_combo.pack(side="left")
        genre_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_genre_defaults())

        # --- Key / Scale ---
        row = ttk.Frame(outer); row.pack(fill="x", **pad)
        ttk.Label(row, text="Key:", width=14).pack(side="left")
        self.key_var = tk.StringVar(value="E")
        ttk.Combobox(row, textvariable=self.key_var, values=me.NOTE_NAMES, width=6, state="readonly").pack(side="left")
        ttk.Label(row, text="  Scale:").pack(side="left")
        self.scale_var = tk.StringVar(value="Natural Minor")
        ttk.Combobox(row, textvariable=self.scale_var, values=list(me.SCALES.keys()), width=16, state="readonly").pack(side="left")

        # --- Tempo ---
        row = ttk.Frame(outer); row.pack(fill="x", **pad)
        ttk.Label(row, text="Tempo (BPM):", width=14).pack(side="left")
        self.tempo_var = tk.IntVar(value=160)
        ttk.Scale(row, from_=50, to=200, variable=self.tempo_var, orient="horizontal",
                  command=lambda v: self.tempo_label.config(text=f"{int(float(v))} BPM")).pack(side="left", fill="x", expand=True)
        self.tempo_label = ttk.Label(row, text="160 BPM", width=8)
        self.tempo_label.pack(side="left")

        # --- Bars / complexity ---
        row = ttk.Frame(outer); row.pack(fill="x", **pad)
        ttk.Label(row, text="Bars:", width=14).pack(side="left")
        self.bars_var = tk.IntVar(value=8)
        ttk.Spinbox(row, from_=2, to=32, textvariable=self.bars_var, width=6).pack(side="left")
        ttk.Label(row, text="  Lead complexity:").pack(side="left")
        self.complexity_var = tk.DoubleVar(value=0.6)
        ttk.Scale(row, from_=0.0, to=1.0, variable=self.complexity_var, orient="horizontal").pack(side="left", fill="x", expand=True)

        # --- Distortion ---
        row = ttk.Frame(outer); row.pack(fill="x", **pad)
        ttk.Label(row, text="Guitar distortion:", width=14).pack(side="left")
        self.distortion_var = tk.DoubleVar(value=0.85)
        ttk.Scale(row, from_=0.0, to=1.0, variable=self.distortion_var, orient="horizontal").pack(side="left", fill="x", expand=True)

        # --- Seed ---
        row = ttk.Frame(outer); row.pack(fill="x", **pad)
        ttk.Label(row, text="Seed (optional):", width=14).pack(side="left")
        self.seed_var = tk.StringVar(value="")
        ttk.Entry(row, textvariable=self.seed_var, width=14).pack(side="left")

        # --- Instruments ---
        inst_box = ttk.LabelFrame(outer, text="Instruments")
        inst_box.pack(fill="x", **pad)
        self.inst_vars = {}
        for name in me.INSTRUMENTS:
            v = tk.BooleanVar(value=True)
            self.inst_vars[name] = v
            ttk.Checkbutton(inst_box, text=name, variable=v).pack(side="left", padx=8, pady=6)

        ttk.Separator(outer).pack(fill="x", pady=10)

        # --- Actions ---
        btn_row = ttk.Frame(outer); btn_row.pack(fill="x", **pad)
        ttk.Button(btn_row, text="Generate", command=self.on_generate).pack(side="left", expand=True, fill="x", padx=4)
        self.play_btn = ttk.Button(btn_row, text="Play", command=self.on_play, state="disabled")
        self.play_btn.pack(side="left", expand=True, fill="x", padx=4)
        self.stop_btn = ttk.Button(btn_row, text="Stop", command=self.on_stop, state="disabled")
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=4)

        btn_row2 = ttk.Frame(outer); btn_row2.pack(fill="x", **pad)
        self.export_wav_btn = ttk.Button(btn_row2, text="Export WAV...", command=self.on_export_wav, state="disabled")
        self.export_wav_btn.pack(side="left", expand=True, fill="x", padx=4)

        if not HAS_AUDIO:
            ttk.Label(outer, text="(pygame not found - install it to enable in-app playback; export still works.)",
                      foreground="#a33", font=("Segoe UI", 8)).pack(pady=(6, 0))

        ttk.Label(
            outer,
            text="Reminder: this app generates original music and is not intended to "
                 "copy or recreate existing copyrighted songs/artists - doing so is at "
                 "your own risk. It's also instrumental-only and never generates "
                 "lyrics; any lyrics you add must be your own original work - using "
                 "copyrighted lyrics is on you, not this app.",
            font=("Segoe UI", 8), foreground="#a33", wraplength=520, justify="left"
        ).pack(pady=(6, 0))

        self.status = tk.StringVar(value="Pick a genre or describe the track above, then click Generate.")
        ttk.Label(outer, textvariable=self.status, wraplength=520, foreground="#333").pack(pady=(12, 0))

    # -- helpers ----------------------------------------------------------

    def _apply_genre_defaults(self):
        genre = self.genre_var.get()
        preset = me.GENRE_PRESETS[genre]
        self.scale_var.set(preset["scale"])
        self.tempo_var.set(preset["tempo"])
        self.tempo_label.config(text=f"{preset['tempo']} BPM")
        self.distortion_var.set(preset["distortion"])
        for name, var in self.inst_vars.items():
            var.set(name in preset["default_instruments"])

    def _seed(self):
        s = self.seed_var.get().strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            return abs(hash(s)) % (10 ** 8)

    def _feature_allowed(self, name):
        return name not in self._disabled_features

    def _apply_feature_restrictions(self, disabled_features):
        self._disabled_features = set(disabled_features)

        if "prompt_box" in self._disabled_features:
            self.prompt_var.set("")
            self.prompt_entry.config(state="disabled")
            self.prompt_apply_btn.config(state="disabled")
            self.prompt_hint_label.config(
                text="Description box turned off after repeated attempts to reference "
                     "a real artist/band/song. Use the controls below instead."
            )

        if "play" in self._disabled_features:
            self.play_btn.config(state="disabled")
        if "export" in self._disabled_features:
            self.export_wav_btn.config(state="disabled")

    def on_apply_prompt(self):
        text = self.prompt_var.get()
        result = pp.parse_prompt(text)

        if result["blocked"]:
            disabled, newly_escalated, locked_until, next_in = restrictions.register_violation()

            if disabled:
                self._apply_feature_restrictions(disabled)
                feature_list = ", ".join(restrictions.FEATURE_LABELS[f] for f in disabled)
                time_left = restrictions.remaining_time_str(locked_until)
                if newly_escalated:
                    messagebox.showerror(
                        "More features restricted",
                        "That's another round of attempts to reference a real "
                        f"copyrighted artist/song. Now turned off for {time_left}:\n\n"
                        f"{feature_list}\n\n"
                        "Anything not listed still works normally."
                    )
                else:
                    messagebox.showerror(
                        "Still restricted",
                        f"Still turned off for {time_left}:\n\n{feature_list}"
                    )
                self.status.set(f"Restricted for {time_left}: {feature_list}.")
                return

            messagebox.showwarning(
                "Can't use that description",
                result["block_reason"] +
                (f"\n\n({next_in} attempt(s) left before more features get restricted.)"
                 if next_in else "")
            )
            self.status.set("Prompt blocked - describe the sound, not an artist/band.")
            return

        if result["mentions_vocals"]:
            messagebox.showinfo(
                "Instrumental only",
                "This app doesn't generate vocals or lyrics. It'll build you an "
                "instrumental backing track you can sing over yourself."
            )

        if result["genre"]:
            self.genre_var.set(result["genre"])
            self._apply_genre_defaults()

        if result["tempo_hint"]:
            self.tempo_var.set(result["tempo_hint"])
            self.tempo_label.config(text=f"{result['tempo_hint']} BPM")

        for inst in result["instruments_mentioned"]:
            self.inst_vars[inst].set(True)
        for inst in result["instruments_excluded"]:
            self.inst_vars[inst].set(False)

        self.status.set("Applied description to the settings below - tweak anything, then Generate.")

    def on_generate(self):
        self.status.set("Generating...")
        self.root.update_idletasks()

        active = {name for name, v in self.inst_vars.items() if v.get()}
        if not active:
            messagebox.showwarning("No instruments selected", "Turn on at least one instrument.")
            self.status.set("Select at least one instrument.")
            return

        try:
            self.buffer = me.render_band(
                key=self.key_var.get(),
                scale_name=self.scale_var.get(),
                genre=self.genre_var.get(),
                bars=int(self.bars_var.get()),
                tempo_bpm=int(self.tempo_var.get()),
                active_instruments=active,
                distortion_amt=float(self.distortion_var.get()),
                complexity=float(self.complexity_var.get()),
                seed=self._seed(),
            )
        except Exception as e:
            messagebox.showerror("Generation failed", str(e))
            self.status.set("Generation failed - see error.")
            return

        self.play_btn.config(state="normal" if HAS_AUDIO and self._feature_allowed("play") else "disabled")
        self.export_wav_btn.config(state="normal" if self._feature_allowed("export") else "disabled")
        self.status.set(f"Generated {self.genre_var.get()} - {', '.join(sorted(active))} - "
                         f"{self.bars_var.get()} bars @ {self.tempo_var.get()} BPM.")

    def on_play(self):
        if not self._feature_allowed("play"):
            return
        if self.buffer is None or not HAS_AUDIO:
            return
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        me.save_wav(self.buffer, path)
        sound = pygame.mixer.Sound(path)
        sound.play()
        self.stop_btn.config(state="normal")
        self.status.set("Playing...")

    def on_stop(self):
        if HAS_AUDIO:
            pygame.mixer.stop()
        self.stop_btn.config(state="disabled")
        self.status.set("Stopped.")

    def on_export_wav(self):
        if not self._feature_allowed("export"):
            return
        if self.buffer is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV audio", "*.wav")])
        if path:
            me.save_wav(self.buffer, path)
            self.status.set(f"Saved WAV to {path}")
            messagebox.showinfo(
                "Saved",
                f"Saved to {path}\n\n"
                "This instrumental is original/algorithmic and yours to use. "
                "Remember: this app is not intended to copy or recreate existing "
                "copyrighted songs or artists - using it that way is at your own "
                "risk. And if you add lyrics of your own on top, make sure "
                "they're your own original writing - you're responsible for "
                "that content, not this app."
            )


if __name__ == "__main__":
    root = tk.Tk()
    MusicGenApp(root)
    root.mainloop()
