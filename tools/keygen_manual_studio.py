"""
================================================================================
(주)드래곤알피에이 매뉴얼 스튜디오 라이선스 발급기 (Keygen Studio)
Manual Studio License Key Generator (GUI & CLI)
================================================================================
"""

import sys
import os
import json
import argparse
from datetime import datetime, timedelta

# 상위 폴더의 license_engine 임포트 가능하도록 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from license_engine import LicenseEngine, LicenseType

LOG_FILE = os.path.join(os.path.dirname(__file__), "issued_licenses.json")

def log_issued_license(record: dict):
    records = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []
    records.append(record)
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to write log: {e}")

def run_cli(args):
    now = datetime.now()
    expiry = args.expiry or "NONE"

    if args.type == LicenseType.SUBSCRIPTION_1M and expiry == "NONE":
        expiry = (now + timedelta(days=30)).strftime("%Y-%m-%d")
    elif args.type == LicenseType.SUBSCRIPTION_1Y and expiry == "NONE":
        expiry = (now + timedelta(days=365)).strftime("%Y-%m-%d")
    elif args.type == LicenseType.TRIAL_EXT_14D and expiry == "NONE":
        expiry = (now + timedelta(days=14)).strftime("%Y-%m-%d")

    hwid = args.hwid
    if not hwid and args.type not in (LicenseType.ENTERPRISE, LicenseType.AIR_GAPPED_SITE):
        hwid = LicenseEngine.get_hwid()

    key = LicenseEngine.generate_license_key(
        license_type=args.type,
        hwid=hwid,
        issued_to=args.name,
        expiry_date=expiry,
        max_seats=args.seats
    )

    record = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "license_type": args.type,
        "issued_to": args.name,
        "hwid": hwid,
        "expiry": expiry,
        "seats": args.seats,
        "serial_key": key
    }
    log_issued_license(record)

    print("=" * 60)
    print(" [DragonRPA] Manual Studio License Key Generated")
    print("=" * 60)
    print(f" Type      : {args.type}")
    print(f" Issued To : {args.name}")
    print(f" HWID      : {hwid}")
    print(f" Expiry    : {expiry}")
    print(f" Seats     : {args.seats}")
    print("-" * 60)
    print(f" SERIAL KEY: {key}")
    print("=" * 60)
    return key

def run_gui():
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton, QTextEdit,
        QDateEdit, QGroupBox, QMessageBox, QFrame
    )
    from PySide6.QtCore import Qt, QDate
    from PySide6.QtGui import QFont, QColor, QPalette

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = QMainWindow()
    win.setWindowTitle("매뉴얼 스튜디오 라이선스 발급기 (Keygen Studio) - DragonRPA Co.")
    win.resize(650, 680)

    central = QWidget()
    win.setCentralWidget(central)
    root_layout = QVBoxLayout(central)
    root_layout.setContentsMargins(20, 20, 20, 20)
    root_layout.setSpacing(15)

    # 1. Header
    header = QLabel("DragonRPA Manual Studio Keygen Studio")
    header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e3a8a; padding-bottom: 5px;")
    sub = QLabel("고객사 납품용 위변조 불가능 정식 라이선스 키 발급 관리 시스템")
    sub.setStyleSheet("font-size: 12px; color: #64748b;")
    root_layout.addWidget(header)
    root_layout.addWidget(sub)

    # Line
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    root_layout.addWidget(line)

    # 2. Form Group
    grp_form = QGroupBox("발급 대상 및 계약 속성 입력")
    grp_form.setStyleSheet("QGroupBox { font-weight: bold; }")
    form_layout = QVBoxLayout(grp_form)
    form_layout.setSpacing(10)

    # Type
    h_type = QHBoxLayout()
    lbl_type = QLabel("라이선스 유형:")
    lbl_type.setFixedWidth(130)
    combo_type = QComboBox()
    types_list = [
        ("1카피 영구 (PERPETUAL)", LicenseType.PERPETUAL),
        ("1카피 1개월 구독 (SUB_1M)", LicenseType.SUBSCRIPTION_1M),
        ("1카피 1년 연간 구독 (SUB_1Y) [추천]", LicenseType.SUBSCRIPTION_1Y),
        ("엔터프라이즈 볼륨 (ENTERPRISE)", LicenseType.ENTERPRISE),
        ("오프라인 폐쇄망 사이트 (AIR_GAPPED)", LicenseType.AIR_GAPPED_SITE),
        ("14일 평가 연장 키 (TRIAL_14D)", LicenseType.TRIAL_EXT_14D)
    ]
    for label, val in types_list:
        combo_type.addItem(label, val)
    h_type.addWidget(lbl_type)
    h_type.addWidget(combo_type)
    form_layout.addLayout(h_type)

    # Customer Name
    h_name = QHBoxLayout()
    lbl_name = QLabel("고객사 / 사용자명:")
    lbl_name.setFixedWidth(130)
    edit_name = QLineEdit("(주)대한렌탈 / 전산팀 홍길동")
    h_name.addWidget(lbl_name)
    h_name.addWidget(edit_name)
    form_layout.addLayout(h_name)

    # HWID
    h_hwid = QHBoxLayout()
    lbl_hwid = QLabel("고객 PC HWID:")
    lbl_hwid.setFixedWidth(130)
    edit_hwid = QLineEdit(LicenseEngine.get_hwid())
    btn_my_hwid = QPushButton("현재 PC 입력")
    btn_my_hwid.setFixedWidth(100)
    btn_my_hwid.clicked.connect(lambda: edit_hwid.setText(LicenseEngine.get_hwid()))
    h_hwid.addWidget(lbl_hwid)
    h_hwid.addWidget(edit_hwid)
    h_hwid.addWidget(btn_my_hwid)
    form_layout.addLayout(h_hwid)

    # Expiry Date
    h_exp = QHBoxLayout()
    lbl_exp = QLabel("만료 일자:")
    lbl_exp.setFixedWidth(130)
    date_exp = QDateEdit()
    date_exp.setCalendarPopup(True)
    date_exp.setDate(QDate.currentDate().addYears(1))
    date_exp.setEnabled(False) # 영구 기본
    h_exp.addWidget(lbl_exp)
    h_exp.addWidget(date_exp)
    form_layout.addLayout(h_exp)

    # Seats
    h_seats = QHBoxLayout()
    lbl_seats = QLabel("허용 좌석 수 (Seats):")
    lbl_seats.setFixedWidth(130)
    spin_seats = QSpinBox()
    spin_seats.setRange(1, 99999)
    spin_seats.setValue(1)
    h_seats.addWidget(lbl_seats)
    h_seats.addWidget(spin_seats)
    form_layout.addLayout(h_seats)

    root_layout.addWidget(grp_form)

    # Type change sync
    def on_type_changed(idx):
        t = combo_type.currentData()
        cur_d = QDate.currentDate()
        if t == LicenseType.PERPETUAL:
            date_exp.setEnabled(False)
            spin_seats.setValue(1)
            spin_seats.setEnabled(False)
            edit_hwid.setEnabled(True)
        elif t == LicenseType.SUBSCRIPTION_1M:
            date_exp.setEnabled(True)
            date_exp.setDate(cur_d.addDays(30))
            spin_seats.setValue(1)
            spin_seats.setEnabled(False)
            edit_hwid.setEnabled(True)
        elif t == LicenseType.SUBSCRIPTION_1Y:
            date_exp.setEnabled(True)
            date_exp.setDate(cur_d.addYears(1))
            spin_seats.setValue(1)
            spin_seats.setEnabled(False)
            edit_hwid.setEnabled(True)
        elif t == LicenseType.TRIAL_EXT_14D:
            date_exp.setEnabled(True)
            date_exp.setDate(cur_d.addDays(14))
            spin_seats.setValue(1)
            spin_seats.setEnabled(False)
            edit_hwid.setEnabled(True)
        elif t in (LicenseType.ENTERPRISE, LicenseType.AIR_GAPPED_SITE):
            date_exp.setEnabled(True)
            date_exp.setDate(cur_d.addYears(1))
            spin_seats.setEnabled(True)
            spin_seats.setValue(50)
            edit_hwid.setText("ENTERPRISE")
            edit_hwid.setEnabled(False)

    combo_type.currentIndexChanged.connect(on_type_changed)

    # 3. Action Buttons
    h_act = QHBoxLayout()
    btn_generate = QPushButton("🔑 정식 라이선스 키 발급")
    btn_generate.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; font-size: 14px; padding: 10px; border-radius: 6px;")
    h_act.addWidget(btn_generate)
    root_layout.addLayout(h_act)

    # 4. Result Group
    grp_res = QGroupBox("발급된 시리얼 키 (클라이언트 전달용)")
    grp_res.setStyleSheet("QGroupBox { font-weight: bold; }")
    res_layout = QVBoxLayout(grp_res)

    edit_result = QTextEdit()
    edit_result.setFixedHeight(80)
    edit_result.setReadOnly(True)
    edit_result.setFont(QFont("Consolas", 12))
    edit_result.setStyleSheet("background-color: #f8fafc; color: #0f172a; border: 1px solid #cbd5e1; padding: 8px;")
    res_layout.addWidget(edit_result)

    h_res_act = QHBoxLayout()
    btn_copy = QPushButton("📋 클립보드 복사")
    btn_copy.setStyleSheet("font-weight: bold; padding: 6px 14px;")
    btn_verify = QPushButton("🧪 발급 키 즉시 검증")
    btn_verify.setStyleSheet("padding: 6px 14px;")

    h_res_act.addWidget(btn_copy)
    h_res_act.addWidget(btn_verify)
    res_layout.addLayout(h_res_act)

    root_layout.addWidget(grp_res)

    # Generate Handler
    def on_generate():
        l_type = combo_type.currentData()
        c_name = edit_name.text().strip() or "Customer"
        h_val = edit_hwid.text().strip()
        s_val = spin_seats.value()
        exp_val = "NONE" if l_type == LicenseType.PERPETUAL else date_exp.date().toString("yyyy-MM-dd")

        key = LicenseEngine.generate_license_key(
            license_type=l_type,
            hwid=h_val,
            issued_to=c_name,
            expiry_date=exp_val,
            max_seats=s_val
        )

        edit_result.setPlainText(key)
        QApplication.clipboard().setText(key)

        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "license_type": l_type,
            "issued_to": c_name,
            "hwid": h_val,
            "expiry": exp_val,
            "seats": s_val,
            "serial_key": key
        }
        log_issued_license(record)

        QMessageBox.information(
            win,
            "발급 완료",
            f"라이선스 키가 정상 발급되었으며 클립보드에 복사되었습니다!\n\n"
            f"• 유형: {combo_type.currentText()}\n"
            f"• 대상: {c_name}\n"
            f"• 만료: {exp_val}\n\n"
            f"이 키를 고객사에게 전달하여 등록 안내를 진행해 주세요."
        )

    def on_copy():
        k = edit_result.toPlainText().strip()
        if k:
            QApplication.clipboard().setText(k)
            QMessageBox.information(win, "복사 완료", "시리얼 키가 클립보드에 복사되었습니다.")

    def on_verify():
        k = edit_result.toPlainText().strip()
        if not k:
            return
        valid, payload, msg = LicenseEngine.verify_license_key(k, edit_hwid.text().strip())
        if valid:
            QMessageBox.information(
                win,
                "검증 성공",
                f"✅ 정상 인증 확인 완료!\n\n"
                f"• 유형: {payload.get('type')}\n"
                f"• 대상: {payload.get('issued_to')}\n"
                f"• 만료일: {payload.get('expiry')}\n"
                f"• 허용 좌석: {payload.get('seats')} 대"
            )
        else:
            QMessageBox.warning(win, "검증 실패", f"❌ 무효 키: {msg}")

    btn_generate.clicked.connect(on_generate)
    btn_copy.clicked.connect(on_copy)
    btn_verify.clicked.connect(on_verify)

    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DragonRPA Manual Studio Keygen")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--type", default=LicenseType.PERPETUAL, choices=[
        LicenseType.PERPETUAL, LicenseType.SUBSCRIPTION_1M, LicenseType.SUBSCRIPTION_1Y,
        LicenseType.ENTERPRISE, LicenseType.AIR_GAPPED_SITE, LicenseType.TRIAL_EXT_14D
    ])
    parser.add_argument("--name", default="DragonRPA Customer", help="Customer/Company Name")
    parser.add_argument("--hwid", default="", help="Client PC HWID (DRPA-XXXX-XXXX-XXXX)")
    parser.add_argument("--expiry", default="", help="Expiration Date (YYYY-MM-DD)")
    parser.add_argument("--seats", type=int, default=1, help="Number of seats")

    args, unknown = parser.parse_known_args()
    if args.cli or len(sys.argv) > 1 and not (len(sys.argv) == 2 and sys.argv[1] == "--gui"):
        run_cli(args)
    else:
        run_gui()
