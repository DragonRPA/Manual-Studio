#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
(주)드래곤알피에이 매뉴얼 스튜디오 Cloudflare R2 원클릭 자동 릴리즈 & 버전 동기화 엔진
Cloudflare R2 Direct Release & Version Synchronization Engine
================================================================================
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import re
import json
import hashlib
import argparse
import datetime
import urllib.request
import urllib.parse
from pathlib import Path

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("[ERROR] boto3 패키지가 필요합니다: pip install boto3")
    sys.exit(1)

# Cloudflare R2 Configuration (SSOT)
R2_CONFIG = {
    "account_id": "35014a2514680107d74e1e68d96e6c32",
    "bucket_name": "dragonrpa",
    "access_key_id": "03cdb7560d37242de608a5db2a976030",
    "secret_access_key": "b2407ab4532e02317860bc3d63226fb7bc232e88083b150c15023906ed141986",
    "public_domain": "https://pub-4bd1b65a7bcc4eef8993da27e7362727.r2.dev",
}

PROJECT_DIR = Path(__file__).resolve().parent
VERSION_JSON_PATH = PROJECT_DIR / "version.json"
STUDIO_PY_PATH = PROJECT_DIR / "manual_capture_studio.py"
BUILD_BAT_PATH = PROJECT_DIR / "build_c.bat"
UPDATER_PY_PATH = PROJECT_DIR / "updater_engine.py"
EXE_CANDIDATES = [
    PROJECT_DIR / "ManualStudio.exe",
    PROJECT_DIR / "dist_c" / "ManualStudio.exe",
    PROJECT_DIR / "dist" / "ManualStudio.exe",
]
APK_PATH = PROJECT_DIR / "ManualStudioMobile.apk"

DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_Glpfg5n7jVKE@ep-tiny-frost-azxnod0v-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"


def calculate_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_version_json() -> dict:
    if VERSION_JSON_PATH.exists():
        with open(VERSION_JSON_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {
        "version": "1.9.2",
        "version_code": 192,
        "release_date": str(datetime.date.today()),
        "release_title": "Manual Studio Update",
        "release_notes": "버그 수정 및 안정성 향상",
        "download_url": "",
        "release_page_url": "https://www.dragonrpa.co.kr/manual-studio",
        "min_required_version": "1.0.0",
        "force_update": False,
    }


def parse_version_tuple(ver_str: str) -> tuple:
    s = str(ver_str).strip().lstrip("vV")
    parts = []
    for token in s.split("."):
        m = re.match(r"(\d+)", token)
        parts.append(int(m.group(1)) if m else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def bump_version(current_ver: str, bump_type: str = "patch") -> str:
    major, minor, patch = parse_version_tuple(current_ver)
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def sync_version_across_project(version: str, release_title: str = None, release_notes: str = None):
    clean_ver = version.strip().lstrip("vV")
    v_tuple = parse_version_tuple(clean_ver)
    version_code = v_tuple[0] * 100 + v_tuple[1] * 10 + v_tuple[2]
    today_str = str(datetime.date.today())

    download_url_latest = f"{R2_CONFIG['public_domain']}/releases/ManualStudio_latest.exe"

    # 1. Update version.json
    v_data = load_version_json()
    v_data["version"] = clean_ver
    v_data["version_code"] = version_code
    v_data["release_date"] = today_str
    if release_title:
        v_data["release_title"] = release_title
    if release_notes:
        v_data["release_notes"] = release_notes
    v_data["download_url"] = download_url_latest

    with open(VERSION_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(v_data, f, ensure_ascii=False, indent=2)
    print(f"[OK] [version.json] v{clean_ver} (code: {version_code}) 갱신 완료")

    # 2. Update manual_capture_studio.py (APP_VERSION = "vX.Y.Z")
    if STUDIO_PY_PATH.exists():
        with open(STUDIO_PY_PATH, "r", encoding="utf-8") as f:
            code = f.read()
        new_code = re.sub(
            r'APP_VERSION\s*=\s*["\']v?[0-9.]+["\']',
            f'APP_VERSION = "v{clean_ver}"',
            code,
            count=1,
        )
        if new_code != code:
            with open(STUDIO_PY_PATH, "w", encoding="utf-8") as f:
                f.write(new_code)
            print(f"[OK] [manual_capture_studio.py] APP_VERSION = 'v{clean_ver}' 동기화 완료")

    # 3. Update build_c.bat file/product versions
    if BUILD_BAT_PATH.exists():
        with open(BUILD_BAT_PATH, "r", encoding="utf-8") as f:
            bat_text = f.read()
        v4_str = f"{v_tuple[0]}.{v_tuple[1]}.{v_tuple[2]}.0"
        bat_text = re.sub(
            r'--windows-file-version=[0-9.]+',
            f'--windows-file-version={v4_str}',
            bat_text,
        )
        bat_text = re.sub(
            r'--windows-product-version=[0-9.]+',
            f'--windows-product-version={v4_str}',
            bat_text,
        )
        with open(BUILD_BAT_PATH, "w", encoding="utf-8") as f:
            f.write(bat_text)
        print(f"[OK] [build_c.bat] 버전 {v4_str} 동기화 완료")

    # 4. Update updater_engine.py primary URL to Cloudflare R2
    if UPDATER_PY_PATH.exists():
        with open(UPDATER_PY_PATH, "r", encoding="utf-8") as f:
            updater_code = f.read()
        cf_version_url = f"{R2_CONFIG['public_domain']}/releases/version.json"
        target_line = f'PRIMARY_VERSION_URL = "{cf_version_url}"'
        new_updater_code = re.sub(
            r'PRIMARY_VERSION_URL\s*=\s*["\'][^"\']+["\']',
            target_line,
            updater_code,
            count=1,
        )
        if new_updater_code != updater_code:
            with open(UPDATER_PY_PATH, "w", encoding="utf-8") as f:
                f.write(new_updater_code)
            print("[OK] [updater_engine.py] PRIMARY_VERSION_URL Cloudflare R2 연동 완료")

    return v_data


def get_r2_client():
    endpoint = f"https://{R2_CONFIG['account_id']}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=R2_CONFIG["access_key_id"],
        aws_secret_access_key=R2_CONFIG["secret_access_key"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


class ProgressPercentage:
    def __init__(self, filename, total_size):
        self._filename = filename
        self._total_size = total_size
        self._seen_so_far = 0

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._total_size) * 100
        mb_seen = self._seen_so_far / (1024 * 1024)
        mb_total = self._total_size / (1024 * 1024)
        sys.stdout.write(
            f"\r   -> 업로드 진행 중: {mb_seen:.1f}MB / {mb_total:.1f}MB ({percentage:.1f}%)"
        )
        sys.stdout.flush()


def upload_file_to_r2(s3, local_path: Path, r2_key: str, content_type: str, cache_control: str):
    total_size = os.path.getsize(local_path)
    print(f"\n[UPLOAD] Cloudflare R2 업로드 시작: {r2_key} ({total_size / (1024 * 1024):.2f} MB)")

    progress = ProgressPercentage(local_path.name, total_size)
    extra_args = {
        "ContentType": content_type,
        "CacheControl": cache_control,
    }

    s3.upload_file(
        str(local_path),
        R2_CONFIG["bucket_name"],
        r2_key,
        ExtraArgs=extra_args,
        Callback=progress,
    )
    print(f"\n[OK] 업로드 완료: {R2_CONFIG['public_domain']}/{r2_key}")


def update_dragonrpa_website_db(version: str, download_url: str):
    try:
        script_dir = Path("D:/01.AntiGravity/www.dragonrpa.co.kr")
        if script_dir.exists():
            import subprocess
            cmd = [
                "node",
                "src/scripts/sync_release_db.js",
                "MANUAL_STUDIO",
                f"v{version}",
                download_url,
            ]
            res = subprocess.run(cmd, cwd=str(script_dir), capture_output=True, timeout=15)
            output = res.stdout.decode("utf-8", errors="ignore").strip()
            if output:
                print(f"[OK] [Neon DB] {output}")
    except Exception as e:
        print("[WARNING] 웹사이트 DB 갱신 중 예외:", e)


def main():
    parser = argparse.ArgumentParser(description="DragonRPA Manual Studio Cloudflare R2 Release Engine")
    parser.add_argument("--version", "-v", help="지정할 버전 (예: 1.9.2)")
    parser.add_argument("--bump", choices=["patch", "minor", "major"], help="버전 자동 증가")
    parser.add_argument("--skip-upload", action="store_true", help="업로드 건너뛰고 버전 동기화만 수행")
    parser.add_argument("--notes", help="릴리즈 노트 요약")
    args = parser.parse_args()

    print("================================================================================")
    print(" (주)드래곤알피에이 [Manual Studio] Cloudflare R2 자동 릴리즈 & 버전 동기화")
    print("================================================================================")

    # 1. Determine target version
    cur_data = load_version_json()
    current_ver = cur_data.get("version", "1.9.2")

    if args.version:
        target_version = args.version.strip().lstrip("vV")
    elif args.bump:
        target_version = bump_version(current_ver, args.bump)
    else:
        next_ver = bump_version(current_ver, "patch")
        print(f"[VERSION] 현재 버전: v{current_ver} ➔ 다음 권장 버전: v{next_ver}")
        print(f"  [1] 다음 버전으로 자동 증가 후 배포 (v{next_ver}) [기본값 - 그냥 엔터]")
        print(f"  [2] 현재 버전 그대로 재배포 (v{current_ver})")
        print(f"  [3] 직접 버전 입력 (예: 2.0.0)")
        choice = input("선택 (엔터: 1번 자동 증가): ").strip()
        if choice == "2":
            target_version = current_ver
        elif choice == "3":
            custom_v = input("배포할 버전 번호 입력: ").strip()
            target_version = custom_v.lstrip("vV") if custom_v else next_ver
        else:
            target_version = next_ver

    print(f"\n[TARGET] 최종 확정 배포 버전: v{target_version}")

    # 2. Synchronize versions across files
    v_data = sync_version_across_project(target_version, release_notes=args.notes)

    # 3. Locate Executable
    exe_file = None
    for cand in EXE_CANDIDATES:
        if cand.exists():
            exe_file = cand
            break

    if not exe_file:
        print("\n[ERROR] 컴파일된 ManualStudio.exe를 찾을 수 없습니다.")
        print("먼저 build_c.bat를 실행하여 C-Compilation 바이너리를 생성하세요.")
        sys.exit(1)

    file_size_mb = os.path.getsize(exe_file) / (1024 * 1024)
    sha256_hash = calculate_sha256(exe_file)
    print(f"\n[BINARY] 배포 파일: {exe_file.name} ({file_size_mb:.2f} MB)")
    print(f"   SHA-256: {sha256_hash}")

    if args.skip_upload:
        print("\n[INFO] --skip-upload 옵션에 의해 Cloudflare R2 업로드를 건너뜁니다.")
        return

    # 4. Upload to Cloudflare R2
    s3 = get_r2_client()

    # 4-1. Upload ManualStudio_latest.exe
    upload_file_to_r2(
        s3,
        exe_file,
        "releases/ManualStudio_latest.exe",
        content_type="application/vnd.microsoft.portable-executable",
        cache_control="no-cache, must-revalidate",
    )

    # 4-2. Upload ManualStudio_vX.Y.Z.exe
    versioned_key = f"releases/ManualStudio_v{target_version}.exe"
    upload_file_to_r2(
        s3,
        exe_file,
        versioned_key,
        content_type="application/vnd.microsoft.portable-executable",
        cache_control="public, max-age=31536000",
    )

    # 4-3. Upload version.json
    upload_file_to_r2(
        s3,
        VERSION_JSON_PATH,
        "releases/version.json",
        content_type="application/json; charset=utf-8",
        cache_control="no-cache, must-revalidate",
    )

    # 4-4. Upload Android APK (if present)
    if APK_PATH.exists():
        apk_mb = os.path.getsize(APK_PATH) / (1024 * 1024)
        print(f"\n[APK] 안드로이드 모바일 패키지 감지: {APK_PATH.name} ({apk_mb:.2f} MB)")
        upload_file_to_r2(
            s3,
            APK_PATH,
            "releases/ManualStudioMobile.apk",
            content_type="application/vnd.android.package-archive",
            cache_control="no-cache, must-revalidate",
        )
        upload_file_to_r2(
            s3,
            APK_PATH,
            f"releases/ManualStudioMobile_v{target_version}.apk",
            content_type="application/vnd.android.package-archive",
            cache_control="public, max-age=31536000",
        )

    # 5. Update dragonrpa.co.kr Website DB
    latest_download_url = f"{R2_CONFIG['public_domain']}/releases/ManualStudio_latest.exe"
    update_dragonrpa_website_db(target_version, latest_download_url)

    print("\n================================================================================")
    print(f"[SUCCESS] Manual Studio v{target_version} Cloudflare R2 배포 및 웹사이트 동기화 100% 완료!")
    print(f"   * 고정 최신 다운로드: {latest_download_url}")
    print(f"   * 버전별 보관 파일:   {R2_CONFIG['public_domain']}/{versioned_key}")
    print(f"   * 원격 버전 체크 URL: {R2_CONFIG['public_domain']}/releases/version.json")
    print(f"   * 공식 웹사이트:      https://www.dragonrpa.co.kr/products")
    print("================================================================================")


if __name__ == "__main__":
    main()
