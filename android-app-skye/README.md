# Skye (Android)

A standalone Android build of the Skye talking sky clock, packaged as a Trusted
Web Activity (TWA) — a thin native wrapper that runs the real, hosted Skye web
app inside Chrome's engine. Installs like a normal Android app: its own icon in
the app drawer, its own task in the app switcher, no visible browser chrome
around it. Because it runs on Chrome (not a limited embedded WebView), the
spoken clock, stopwatch, timer, calculator, and "Hey Skye" voice activation all
work exactly as they do in a full browser tab.

It needs a network connection to load the page the first time; after that, a
service worker caches it so it also opens offline.

## Get the installer

Permanent download link (rebuilt automatically on every push to `main`):

https://github.com/Mistiqueman1994/Chimes/releases/download/skye-android-latest/Skye.apk

Download `Skye.apk` on your phone, open it, and allow "install unknown apps"
for your browser/file manager if prompted — the app isn't distributed through
the Play Store, so Android needs that one-time permission to sideload it.

**Known limitation:** this app isn't cryptographically verified against the
`mistiqueman1994.github.io` domain (that requires a `.well-known/assetlinks.json`
file hosted at the domain root, which belongs to a different repository than
this one). In practice this means Chrome may show a small toolbar at the top
of the window instead of running fully chrome-less. Everything still works —
it's a cosmetic difference, not a functional one.

## Build it yourself

```
cd android-app-skye
gradle :app:assembleRelease
```

Produces `app/build/outputs/apk/release/app-release.apk`, signed with the
keystore committed at `keystore/skye-release.keystore` (password
`skye-chimes-2026` — not sensitive, this is a hobby project keystore, not a
production signing key).
