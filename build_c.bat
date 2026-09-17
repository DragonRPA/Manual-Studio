@echo off
chcp 65001 > nul
echo ========================================================
echo [DragonRPA] Manual Studio C-Compilation (Nuitka C-Compiler)
echo ========================================================

REM 1. Set clean ASCII working directories to bypass Korean path issues
if not exist "C:\ManualStudioBuild\temp" mkdir "C:\ManualStudioBuild\temp"
set TEMP=C:\ManualStudioBuild\temp
set TMP=C:\ManualStudioBuild\temp

REM 2. Read version from version.json (Python one-liner)
for /f "delims=" %%V in ('python -c "import json; d=json.load(open('version.json',encoding='utf-8')); print(d['version'])"') do set APP_VERSION=%%V
if "%APP_VERSION%"=="" (
  echo [WARN] version.json 읽기 실패 - 기본값 1.0.0 사용
  set APP_VERSION=1.0.0
)

REM 3. Build version suffix for filename: v1.9.3 -> v1_9_3 (경로 안전)
set VER_SAFE=%APP_VERSION:.=_%
set OUTPUT_NAME=ManualStudio_v%APP_VERSION%.exe
set OUTPUT_NAME_SAFE=ManualStudio_v%VER_SAFE%.exe

echo Version  : %APP_VERSION%
echo Output   : %OUTPUT_NAME%
echo.

REM 4. Run Nuitka C-Compilation
python -m nuitka ^
  --standalone ^
  --onefile ^
  --enable-plugin=pyside6 ^
  --experimental=force-dependencies-pefile ^
  --lto=no ^
  --windows-console-mode=attach ^
  --include-windows-runtime-dlls=yes ^
  --include-package=winsdk ^
  --no-deployment-flag=excluded-module-usage ^
  --nofollow-import-to=torch,torchvision,cv2,onnxruntime,rapidocr_onnxruntime,matplotlib,pandas,scipy ^
  --include-module=manual_cli ^
  --include-module=mcp_server ^
  --include-module=mobile_link_server ^
  --include-data-dir="assets=assets" ^
  --include-data-dir="fonts=fonts" ^
  --include-data-files="config.json=config.json" ^
  --include-data-files="version.json=version.json" ^
  --include-data-files="AGENTS.md=AGENTS.md" ^
  --windows-icon-from-ico="assets/manual_studio.ico" ^
  --windows-company-name="DragonRPA Co." ^
  --windows-product-name="Manual Studio" ^
  --windows-file-version=%APP_VERSION%.0 ^
  --windows-product-version=%APP_VERSION%.0 ^
  --windows-file-description="DragonRPA Manual Studio v%APP_VERSION%" ^
  --assume-yes-for-downloads ^
  --output-dir="C:\ManualStudioBuild" ^
  --output-filename="%OUTPUT_NAME%" ^
  manual_capture_studio.py

if %ERRORLEVEL% NEQ 0 (
  echo [ERROR] C-Compilation failed.
  exit /b %ERRORLEVEL%
)

REM 5. Copy to project root (버전 포함 파일명 + 최신본 고정 파일명 둘 다 유지)
if not exist "dist_c" mkdir "dist_c"
copy /y "C:\ManualStudioBuild\%OUTPUT_NAME%" "dist_c\%OUTPUT_NAME%"
copy /y "C:\ManualStudioBuild\%OUTPUT_NAME%" "%OUTPUT_NAME%"
copy /y "C:\ManualStudioBuild\%OUTPUT_NAME%" "ManualStudio_latest.exe"

REM 6. 빌드 크기 출력
for %%F in ("%OUTPUT_NAME%") do set FILE_SIZE=%%~zF
set /a FILE_MB=%FILE_SIZE% / 1048576

echo.
echo [SUCCESS] C-Compilation completed successfully!
echo Output (versioned) : %OUTPUT_NAME%  (%FILE_MB% MB)
echo Output (latest)    : ManualStudio_latest.exe
echo dist_c\            : dist_c\%OUTPUT_NAME%
