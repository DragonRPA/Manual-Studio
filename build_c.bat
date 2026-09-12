@echo off
chcp 65001 > nul
echo ========================================================
echo [DragonRPA] Manual Studio C-Compilation (Nuitka C-Compiler)
echo ========================================================

REM 1. Set clean ASCII working directories to bypass Korean path issues
if not exist "C:\ManualStudioBuild\temp" mkdir "C:\ManualStudioBuild\temp"
set TEMP=C:\ManualStudioBuild\temp
set TMP=C:\ManualStudioBuild\temp

REM 2. Run Nuitka C-Compilation
python -m nuitka ^
  --standalone ^
  --onefile ^
  --enable-plugin=pyside6 ^
  --experimental=force-dependencies-pefile ^
  --lto=no ^
  --windows-console-mode=disable ^
  --include-windows-runtime-dlls=yes ^
  --include-data-dir="assets=assets" ^
  --include-data-dir="fonts=fonts" ^
  --include-data-files="config.json=config.json" ^
  --include-data-files="version.json=version.json" ^
  --windows-icon-from-ico="assets/dragon_rpa.ico" ^
  --windows-company-name="DragonRPA Co." ^
  --windows-product-name="Manual Studio" ^
  --windows-file-version=1.4.0.12 ^
  --windows-product-version=1.4.0.12 ^
  --windows-file-description="DragonRPA Manual Studio" ^
  --assume-yes-for-downloads ^
  --output-dir="C:\ManualStudioBuild" ^
  --output-filename="ManualStudio.exe" ^
  manual_capture_studio.py

if %ERRORLEVEL% NEQ 0 (
  echo [ERROR] C-Compilation failed.
  exit /b %ERRORLEVEL%
)

REM 3. Copy compiled executable to project directory
if not exist "dist_c" mkdir "dist_c"
copy /y "C:\ManualStudioBuild\ManualStudio.exe" "dist_c\ManualStudio.exe"
copy /y "C:\ManualStudioBuild\ManualStudio.exe" "ManualStudio.exe"

echo [SUCCESS] C-Compilation completed successfully!
echo Binary path: ManualStudio.exe (27.97 MB)
