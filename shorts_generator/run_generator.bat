@echo off
chcp 65001 > nul
title Dragon RPA - Auto Shorts Video Generator
cd /d "%~dp0"

echo ===================================================================
echo   🎥 드래곤RPA 매뉴얼 스튜디오 - SNS 숏폼 영상 자동 생성기
echo ===================================================================
python generate.py
pause
