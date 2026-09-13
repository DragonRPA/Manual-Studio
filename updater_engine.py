"""
================================================================================
(주)드래곤알피에이 매뉴얼 스튜디오 스마트 자동 업데이트(Smart Auto-Updater) 엔진
Smart Auto-Updater & Remote Version Audit Engine for Manual Studio
================================================================================
"""

import os
import sys
import re
import json
import tempfile
import subprocess
import urllib.request
import urllib.error

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal as pyqtSignal, QTimer, QSize, QUrl
from PySide6.QtGui import QIcon, QFont, QColor, QDesktopServices

from dragon_rpa_ci_data import get_dragon_rpa_ci_pixmap
from i18n_manager import tr

PRIMARY_VERSION_URL = "https://raw.githubusercontent.com/DragonRPA/Manual-Studio/main/version.json"
FALLBACK_GITHUB_API = "https://api.github.com/repos/DragonRPA/Manual-Studio/releases/latest"
DEFAULT_RELEASE_PAGE = "https://github.com/DragonRPA/Manual-Studio/releases"


class VersionComparator:
    """3~4단계 시맨틱 버전(vX.Y.Z 또는 vX.Y.Z.Build.N) 정밀 크기 비교기"""

    @staticmethod
    def parse_version(ver_str: str) -> tuple:
        if not ver_str:
            return (0, 0, 0, 0)
        s = str(ver_str).strip().lstrip("vV")
        # Build 분리 (e.g. 1.4.0.Build.1 또는 1.4.0-build.1)
        s = re.sub(r'[-_.]?[Bb]uild[-_.]?', '.', s)
        parts = []
        for token in s.split("."):
            m = re.match(r'(\d+)', token)
            if m:
                parts.append(int(m.group(1)))
            else:
                parts.append(0)
        while len(parts) < 4:
            parts.append(0)
        return tuple(parts[:4])

    @classmethod
    def is_newer(cls, remote_ver: str, local_ver: str) -> bool:
        return cls.parse_version(remote_ver) > cls.parse_version(local_ver)


class UpdateCheckerThread(QThread):
    """원격 서버 버전 백그라운드 비동기 조회 스레드"""
    sig_update_available = pyqtSignal(dict)   # {version, release_date, release_title, release_notes, download_url, force_update}
    sig_up_to_date = pyqtSignal(str)          # current_version
    sig_check_failed = pyqtSignal(str)        # error_message

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version

    def run(self):
        meta = self._fetch_version_metadata()
        if not meta:
            self.sig_check_failed.emit("원격 업데이트 서버와 통신할 수 없습니다.")
            return

        remote_ver = meta.get("version", "")
        if VersionComparator.is_newer(remote_ver, self.current_version):
            self.sig_update_available.emit(meta)
        else:
            self.sig_up_to_date.emit(self.current_version)

    def _fetch_version_metadata(self) -> dict:
        headers = {"User-Agent": "DragonRPA-ManualStudio-Updater/1.5"}

        # 1. 고속 CDN raw.githubusercontent.com version.json 우선 조회 (Rate-limit 없음)
        try:
            req = urllib.request.Request(PRIMARY_VERSION_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    raw_data = resp.read().decode("utf-8")
                    data = json.loads(raw_data)
                    if "release_page_url" not in data:
                        data["release_page_url"] = DEFAULT_RELEASE_PAGE
                    return data
        except Exception:
            pass

        # 2. GitHub Releases API 폴백 조회
        try:
            req = urllib.request.Request(FALLBACK_GITHUB_API, headers=headers)
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    tag_name = data.get("tag_name", "").lstrip("vV")
                    dl_url = ""
                    for asset in data.get("assets", []):
                        if asset.get("name", "").endswith(".exe"):
                            dl_url = asset.get("browser_download_url", "")
                            break
                    return {
                        "version": tag_name,
                        "release_date": data.get("published_at", "")[:10],
                        "release_title": data.get("name", f"Manual Studio v{tag_name}"),
                        "release_notes": data.get("body", ""),
                        "download_url": dl_url,
                        "release_page_url": data.get("html_url", DEFAULT_RELEASE_PAGE),
                        "force_update": False
                    }
        except Exception:
            pass

        return None


class UpdateDownloadThread(QThread):
    """최신 바이너리 청크 스트림 백그라운드 다운로드 스레드"""
    sig_progress = pyqtSignal(int, int)          # bytes_downloaded, total_bytes
    sig_download_completed = pyqtSignal(str)     # downloaded_file_path
    sig_download_failed = pyqtSignal(str)        # error_message

    def __init__(self, download_url: str, dest_path: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.dest_path = dest_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if not self.download_url:
            self.sig_download_failed.emit("다운로드 URL이 유효하지 않습니다.")
            return

        headers = {"User-Agent": "DragonRPA-ManualStudio-Updater/1.5"}
        try:
            req = urllib.request.Request(self.download_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                total_length = resp.headers.get("Content-Length")
                total_bytes = int(total_length) if total_length else 0

                downloaded = 0
                chunk_size = 65536
                os.makedirs(os.path.dirname(os.path.abspath(self.dest_path)), exist_ok=True)

                with open(self.dest_path, "wb") as out_file:
                    while True:
                        if self._is_cancelled:
                            self.sig_download_failed.emit("사용자에 의해 다운로드가 취소되었습니다.")
                            return
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        self.sig_progress.emit(downloaded, total_bytes)

            self.sig_download_completed.emit(self.dest_path)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.sig_download_failed.emit(
                    f"배포 파일이 서버에 등록되지 않았습니다 (HTTP 404 Not Found).\n"
                    f"현재 버전의 릴리즈 패키지가 아직 생성/업로드 중일 수 있습니다.\n"
                    f"공식 릴리즈 페이지에서 최신 패키지 빌드 상태를 확인해 주십시오."
                )
            elif e.code == 403:
                self.sig_download_failed.emit(
                    f"GitHub 서버 접근 제한 또는 Rate-Limit(요청 한도)이 초과되었습니다 (HTTP 403).\n"
                    f"잠시 후 다시 시도해 주십시오."
                )
            else:
                self.sig_download_failed.emit(f"서버 응답 오류 (HTTP {e.code}): {e.reason}")
        except urllib.error.URLError as e:
            self.sig_download_failed.emit(f"원격 서버 연결 실패: {e.reason}")
        except Exception as e:
            self.sig_download_failed.emit(f"다운로드 실패: {e}")


class WindowsPatcher:
    """윈도우 프로세스 파일 잠금(Lock)을 우회하는 원자적 교체 및 재실행 전담 클래스"""

    @staticmethod
    def get_patcher_script_content(target_exe: str, new_exe: str, pid: int) -> str:
        clean_target = os.path.abspath(target_exe).replace('"', '')
        clean_new = os.path.abspath(new_exe).replace('"', '')
        return f"""@echo off
chcp 65001 > nul
echo [DragonRPA] Manual Studio 스마트 업데이트 패처 실행 중...
timeout /t 1 /nobreak > nul

:wait_loop
tasklist /fi "PID eq {pid}" | find "{pid}" > nul
if %ERRORLEVEL% equ 0 (
    timeout /t 1 /nobreak > nul
    goto wait_loop
)

REM 기존 실행파일 백업 및 새 실행파일로 교체
copy /y "{clean_new}" "{clean_target}" > nul
if %ERRORLEVEL% equ 0 (
    del /f /q "{clean_new}" > nul
    start "" "{clean_target}"
) else (
    echo [ERROR] 실행파일 업데이트 교체에 실패했습니다. 관리자 권한을 확인하세요.
    pause
)

del "%~f0"
"""

    @classmethod
    def apply_update_and_restart(cls, target_exe: str, new_exe: str) -> bool:
        try:
            # 안전 검사: 개발 환경에서 python.exe 덮어쓰기 방지
            if os.path.basename(target_exe).lower().startswith("python"):
                target_dir = os.path.dirname(os.path.abspath(target_exe))
                target_exe = os.path.join(target_dir, "ManualStudio.exe")

            pid = os.getpid()
            bat_dir = tempfile.gettempdir()
            bat_path = os.path.join(bat_dir, f"update_patcher_{pid}.bat")
            script_content = cls.get_patcher_script_content(target_exe, new_exe, pid)
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # 비동기로 패처 배치 파일 실행
            subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                shell=True
            )
            return True
        except Exception as e:
            print(f"[WindowsPatcher Error]: {e}")
            return False


class UpdateDialog(QDialog):
    """스마트 자동 업데이트 전용 대화상자 (전사 표준 헌장 카테고리 III 디자인 준수)"""

    def __init__(self, metadata: dict, current_version: str, target_exe_path: str = None, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self.current_version = current_version
        self.target_exe_path = target_exe_path or sys.executable
        self.download_thread = None

        self.setWindowTitle(tr("update_dialog_title", "스마트 자동 업데이트"))
        self.setFixedSize(540, 460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        ci_pix = get_dragon_rpa_ci_pixmap()
        if not ci_pix.isNull():
            self.setWindowIcon(QIcon(ci_pix))

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { font-family: 'Segoe UI', 'Malgun Gothic'; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        # 1. 헤더 (버전 비교 배너)
        header_card = QFrame(self)
        header_card.setStyleSheet("""
            QFrame {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 8px;
            }
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(14, 12, 14, 12)
        h_layout.setSpacing(4)

        remote_ver = self.metadata.get("version", "최신")
        lbl_h_title = QLabel(f"{tr('update_found_title', '신규 버전이 발견되었습니다')}: {remote_ver}", header_card)
        lbl_h_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E40AF; border: none;")
        h_layout.addWidget(lbl_h_title)

        rel_date = self.metadata.get("release_date", "")
        v_info_text = f"{tr('update_current_ver', '현재 버전')}: {self.current_version}  ➔  {tr('update_latest_ver', '최신 버전')}: {remote_ver}"
        if rel_date:
            v_info_text += f" ({tr('update_rel_date', '배포일')}: {rel_date})"
        lbl_v_info = QLabel(v_info_text, header_card)
        lbl_v_info.setStyleSheet("font-size: 11.5px; color: #3B82F6; border: none; font-weight: 500;")
        h_layout.addWidget(lbl_v_info)

        layout.addWidget(header_card)

        # 2. 릴리즈 노트 영역
        lbl_rn_title = QLabel(tr("update_rn_title", "업데이트 주요 변경 내역:"), self)
        lbl_rn_title.setStyleSheet("font-size: 11.5px; font-weight: bold; color: #334155; margin-top: 4px;")
        layout.addWidget(lbl_rn_title)

        self.text_notes = QTextEdit(self)
        self.text_notes.setReadOnly(True)
        rel_notes = self.metadata.get("release_notes", "").strip() or tr("update_no_notes", "상세 개선 사항이 제공되지 않았습니다.")
        self.text_notes.setPlainText(rel_notes)
        self.text_notes.setStyleSheet("""
            QTextEdit {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Segoe UI', 'Malgun Gothic';
                font-size: 11.5px;
                color: #1E293B;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.text_notes, 1)

        # 3. 다운로드 프로그레스 바 (평상시 숨김)
        self.progress_frame = QFrame(self)
        self.progress_frame.setVisible(False)
        p_layout = QVBoxLayout(self.progress_frame)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(4)

        self.lbl_progress_status = QLabel(tr("update_progress_ready", "다운로드 준비 중..."), self.progress_frame)
        self.lbl_progress_status.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")
        p_layout.addWidget(self.lbl_progress_status)

        self.progress_bar = QProgressBar(self.progress_frame)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                text-align: center;
                background-color: #F1F5F9;
                font-size: 10.5px;
                font-weight: bold;
                color: #0F172A;
            }
            QProgressBar::chunk {
                background-color: #2563EB;
                border-radius: 3px;
            }
        """)
        p_layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_frame)

        # 4. 하단 버튼 바
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.lbl_notice = QLabel(tr("update_notice_license", "라이선스는 자동으로 유지됩니다."), self)
        self.lbl_notice.setStyleSheet("font-size: 11px; color: #059669; font-weight: bold;")
        btn_box.addWidget(self.lbl_notice)
        btn_box.addStretch(1)

        self.btn_web = QPushButton(tr("update_btn_web", "릴리즈 웹페이지"), self)
        self.btn_web.setFixedHeight(34)
        self.btn_web.setCursor(Qt.PointingHandCursor)
        self.btn_web.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                color: #2563EB;
                border: 1px solid #BFDBFE;
                border-radius: 5px;
                padding: 0 14px;
                font-size: 11.5px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #EFF6FF; }
        """)
        rel_page_url = self.metadata.get("release_page_url", DEFAULT_RELEASE_PAGE)
        self.btn_web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(rel_page_url)))
        btn_box.addWidget(self.btn_web)

        self.btn_update = QPushButton(tr("update_btn_now", "업데이트 실행"), self)
        self.btn_update.setFixedHeight(34)
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 0 18px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:disabled { background-color: #94A3B8; }
        """)
        self.btn_update.clicked.connect(self.start_download)
        btn_box.addWidget(self.btn_update)

        self.btn_later = QPushButton(tr("update_btn_later", "다음에 하기"), self)
        self.btn_later.setFixedHeight(34)
        self.btn_later.setCursor(Qt.PointingHandCursor)
        self.btn_later.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
                padding: 0 16px;
                font-size: 11.5px;
            }
            QPushButton:hover { background-color: #F1F5F9; }
        """)
        self.btn_later.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_later)

        layout.addLayout(btn_box)

    def start_download(self):
        dl_url = self.metadata.get("download_url", "")
        if not dl_url:
            QMessageBox.warning(self, tr("title_input_error", "오류"), "다운로드 파일 경로가 지정되어 있지 않습니다.")
            return

        self.btn_update.setEnabled(False)
        self.btn_later.setText(tr("update_btn_cancel", "취소"))
        self.progress_frame.setVisible(True)
        self.lbl_progress_status.setText(tr("update_progress_start", "최신 실행 파일 다운로드 시작..."))

        dest_dir = tempfile.gettempdir()
        temp_exe = os.path.join(dest_dir, f"ManualStudio_Update_{self.metadata.get('version', 'new')}.exe")

        self.download_thread = UpdateDownloadThread(dl_url, temp_exe, self)
        self.download_thread.sig_progress.connect(self.on_download_progress)
        self.download_thread.sig_download_completed.connect(self.on_download_completed)
        self.download_thread.sig_download_failed.connect(self.on_download_failed)
        self.download_thread.start()

    def on_download_progress(self, downloaded: int, total: int):
        if total > 0:
            pct = int((downloaded / total) * 100)
            self.progress_bar.setValue(pct)
            mb_down = downloaded / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            self.lbl_progress_status.setText(f"{mb_down:.1f}MB / {mb_tot:.1f}MB ({pct}%)")
        else:
            mb_down = downloaded / (1024 * 1024)
            self.lbl_progress_status.setText(f"{mb_down:.1f}MB")

    def on_download_completed(self, downloaded_file: str):
        self.progress_bar.setValue(100)
        self.lbl_progress_status.setText(tr("update_completed_title", "업데이트 완료"))

        res = QMessageBox.question(
            self,
            tr("update_completed_title", "스마트 업데이트 완료"),
            tr("update_completed_msg", "새로운 버전 다운로드가 완료되었습니다.\n지금 바로 프로그램을 재시작하여 최신 버전을 적용하시겠습니까?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if res == QMessageBox.Yes:
            # 윈도우 원자적 교체 및 재시작 트리거
            ok = WindowsPatcher.apply_update_and_restart(self.target_exe_path, downloaded_file)
            if ok:
                QApplication.quit()
                sys.exit(0)
            else:
                QMessageBox.critical(self, tr("title_input_error", "업데이트 오류"), "패처 스크립트 실행에 실패했습니다.")
        else:
            self.accept()

    def on_download_failed(self, err_msg: str):
        self.progress_frame.setVisible(False)
        self.btn_update.setEnabled(True)
        self.btn_later.setText(tr("btn_close", "닫기"))

        rel_page_url = self.metadata.get("release_page_url", DEFAULT_RELEASE_PAGE)

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(tr("update_failed_title", "다운로드 실패"))
        msg_box.setText(err_msg)
        btn_open_web = msg_box.addButton(tr("update_btn_open_web", "릴리즈 웹페이지 열기"), QMessageBox.ActionRole)
        btn_ok = msg_box.addButton(tr("btn_confirm", "확인"), QMessageBox.AcceptRole)
        msg_box.setDefaultButton(btn_ok)
        msg_box.exec()

        if msg_box.clickedButton() == btn_open_web:
            QDesktopServices.openUrl(QUrl(rel_page_url))
