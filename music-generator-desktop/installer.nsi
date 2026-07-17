; NSIS installer for the Original Music Generator desktop app.
; Packages the PyInstaller-built exe (dist\OriginalMusicGenerator.exe) into a
; normal per-user Windows installer: Start Menu + Desktop shortcuts, and an
; uninstaller listed in "Apps & Features" - no admin elevation required.
;
; Build with:  makensis installer.nsi
; (run from the music-generator-desktop directory, after PyInstaller has
; produced dist\OriginalMusicGenerator.exe)

!include "MUI2.nsh"

!define APPNAME "Original Music Generator"
!define COMPANYNAME "Chimes"
!define DESCRIPTION "Algorithmic full-band instrumental backing track generator"
!define EXE_NAME "OriginalMusicGenerator.exe"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

Name "${APPNAME}"
OutFile "dist_installer\MusicGenerator-Setup.exe"
InstallDir "$LOCALAPPDATA\${APPNAME}"
InstallDirRegKey HKCU "${UNINSTALL_KEY}" "InstallLocation"
RequestExecutionLevel user

!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\${EXE_NAME}"
  File "assets\icon.ico"

  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\icon.ico"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall ${APPNAME}.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\icon.ico"
  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\icon.ico"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\icon.ico"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "${COMPANYNAME}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "1.0.0"
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\${EXE_NAME}"
  Delete "$INSTDIR\icon.ico"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Uninstall ${APPNAME}.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  Delete "$DESKTOP\${APPNAME}.lnk"

  DeleteRegKey HKCU "${UNINSTALL_KEY}"
SectionEnd
