@echo off
chcp 65001 > nul
title Dragon RPA - Auto Shorts Video Generator
cd /d "%~dp0\shorts_generator"
python generate.py
pause
