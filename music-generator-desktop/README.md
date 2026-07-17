# Original Music Generator (desktop)

A Tkinter desktop app that generates original, algorithmic instrumental
backing tracks - full band (drums, bass, rhythm guitar, lead guitar).
Every sound is synthesized from scratch with basic oscillators, envelopes,
and a distortion curve; there are no samples, loops, or recordings of any
kind, and the app never generates vocals or lyrics.

## Run it

```
cd music-generator-desktop
pip install -r requirements.txt
python app.py
```

`pygame` is only needed for in-app playback; if it's not installed the app
still runs and you can export WAV files.

## What it does

- Pick a genre (Heavy Metal, Punk Rock, Blues Rock, Classic Rock, Pop Rock,
  Funk, Synthwave, Ambient) or describe the track in the text box - genre,
  tempo, and instrument selection are inferred from the description.
- Choose key/scale, tempo, bar count, lead complexity, guitar distortion,
  and an optional seed for reproducible output.
- Toggle instruments (Drums / Bass / Rhythm Guitar / Lead Guitar).
- Generate, play back in-app, and export a `.wav` file to use as a backing
  track for your own vocals.

## Files

- `app.py` - Tkinter UI and app flow.
- `music_engine.py` - the synthesis engine: oscillators, envelopes,
  distortion, drum/bass/guitar voices, chord progressions, and WAV export.
- `prompt_parser.py` - turns the free-text description into generator
  settings (genre/tempo/instrument hints, vocals mention) and screens for
  attempts to reference a real artist, band, or song.
- `lockout.py` - locks the app for 24 hours after 3 blocked-prompt
  attempts, persisted to a small JSON file in the user's home directory.

## Copyright note

This app is built to make original music, not to recreate or imitate any
existing copyrighted recording or artist. The prompt box only accepts
descriptions of sound (genre, instruments, mood, tempo) - it rejects
references to real artists, bands, or songs. It's instrumental-only and
never writes lyrics; any lyrics you add on top of the exported track are
your own responsibility to make sure they're original.
