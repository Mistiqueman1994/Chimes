# Snake (desktop)

A standalone Windows build of the Nokia-style Snake game, packaged with Electron.
Opens in its own window titled "Snake" — no browser required.

## Get the .exe

Download the latest build from the repo's GitHub Actions run for
**Build Windows Snake app** (Actions tab → latest successful run → Artifacts →
`Snake-windows`). Unzip it and run `Snake.exe`.

## Build it yourself

```
cd desktop-app
npm install
npm run package:win
```

Produces `dist/Snake-win32-x64/Snake.exe`.
