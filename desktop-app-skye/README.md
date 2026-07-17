# Skye (desktop)

A standalone Windows build of the Skye talking sky clock, packaged with Electron
and an NSIS installer. Installs like a normal Windows app — Start Menu shortcut,
optional desktop shortcut, and an uninstaller in "Add or remove programs" — and
opens in its own window titled "Skye", no browser required.

## Get the installer

Permanent download link (rebuilt automatically on every push to `main`):

https://github.com/Mistiqueman1994/Chimes/releases/download/skye-latest/Skye-Setup.exe

Run it and follow the installer.

## Build it yourself

```
cd desktop-app-skye
npm install
npm run package:win
```

Produces `dist/Skye-Setup.exe`.
