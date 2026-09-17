@echo off
chcp 65001 > nul
title [DragonRPA] Manual Studio Cloudflare R2 Release Engine
cd /d "%~dp0"

echo =======================================================================
echo  [DragonRPA] Manual Studio Cloudflare R2 자동 릴리즈 실행기
echo =======================================================================
echo.

python release_to_cf.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] 배포 도중 오류가 발생했습니다.
) else (
    echo.
    echo [SUCCESS] 모든 배포 작업이 성공적으로 완결되었습니다!
)

echo.
pause
