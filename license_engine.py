"""
================================================================================
(주)드래곤알피에이 매뉴얼 스튜디오 엔터프라이즈 라이선스 엔진
Manual Studio Enterprise License & DRM Security Engine
================================================================================
"""

import os
import sys
import json
import hmac
import hashlib
import base64
import winreg
from datetime import datetime, timedelta

class LicenseType:
    PERPETUAL = "PERPETUAL"           # 1카피 영구 (MS1P)
    SUBSCRIPTION_1M = "SUB_1M"        # 1카피 1개월 (MS1M)
    SUBSCRIPTION_1Y = "SUB_1Y"        # 1카피 1년 (MS1Y)
    ENTERPRISE = "ENTERPRISE"         # 엔터프라이즈 볼륨 (MSENT)
    AIR_GAPPED_SITE = "AIR_GAPPED"    # 오프라인 폐쇄망 사이트 (MSSITE)
    TRIAL_EXT_14D = "TRIAL_14D"       # 14일 평가 연장 (MST14)

    SUB_1M = SUBSCRIPTION_1M
    SUB_1Y = SUBSCRIPTION_1Y
    AIR_GAPPED = AIR_GAPPED_SITE
    TRIAL_14D = TRIAL_EXT_14D

class LicenseEngine:
    MASTER_SECRET = b"DragonRPA-ManualStudio-MasterSecret-2026-v1.4"
    REG_SUBKEY = r"Software\DragonRPA\ManualStudio\License"
    REG_VAL_KEY = "SerialKey"
    REG_VAL_DATA = "Payload"
    KEY_FILE = "license.key"

    PREFIX_MAP = {
        LicenseType.PERPETUAL: "MS1P",
        LicenseType.SUBSCRIPTION_1M: "MS1M",
        LicenseType.SUBSCRIPTION_1Y: "MS1Y",
        LicenseType.ENTERPRISE: "MSENT",
        LicenseType.AIR_GAPPED_SITE: "MSSITE",
        LicenseType.TRIAL_EXT_14D: "MST14"
    }

    PREFIX_REV_MAP = {v: k for k, v in PREFIX_MAP.items()}

    _cached_status = None

    @classmethod
    def get_hwid(cls) -> str:
        """
        클라이언트 PC 고유 식별자(HWID) 산출
        Windows MachineGuid + 시스템 환경 변수 해시
        반환: DRPA-XXXX-XXXX-XXXX (16자리)
        """
        raw_id = ""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                raw_id, _ = winreg.QueryValueEx(key, "MachineGuid")
        except Exception:
            pass

        if not raw_id:
            raw_id = os.environ.get("COMPUTERNAME", "UNKNOWN-PC") + ":" + os.environ.get("PROCESSOR_IDENTIFIER", "CPU")

        h = hashlib.sha256(raw_id.encode("utf-8")).hexdigest().upper()
        return f"DRPA-{h[0:4]}-{h[4:8]}-{h[8:12]}"

    @classmethod
    def generate_license_key(cls, license_type: str, hwid: str, issued_to: str, expiry_date: str = "NONE", max_seats: int = 1) -> str:
        """
        사장님/키젠 전용: 위변조 불가능한 정식 라이선스 시리얼 키 생성
        """
        prefix = cls.PREFIX_MAP.get(license_type, "MS1P")
        clean_hwid = hwid.strip().upper() if license_type not in (LicenseType.ENTERPRISE, LicenseType.AIR_GAPPED_SITE) else "ENTERPRISE"
        clean_issued = issued_to.strip().replace(":", "_").replace("|", "_")

        payload = {
            "type": license_type,
            "hwid": clean_hwid,
            "issued_to": clean_issued,
            "expiry": expiry_date,
            "seats": max_seats,
            "issued_at": datetime.now().strftime("%Y-%m-%d")
        }

        payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        sig = hmac.new(cls.MASTER_SECRET, payload_json.encode("utf-8"), hashlib.sha256).hexdigest().upper()

        # 압축 패킷 인코딩 (Base64 URL-safe)
        p_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("ascii").rstrip("=")
        # 시리얼 포맷: PREFIX-SIG8-PAYLOAD_B64
        # e.g. MS1P-A1B2C3D4-eyJ...
        serial_key = f"{prefix}-{sig[:8]}-{p_b64}"
        return serial_key

    @classmethod
    def verify_license_key(cls, serial_key: str, current_hwid: str = None) -> tuple:
        """
        시리얼 키 검증
        반환값: (is_valid: bool, license_info: dict, message: str)
        """
        if not serial_key or not isinstance(serial_key, str):
            return False, {}, "라이선스 키가 입력되지 않았습니다."

        parts = serial_key.strip().split("-", 2)
        if len(parts) != 3:
            return False, {}, "올바르지 않은 라이선스 키 형식입니다."

        prefix, sig_chunk, p_b64 = parts
        expected_type = cls.PREFIX_REV_MAP.get(prefix)
        if not expected_type:
            return False, {}, "인식할 수 없는 라이선스 유형 접두사입니다."

        # 패딩 복원 후 디코딩
        missing_padding = len(p_b64) % 4
        if missing_padding:
            p_b64 += "=" * (4 - missing_padding)

        try:
            payload_json = base64.urlsafe_b64decode(p_b64.encode("ascii")).decode("utf-8")
            payload = json.loads(payload_json)
        except Exception:
            return False, {}, "라이선스 데이터가 손상되었거나 위변조되었습니다."

        # 1. 서명 무결성 검증
        expected_sig = hmac.new(cls.MASTER_SECRET, payload_json.encode("utf-8"), hashlib.sha256).hexdigest().upper()
        if not hmac.compare_digest(expected_sig[:8], sig_chunk):
            return False, {}, "라이선스 디지털 서명 검증에 실패했습니다. (위변조된 키)"

        # 2. HWID 노드락 검증
        target_hwid = payload.get("hwid", "")
        if payload.get("type") not in (LicenseType.ENTERPRISE, LicenseType.AIR_GAPPED_SITE):
            curr = current_hwid or cls.get_hwid()
            if target_hwid != curr:
                return False, {}, f"다른 PC용으로 발급된 라이선스입니다. (발급 HWID: {target_hwid})"

        # 3. 만료일 검증
        expiry_str = payload.get("expiry", "NONE")
        if expiry_str != "NONE":
            try:
                exp_dt = datetime.strptime(expiry_str, "%Y-%m-%d")
                if datetime.now() > exp_dt.replace(hour=23, minute=59, second=59):
                    return False, {}, f"라이선스 유효 기간({expiry_str})이 만료되었습니다."
            except Exception:
                return False, {}, "라이선스 만료일 형식이 잘못되었습니다."

        return True, payload, "정상 인증되었습니다."

    @classmethod
    def save_license(cls, serial_key: str) -> bool:
        """레지스트리 및 로컬 파일에 라이선스 키 영구 보존"""
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cls.REG_SUBKEY) as key:
                winreg.SetValueEx(key, cls.REG_VAL_KEY, 0, winreg.REG_SZ, serial_key)
        except Exception:
            pass

        try:
            with open(cls.KEY_FILE, "w", encoding="utf-8") as f:
                f.write(serial_key.strip())
        except Exception:
            pass

        cls._cached_status = None
        return True

    @classmethod
    def load_saved_license(cls) -> str:
        """저장된 라이선스 키 로드 (레지스트리 1순위, 파일 2순위)"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_SUBKEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, cls.REG_VAL_KEY)
                if val:
                    return val.strip()
        except Exception:
            pass

        if os.path.exists(cls.KEY_FILE):
            try:
                with open(cls.KEY_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return content
            except Exception:
                pass
        return ""

    @classmethod
    def check_license_status(cls) -> dict:
        """
        현재 프로그램 라이선스 상태 판정
        반환값:
        {
            "is_licensed": bool,
            "license_type": str,
            "issued_to": str,
            "expiry": str,
            "badge_text": str,
            "message": str
        }
        """
        key = cls.load_saved_license()
        if not key:
            return {
                "is_licensed": False,
                "license_type": "TRIAL",
                "issued_to": "Evaluation User",
                "expiry": "2026-12-31",
                "badge_text": "평가판 (Trial)",
                "message": "미등록 평가판 모드로 동작 중입니다."
            }

        valid, payload, msg = cls.verify_license_key(key)
        if valid:
            l_type = payload.get("type", "PERPETUAL")
            type_names = {
                LicenseType.PERPETUAL: "정식 영구 라이선스",
                LicenseType.SUBSCRIPTION_1M: "1개월 구독 라이선스",
                LicenseType.SUBSCRIPTION_1Y: "1년 연간 라이선스",
                LicenseType.ENTERPRISE: "엔터프라이즈 볼륨 라이선스",
                LicenseType.AIR_GAPPED_SITE: "오프라인 사이트 라이선스",
                LicenseType.TRIAL_EXT_14D: "14일 평가 연장 라이선스"
            }
            return {
                "is_licensed": True,
                "license_type": l_type,
                "issued_to": payload.get("issued_to", "Registered User"),
                "expiry": payload.get("expiry", "무제한 (None)"),
                "badge_text": type_names.get(l_type, "정식 라이선스"),
                "message": msg
            }
        else:
            return {
                "is_licensed": False,
                "license_type": "EXPIRED_OR_INVALID",
                "issued_to": "Evaluation User",
                "expiry": "만료됨",
                "badge_text": "평가판 (만료/오류)",
                "message": msg
            }

    @classmethod
    def is_licensed(cls) -> bool:
        return cls.check_license_status().get("is_licensed", False)
