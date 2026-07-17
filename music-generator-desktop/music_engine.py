"""
music_engine.py
----------------
100% algorithmic audio synthesis. Every waveform in this module is generated
from basic oscillators (sine/saw/square/noise) shaped with envelopes and a
soft-clip "distortion" curve - there are no samples, loops, or recordings of
any kind involved anywhere in this file.

Public surface used by app.py:
    SAMPLE_RATE, NOTE_NAMES, SCALES, GENRE_PRESETS, INSTRUMENTS
    render_band(...)  -> numpy float32 array, mono, range roughly [-1, 1]
    save_wav(buffer, path)
"""

import wave
import struct

import numpy as np

SAMPLE_RATE = 44100

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Intervals (semitones from the root) that make up one octave of each scale.
SCALES = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Natural Minor": [0, 2, 3, 5, 7, 8, 10],
    "Harmonic Minor": [0, 2, 3, 5, 7, 8, 11],
    "Dorian": [0, 2, 3, 5, 7, 9, 10],
    "Phrygian": [0, 1, 3, 5, 7, 8, 10],
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "Major Pentatonic": [0, 2, 4, 7, 9],
    "Minor Pentatonic": [0, 3, 5, 7, 10],
    "Blues": [0, 3, 5, 6, 7, 10],
}

INSTRUMENTS = ["Drums", "Bass", "Rhythm Guitar", "Lead Guitar"]

GENRE_PRESETS = {
    "Heavy Metal": {
        "scale": "Natural Minor", "tempo": 160, "distortion": 0.85,
        "default_instruments": {"Drums", "Bass", "Rhythm Guitar", "Lead Guitar"},
    },
    "Punk Rock": {
        "scale": "Minor Pentatonic", "tempo": 180, "distortion": 0.7,
        "default_instruments": {"Drums", "Bass", "Rhythm Guitar"},
    },
    "Blues Rock": {
        "scale": "Blues", "tempo": 100, "distortion": 0.5,
        "default_instruments": {"Drums", "Bass", "Rhythm Guitar", "Lead Guitar"},
    },
    "Classic Rock": {
        "scale": "Major Pentatonic", "tempo": 122, "distortion": 0.55,
        "default_instruments": {"Drums", "Bass", "Rhythm Guitar", "Lead Guitar"},
    },
    "Pop Rock": {
        "scale": "Major", "tempo": 118, "distortion": 0.3,
        "default_instruments": {"Drums", "Bass", "Rhythm Guitar"},
    },
    "Funk": {
        "scale": "Dorian", "tempo": 105, "distortion": 0.15,
        "default_instruments": {"Drums", "Bass", "Rhythm Guitar"},
    },
    "Synthwave": {
        "scale": "Natural Minor", "tempo": 110, "distortion": 0.2,
        "default_instruments": {"Drums", "Bass", "Lead Guitar"},
    },
    "Ambient": {
        "scale": "Major Pentatonic", "tempo": 72, "distortion": 0.0,
        "default_instruments": {"Bass", "Lead Guitar"},
    },
}

# ---------------------------------------------------------------------------
# Pitch helpers
# ---------------------------------------------------------------------------

def _midi_to_freq(midi_note):
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def _root_midi(key):
    """MIDI note number for `key` in the octave used as the guitar/bass root."""
    idx = NOTE_NAMES.index(key)
    return 40 + idx  # around E2/F2 - a comfortable low guitar/bass register


def _scale_midi_notes(key, scale_name, octaves=3, base_octave_offset=0):
    """Ascending list of MIDI notes covering `octaves` octaves of the scale."""
    root = _root_midi(key) + 12 + base_octave_offset
    intervals = SCALES[scale_name]
    notes = []
    for o in range(octaves):
        for iv in intervals:
            notes.append(root + o * 12 + iv)
    return notes


def _diatonic_triad(scale_notes, degree):
    """Stack-of-thirds triad starting at `degree` within a scale note list."""
    n = len(scale_notes)
    root = scale_notes[degree % n]
    third = scale_notes[(degree + 2) % n] + (12 if (degree + 2) >= n else 0)
    fifth = scale_notes[(degree + 4) % n] + (12 if (degree + 4) >= n else 0)
    return [root, third, fifth]


# ---------------------------------------------------------------------------
# Oscillators / shaping
# ---------------------------------------------------------------------------

def _time_axis(duration):
    n = max(1, int(duration * SAMPLE_RATE))
    return np.linspace(0, duration, n, endpoint=False)


def _sine(freq, duration):
    t = _time_axis(duration)
    return np.sin(2 * np.pi * freq * t)


def _saw(freq, duration):
    t = _time_axis(duration)
    phase = (t * freq) % 1.0
    return 2.0 * phase - 1.0


def _square(freq, duration, width=0.5):
    t = _time_axis(duration)
    phase = (t * freq) % 1.0
    return np.where(phase < width, 1.0, -1.0)


def _noise(duration, rng):
    n = max(1, int(duration * SAMPLE_RATE))
    return rng.uniform(-1.0, 1.0, n)


def _adsr(n, attack=0.01, decay=0.08, sustain=0.6, release=0.15):
    """Simple linear ADSR envelope of length n (samples)."""
    a = max(1, int(attack * SAMPLE_RATE))
    d = max(1, int(decay * SAMPLE_RATE))
    r = max(1, int(release * SAMPLE_RATE))
    s = max(0, n - a - d - r)
    env = np.concatenate([
        np.linspace(0, 1, a, endpoint=False),
        np.linspace(1, sustain, d, endpoint=False),
        np.full(s, sustain),
        np.linspace(sustain, 0, r, endpoint=True),
    ])
    if len(env) > n:
        env = env[:n]
    elif len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return env


def _exp_decay_env(n, rate=8.0):
    t = np.linspace(0, 1, n, endpoint=False)
    return np.exp(-rate * t)


def _soft_clip(signal, amount):
    """0 = clean, 1 = heavily saturated. Tanh-based waveshaping distortion."""
    if amount <= 0:
        return signal
    drive = 1.0 + amount * 14.0
    shaped = np.tanh(signal * drive)
    peak = np.max(np.abs(shaped)) or 1.0
    return shaped / peak


def _lowpass(signal, alpha):
    """Very small one-pole lowpass filter, used to soften bass/drum tone."""
    if alpha <= 0:
        return signal
    out = np.empty_like(signal)
    prev = 0.0
    for i in range(len(signal)):
        prev = prev + alpha * (signal[i] - prev)
        out[i] = prev
    return out


def _mix_into(master, voice, start_sample, gain=1.0):
    n = len(voice)
    end = start_sample + n
    if end > len(master):
        n = len(master) - start_sample
        if n <= 0:
            return
        voice = voice[:n]
        end = start_sample + n
    master[start_sample:end] += voice * gain


# ---------------------------------------------------------------------------
# Instrument voices
# ---------------------------------------------------------------------------

def _kick(rng):
    dur = 0.18
    t = _time_axis(dur)
    freq = np.linspace(120, 45, len(t))
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    env = _exp_decay_env(len(t), rate=14)
    click = _noise(0.004, rng) * _exp_decay_env(max(1, int(0.004 * SAMPLE_RATE)), rate=30)
    out = tone * env
    out[:len(click)] += click * 0.5
    return _soft_clip(out, 0.3)


def _snare(rng):
    dur = 0.16
    n = int(dur * SAMPLE_RATE)
    noise = _noise(dur, rng)
    tone = _sine(190, dur)
    env = _exp_decay_env(n, rate=16)
    out = (noise * 0.7 + tone * 0.3) * env
    return _soft_clip(out, 0.2)


def _hihat(rng, open_hat=False):
    dur = 0.28 if open_hat else 0.06
    n = int(dur * SAMPLE_RATE)
    noise = _noise(dur, rng)
    # crude high-pass: subtract a smoothed copy to remove low rumble
    smoothed = _lowpass(noise, 0.35)
    hp = noise - smoothed
    env = _exp_decay_env(n, rate=6 if open_hat else 26)
    return hp * env * 0.6


def _drum_pattern(genre):
    """8 steps per bar (eighth notes): each step -> set of {'K','S','H','O'}."""
    patterns = {
        "Heavy Metal": ["K", "H", "S", "H", "K", "H", "S", "H"],
        "Punk Rock": ["K", "H", "S", "H", "K", "K", "S", "H"],
        "Blues Rock": ["K", "H", "S", "H", "K", "H", "S", "O"],
        "Classic Rock": ["K", "H", "S", "H", "K", "H", "S", "H"],
        "Pop Rock": ["K", "H", "S", "H", "K", "H", "S", "H"],
        "Funk": ["K", "H", "H", "S", "H", "K", "H", "S"],
        "Synthwave": ["K", "H", "S", "H", "K", "H", "S", "H"],
        "Ambient": ["K", "", "", "", "S", "", "", ""],
    }
    return patterns.get(genre, patterns["Classic Rock"])


def _render_drums(bars, beat_dur, genre, rng):
    bar_dur = beat_dur * 4
    total = int(bars * bar_dur * SAMPLE_RATE) + SAMPLE_RATE
    master = np.zeros(total, dtype=np.float64)
    step_dur = beat_dur / 2  # eighth notes
    pattern = _drum_pattern(genre)

    for bar in range(bars):
        for step, hit in enumerate(pattern):
            if not hit:
                continue
            start = int((bar * bar_dur + step * step_dur) * SAMPLE_RATE)
            if hit == "K":
                _mix_into(master, _kick(rng), start, gain=1.0)
            elif hit == "S":
                _mix_into(master, _snare(rng), start, gain=0.9)
            elif hit == "H":
                _mix_into(master, _hihat(rng, open_hat=False), start, gain=0.5)
            elif hit == "O":
                _mix_into(master, _hihat(rng, open_hat=True), start, gain=0.5)
    return master


def _chord_progression(scale_notes, bars):
    """Common 4-chord loop (by scale degree), repeated/extended to `bars`."""
    degrees = [0, 5, 3, 4] if len(scale_notes) >= 6 else [0, 2, 3, 0]
    prog = []
    for i in range(bars):
        prog.append(degrees[i % len(degrees)])
    return prog


def _render_bass(key, scale_name, bars, beat_dur, complexity, rng):
    scale_notes = _scale_midi_notes(key, scale_name, octaves=2)
    prog = _chord_progression(scale_notes, bars)
    bar_dur = beat_dur * 4
    total = int(bars * bar_dur * SAMPLE_RATE) + SAMPLE_RATE
    master = np.zeros(total, dtype=np.float64)

    for bar, degree in enumerate(prog):
        root_note = _diatonic_triad(scale_notes, degree)[0] - 12  # low register
        # quarter notes, occasionally an eighth-note walk driven by complexity
        beats = 4
        for b in range(beats):
            note = root_note
            if complexity > 0.5 and rng.random() < (complexity - 0.5):
                note += rng.choice([-2, 2, 5, 7])
            freq = _midi_to_freq(note)
            dur = beat_dur * 0.95
            voice = _saw(freq, dur) * 0.5 + _sine(freq, dur) * 0.5
            env = _adsr(len(voice), attack=0.005, decay=0.05, sustain=0.8, release=0.08)
            voice = _lowpass(voice * env, 0.5)
            start = int((bar * bar_dur + b * beat_dur) * SAMPLE_RATE)
            _mix_into(master, voice, start, gain=0.8)
    return master


def _render_rhythm_guitar(key, scale_name, genre, bars, beat_dur, distortion_amt, rng):
    scale_notes = _scale_midi_notes(key, scale_name, octaves=2)
    prog = _chord_progression(scale_notes, bars)
    bar_dur = beat_dur * 4
    total = int(bars * bar_dur * SAMPLE_RATE) + SAMPLE_RATE
    master = np.zeros(total, dtype=np.float64)

    palm_muted = genre in ("Heavy Metal", "Punk Rock", "Blues Rock", "Classic Rock")
    step_dur = beat_dur / 2  # eighth-note chugs
    steps_per_bar = 8

    for bar, degree in enumerate(prog):
        triad = _diatonic_triad(scale_notes, degree)
        power_chord = [triad[0] - 12, triad[0], triad[2]]  # root, root, fifth-ish
        for step in range(steps_per_bar):
            note_dur = step_dur * (0.55 if palm_muted else 0.95)
            chord_audio = np.zeros(int(note_dur * SAMPLE_RATE))
            for note in power_chord:
                freq = _midi_to_freq(note)
                voice = _square(freq, note_dur, width=0.5)
                chord_audio = chord_audio[:len(voice)] + voice if len(chord_audio) else voice
            env = _adsr(len(chord_audio), attack=0.003, decay=0.03,
                        sustain=0.5 if palm_muted else 0.7, release=0.05)
            chord_audio = _soft_clip(chord_audio * env, distortion_amt)
            start = int((bar * bar_dur + step * step_dur) * SAMPLE_RATE)
            _mix_into(master, chord_audio, start, gain=0.5)
    return master


def _render_lead_guitar(key, scale_name, bars, beat_dur, distortion_amt, complexity, rng):
    scale_notes = _scale_midi_notes(key, scale_name, octaves=3, base_octave_offset=12)
    bar_dur = beat_dur * 4
    total = int(bars * bar_dur * SAMPLE_RATE) + SAMPLE_RATE
    master = np.zeros(total, dtype=np.float64)

    # note density scales with complexity: sparse long notes -> busy runs
    subdivisions = [4, 4, 8, 8, 16][min(4, int(complexity * 5))]
    step_dur = (beat_dur * 4) / subdivisions

    idx = len(scale_notes) // 2
    for bar in range(bars):
        for step in range(subdivisions):
            if rng.random() > (0.4 + complexity * 0.5):
                continue  # leave rests so the line breathes
            move = rng.choice([-2, -1, -1, 0, 1, 1, 2], p=None)
            idx = max(0, min(len(scale_notes) - 1, idx + move))
            freq = _midi_to_freq(scale_notes[idx])
            note_dur = step_dur * 0.9
            voice = _saw(freq, note_dur) * 0.6 + _square(freq, note_dur) * 0.4
            env = _adsr(len(voice), attack=0.005, decay=0.05, sustain=0.55, release=0.12)
            voice = _soft_clip(voice * env, distortion_amt * 0.8)
            start = int((bar * bar_dur + step * step_dur) * SAMPLE_RATE)
            _mix_into(master, voice, start, gain=0.55)
    return master


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_band(key, scale_name, genre, bars, tempo_bpm, active_instruments,
                 distortion_amt, complexity, seed=None):
    if key not in NOTE_NAMES:
        raise ValueError(f"Unknown key: {key}")
    if scale_name not in SCALES:
        raise ValueError(f"Unknown scale: {scale_name}")
    if bars < 1:
        raise ValueError("Need at least 1 bar.")
    if tempo_bpm <= 0:
        raise ValueError("Tempo must be positive.")

    rng = np.random.default_rng(seed)
    beat_dur = 60.0 / tempo_bpm
    bar_dur = beat_dur * 4
    total = int(bars * bar_dur * SAMPLE_RATE) + SAMPLE_RATE
    master = np.zeros(total, dtype=np.float64)

    tracks = []
    if "Drums" in active_instruments:
        tracks.append(_render_drums(bars, beat_dur, genre, rng))
    if "Bass" in active_instruments:
        tracks.append(_render_bass(key, scale_name, bars, beat_dur, complexity, rng))
    if "Rhythm Guitar" in active_instruments:
        tracks.append(_render_rhythm_guitar(key, scale_name, genre, bars, beat_dur, distortion_amt, rng))
    if "Lead Guitar" in active_instruments:
        tracks.append(_render_lead_guitar(key, scale_name, bars, beat_dur, distortion_amt, complexity, rng))

    for track in tracks:
        n = min(len(master), len(track))
        master[:n] += track[:n]

    # trim trailing silence padding, normalize to avoid clipping
    used_samples = int(bars * bar_dur * SAMPLE_RATE)
    master = master[:used_samples]
    peak = np.max(np.abs(master)) if master.size else 0.0
    if peak > 1e-6:
        master = master / peak * 0.92
    return master.astype(np.float32)


def save_wav(buffer, path):
    """Write a mono float32 [-1, 1] buffer out as 16-bit PCM WAV."""
    clipped = np.clip(buffer, -1.0, 1.0)
    ints = (clipped * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack("<%dh" % len(ints), *ints))
