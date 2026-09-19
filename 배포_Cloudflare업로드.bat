@echo off
chcp 65001 > nul
cd /d "%~dp0"
title [DragonRPA] Manual Studio Cloudflare R2 Release Engine

echo =======================================================================
echo  [DragonRPA] Manual Studio Cloudflare R2 Release Engine
echo =======================================================================
echo.

python release_to_cf.py %*

if errorlevel 1 (
    echo.
    echo [ERROR] Deployment failed.
) else (
    echo.
    echo [SUCCESS] Deployment completed successfully!
)

echo.
pause
