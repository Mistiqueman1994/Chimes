# Skye

A full-screen day/night sky clock for phones and desktops. The sky and a sun/moon
arc track the real time of day, Skye speaks the time on the half hour (with a
configurable silent window and "Hey Skye" voice activation), and it bundles an
always-narrating stopwatch, timer, and calculator.

## Features

- **Sky clock** — sky color and a sun/moon arc animate across the day/night
  cycle; digital or analogue clock face.
- **Spoken announcements** — Skye speaks the time every half hour, with an
  optional silent period (e.g. overnight) and optional date readout.
- **"Hey Skye" voice activation** — ask Skye for the time or date out loud
  (Chrome, Edge, and Safari; needs microphone access and HTTPS).
- **Stopwatch** — counts up, announces every elapsed second and each lap.
- **Timer** — microwave-style keypad entry, announces the set duration, beeps
  and announces when it finishes.
- **Calculator** — reads back every digit, operation, and result.
- **Installable PWA** — add to your home screen for a full-screen, offline-
  capable app (`manifest.json` + `sw.js`).

## Running locally

Skye is a static site — no build step. Serve the folder over HTTP(S) (voice
activation and the wake lock both require a secure context, and `file://`
won't work for the service worker):

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Deploying

Push the contents of this repo to any static host (GitHub Pages, Netlify,
Vercel, etc.) — `index.html`, `manifest.json`, `sw.js`, and the icon files are
all that's needed.

## Files

- `index.html` — the entire app (markup, styles, and logic).
- `manifest.json` — PWA manifest (name, icons, colors, display mode).
- `sw.js` — service worker for offline caching.
- `icon-192.png` / `icon-180.png` — home-screen icons.
