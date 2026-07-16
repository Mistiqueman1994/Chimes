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

## On iPhone, without a Mac

iOS apps normally need Xcode (Mac-only) to compile, but you don't need a
compiled app to get Skye on your Home Screen. Once the site is hosted (see
[Deploying](#deploying-as-a-website--pwa) below):

1. Open the hosted URL in **Safari** on the iPhone (must be Safari, not
   another browser — only Safari can install home-screen apps on iOS).
2. Tap the **Share** button, then **Add to Home Screen**.
3. Launch Skye from its new Home Screen icon — it opens full-screen, with no
   Safari address bar, and keeps working offline.

Everything works this way except "Hey Skye" voice activation — iOS restricts
the `SpeechRecognition` API for home-screen web apps, so that toggle may not
respond. Spoken time announcements, the stopwatch/timer/calculator narration,
and the wake lock all work normally.

## Windows desktop app

Skye is also wrapped with [Electron](https://www.electronjs.org) into a
Windows desktop app (`electron/main.js` loads `www/index.html` in a native
window).

This sandbox's network policy blocks the Electron binary download (it comes
from GitHub releases, which isn't reachable here), so it can't be built or
launched locally in this environment. Instead, `.github/workflows/build-windows.yml`
builds it on GitHub's own `windows-latest` runner, which has full internet
access — no Wine, no local Windows machine, no cost to you:

1. Push (or re-run) the workflow — it's already wired to run on every push.
2. Open the repo's **Actions** tab → the latest **Build Skye for Windows**
   run.
3. Before packaging, the workflow actually launches the app for 8 seconds and
   fails the run if it crashes — so a green run means it genuinely starts, not
   just that it compiled.
4. Download the **skye-windows** artifact (a zip containing `Skye Setup
   *.exe` installer and a portable `.exe`) from the run's summary page.

To build it yourself instead (on an actual Windows machine, where the
Electron download isn't blocked):

```sh
npm install
npm run dist:win
```

Output lands in `dist-electron/`.

### Known limitation: voice activation in the desktop app

Same root cause as the mobile apps, different mechanism: Chromium's built-in
speech recognition backend needs a Google API key that's only embedded in
official Google Chrome builds — Electron ships open-source Chromium without
it, so `webkitSpeechRecognition` typically fails silently or errors out in
Electron apps. "Hey Skye" voice activation is unlikely to work in the Windows
app. Everything else — spoken announcements, stopwatch/timer/calculator
narration, the sky clock — runs normally, since it's the same engine already
verified in [Running in a browser](#running-in-a-browser).

## Running in a browser

Skye is a static site — no build step. Serve `www/` over HTTP(S) (voice
activation and the wake lock both require a secure context, and `file://`
won't work for the service worker):

```sh
cd www && python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Deploying as a website / PWA

A GitHub Actions workflow (`.github/workflows/deploy-pages.yml`) is already
set up to publish `www/` to GitHub Pages on every push to `main`. To turn it
on: go to the repo's **Settings → Pages**, and under "Build and deployment"
set **Source** to **GitHub Actions** (one-time, manual — GitHub doesn't allow
enabling this via API). After that, each push re-deploys automatically, and
the live URL shows up on the same Settings → Pages screen (typically
`https://<username>.github.io/<repo>/`).

You can just as easily push the contents of `www/` to any other static host
(Netlify, Vercel, etc.) instead — `index.html`, `manifest.json`, `sw.js`, and
the icon files are all that's needed.

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
