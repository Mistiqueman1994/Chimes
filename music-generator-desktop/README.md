# Original Music Generator (desktop)

A Tkinter desktop app that generates original, algorithmic instrumental
backing tracks - full band (drums, bass, rhythm guitar, lead guitar).
Every sound is synthesized from scratch with basic oscillators, envelopes,
and a distortion curve; there are no samples, loops, or recordings of any
kind, and the app never generates vocals or lyrics.

## Get the Windows installer

Permanent download link (rebuilt automatically on every push to `main`):

https://github.com/Mistiqueman1994/Chimes/releases/download/music-generator-latest/MusicGenerator-Setup.exe

Run it and follow the installer - no admin rights required. It adds a Start
Menu shortcut, an optional desktop shortcut, and an uninstaller listed under
"Apps & Features".

## Run from source

```
cd music-generator-desktop
pip install -r requirements.txt
python app.py
```

`pygame` is only needed for in-app playback; if it's not installed the app
still runs and you can export WAV files.

## Build the installer yourself

```
cd music-generator-desktop
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "OriginalMusicGenerator" \
  --icon assets/icon.ico --add-data "assets/icon.ico;assets" \
  --add-data "EULA.md;." app.py
makensis installer.nsi
```

Produces `dist_installer/MusicGenerator-Setup.exe`. (On Windows, PyInstaller's
`--add-data` separator is `;`; on macOS/Linux it's `:`.)

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
- `assets/icon.ico` / `assets/icon.png` - app icon (window/taskbar icon and
  the installer/exe icon).
- `installer.nsi` - NSIS script that packages the PyInstaller build into a
  Windows installer.
- `EULA.md` - the "Before You Use This App" notice shown (and requiring
  explicit checkbox agreement) every time the app starts.
- `THIRD-PARTY-NOTICES.md` - license notices for the open-source
  libraries (NumPy, Pygame) bundled into the Windows installer.
- `restrictions.py` - the escalating feature-restriction ladder described
  below, persisted to a small JSON file in this app's own local data
  folder (`%LOCALAPPDATA%\Original Music Generator` on Windows) -
  contained to this app on this PC, never system-wide, never roaming to
  another machine, and never something that stops the app from opening.

## Before You Use This App

Every time the app starts, it shows `EULA.md` and requires you to check
"I agree to the conditions of the EULA" before "Continue" is enabled;
clicking "Decline" closes the app immediately. This isn't meant as a
lawyer-drafted contract - it's there to make sure you actually understand
what the app does and doesn't do before you use it, in plain language:

This app is built to make original music, not to recreate or imitate any
existing copyrighted recording or artist. The prompt box only accepts
descriptions of sound (genre, instruments, mood, tempo) and rejects
references to real artists, bands, or songs - but trying to work around
that and use the app to copy someone else's copyrighted work doesn't make
you immune from the consequences of doing so. Triggering that filter
repeatedly escalates: 3 attempts turns off the description box for 24
hours, then every 2 more attempts turns off one more feature (playback,
then exporting, then generating) for another 24 hours - never the app
itself, which always still opens. It's instrumental-only and never writes
lyrics; any lyrics you add on top of the exported track are your own
responsibility to make sure they're original. See `EULA.md` for the full
text and `THIRD-PARTY-NOTICES.md` for bundled third-party licenses.
