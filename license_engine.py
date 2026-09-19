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
import threading
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta

class LicenseType:
    PERSONAL = "PERSONAL"             # 개인용 1카피 (MSPS)
    ENTERPRISE = "ENTERPRISE"         # 기업용 볼륨/사이트 - 공기업 포함 (MSENT)
    EDUCATION = "EDUCATION"           # 교육용 (MSED)
    GOVERNMENT = "GOVERNMENT"         # 관공서용 - 행정/지자체 (MSGOV)

    # 레거시 및 하위 호환
    PERPETUAL = "PERPETUAL"           # 레거시 1카피 영구 (MS1P)
    SUBSCRIPTION_1M = "SUB_1M"        # 레거시 1카피 1개월 (MS1M)
    SUBSCRIPTION_1Y = "SUB_1Y"        # 레거시 1카피 1년 (MS1Y)
    TRIAL_EXT_14D = "TRIAL_14D"       # 14일 평가 연장 (MST14)

    SUB_1M = SUBSCRIPTION_1M
    SUB_1Y = SUBSCRIPTION_1Y
    TRIAL_14D = TRIAL_EXT_14D

class LicenseEngine:
    MASTER_SECRET = b"DragonRPA-ManualStudio-MasterSecret-2026-v1.4"
    
    # ── RSA-2048 비대칭키 공개키 (SSOT) ──────────────────────────────────
    # 개인키(Private Key)는 사장님 PC 및 판매 서버에만 보관되며, 클라이언트에는 오직 검증용 공개키만 탑재됩니다.
    RSA_PUBLIC_N = 0x9fbbff932b99e40895681a1f5d95f695fc0824ce1ee0ef51a20499eb83bae1ad5b16124629b0d77b27b2e93d323c1d8adf5f57780c5575c9aed6f76642fa3d0fa5421a53a1a91e003f62a6455e81c1bc37e89ad4bfbab360b1a7f00baa3e1cee28cda2dac1bf1bd899850d0fa6341c9b3fa8a4d240cd1648896241303b452478ec72be3828da3299a453701a431c857235f9bbdaf4d70332b3be8e948359308d2c75d13559efc5e409852a3fd15b73270d6783bbb3a6304a17f2702346220b547fe2d843565e27f82622fefac0c8087b1df1be509c30d0f2cf1cd58a058abc1204cd6cabc27b464837a34d3fb6754e1a061cebcff09229d51a61b52ab9dc0b9b
    RSA_PUBLIC_E = 65537

    REG_SUBKEY = r"Software\DragonRPA\ManualStudio\License"
    REG_VAL_KEY = "SerialKey"
    REG_VAL_DATA = "Payload"
    KEY_FILE = "license.key"

    PREFIX_MAP = {
        LicenseType.PERSONAL: "MSPS",
        LicenseType.ENTERPRISE: "MSENT",
        LicenseType.EDUCATION: "MSED",
        LicenseType.GOVERNMENT: "MSGOV",
        LicenseType.PERPETUAL: "MS1P",
        LicenseType.SUBSCRIPTION_1M: "MS1M",
        LicenseType.SUBSCRIPTION_1Y: "MS1Y",
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
    def generate_license_key(cls, license_type: str, hwid: str, issued_to: str, expiry_date: str = "NONE", max_seats: int = 1, private_key_pem: bytes = None) -> str:
        """
        사장님/키젠/판매서버 전용: RSA-2048 비대칭키 디지털 서명 정식 라이선스 시리얼 키 생성
        """
        prefix = cls.PREFIX_MAP.get(license_type, "MSPS")
        if license_type in (LicenseType.ENTERPRISE, LicenseType.GOVERNMENT):
            clean_hwid = "ENTERPRISE" if license_type == LicenseType.ENTERPRISE else "GOVERNMENT"
        else:
            clean_hwid = hwid.strip().upper()
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
        payload_bytes = payload_json.encode("utf-8")

        # 1. 개인키 로드 시도 (인자 -> 파일 tools/secret_private_key.pem)
        pem_bytes = private_key_pem
        if not pem_bytes:
            possible_key_paths = [
                os.path.join(os.path.dirname(__file__), "tools", "secret_private_key.pem"),
                os.path.join(os.path.dirname(__file__), "secret_private_key.pem"),
            ]
            for p in possible_key_paths:
                if os.path.exists(p):
                    try:
                        with open(p, "rb") as kf:
                            pem_bytes = kf.read()
                        break
                    except Exception:
                        pass

        p_b64 = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")

        if pem_bytes:
            try:
                from cryptography.hazmat.primitives.asymmetric import padding
                from cryptography.hazmat.primitives import hashes, serialization
                private_key = serialization.load_pem_private_key(pem_bytes, password=None)
                signature = private_key.sign(
                    payload_bytes,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                sig_hex = signature.hex()
                # RSA 시리얼 포맷: PREFIX-RSA-SIG_HEX-PAYLOAD_B64
                return f"{prefix}-RSA-{sig_hex}-{p_b64}"
            except Exception as e:
                print(f"[WARN] RSA signing failed ({e}), falling back to HMAC")

        # Fallback: 레거시 HMAC 방식
        sig = hmac.new(cls.MASTER_SECRET, payload_bytes, hashlib.sha256).hexdigest().upper()
        return f"{prefix}-{sig[:8]}-{p_b64}"

    @classmethod
    def verify_license_key(cls, serial_key: str, current_hwid: str = None) -> tuple:
        """
        시리얼 키 검증 (RSA-2048 비대칭키 디지털 서명 + 레거시 HMAC 하위 호환)
        반환값: (is_valid: bool, license_info: dict, message: str)
        """
        if not serial_key or not isinstance(serial_key, str):
            return False, {}, "라이선스 키가 입력되지 않았습니다."

        raw_key = serial_key.strip()
        parts = raw_key.split("-", 3)
        if len(parts) < 3:
            return False, {}, "올바르지 않은 라이선스 키 형식입니다."

        prefix = parts[0]
        expected_type = cls.PREFIX_REV_MAP.get(prefix)
        if not expected_type:
            return False, {}, "인식할 수 없는 라이선스 유형 접두사입니다."

        is_rsa = (len(parts) == 4 and parts[1] == "RSA")
        
        if is_rsa:
            # ── 1. RSA-2048 비대칭키 검증 모드 ──────────────────────────
            _, _, sig_hex, p_b64 = parts

            # 패딩 복원
            p_pad = len(p_b64) % 4
            if p_pad: p_b64 += "=" * (4 - p_pad)

            try:
                payload_bytes = base64.urlsafe_b64decode(p_b64.encode("ascii"))
                payload = json.loads(payload_bytes.decode("utf-8"))
                sig_bytes = bytes.fromhex(sig_hex)
            except Exception:
                return False, {}, "라이선스 데이터가 손상되었거나 위변조되었습니다."

            # 순수 파이썬 제로 디펜던시 RSA-2048 PKCS#1 v1.5 with SHA-256 수학적 검증
            try:
                sig_int = int.from_bytes(sig_bytes, "big")
                decrypted_int = pow(sig_int, cls.RSA_PUBLIC_E, cls.RSA_PUBLIC_N)
                decrypted_bytes = decrypted_int.to_bytes(256, "big")

                sha256_prefix = bytes.fromhex("3031300d060960864801650304020105000420")
                expected_hash = hashlib.sha256(payload_bytes).digest()
                expected_payload = sha256_prefix + expected_hash

                is_sig_valid = decrypted_bytes.startswith(bytes.fromhex("0001")) and decrypted_bytes.endswith(expected_payload)
                if not is_sig_valid:
                    return False, {}, "RSA 디지털 서명 검증에 실패했습니다. (위변조된 라이선스 키)"
            except Exception as e:
                return False, {}, f"디지털 서명 검증 오류: {e}"

        else:
            # ── 2. 레거시 HMAC-SHA256 검증 모드 (하위 호환) ──────────────
            legacy_parts = raw_key.split("-", 2)
            if len(legacy_parts) != 3:
                return False, {}, "올바르지 않은 레거시 라이선스 키 형식입니다."
            prefix, sig_chunk, p_b64 = legacy_parts

            p_pad = len(p_b64) % 4
            if p_pad: p_b64 += "=" * (4 - p_pad)

            try:
                payload_json = base64.urlsafe_b64decode(p_b64.encode("ascii")).decode("utf-8")
                payload = json.loads(payload_json)
            except Exception:
                return False, {}, "라이선스 데이터가 손상되었거나 위변조되었습니다."

            expected_sig = hmac.new(cls.MASTER_SECRET, payload_json.encode("utf-8"), hashlib.sha256).hexdigest().upper()
            if not hmac.compare_digest(expected_sig[:8], sig_chunk):
                return False, {}, "라이선스 디지털 서명 검증에 실패했습니다. (위변조된 키)"

        # ── 공통: HWID 노드락 검증 ────────────────────────────────────────
        target_hwid = payload.get("hwid", "")
        if payload.get("type") not in (LicenseType.ENTERPRISE, LicenseType.GOVERNMENT):
            curr = current_hwid or cls.get_hwid()
            if target_hwid and target_hwid not in ("ALL", "ENTERPRISE", "GOVERNMENT") and target_hwid != curr:
                return False, {}, f"다른 PC용으로 발급된 라이선스입니다. (발급 HWID: {target_hwid})"

        # ── 공통: 만료일 검증 ────────────────────────────────────────────
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
        if cls._cached_status is not None:
            return cls._cached_status

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
            l_type = payload.get("type", LicenseType.PERSONAL)
            type_names = {
                LicenseType.PERSONAL: "개인용 라이선스 (Personal)",
                LicenseType.ENTERPRISE: "기업용 라이선스 (Enterprise / 공기업 포함)",
                LicenseType.EDUCATION: "교육용 라이선스 (Education)",
                LicenseType.GOVERNMENT: "관공서용 라이선스 (Government / 행정·지자체)",
                LicenseType.PERPETUAL: "정식 영구 라이선스 (Legacy)",
                LicenseType.SUBSCRIPTION_1M: "1개월 구독 라이선스 (Legacy)",
                LicenseType.SUBSCRIPTION_1Y: "1년 연간 라이선스 (Legacy)",
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

    @classmethod
    def can_use_custom_watermark(cls) -> bool:
        """기업용(공기업 포함), 교육용, 관공서용 라이선스 대상 커스텀 워터마크 권한 판별"""
        status = cls.check_license_status()
        if not status.get("is_licensed"):
            return False
        l_type = status.get("license_type", "")
        return l_type in (LicenseType.ENTERPRISE, LicenseType.EDUCATION, LicenseType.GOVERNMENT)


# ================================================================================
# [v1.4.0.Build.18] 하이브리드 라이선스 인증 엔진 (3-레이어 아키텍처)
# OnlineLicenseVerifier / HybridLicenseCheck / LicenseFileGenerator
# ================================================================================

class OnlineLicenseVerifier:
    """
    중앙 인증 서버 통신 + 로컬 캐시 토큰 관리 + 오프라인 .lic 파일 검증

    인증 레이어:
    1. 로컬 캐시 토큰 (유효기간 30일) → 즉시 실행
    2. 온라인 서버 인증 → 캐시 갱신
    3. 오프라인 유예 기간 (14일, 마지막 온라인 성공 기준)
    4. 폐쇄망 .lic 파일 (HMAC 서명 검증)
    """

    VERIFY_URL = "https://license.dragonrpa.co.kr/v1/verify"  # 플레이스홀더 — 서버 구축 후 교체
    CACHE_TOKEN_DAYS = 30           # 캐시 토큰 유효 기간 (일)
    GRACE_PERIOD_DAYS = 14          # 오프라인 유예 기간 (일)
    ONLINE_TIMEOUT_SEC = 5          # 서버 응답 타임아웃 (초)
    OFFLINE_LIC_FILENAME = "license.lic"

    REG_CACHE_SUBKEY = r"Software\DragonRPA\ManualStudio\License"
    REG_CACHE_VAL = "CacheToken"

    _cache_dir = Path(os.environ.get("APPDATA", ".")) / "DragonRPA" / "ManualStudio"

    # ── 내부 유틸 ─────────────────────────────────────────────────────────────

    @classmethod
    def _get_cache_file(cls) -> Path:
        cls._cache_dir.mkdir(parents=True, exist_ok=True)
        return cls._cache_dir / "auth_cache.bin"

    @classmethod
    def _sign_token(cls, data: dict) -> str:
        """dict → HMAC-SHA256 서명 (sig 필드 자신은 제외)"""
        payload_json = json.dumps(data, separators=(',', ':'), sort_keys=True)
        return hmac.new(LicenseEngine.MASTER_SECRET, payload_json.encode("utf-8"), hashlib.sha256).hexdigest().upper()

    # ── 캐시 토큰 저장 / 로드 ─────────────────────────────────────────────────

    @classmethod
    def save_cache_token(cls, token_dict: dict) -> bool:
        """암호화 캐시 토큰을 레지스트리(1순위) + 파일(2순위) 이중 저장"""
        try:
            sign_data = {k: v for k, v in token_dict.items() if k != "sig"}
            token_dict["sig"] = cls._sign_token(sign_data)
            token_b64 = base64.urlsafe_b64encode(
                json.dumps(token_dict, separators=(',', ':')).encode("utf-8")
            ).decode("ascii")

            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cls.REG_CACHE_SUBKEY) as key:
                    winreg.SetValueEx(key, cls.REG_CACHE_VAL, 0, winreg.REG_SZ, token_b64)
            except Exception:
                pass

            try:
                cls._get_cache_file().write_text(token_b64, encoding="utf-8")
            except Exception:
                pass

            return True
        except Exception:
            return False

    @classmethod
    def load_cache_token(cls) -> dict | None:
        """캐시 토큰 로드 → HMAC 무결성 검증 후 반환. 위변조/없음이면 None."""
        token_b64 = ""

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.REG_CACHE_SUBKEY, 0, winreg.KEY_READ) as key:
                token_b64, _ = winreg.QueryValueEx(key, cls.REG_CACHE_VAL)
        except Exception:
            pass

        if not token_b64:
            try:
                cache_file = cls._get_cache_file()
                if cache_file.exists():
                    token_b64 = cache_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        if not token_b64:
            return None

        try:
            missing = len(token_b64) % 4
            if missing:
                token_b64 += "=" * (4 - missing)
            token_dict = json.loads(base64.urlsafe_b64decode(token_b64.encode("ascii")).decode("utf-8"))
        except Exception:
            return None

        stored_sig = token_dict.get("sig", "")
        sign_data = {k: v for k, v in token_dict.items() if k != "sig"}
        if not hmac.compare_digest(stored_sig, cls._sign_token(sign_data)):
            return None  # 위변조 감지

        return token_dict

    # ── 유효성 판정 ───────────────────────────────────────────────────────────

    @classmethod
    def is_cache_valid(cls, token_dict: dict) -> bool:
        """캐시 토큰 30일 유효 기간 이내인지 확인"""
        if not token_dict:
            return False
        try:
            cache_exp = datetime.strptime(token_dict["cache_expires_at"], "%Y-%m-%d")
            return datetime.now() <= cache_exp.replace(hour=23, minute=59, second=59)
        except Exception:
            return False

    @classmethod
    def is_license_expired(cls, token_dict: dict) -> bool:
        """
        라이선스 자체 만료일 즉시 판정 — 유예 기간 없음.
        expiry == "NONE" 이면 영구 라이선스(False).
        """
        if not token_dict:
            return True
        expiry_str = token_dict.get("expiry", "NONE")
        if expiry_str == "NONE":
            return False
        try:
            exp_dt = datetime.strptime(expiry_str, "%Y-%m-%d")
            return datetime.now() > exp_dt.replace(hour=23, minute=59, second=59)
        except Exception:
            return True

    @classmethod
    def get_grace_remaining_days(cls, token_dict: dict) -> int:
        """
        마지막 온라인 인증 성공 시각 기준 오프라인 유예 잔여 일수.
        0 이하 → 유예 초과.
        """
        if not token_dict:
            return 0
        try:
            last_online = datetime.strptime(token_dict["last_online_at"], "%Y-%m-%d")
            elapsed = (datetime.now() - last_online).days
            return max(0, cls.GRACE_PERIOD_DAYS - elapsed)
        except Exception:
            return 0

    # ── 온라인 서버 인증 ──────────────────────────────────────────────────────

    @classmethod
    def verify_online(cls, serial_key: str, hwid: str) -> tuple:
        """
        중앙 서버 POST 인증.
        성공 시 내부적으로 캐시 토큰 자동 저장.
        반환: (success: bool, token_dict: dict, message: str)

        서버 요청 페이로드:
            {"serial_key": "...", "hwid": "...", "client_version": "1.4.0"}
        서버 응답 예시:
            {"status": "ok", "issued_to": "...", "license_type": "PERPETUAL", "expiry": "NONE"}
        """
        try:
            req_body = json.dumps({
                "serial_key": serial_key.strip(),
                "hwid": hwid.strip(),
                "client_version": "1.4.0",
            }).encode("utf-8")
            req = urllib.request.Request(
                cls.VERIFY_URL,
                data=req_body,
                headers={"Content-Type": "application/json", "User-Agent": "ManualStudio/1.4.0"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=cls.ONLINE_TIMEOUT_SEC) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError:
            return False, {}, "서버에 연결할 수 없습니다. (네트워크 오류)"
        except Exception as e:
            return False, {}, f"인증 서버 통신 오류: {e}"

        if resp_body.get("status") != "ok":
            return False, {}, resp_body.get("message", "서버 인증 거부")

        now_str = datetime.now().strftime("%Y-%m-%d")
        token_dict = {
            "serial_key": serial_key.strip(),
            "hwid": hwid.strip(),
            "issued_to": resp_body.get("issued_to", "Registered User"),
            "license_type": resp_body.get("license_type", "PERPETUAL"),
            "expiry": resp_body.get("expiry", "NONE"),
            "cached_at": now_str,
            "cache_expires_at": (datetime.now() + timedelta(days=cls.CACHE_TOKEN_DAYS)).strftime("%Y-%m-%d"),
            "last_online_at": now_str,
        }
        cls.save_cache_token(token_dict)
        return True, token_dict, "온라인 인증 성공"

    # ── 폐쇄망 .lic 파일 검증 ────────────────────────────────────────────────

    @classmethod
    def verify_offline_lic_file(cls, lic_path: str = None) -> tuple:
        """
        폐쇄망 오프라인 .lic 파일 HMAC 검증.
        탐색 순서: ① 지정 경로 ② 실행파일 디렉터리 ③ APPDATA ④ 현재 디렉터리

        반환: (success: bool, lic_data: dict, message: str)
        """
        search_paths = []
        if lic_path:
            search_paths.append(Path(lic_path))
        try:
            search_paths.append(Path(sys.executable).parent / cls.OFFLINE_LIC_FILENAME)
        except Exception:
            pass
        search_paths.append(cls._cache_dir / cls.OFFLINE_LIC_FILENAME)
        search_paths.append(Path(".") / cls.OFFLINE_LIC_FILENAME)

        lic_data = None
        found_path = None
        for p in search_paths:
            try:
                if p.exists():
                    lic_data = json.loads(p.read_text(encoding="utf-8"))
                    found_path = p
                    break
            except Exception:
                continue

        if not lic_data:
            return False, {}, ".lic 파일을 찾을 수 없습니다."

        # 서명 분리 후 검증
        stored_sig = lic_data.pop("sig", "")
        payload_json = json.dumps(lic_data, separators=(',', ':'), sort_keys=True)
        expected_sig = hmac.new(LicenseEngine.MASTER_SECRET, payload_json.encode("utf-8"), hashlib.sha256).hexdigest().upper()
        if not hmac.compare_digest(stored_sig, expected_sig):
            return False, {}, f".lic 파일이 위변조되었습니다. ({found_path})"

        # HWID 노드락 (ENTERPRISE / GOVERNMENT 제외)
        lic_type = lic_data.get("type", "")
        if lic_type not in (LicenseType.ENTERPRISE, LicenseType.GOVERNMENT):
            curr = LicenseEngine.get_hwid()
            if lic_data.get("hwid", "") != curr:
                return False, {}, f".lic 파일이 다른 PC용으로 발급되었습니다. (발급 HWID: {lic_data.get('hwid')})"

        # 만료일 즉시 판정 (유예 없음)
        expiry_str = lic_data.get("expiry", "NONE")
        if expiry_str != "NONE":
            try:
                exp_dt = datetime.strptime(expiry_str, "%Y-%m-%d")
                if datetime.now() > exp_dt.replace(hour=23, minute=59, second=59):
                    return False, {}, f".lic 라이선스 만료일({expiry_str})이 지났습니다."
            except Exception:
                return False, {}, ".lic 만료일 형식 오류"

        return True, lic_data, f"오프라인 .lic 인증 성공 ({found_path})"


class HybridLicenseCheck:
    """
    3-레이어 하이브리드 라이선스 인증 플로우 통합 실행기

    mode 반환값:
    - "cache"       : 로컬 캐시 토큰 유효 (0초 즉시 실행)
    - "online"      : 온라인 서버 인증 성공 (캐시 갱신)
    - "grace"       : 오프라인 유예 기간 이내 (경고 배너 표시 후 실행)
    - "offline_lic" : 오프라인 .lic 파일 인증 성공
    - "trial"       : 미등록 평가판
    - "expired"     : 라이선스 만료 (즉시 차단, 유예 없음)
    - "blocked"     : 유예 초과 / 인증 완전 실패
    """

    _TYPE_NAMES = {
        LicenseType.PERSONAL: "개인용 라이선스 (Personal)",
        LicenseType.ENTERPRISE: "기업용 라이선스 (Enterprise / 공기업 포함)",
        LicenseType.EDUCATION: "교육용 라이선스 (Education)",
        LicenseType.GOVERNMENT: "관공서용 라이선스 (Government / 행정·지자체)",
        LicenseType.PERPETUAL: "정식 영구 라이선스 (Legacy)",
        LicenseType.SUBSCRIPTION_1M: "1개월 구독 라이선스 (Legacy)",
        LicenseType.SUBSCRIPTION_1Y: "1년 연간 라이선스 (Legacy)",
        LicenseType.TRIAL_EXT_14D: "14일 평가 연장 라이선스",
    }

    @classmethod
    def run(cls, serial_key: str = None, async_refresh: bool = True) -> dict:
        """
        하이브리드 인증 실행. 비블로킹(async_refresh=True)이 기본.

        Returns:
            {
              "is_licensed": bool,
              "mode": str,
              "license_type": str,
              "issued_to": str,
              "expiry": str,
              "badge_text": str,
              "message": str,
              "grace_days_left": int,
            }
        """
        v = OnlineLicenseVerifier

        # 시리얼 키 확보
        if not serial_key:
            serial_key = LicenseEngine.load_saved_license()
        if not serial_key:
            return cls._trial("미등록 평가판 모드입니다.")

        # ── 1단계: 로컬 캐시 토큰 ──────────────────────────────────────────
        token = v.load_cache_token()
        if token:
            if v.is_license_expired(token):          # 만료 즉시 차단
                return cls._expired(token.get("expiry", ""))
            if v.is_cache_valid(token):               # 캐시 유효 → 즉시 실행
                if async_refresh:
                    cls._schedule_bg_refresh(serial_key, token)
                return cls._ok("cache", token, "로컬 캐시 인증 (즉시 실행)")

        # ── 로컬 HMAC 시리얼 키 선행 검증 ──────────────────────────────────
        hwid = LicenseEngine.get_hwid()
        local_valid, local_payload, local_msg = LicenseEngine.verify_license_key(serial_key, hwid)
        if not local_valid:
            return cls._blocked(local_msg)

        # 라이선스 자체 만료 즉시 판정
        expiry_str = local_payload.get("expiry", "NONE")
        if expiry_str != "NONE":
            try:
                if datetime.now() > datetime.strptime(expiry_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59):
                    return cls._expired(expiry_str)
            except Exception:
                pass

        # ── 2단계: 온라인 서버 인증 ─────────────────────────────────────────
        ok, new_token, msg = v.verify_online(serial_key, hwid)
        if ok:
            return cls._ok("online", new_token, "온라인 서버 인증 성공")

        # ── 3단계: 오프라인 유예 기간 (14일) ────────────────────────────────
        if token:
            grace = v.get_grace_remaining_days(token)
            if grace > 0:
                return cls._grace(token, grace)

        # ── 4단계: 오프라인 .lic 파일 ─────────────────────────────────────────
        lic_ok, lic_data, lic_msg = v.verify_offline_lic_file()
        if lic_ok:
            return {
                "is_licensed": True,
                "mode": "offline_lic",
                "license_type": lic_data.get("type", LicenseType.ENTERPRISE),
                "issued_to": lic_data.get("issued_to", "Offline User"),
                "expiry": lic_data.get("expiry", "NONE"),
                "badge_text": "오프라인 라이선스",
                "message": lic_msg,
                "grace_days_left": 0,
            }

        # ── 전 레이어 실패 ────────────────────────────────────────────────────
        return cls._blocked(f"인증 실패: 서버 연결 불가, 유예 기간 초과, .lic 파일 없음. ({msg})")

    # ── 백그라운드 캐시 갱신 ──────────────────────────────────────────────────

    @classmethod
    def _schedule_bg_refresh(cls, serial_key: str, token: dict):
        """캐시 만료 7일 전부터 백그라운드 스레드로 조용히 서버 갱신"""
        try:
            cache_exp = datetime.strptime(token.get("cache_expires_at", "2000-01-01"), "%Y-%m-%d")
            if (cache_exp - datetime.now()).days > 7:
                return
        except Exception:
            pass

        def _refresh():
            OnlineLicenseVerifier.verify_online(serial_key, LicenseEngine.get_hwid())

        threading.Thread(target=_refresh, daemon=True, name="LicenseRefreshBG").start()

    # ── 결과 빌더 헬퍼 ───────────────────────────────────────────────────────

    @classmethod
    def _ok(cls, mode: str, token: dict, message: str) -> dict:
        l_type = token.get("license_type", LicenseType.PERPETUAL)
        return {
            "is_licensed": True,
            "mode": mode,
            "license_type": l_type,
            "issued_to": token.get("issued_to", "Registered User"),
            "expiry": token.get("expiry", "NONE"),
            "badge_text": cls._TYPE_NAMES.get(l_type, "정식 라이선스"),
            "message": message,
            "grace_days_left": 0,
        }

    @classmethod
    def _grace(cls, token: dict, grace_days: int) -> dict:
        return {
            "is_licensed": True,
            "mode": "grace",
            "license_type": token.get("license_type", LicenseType.PERPETUAL),
            "issued_to": token.get("issued_to", "Registered User"),
            "expiry": token.get("expiry", "NONE"),
            "badge_text": f"오프라인 유예 ({grace_days}일 남음)",
            "message": f"서버 연결 불가 — 오프라인 유예 {grace_days}일 남음. 인터넷 연결 시 자동 갱신됩니다.",
            "grace_days_left": grace_days,
        }

    @classmethod
    def _expired(cls, expiry_str: str) -> dict:
        return {
            "is_licensed": False,
            "mode": "expired",
            "license_type": "EXPIRED",
            "issued_to": "",
            "expiry": expiry_str,
            "badge_text": "라이선스 만료",
            "message": f"라이선스 유효 기간({expiry_str})이 만료되었습니다. 갱신 후 사용하십시오.",
            "grace_days_left": 0,
        }

    @classmethod
    def _blocked(cls, message: str) -> dict:
        return {
            "is_licensed": False,
            "mode": "blocked",
            "license_type": "INVALID",
            "issued_to": "",
            "expiry": "",
            "badge_text": "인증 실패",
            "message": message,
            "grace_days_left": 0,
        }

    @classmethod
    def _trial(cls, message: str) -> dict:
        return {
            "is_licensed": False,
            "mode": "trial",
            "license_type": "TRIAL",
            "issued_to": "Evaluation User",
            "expiry": "",
            "badge_text": "평가판 (Trial)",
            "message": message,
            "grace_days_left": 0,
        }


class LicenseFileGenerator:
    """
    폐쇄망 오프라인 .lic 파일 생성기 (관리자 / 서버 전용 도구)

    고객 PC의 HWID를 받아 암호화 서명된 .lic 파일을 생성.
    생성된 파일을 USB로 복사하여 폐쇄망 PC에 배포.

    .lic 파일 탐색 위치 (OnlineLicenseVerifier.verify_offline_lic_file 참조):
    ① 실행파일 디렉터리  ② %APPDATA%\\DragonRPA\\ManualStudio\\  ③ 현재 디렉터리
    """

    @classmethod
    def generate_offline_lic(
        cls,
        hwid: str,
        issued_to: str,
        expiry: str = "NONE",
        license_type: str = LicenseType.ENTERPRISE,
        max_seats: int = 1,
        output_path: str = None,
    ) -> tuple:
        """
        오프라인 .lic 파일 생성.

        Args:
            hwid         : 대상 PC HWID (DRPA-XXXX-XXXX-XXXX). ENTERPRISE/GOVERNMENT는 "ENTERPRISE" 또는 "GOVERNMENT" 로 통일.
            issued_to    : 발급 대상 회사명
            expiry       : 만료일 "YYYY-MM-DD" 또는 "NONE" (영구)
            license_type : LicenseType 상수
            max_seats    : 허용 시트 수
            output_path  : 저장 경로 (None → 현재 디렉터리 license.lic)

        Returns:
            (success: bool, file_path: str, message: str)
        """
        now_str = datetime.now().strftime("%Y-%m-%d")
        clean_hwid = (
            "ENTERPRISE"
            if license_type in (LicenseType.ENTERPRISE, LicenseType.GOVERNMENT)
            else hwid.strip().upper()
        )

        lic_data = {
            "version": "1.0",
            "type": license_type,
            "hwid": clean_hwid,
            "issued_to": issued_to.strip().replace(":", "_").replace("|", "_"),
            "expiry": expiry,
            "seats": max_seats,
            "issued_at": now_str,
        }

        payload_json = json.dumps(lic_data, separators=(',', ':'), sort_keys=True)
        sig = hmac.new(LicenseEngine.MASTER_SECRET, payload_json.encode("utf-8"), hashlib.sha256).hexdigest().upper()
        lic_data["sig"] = sig

        if not output_path:
            output_path = OnlineLicenseVerifier.OFFLINE_LIC_FILENAME

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(lic_data, f, ensure_ascii=False, indent=2)
            return True, output_path, f"오프라인 .lic 파일 생성 완료: {output_path}"
        except Exception as e:
            return False, "", f".lic 파일 저장 실패: {e}"
