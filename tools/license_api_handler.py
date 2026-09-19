"""
================================================================================
(주)드래곤알피에이 매뉴얼 스튜디오 판매 사이트 연동 라이선스 자동 발급 API 엔진
Manual Studio Sales Website License Issuance Webhook & API Handler
================================================================================
쇼핑몰(자사몰, 스마트스토어, 아임웹, 포트원/토스 결제 웹훅 등)에서
결제 완료 시 호출하여 정식 RSA-2048 비대칭키 라이선스를 즉시 발급·반환합니다.
"""

import os
import sys
import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta

# 상위 디렉토리 임포트 지원
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from license_engine import LicenseEngine, LicenseType

PRIVATE_KEY_PATH = os.path.join(os.path.dirname(__file__), "secret_private_key.pem")
ISSUED_LOG_PATH = os.path.join(os.path.dirname(__file__), "issued_licenses.json")


def load_private_key_bytes() -> bytes:
    """서버에 보관된 RSA 개인키 로드"""
    if os.path.exists(PRIVATE_KEY_PATH):
        with open(PRIVATE_KEY_PATH, "rb") as f:
            return f.read()
    # 환경변수에 PRIVATE_KEY_PEM이 등록되어 있는 경우 (서버리스 환경)
    env_pem = os.environ.get("DRPA_LICENSE_PRIVATE_KEY")
    if env_pem:
        return env_pem.encode("utf-8")
    return b""


def issue_license_for_order(
    license_type: str = LicenseType.SUBSCRIPTION_1Y,
    customer_name: str = "고객사",
    hwid: str = "ENTERPRISE",
    expiry_date: str = "NONE",
    seats: int = 1,
    order_id: str = ""
) -> dict:
    """
    판매 사이트/웹훅 연동 핵심 함수 (어디서나 호출 가능)
    
    :param license_type: PERPETUAL, SUB_1M, SUB_1Y, ENTERPRISE, AIR_GAPPED, TRIAL_14D
    :param customer_name: 주문자명 또는 회사명
    :param hwid: 클라이언트 HWID (지정 없거나 엔터프라이즈면 ENTERPRISE)
    :param expiry_date: 만료일 (YYYY-MM-DD 또는 NONE)
    :param seats: 허용 PC 대수
    :param order_id: 주문 고유번호
    :return: 발급 결과 딕셔너리
    """
    now = datetime.now()
    clean_type = license_type.upper().strip()

    # 만료일 자동 계산
    clean_expiry = expiry_date
    if clean_expiry in ("NONE", "", None):
        if clean_type in (LicenseType.SUBSCRIPTION_1M, "SUB_1M", "1M"):
            clean_type = LicenseType.SUBSCRIPTION_1M
            clean_expiry = (now + timedelta(days=30)).strftime("%Y-%m-%d")
        elif clean_type in (LicenseType.SUBSCRIPTION_1Y, "SUB_1Y", "1Y"):
            clean_type = LicenseType.SUBSCRIPTION_1Y
            clean_expiry = (now + timedelta(days=365)).strftime("%Y-%m-%d")
        elif clean_type in (LicenseType.TRIAL_EXT_14D, "TRIAL_14D"):
            clean_type = LicenseType.TRIAL_EXT_14D
            clean_expiry = (now + timedelta(days=14)).strftime("%Y-%m-%d")
        else:
            clean_type = LicenseType.PERPETUAL
            clean_expiry = "NONE"

    pem_bytes = load_private_key_bytes()
    serial_key = LicenseEngine.generate_license_key(
        license_type=clean_type,
        hwid=hwid,
        issued_to=customer_name,
        expiry_date=clean_expiry,
        max_seats=seats,
        private_key_pem=pem_bytes
    )

    record = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "order_id": order_id,
        "license_type": clean_type,
        "issued_to": customer_name,
        "hwid": hwid,
        "expiry": clean_expiry,
        "seats": seats,
        "serial_key": serial_key
    }

    # 발급 로그 기록
    try:
        records = []
        if os.path.exists(ISSUED_LOG_PATH):
            with open(ISSUED_LOG_PATH, "r", encoding="utf-8") as f:
                records = json.load(f)
        records.append(record)
        with open(ISSUED_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to write license log: {e}")

    return {
        "status": "success",
        "order_id": order_id,
        "serial_key": serial_key,
        "license_type": clean_type,
        "issued_to": customer_name,
        "expiry": clean_expiry,
        "seats": seats,
        "issued_at": now.strftime("%Y-%m-%d")
    }


class LicenseApiRequestHandler(BaseHTTPRequestHandler):
    """판매 사이트 결제 웹훅 수신용 경량 HTTP 서버 핸들러"""

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-KEY")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        """서버 상태 확인 (Health check)"""
        self._set_headers(200)
        resp = {
            "service": "DragonRPA Manual Studio License API",
            "version": "1.0-RSA2048",
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))

    def do_POST(self):
        """
        웹훅 결제 완료 수신 엔드포인트: /api/v1/issue-license
        요청 JSON 예시:
        {
            "order_id": "ORD-20260919-001",
            "license_type": "SUB_1Y",
            "customer_name": "홍길동 / (주)한라렌탈",
            "customer_email": "user@example.com",
            "hwid": "DRPA-XXXX-XXXX-XXXX",
            "seats": 1
        }
        """
        if self.path not in ("/api/v1/issue-license", "/issue"):
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))

            order_id = payload.get("order_id", f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            l_type = payload.get("license_type", LicenseType.SUBSCRIPTION_1Y)
            name = payload.get("customer_name", "Valued Customer")
            hwid = payload.get("hwid", "ENTERPRISE")
            expiry = payload.get("expiry_date", "NONE")
            seats = int(payload.get("seats", 1))

            result = issue_license_for_order(
                license_type=l_type,
                customer_name=name,
                hwid=hwid,
                expiry_date=expiry,
                seats=seats,
                order_id=order_id
            )

            self._set_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))

        except Exception as e:
            self._set_headers(500)
            err_resp = {"status": "error", "message": str(e)}
            self.wfile.write(json.dumps(err_resp, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass


def run_api_server(port: int = 19860):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, LicenseApiRequestHandler)
    print("=" * 65)
    print(" [DragonRPA] Manual Studio License API Server Running")
    print("=" * 65)
    print(f" Port    : {port}")
    print(f" Endpoint: http://localhost:{port}/api/v1/issue-license (POST)")
    print(" Health  : http://localhost:{port}/ (GET)")
    print(" Press Ctrl+C to terminate server.")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] License API Server shutting down...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DragonRPA License Webhook API Engine")
    parser.add_argument("--server", action="store_true", help="HTTP API 서버 실행")
    parser.add_argument("--port", type=int, default=19860, help="HTTP 서버 포트 (기본: 19860)")
    parser.add_argument("--issue", action="store_true", help="단일 주문 테스트 발급")
    parser.add_argument("--type", default="SUB_1Y", help="라이선스 유형")
    parser.add_argument("--name", default="테스트 고객사", help="고객사명")
    parser.add_argument("--hwid", default="ENTERPRISE", help="HWID (기본: ENTERPRISE)")
    parser.add_argument("--order-id", default="TEST-001", help="주문 번호")
    args = parser.parse_args()

    if args.server:
        run_api_server(args.port)
    elif args.issue:
        res = issue_license_for_order(
            license_type=args.type,
            customer_name=args.name,
            hwid=args.hwid,
            order_id=args.order_id
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        res = issue_license_for_order(
            license_type="SUB_1Y",
            customer_name="네이버스마트스토어 주문자",
            hwid="DRPA-TEST-1234-5678",
            order_id="SMARTSTORE-998811"
        )
        print("API 모듈이 정상 준비되었습니다. 테스트 발급 결과:")
        print(json.dumps(res, ensure_ascii=False, indent=2))
