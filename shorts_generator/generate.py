# -*- coding: utf-8 -*-
"""
Dragon RPA - Automated SNS Shorts / Reels Video Generator
Target: YouTube Shorts (9:16), Instagram Reels, TikTok, Facebook
Author: Dragon RPA Engineering Team
"""

import os
import sys

# Ensure UTF-8 console output for Windows cmd / PowerShell
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import argparse
import time

# Add root directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from engine.video_composer import render_scenario_to_video

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SCENARIOS_DIR = os.path.join(BASE_DIR, "scenarios")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

SCENARIO_MAP = {
    "1": "scenario_1_overtime.json",
    "2": "scenario_2_before_after.json",
    "3": "scenario_3_privacy_blur.json"
}

def load_scenario(scenario_filename_or_path: str) -> dict:
    if os.path.exists(scenario_filename_or_path):
        target_path = scenario_filename_or_path
    else:
        target_path = os.path.join(SCENARIOS_DIR, scenario_filename_or_path)
        
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"시나리오 파일을 찾을 수 없습니다: {target_path}")
        
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_single_scenario(scenario_key_or_file: str):
    start_clock = time.time()
    if scenario_key_or_file in SCENARIO_MAP:
        scenario_file = SCENARIO_MAP[scenario_key_or_file]
    else:
        scenario_file = scenario_key_or_file
        
    scenario_data = load_scenario(scenario_file)
    scenario_id = scenario_data.get("id", "shorts_output")
    output_mp4 = os.path.join(OUTPUT_DIR, f"{scenario_id}.mp4")
    
    print("\n" + "="*65)
    print(f">> [영상 제작 시작] {scenario_data.get('title')} ({scenario_id})")
    print(f"   규격: 1080x1920 (9:16 Vertical) | 성우: {scenario_data.get('voice')}")
    print("="*65)
    
    render_scenario_to_video(
        scenario=scenario_data,
        assets_dir=ASSETS_DIR,
        output_mp4_path=output_mp4,
        temp_dir=TEMP_DIR,
        fps=30
    )
    
    elapsed = time.time() - start_clock
    print("\n" + "="*65)
    print(f">> [렌더링 완료] 소요 시간: {elapsed:.1f}초")
    print(f"   완성 영상 파일: {output_mp4}")
    print("="*65 + "\n")
    return output_mp4

def run_interactive():
    while True:
        print("\n" + "="*65)
        print("   드래곤RPA 매뉴얼 스튜디오 - SNS 숏폼 영상 자동 생성기")
        print("   (YouTube Shorts, Instagram Reels, TikTok, Facebook 1080x1920)")
        print("="*65)
        print("  [1] 칼퇴 공감 편 (팀장님, 매뉴얼 다 만들었습니다!)")
        print("  [2] 비포 & 애프터 편 (캡처 도구 복붙 지옥 vs 매뉴얼 스튜디오)")
        print("  [3] 개인정보 & 보안 편 (매뉴얼 만들다 고객 정보 유출될 뻔?)")
        print("  [4] 기본 3편 전체 일괄 생성")
        print("  [Q] 종료")
        print("="*65)
        
        choice = input(">> 실행할 번호를 선택하세요 (1/2/3/4/Q): ").strip().upper()
        if choice == "Q":
            print("프로그램을 종료합니다.")
            break
        elif choice in ["1", "2", "3"]:
            run_single_scenario(choice)
        elif choice == "4":
            print("\n>> 기본 3편 일괄 생성을 시작합니다...")
            for k in ["1", "2", "3"]:
                run_single_scenario(k)
            print("\n>> 모든 숏폼 영상 생성이 성공적으로 완료되었습니다!")
        else:
            print("올바른 번호를 입력해주세요.")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    parser = argparse.ArgumentParser(description="Dragon RPA Auto Shorts Video Generator")
    parser.add_argument("--scenario", "-s", choices=["1", "2", "3"], help="기본 시나리오 번호 (1, 2, 3)")
    parser.add_argument("--all", "-a", action="store_true", help="기본 3편 전체 일괄 생성")
    parser.add_argument("--file", "-f", help="커스텀 시나리오 JSON 파일 경로")
    
    args = parser.parse_args()
    
    if args.all:
        for k in ["1", "2", "3"]:
            run_single_scenario(k)
    elif args.scenario:
        run_single_scenario(args.scenario)
    elif args.file:
        run_single_scenario(args.file)
    else:
        run_interactive()

if __name__ == "__main__":
    main()
