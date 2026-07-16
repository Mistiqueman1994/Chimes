# Skye

A full-screen day/night sky clock for phones and desktops. The sky and a sun/moon
arc track the real time of day, Skye speaks the time on the half hour (with a
configurable silent window and "Hey Skye" voice activation), and it bundles an
always-narrating stopwatch, timer, and calculator.

The web app lives in `www/`. It's wrapped with [Capacitor](https://capacitorjs.com)
into native Android (`android/`) and iOS (`ios/`) app projects, so it can also be
built and installed as a real app rather than just a browser tab / home-screen icon.

## Features

- **Sky clock** — sky color and a sun/moon arc animate across the day/night
  cycle; digital or analogue clock face.
- **Spoken announcements** — Skye speaks the time every half hour, with an
  optional silent period (e.g. overnight) and optional date readout.
- **"Hey Skye" voice activation** — ask Skye for the time or date out loud
  (Chrome, Edge, and Safari; needs microphone access and HTTPS). See the
  native-app limitation below.
- **Stopwatch** — counts up, announces every elapsed second and each lap.
- **Timer** — microwave-style keypad entry, announces the set duration, beeps
  and announces when it finishes.
- **Calculator** — reads back every digit, operation, and result.
- **Installable PWA** — add to your home screen for a full-screen, offline-
  capable app (`manifest.json` + `sw.js`).

## Running in a browser

Skye is a static site — no build step. Serve `www/` over HTTP(S) (voice
activation and the wake lock both require a secure context, and `file://`
won't work for the service worker):

```sh
cd www && python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Deploying as a website / PWA

Push the contents of `www/` to any static host (GitHub Pages, Netlify, Vercel,
etc.) — `index.html`, `manifest.json`, `sw.js`, and the icon files are all
that's needed.

## Building the native app

This repo is a [Capacitor](https://capacitorjs.com) project. `www/` is the
single source of truth for the app's UI; `npx cap sync` copies it into the
native Android/iOS projects.

```sh
npm install
npx cap sync
```

### Android

Requires [Android Studio](https://developer.android.com/studio) (which
provides the Android SDK).

```sh
npx cap open android
```

This opens `android/` in Android Studio — press Run to build and install on a
device/emulator, or use Build → Generate Signed Bundle/APK for a release
build. Building from the command line instead requires the Android SDK on
your `PATH`/`ANDROID_HOME`:

```sh
cd android && ./gradlew assembleDebug
```

### iOS

Requires a Mac with Xcode and [CocoaPods](https://cocoapods.org).

```sh
cd ios/App && pod install
cd ../.. && npx cap open ios
```

This opens `ios/App/App.xcworkspace` in Xcode — press Run to build and
install on a simulator/device, or Product → Archive for a release build.

### After editing the web app

Any time you change files in `www/`, re-sync before rebuilding the native
apps:

```sh
npx cap sync
```

### Known limitation: voice activation in the native app

"Hey Skye" relies on the Web Speech `SpeechRecognition` API. Android's system
WebView and iOS's WKWebView (which Capacitor apps run on) don't implement
that API — it's effectively Chrome/Safari-browser-only. The toggle already
disables itself gracefully when the API isn't available, so the native app
just won't offer voice activation. Everything else (spoken announcements,
stopwatch/timer/calculator narration, wake lock, sky clock) uses APIs that
are supported in both WebViews and works normally.

## Files

- `www/` — the web app (`index.html`, `manifest.json`, `sw.js`, icons) —
  edit this.
- `android/` — generated native Android project (Capacitor).
- `ios/` — generated native iOS project (Capacitor).
- `capacitor.config.json` — Capacitor app id/name and web asset location.
- `package.json` — Capacitor CLI/runtime dependencies.
