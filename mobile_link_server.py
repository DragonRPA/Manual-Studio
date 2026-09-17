"""
================================================================================
DragonRPA Manual Studio - Mobile Link Server Engine
================================================================================
스마트폰/태블릿에서 작성된 플로우차트 JSON 또는 손그림 사진을 동일 Wi-Fi 로컬
네트워크를 통해 PC 매뉴얼 스튜디오로 직접 전송받는 경량 인메모리 P2P 서버.
외부 서버에 데이터를 남기지 않는 무저장(Zero-Disk) 원칙을 준수합니다.
================================================================================
"""

import os
import sys
import json
import time
import socket
import random
import io
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QPixmap, QImage


def get_local_ip() -> str:
    """활성 로컬 Wi-Fi/LAN IP 주소 자동 탐지"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # 외부로 실제 패킷을 보내지 않고 로컬 라우팅 인터페이스 IP 획득
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class MobileRequestHandler(BaseHTTPRequestHandler):
    server_instance = None  # MobileLinkServer 참조

    def _set_cors_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-PIN")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in ("", "/", "/index.html"):
            # 모바일 웹 앱 HTML 서빙 (APK 미설치자도 QR 스캔만으로 즉시 브라우저에서 사용 가능)
            html_content = self.server_instance.get_mobile_web_app_html()
            self._set_cors_headers(200, "text/html; charset=utf-8")
            self.wfile.write(html_content.encode("utf-8"))
            return

        if path == "/api/info":
            info = {
                "status": "ok",
                "app": "ManualStudio",
                "name": socket.gethostname(),
                "pin": self.server_instance.session_pin,
                "port": self.server_instance.port
            }
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(info, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/qr":
            pix = self.server_instance.get_qr_png_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(pix)
            return

        self._set_cors_headers(404)
        self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/upload":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"status": "error", "message": "데이터가 비어 있습니다."}).encode("utf-8"))
                return

            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception as e:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"status": "error", "message": f"잘못된 JSON 형식: {e}"}).encode("utf-8"))
                return

            # PIN 검증 (헤더 또는 바디)
            req_pin = self.headers.get("X-PIN") or payload.get("pin")
            if req_pin and req_pin.replace("-", "").strip() != self.server_instance.session_pin.replace("-", "").strip():
                self._set_cors_headers(401)
                self.wfile.write(json.dumps({"status": "error", "message": "인증 PIN 번호가 일치하지 않습니다."}).encode("utf-8"))
                return

            # Qt 메인 스레드로 안전하게 페이로드 전달
            self.server_instance.sig_payload_received.emit(payload)

            self._set_cors_headers(200)
            self.wfile.write(json.dumps({
                "status": "ok",
                "message": "매뉴얼 스튜디오 캔버스에 성공적으로 전송되었습니다."
            }, ensure_ascii=False).encode("utf-8"))
            return

        self._set_cors_headers(404)
        self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # 불필요한 콘솔 로그 억제
        pass


class MobileLinkServer(QObject):
    sig_payload_received = Signal(dict)
    sig_server_started = Signal(str, int, str)  # ip, port, pin
    sig_server_stopped = Signal()

    def __init__(self, port=19850, parent=None):
        super().__init__(parent)
        self.port = port
        self.local_ip = get_local_ip()
        self.session_pin = f"{random.randint(100, 999)}-{random.randint(100, 999)}"
        self.httpd = None
        self.server_thread = None
        self.is_running = False

    def start_server(self):
        if self.is_running:
            return True

        self.local_ip = get_local_ip()
        for attempt_port in range(self.port, self.port + 10):
            try:
                handler = MobileRequestHandler
                handler.server_instance = self
                self.httpd = HTTPServer(("0.0.0.0", attempt_port), handler)
                self.port = attempt_port
                break
            except OSError:
                continue

        if not self.httpd:
            return False

        self.is_running = True
        self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()
        self.sig_server_started.emit(self.local_ip, self.port, self.session_pin)
        return True

    def stop_server(self):
        if self.httpd and self.is_running:
            self.is_running = False
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
            self.sig_server_stopped.emit()

    def get_connection_url(self) -> str:
        return f"http://{self.local_ip}:{self.port}/?pin={self.session_pin}"

    def get_qr_png_bytes(self) -> bytes:
        import qrcode
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(self.get_connection_url())
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E293B", back_color="#FFFFFF")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def get_qr_pixmap(self) -> QPixmap:
        raw_bytes = self.get_qr_png_bytes()
        qimg = QImage.fromData(raw_bytes)
        return QPixmap.fromImage(qimg)

    def get_mobile_web_app_html(self) -> str:
        """스마트폰 카메라로 QR 스캔 시 즉시 실행되는 모바일 웹 터치 스튜디오 (APK 미설치 환경 완벽 지원)"""
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>매뉴얼 스튜디오 모바일 (Manual Studio Mobile)</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; -webkit-user-select: none; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0F172A; color: #F8FAFC; height: 100vh; display: flex; flex-direction: column; overflow: hidden; padding-bottom: env(safe-area-inset-bottom, 0); }}
header {{ background: #1E293B; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #334155; }}
header h1 {{ font-size: 14px; font-weight: 700; color: #38BDF8; display: flex; align-items: center; gap: 4px; }}
header .actions {{ display: flex; gap: 6px; }}
.btn {{ border: none; border-radius: 5px; padding: 5px 10px; font-size: 11px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 3px; }}
.btn-primary {{ background: #2563EB; color: #FFFFFF; }}
.btn-primary:active {{ background: #1D4ED8; }}
.btn-secondary {{ background: #334155; color: #E2E8F0; }}
.btn-camera {{ background: #059669; color: #FFFFFF; }}
#toolbar {{ background: #1E293B; padding: 6px 8px; display: flex; gap: 5px; overflow-x: auto; border-bottom: 1px solid #334155; }}
.tool-btn {{ background: #334155; color: #E2E8F0; border: 1px solid #475569; border-radius: 4px; padding: 4px 8px; font-size: 10px; white-space: nowrap; }}
.tool-btn.active {{ background: #2563EB; border-color: #60A5FA; color: #FFFFFF; }}
#canvas-container {{ flex: 1; position: relative; background: #0B1120; overflow: hidden; touch-action: none; }}
.node {{ position: absolute; min-width: 66px; min-height: 30px; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; cursor: move; border: 1.5px solid #2563EB; background: #EFF6FF; color: #0F172A; padding: 2px 4px; text-align: center; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }}
.node.terminal {{ border-radius: 15px; border-color: #059669; background: #ECFDF5; }}
.node.decision {{ clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); border: none; background: #FFFBEB; color: #D97706; outline: 1.5px solid #D97706; outline-offset: -1.5px; }}
.node.database {{ border-radius: 3px; border-color: #7C3AED; background: #FAF5FF; }}
.node.io {{ transform: skew(-12deg); border-color: #16A34A; background: #F0FDF4; }}
.node.document {{ clip-path: polygon(0% 0%, 100% 0%, 100% 85%, 75% 100%, 25% 75%, 0% 90%); border: none; background: #EEF2FF; color: #4F46E5; outline: 1.5px solid #4F46E5; outline-offset: -1.5px; }}
.port {{ position: absolute; width: 6px; height: 6px; border-radius: 50%; background: #3B82F6; border: 1px solid #FFFFFF; }}
.port.top {{ top: -3px; left: calc(50% - 3px); }}
.port.bottom {{ bottom: -3px; left: calc(50% - 3px); }}
.port.left {{ left: -3px; top: calc(50% - 3px); }}
.port.right {{ right: -3px; top: calc(50% - 3px); }}
#toast {{ position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(15,23,42,0.95); border: 1px solid #38BDF8; color: #FFFFFF; padding: 8px 16px; border-radius: 16px; font-size: 12px; z-index: 1000; opacity: 0; transition: opacity 0.3s; pointer-events: none; }}
#photo-input {{ display: none; }}
</style>
</head>
<body>
<header>
  <h1>매뉴얼 스튜디오 모바일</h1>
  <div class="actions">
    <button class="btn btn-camera" onclick="document.getElementById('photo-input').click()">📷 사진</button>
    <button class="btn btn-secondary" onclick="autoAlign()">⚡ 정렬</button>
    <button class="btn btn-primary" onclick="sendToPc()">💻 PC 전송</button>
  </div>
</header>
<div id="toolbar">
  <button class="tool-btn" onclick="addNode('terminal', '시작/종료')">🟢 시작/종료</button>
  <button class="tool-btn" onclick="addNode('process', '일반 작업')">🟦 일반작업</button>
  <button class="tool-btn" onclick="addNode('decision', '조건 분기')">🔶 조건분기</button>
  <button class="tool-btn" onclick="addNode('io', '데이터 입출력')">🟩 입출력</button>
  <button class="tool-btn" onclick="addNode('database', '데이터베이스')">🟪 DB</button>
  <button class="tool-btn" onclick="addNode('document', '문서 서식')">📄 문서</button>
  <button class="tool-btn" onclick="clearCanvas()">🗑️ 비우기</button>
</div>
<div id="canvas-container"></div>
<input type="file" id="photo-input" accept="image/*" capture="environment" onchange="handlePhotoUpload(this)">
<div id="toast"></div>

<script>
const PIN = "{self.session_pin}";
let nodes = [];
let nextId = 1;
const container = document.getElementById('canvas-container');

function showToast(msg) {{
  const t = document.getElementById('toast');
  t.innerText = msg;
  t.style.opacity = '1';
  setTimeout(() => t.style.opacity = '0', 2200);
}}

function addNode(type, text, x, y) {{
  const id = 'node_' + (nextId++);
  const cx = x || (container.clientWidth / 2 - 32 + (nodes.length % 5) * 12);
  const cy = y || (40 + nodes.length * 36);
  const node = {{ id, type, text, x: Math.max(10, cx), y: Math.max(10, cy), w: 65, h: 28 }};
  nodes.push(node);
  renderNode(node);
  saveLocal();
}}

function renderNode(node) {{
  const el = document.createElement('div');
  el.id = node.id;
  el.className = 'node ' + node.type;
  el.innerText = node.text;
  el.style.left = node.x + 'px';
  el.style.top = node.y + 'px';
  
  // 터치 드래그 이동
  let startX = 0, startY = 0, initX = 0, initY = 0;
  el.addEventListener('touchstart', (e) => {{
    const t = e.touches[0];
    startX = t.clientX;
    startY = t.clientY;
    initX = node.x;
    initY = node.y;
    e.stopPropagation();
  }});
  el.addEventListener('touchmove', (e) => {{
    const t = e.touches[0];
    node.x = initX + (t.clientX - startX);
    node.y = initY + (t.clientY - startY);
    el.style.left = node.x + 'px';
    el.style.top = node.y + 'px';
    e.preventDefault();
  }});
  el.addEventListener('touchend', () => {{ saveLocal(); }});
  
  // 탭하여 텍스트 수정
  el.addEventListener('dblclick', () => {{
    const newText = prompt('노드 텍스트 입력:', node.text);
    if (newText && newText.trim()) {{
      node.text = newText.trim();
      el.innerText = node.text;
      saveLocal();
    }}
  }});
  
  container.appendChild(el);
}}

let currentDirection = 'TD';
function autoAlign() {{
  if (nodes.length === 0) return;
  currentDirection = (currentDirection === 'TD') ? 'LR' : 'TD';
  const startX = 30, startY = 30;
  const xGap = (currentDirection === 'TD') ? 75 : 85;
  const yGap = (currentDirection === 'TD') ? 42 : 36;
  
  nodes.forEach((n, idx) => {{
    if (currentDirection === 'TD') {{
      n.x = startX;
      n.y = startY + idx * yGap;
    }} else {{
      n.x = startX + idx * xGap;
      n.y = startY;
    }}
    const el = document.getElementById(n.id);
    if (el) {{
      el.style.left = n.x + 'px';
      el.style.top = n.y + 'px';
    }}
  }});
  saveLocal();
  showToast('자동정렬 완료 (' + (currentDirection === 'TD' ? '상하 TD' : '좌우 LR') + ')');
}}

function clearCanvas() {{
  if (confirm('캔버스의 모든 노드를 삭제하시겠습니까?')) {{
    nodes = [];
    container.innerHTML = '';
    saveLocal();
  }}
}}

function saveLocal() {{
  try {{
    localStorage.setItem('ms_mobile_nodes', JSON.stringify(nodes));
  }} catch(e) {{}}
}}

function loadLocal() {{
  try {{
    const saved = localStorage.getItem('ms_mobile_nodes');
    if (saved) {{
      nodes = JSON.parse(saved);
      nodes.forEach(renderNode);
    }} else {{
      addNode('terminal', '시작');
      addNode('process', '작업 진행');
      addNode('decision', '정상 확인?');
      addNode('terminal', '완료');
      autoAlign();
    }}
  }} catch(e) {{}}
}}

function sendToPc() {{
  if (nodes.length === 0) {{
    alert('전송할 플로우차트 노드가 없습니다.');
    return;
  }}
  
  const payload = {{
    pin: PIN,
    type: 'flowchart',
    direction: currentDirection,
    data: {{
      nodes: nodes.map(n => ({{
        id: n.id,
        text: n.text,
        shape: n.type,
        x: n.x,
        y: n.y,
        w: n.w,
        h: n.h
      }})),
      items: nodes.map((n, idx) => ({{
        type: 'FlowchartNodeItem',
        text: n.text,
        x: n.x,
        y: n.y,
        w: 75,
        h: 32,
        shape_type: n.type,
        style: {{
          bg_color: n.type === 'terminal' ? '#ECFDF5' : (n.type === 'decision' ? '#FFFBEB' : (n.type === 'database' ? '#FAF5FF' : '#EFF6FF')),
          border_color: n.type === 'terminal' ? '#059669' : (n.type === 'decision' ? '#D97706' : (n.type === 'database' ? '#7C3AED' : '#2563EB')),
          border_width: 1.5,
          text_color: '#1E293B',
          font_size: 7,
          font_bold: true
        }}
      }}))
    }}
  }};
  
  fetch('/api/upload', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json', 'X-PIN': PIN }},
    body: JSON.stringify(payload)
  }})
  .then(res => res.json())
  .then(data => {{
    if (data.status === 'ok') {{
      showToast('🎉 PC 캔버스에 전송 성공!');
    }} else {{
      alert('전송 실패: ' + (data.message || '오류 발생'));
    }}
  }})
  .catch(err => {{
    alert('PC 연결 실패: ' + err.message);
  }});
}}

function handlePhotoUpload(input) {{
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  const reader = new FileReader();
  reader.onload = function(e) {{
    const base64Data = e.target.result;
    showToast('사진 업로드 중...');
    
    const payload = {{
      pin: PIN,
      type: 'image',
      title: '모바일 손그림 사진 (' + new Date().toLocaleTimeString() + ')',
      image_base64: base64Data
    }};
    
    fetch('/api/upload', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json', 'X-PIN': PIN }},
      body: JSON.stringify(payload)
    }})
    .then(res => res.json())
    .then(data => {{
      if (data.status === 'ok') {{
        showToast('📷 손그림 사진 PC 전송 성공!');
      }} else {{
        alert('전송 실패: ' + data.message);
      }}
    }})
    .catch(err => alert('전송 오류: ' + err.message));
  }};
  reader.readAsDataURL(file);
}}

window.onload = loadLocal;
</script>
</body>
</html>
"""
