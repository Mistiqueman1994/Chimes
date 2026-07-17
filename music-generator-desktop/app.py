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
import tempfile
import os
import sys

import music_engine as me
import prompt_parser as pp
import lockout


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

        locked, locked_until = lockout.is_locked()
        if locked:
            self._show_locked_screen(locked_until)
            return

        self.melody = None
        self.buffer = None

        self._build_ui()
        self._apply_genre_defaults()
        self.root.after(200, self._show_lyrics_disclaimer)

    def _set_window_icon(self):
        icon_path = _resource_path("assets", "icon.ico")
        try:
            if sys.platform.startswith("win"):
                self.root.iconbitmap(icon_path)
            else:
                self.root.iconphoto(True, tk.PhotoImage(file=_resource_path("assets", "icon.png")))
        except Exception:
            pass

    def _show_locked_screen(self, locked_until):
        for w in self.root.winfo_children():
            w.destroy()
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        ttk.Label(frame, text="App Locked", font=("Segoe UI", 16, "bold"), foreground="#a33").pack(pady=(10, 8))
        ttk.Label(
            frame,
            text=(
                "This app was locked after 3 attempts to use the prompt box to "
                "reference real copyrighted artists/songs.\n\n"
                f"Time remaining: {lockout.remaining_time_str(locked_until)}\n\n"
                "The app will unlock automatically once the 24-hour period has "
                "passed. In the meantime, please close this window."
            ),
            wraplength=480, justify="left"
        ).pack(pady=(0, 10))
        ttk.Button(frame, text="Close", command=self.root.destroy).pack()

    def _show_lyrics_disclaimer(self):
        messagebox.showinfo(
            "Before you use this app",
            "This app is built to generate original, algorithmic music. It is "
            "NOT intended to be used to recreate, copy, or imitate any existing "
            "copyrighted song, recording, or artist's work - for example by "
            "typing in details of a real song and trying to reproduce it. "
            "Attempting to use this app that way is done entirely at your own "
            "risk and is your responsibility, not the app creator's.\n\n"
            "This app also generates instrumental music only - it never writes "
            "or suggests lyrics. If you write or record your own lyrics over a "
            "track you make here, you are solely responsible for making sure "
            "those lyrics are your own original work. Using someone else's "
            "copyrighted lyrics (even a line or two) is copyright infringement, "
            "and any legal or financial consequences from that are yours to "
            "bear - not the creator of this app.\n\n"
            "This message will show each time the app starts."
        )

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
        entry = ttk.Entry(prompt_box, textvariable=self.prompt_var, width=58)
        entry.pack(side="left", padx=6, pady=8, fill="x", expand=True)
        ttk.Button(prompt_box, text="Apply", command=self.on_apply_prompt).pack(side="left", padx=6)
        ttk.Label(outer, text="Describe style/instruments only - no artist, band, or song names "
                              "(and no vocals - this app is instrumental-only).",
                  font=("Segoe UI", 8), foreground="#777", wraplength=520).pack(pady=(0, 8))

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

    def on_apply_prompt(self):
        text = self.prompt_var.get()
        result = pp.parse_prompt(text)

        if result["blocked"]:
            violations, newly_locked, locked_until = lockout.register_violation()

            if newly_locked:
                messagebox.showerror(
                    "App locked",
                    "That's 3 attempts to reference a real copyrighted artist/song "
                    "in the prompt box. This app is now locked for 24 hours.\n\n"
                    f"Time remaining: {lockout.remaining_time_str(locked_until)}"
                )
                self._show_locked_screen(locked_until)
                return

            remaining = lockout.MAX_VIOLATIONS - violations
            messagebox.showwarning(
                "Can't use that description",
                result["block_reason"] +
                f"\n\n({remaining} attempt(s) left before this app locks for 24 hours.)"
            )
            self.status.set(f"Prompt blocked ({violations}/{lockout.MAX_VIOLATIONS} strikes) - "
                             "describe the sound, not an artist/band.")
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

        self.play_btn.config(state="normal" if HAS_AUDIO else "disabled")
        self.export_wav_btn.config(state="normal")
        self.status.set(f"Generated {self.genre_var.get()} - {', '.join(sorted(active))} - "
                         f"{self.bars_var.get()} bars @ {self.tempo_var.get()} BPM.")

    def on_play(self):
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
