# -*- coding: utf-8 -*-
"""
================================================================================
(주)드래곤알피에이 매뉴얼 스튜디오 다국어 EULA 매니저 (EulaManager)
Multilingual End User License Agreement Catalog & Service for Manual Studio
Supported: KO, EN, ZH, JA, DE, ES, FR, PT, RU (9 Languages)
================================================================================
"""

from typing import Dict, Tuple, List


class EulaManager:
    """
    DragonRPA Manual Studio EULA Multi-language Provider
    Provides localized HTML and Plain-text versions of the 7-Article EULA.
    """

    SUPPORTED_LOCALES: Dict[str, str] = {
        "ko": "한국어 (Korean)",
        "en": "English",
        "zh": "简体中文 (Chinese)",
        "ja": "日本語 (Japanese)",
        "de": "Deutsch (German)",
        "es": "Español (Spanish)",
        "fr": "Français (French)",
        "pt": "Português (Portuguese)",
        "ru": "Русский (Russian)"
    }

    _DATA = {
        "ko": {
            "title": "(주)드래곤알피에이 소프트웨어 최종 사용자 라이선스 계약서 (EULA)",
            "subtitle": "End User License Agreement for Manual Studio | (주)드래곤알피에이 (DragonRPA Co., Ltd.)",
            "preamble": "본 계약은 <b>(주)드래곤알피에이</b>(이하 \"회사\")와 본 소프트웨어 <b>'매뉴얼 스튜디오(Manual Studio)'</b>(이하 \"소프트웨어\")를 다운로드, 복사, 설치 또는 사용하는 개인 또는 법인(이하 \"사용자\") 간에 체결되는 법적 구속력을 가진 사용권 계약입니다. 사용자가 본 \"소프트웨어\"를 다운로드, 설치 또는 사용하는 것은 본 계약 조건에 동의한 것으로 간주됩니다.",
            "articles": [
                (
                    "제1조 (목적)",
                    "본 계약은 \"회사\"가 개발한 \"소프트웨어\"에 대한 비독점적이고 양도 불가능한 사용 권한을 \"사용자\"에게 허여하고, 당사자 간의 권리 및 의무를 규정함을 목적으로 합니다."
                ),
                (
                    "제2조 (지식재산권의 귀속)",
                    "1. 본 \"소프트웨어\", 관련 설명 문서, 소스코드, 바이너리, 그래픽, UI/UX 디자인에 대한 저작권, 특허권, 상표권, 영업비밀 등 일체의 지식재산권은 대한민국 저작권법 및 국제 협약에 따라 <b>(주)드래곤알피에이</b>에 배타적으로 귀속됩니다.<br/>"
                    "2. 본 계약에 따른 제공은 소유권의 이전이 아니며, 명시된 조건 범위 내에서의 <b>'제한적 사용권(License)'</b>만을 허여합니다."
                ),
                (
                    "제3조 (사용권의 범위 및 조건)",
                    "1. <b>[평가판 (Trial License)]</b>: \"회사\"가 공지한 평가판은 명시된 사용 유효 기간(2026년 12월 31일까지) 동안 비상업적 검토, 기능 테스트 및 평가 목적으로만 무상 사용할 수 있습니다. 기간 만료 후에는 정규 라이선스 없이 계속 사용할 수 없습니다.<br/>"
                    "2. <b>[정규 라이선스 (Commercial License)]</b>: 정식 라이선스는 1개의 라이선스 키당 지정된 단일 하드웨어 머신(1PC-1Key 노드락)에서만 설치 및 실행이 허용됩니다."
                ),
                (
                    "제4조 (금지 행위 - 역공학 및 무단 배포 금지)",
                    "사용자는 다음 각 호의 행위를 하여서는 아니 되며, 위반 시 저작권법 등에 따른 민·형사상 책임을 집니다.<br/>"
                    "1. <b>역공학 및 디컴파일 금지</b>: 소스코드나 내부 알고리즘을 추출하기 위한 리버스 엔지니어링, 역컴파일(Decompile), 디스어셈블(Disassemble) 또는 코드 수정 행위<br/>"
                    "2. <b>보안 메커니즘 조작 금지</b>: 하드웨어 식별값(HWID), 시계 변조 방지, 암호화 키 등 라이선스 검증 장치를 우회, 변조, 크랙하는 행위<br/>"
                    "3. <b>무단 재배포 및 상업적 재판매 금지</b>: \"회사\"의 사전 서면 승인 없이 제3자에게 유상 판매, 대여, 양도하거나 온라인 자료실/공중망에 무단 배포하는 행위<br/>"
                    "4. <b>저작권 표시 삭제 금지</b>: \"소프트웨어\" 내에 표시된 \"회사\"의 상표, 로고, 저작권 안내문, 평가판 기한 등의 법적 고지 사항을 임의로 변경, 제거하는 행위"
                ),
                (
                    "제5조 (보증의 한계 및 면책)",
                    "1. 본 \"소프트웨어\"는 <b>\"있는 그대로(AS-IS)\"</b> 제공되며, 회사는 특정 목적에의 적합성, 무결성 등에 대해 명시적 또는 묵시적 보증을 하지 않습니다.<br/>"
                    "2. 회사는 \"소프트웨어\"의 사용 또는 사용 불능으로 인하여 발생하는 간접적, 부수적 손해(영업손실, 데이터 손실 등)에 대해 책임을 지지 않습니다."
                ),
                (
                    "제6조 (위약벌 및 손해배상)",
                    "사용자가 제4조(금지 행위)를 고의 또는 중과실로 위반한 경우, <b>정규 라이선스 정가의 5배에 해당하는 금액을 위약벌로 회사에 즉시 지급</b>하여야 하며, 이와 별도로 회사가 입은 실제 손해를 전액 배상하여야 합니다."
                ),
                (
                    "제7조 (준거법 및 전속 관할)",
                    "본 계약은 대한민국 법률에 따라 규율되며, 본 계약과 관련하여 발생하는 모든 분쟁은 <b>(주)드래곤알피에이 본점 소재지를 관할하는 법원(서울중앙지방법원)을 제1심 전속 관할 법원</b>으로 합니다."
                )
            ],
            "footer": "공고일자: 2026.09.11 | 시행일자: 2026.09.11<br/>(주)드래곤알피에이 (DragonRPA Co., Ltd.) | 대표이사: 이정용 | 문의: 77.victor.lee@gmail.com",
            "dialog_title": "최종 사용자 라이선스 계약서 (EULA) - (주)드래곤알피에이",
            "btn_close": "닫기",
            "btn_copy": "📋 전체 복사",
            "copied_toast": "EULA 내용이 클립보드에 복사되었습니다."
        },
        "en": {
            "title": "DragonRPA Software End User License Agreement (EULA)",
            "subtitle": "End User License Agreement for Manual Studio | DragonRPA Co., Ltd.",
            "preamble": "This End User License Agreement (\"Agreement\" or \"EULA\") is a legally binding contract between <b>DragonRPA Co., Ltd.</b> (\"Company\") and any individual or legal entity (\"User\") who downloads, copies, installs, or uses the software <b>'Manual Studio'</b> (\"Software\"). By downloading, installing, or using the Software, the User agrees to be bound by all terms and conditions of this Agreement.",
            "articles": [
                (
                    "Article 1 (Purpose)",
                    "The purpose of this Agreement is to grant the User a non-exclusive, non-transferable license to use the \"Software\" developed by the \"Company\" and to define the rights and obligations between the parties."
                ),
                (
                    "Article 2 (Intellectual Property & Ownership)",
                    "1. All copyrights, patents, trademarks, trade secrets, and other intellectual property rights in and to the \"Software\", accompanying documentation, source code, binaries, graphics, and UI/UX designs are exclusively owned by <b>DragonRPA Co., Ltd.</b> under the Copyright Act of the Republic of Korea and international treaties.<br/>"
                    "2. The provision of the \"Software\" under this Agreement does not constitute a transfer of ownership, granting solely a <b>limited, revocable license to use (License)</b> within the scope of specified terms."
                ),
                (
                    "Article 3 (Scope of License & Conditions)",
                    "1. <b>[Evaluation / Trial License]</b>: The evaluation version made available by the Company may be used free of charge solely for non-commercial review, feature testing, and evaluation during the designated validity period (until December 31, 2026). Continuous use after expiration is strictly prohibited without a valid commercial license.<br/>"
                    "2. <b>[Commercial License]</b>: A commercial license authorizes installation and execution solely on a single designated hardware device per license key (1PC-1Key Node-Locked)."
                ),
                (
                    "Article 4 (Prohibited Acts - Reverse Engineering & Redistribution)",
                    "The User shall not commit any of the following acts; any violation shall subject the User to civil and criminal liabilities under applicable copyright and related laws:<br/>"
                    "1. <b>Prohibition of Reverse Engineering</b>: Reverse engineering, decompiling, disassembling, or modifying code to extract source code or underlying algorithms.<br/>"
                    "2. <b>Prohibition of Security Tampering</b>: Bypassing, modifying, cracking, or tampering with license verification mechanisms including Hardware ID (HWID), anti-clock tampering checks, or cryptographic keys.<br/>"
                    "3. <b>Prohibition of Unauthorized Distribution & Resale</b>: Selling, renting, leasing, sublicensing, or distributing the Software to third parties or uploading to public networks/archives without prior written consent.<br/>"
                    "4. <b>Prohibition of Removing Notices</b>: Arbitrarily altering or removing trademarks, logos, copyright notices, or trial expiration notices embedded within the Software."
                ),
                (
                    "Article 5 (Disclaimer of Warranties & Limitation of Liability)",
                    "1. The \"Software\" is provided <b>\"AS-IS\"</b> without warranties of any kind, express or implied, including but not limited to merchantability, fitness for a particular purpose, or error-free operation.<br/>"
                    "2. The Company shall not be liable for any indirect, incidental, special, or consequential damages (including loss of business profits, business interruption, or data loss) arising out of the use or inability to use the Software."
                ),
                (
                    "Article 6 (Liquidated Damages & Indemnification)",
                    "If the User violates Article 4 (Prohibited Acts) intentionally or through gross negligence, the User shall <b>immediately pay liquidated damages equal to 5 (five) times the regular commercial license list price</b> to the Company, without prejudice to the Company's right to claim full compensation for actual damages incurred."
                ),
                (
                    "Article 7 (Governing Law & Exclusive Jurisdiction)",
                    "This Agreement shall be governed by and construed in accordance with the laws of the Republic of Korea. Any disputes arising out of or in connection with this Agreement shall be subject to the <b>exclusive jurisdiction of the court having jurisdiction over the location of the principal office of DragonRPA Co., Ltd. (Seoul Central District Court)</b> as the court of first instance."
                )
            ],
            "footer": "Announcement Date: 2026.09.11 | Effective Date: 2026.09.11<br/>DragonRPA Co., Ltd. | CEO: Lee Jeong-yong | Contact: 77.victor.lee@gmail.com",
            "dialog_title": "End User License Agreement (EULA) - DragonRPA Co., Ltd.",
            "btn_close": "Close",
            "btn_copy": "📋 Copy All",
            "copied_toast": "EULA text copied to clipboard."
        },
        "zh": {
            "title": "DragonRPA 软件最终用户许可协议 (EULA)",
            "subtitle": "Manual Studio 最终用户许可协议 | 龙软科技有限责任公司 (DragonRPA Co., Ltd.)",
            "preamble": "本协议是 <b>DragonRPA Co., Ltd.</b>（以下简称“公司”）与下载、复制、安装或使用<b>“Manual Studio”</b>软件（以下简称“本软件”）的个人或法人（以下简称“用户”）之间签订的具有法律约束力的许可使用协议。用户下载、安装或使用本软件，即视为同意并接受本协议的全部条款与条件。",
            "articles": [
                (
                    "第1条 (目的)",
                    "本协议旨在向用户授予本公司开发的本软件之非排他性、不可转让的使用许可，并明确双方在软件使用过程中的权利与义务。"
                ),
                (
                    "第2条 (知识产权归属)",
                    "1. 本软件及其相关说明文档、源代码、二进制程序、图形、UI/UX 设计的所有版权、专利权、商标权及商业秘密等知识产权，均依照大韩民国著作权法及相关国际公约专属于 <b>DragonRPA Co., Ltd.</b>。<br/>"
                    "2. 本协议项下的提供不构成软件所有权的转移，仅在明确约定的条件范围内授予有限的<b>“许可使用权(License)”</b>。"
                ),
                (
                    "第3条 (许可范围与条件)",
                    "1. <b>[评估/试用版 (Trial License)]</b>: 公司发布的试用版仅限在指定有效期内（截至2026年12月31日）用于非商业性的功能测试与评估。有效期届满后，未购买正版商业许可不得继续使用。<br/>"
                    "2. <b>[商业许可 (Commercial License)]</b>: 正式商业许可实行单机单码绑定（1PC-1Key 节点锁定），仅允许在绑定的单台硬件设备上安装和运行。"
                ),
                (
                    "第4条 (禁止行为 - 禁止逆向工程及未授权分发)",
                    "用户不得实施以下行为；如有违反，将依据相关著作权法律承担民事及刑事法律责任：<br/>"
                    "1. <b>禁止逆向工程</b>: 对本软件进行反向工程、反编译(Decompile)、反汇编(Disassemble)或修改代码以提取源码或核心算法；<br/>"
                    "2. <b>禁止篡改安全机制</b>: 绕过、修改、破解硬件识别码(HWID)、防时钟篡改机制、加密密钥等许可验证系统；<br/>"
                    "3. <b>禁止未授权分发与商业转售</b>: 未经公司事先书面批准，向任何第三方出租、转售、再许可，或上传至公用网络/下载站分发；<br/>"
                    "4. <b>禁止删除版权标识</b>: 任意更改或删除软件内部包含的商标、LOGO、版权声明及试用期限等法律告知信息。"
                ),
                (
                    "第5条 (免责声明与责任限制)",
                    "1. 本软件按<b>“现状(AS-IS)”</b>提供，公司对其适销性、特定用途适用性或无差错运行不作任何明示或默示的保证。<br/>"
                    "2. 公司不对因使用或无法使用本软件而导致的任何间接、附带或衍生性损失（包括商业利润损失、营业中断或数据丢失）承担责任。"
                ),
                (
                    "第6条 (违约罚金与损害赔偿)",
                    "用户如因故意或重大过失违反第4条（禁止行为），<b>应立即向公司支付相当于正版商业许可售价 5 倍的惩罚性违约金</b>，且不影响公司就实际遭受的全部损失要求进一步全额赔偿的权利。"
                ),
                (
                    "第7条 (准据法与专属管辖)",
                    "本协议受大韩民国法律管辖并按其解释。因本协议引起的或与之相关的所有争议，均应提交 <b>DragonRPA Co., Ltd. 总部所在地管辖法院（首尔中央地方法院）</b>作为第一审专属管辖法院。"
                )
            ],
            "footer": "公布日期: 2026.09.11 | 施行日期: 2026.09.11<br/>DragonRPA Co., Ltd. | 代表理事: 李廷龙 (Lee Jeong-yong) | 咨询: 77.victor.lee@gmail.com",
            "dialog_title": "最终用户许可协议 (EULA) - DragonRPA Co., Ltd.",
            "btn_close": "关闭",
            "btn_copy": "📋 复制全文",
            "copied_toast": "EULA 内容已复制到剪贴板。"
        },
        "ja": {
            "title": "株式会社DragonRPA ソフトウェア エンドユーザー使用許諾契約書 (EULA)",
            "subtitle": "Manual Studio エンドユーザーライセンス契約 | 株式会社DragonRPA (DragonRPA Co., Ltd.)",
            "preamble": "本契約は、<b>株式会社DragonRPA</b>（以下「当社」）と、ソフトウェア<b>「Manual Studio」</b>（以下「本ソフトウェア」）をダウンロード、複製、インストール、または使用する個人または法人（以下「ユーザー」）との間で締結される法的拘束力を有するライセンス契約です。ユーザーが本ソフトウェアをダウンロード、インストール、または使用した時点で、本契約のすべての条項に同意したものとみなされます。",
            "articles": [
                (
                    "第1条 (目的)",
                    "本契約は、当社が開発した本ソフトウェアに関する非独占的かつ譲渡不可能な使用権をユーザーに許諾し、当事者間の権利および義務を定めることを目的とします。"
                ),
                (
                    "第2条 (知的財産権の帰属)",
                    "1. 本ソフトウェア、関連文書、ソースコード、バイナリ、グラフィックス、UI/UXデザインに関する著作権、特許権、商標権、営業秘密を含む一切の知的財産権は、大韓民国著作権法および国際条約に基づき、<b>株式会社DragonRPA</b>に排他的に帰属します。<br/>"
                    "2. 本契約に基づく提供は所有権の移転を意味するものではなく、定められた条件の範囲内における<b>「限定的使用権（ライセンス）」</b>のみを許諾するものです。"
                ),
                (
                    "第3条 (ライセンスの範囲および条件)",
                    "1. <b>[評価版/トライアル (Trial License)]</b>: 当社が公開した評価版は、指定された有効期限内（2026年12月31日まで）に限り、非商用目的での機能確認および評価にのみ無償で使用できます。期限満了後は正規ライセンスを購入することなく継続して使用することはできません。<br/>"
                    "2. <b>[正規ライセンス (Commercial License)]</b>: 正式ライセンスは、1つのライセンスキーにつき指定された単一のハードウェア端末（1PC-1Key ノードロック）でのみインストールおよび実行が許可されます。"
                ),
                (
                    "第4条 (禁止事項 - リバースエンジニアリングおよび無断配布の禁止)",
                    "ユーザーは以下の行為を行ってはならず、違反した場合は著作権法等に基づき民事上および刑事上の責任を負います。<br/>"
                    "1. <b>リバースエンジニアリングの禁止</b>: ソースコードや内部アルゴリズムを抽出するためのリバースエンジニアリング、逆コンパイル(Decompile)、逆アセンブル(Disassemble)、またはコード改変行為。<br/>"
                    "2. <b>セキュリティ機構の改ざん禁止</b>: ハードウェア識別子(HWID)、時計改ざん防止機能、暗号化キーなどのライセンス認証機構を迂回、改ざん、クラックする行為。<br/>"
                    "3. <b>無断再配布および商用再販の禁止</b>: 当社の事前の書面による承諾なく、第三者へ有償販売、貸与、譲渡、または公衆送信/オンライン配布する行為。<br/>"
                    "4. <b>著作権表示の削除禁止</b>: 本ソフトウェア内に表示されている商標、ロゴ、著作権表示、評価版告知等の法的通知を改変または削除する行為。"
                ),
                (
                    "第5条 (保証の制限および免責)",
                    "1. 本ソフトウェアは<b>「現状有姿(AS-IS)」</b>で提供され、当社は特定目的への適合性やエラーのない動作を含め、明示的にも黙示的にもいかなる保証も行いません。<br/>"
                    "2. 当社は、本ソフトウェアの使用または使用不能から生じるいかなる間接損害、付随的損害（営業損失、データ消失等）についても一切の責任を負いません。"
                ),
                (
                    "第6条 (違約罰および損害賠償)",
                    "ユーザーが故意または重大な過失により第4条（禁止事項）に違反した場合、<b>正規ライセンス定価の5倍に相当する金額を違約罰として当社に直ちに支払う</b>ものとし、当社が被った実際の損害全額を別途賠償するものとします。"
                ),
                (
                    "第7条 (準拠法および管轄裁判所)",
                    "本契約は大韓民国の法律に準拠し、これに従って解釈されます。本契約に関連して生じる一切の紛争については、<b>株式会社DragonRPAの本店所在地を管轄する大韓民国の裁判所（ソウル中央地方法院）</b>を第一審の専属的合意管轄裁判所とします。"
                )
            ],
            "footer": "告知日: 2026.09.11 | 施行日: 2026.09.11<br/>株式会社DragonRPA (DragonRPA Co., Ltd.) | 代表取締役: 李廷龍 (Lee Jeong-yong) | お問い合わせ: 77.victor.lee@gmail.com",
            "dialog_title": "エンドユーザー使用許諾契約書 (EULA) - 株式会社DragonRPA",
            "btn_close": "閉じる",
            "btn_copy": "📋 全文コピー",
            "copied_toast": "EULAの内容がクリップボードにコピーされました。"
        },
        "de": {
            "title": "DragonRPA Endbenutzer-Lizenzvertrag (EULA)",
            "subtitle": "End User License Agreement for Manual Studio | DragonRPA Co., Ltd.",
            "preamble": "Dieser Endbenutzer-Lizenzvertrag („Vertrag“ oder „EULA“) ist eine rechtsverbindliche Vereinbarung zwischen der <b>DragonRPA Co., Ltd.</b> („Unternehmen“) und jeder natürlichen oder juristischen Person („Benutzer“), die die Software <b>‚Manual Studio‘</b> („Software“) herunterlädt, kopiert, installiert oder verwendet. Durch das Herunterladen, Installieren oder Verwenden der Software erklärt sich der Benutzer mit den Bestimmungen dieses Vertrags einverstanden.",
            "articles": [
                (
                    "Artikel 1 (Zweck)",
                    "Zweck dieses Vertrags ist die Gewährung einer nicht-exklusiven, nicht übertragbaren Lizenz zur Nutzung der vom Unternehmen entwickelten Software an den Benutzer sowie die Festlegung der gegenseitigen Rechte und Pflichten."
                ),
                (
                    "Artikel 2 (Geistiges Eigentum und Inhaberschaft)",
                    "1. Sämtliche Urheberrechte, Patente, Marken, Geschäftsgeheimnisse und sonstigen geistigen Eigentumsrechte an der Software, Dokumentation, Quellcode, Binärdateien, Grafiken und UI/UX-Designs stehen nach dem Urheberrechtsgesetz der Republik Korea und internationalen Abkommen ausschließlich der <b>DragonRPA Co., Ltd.</b> zu.<br/>"
                    "2. Dieser Vertrag begründet keine Eigentumsübertragung, sondern gewährt lediglich ein <b>beschränktes Nutzungsrecht (Lizenz)</b> im Rahmen der festgelegten Bedingungen."
                ),
                (
                    "Artikel 3 (Umfang der Lizenz und Bedingungen)",
                    "1. <b>[Testlizenz (Trial License)]</b>: Die vom Unternehmen bereitgestellte Evaluierungsversion darf ausschließlich während der angegebenen Gültigkeitsdauer (bis zum 31. Dezember 2026) für nicht-kommerzielle Funktionsprüfungen und Bewertungen kostenfrei genutzt werden. Eine Weiternutzung nach Ablauf ist ohne kommerzielle Lizenz unzulässig.<br/>"
                    "2. <b>[Kommerzielle Lizenz (Commercial License)]</b>: Eine reguläre Lizenz berechtigt zur Installation und Ausführung auf einem einzigen festgelegten Hardware-Gerät pro Lizenzschlüssel (1PC-1Key Node-Locked)."
                ),
                (
                    "Artikel 4 (Unzulässige Handlungen - Reverse Engineering und Vertriebsverbot)",
                    "Dem Benutzer sind folgende Handlungen untersagt; Zuwiderhandlungen führen zu zivil- und strafrechtlicher Verfolgung:<br/>"
                    "1. <b>Verbot von Reverse Engineering</b>: Zurückentwicklung, Dekompilierung (Decompile), Disassemblierung (Disassemble) oder Quellcode-Modifikation zur Offenlegung von Algorithmen oder Quellcode.<br/>"
                    "2. <b>Verbot der Manipulation von Sicherheitsmechanismen</b>: Umgehung, Modifikation oder Cracking von Lizenzprüfungen wie Hardware-ID (HWID), Zeitsperren oder kryptografischen Schlüsseln.<br/>"
                    "3. <b>Verbot unbefugter Weitergabe und Weiterverkaufs</b>: Vermietung, Verleih, Unterlizenzierung oder öffentliche Verbreitung im Internet ohne vorherige schriftliche Zustimmung des Unternehmens.<br/>"
                    "4. <b>Verbot der Entfernung von Urheberrechtshinweisen</b>: Veränderung oder Löschung von im Programm enthaltenen Marken, Logos, Urheberrechts- und Testzeitraum-Hinweisen."
                ),
                (
                    "Artikel 5 (Haftungsausschluss und Gewährleistungsbegrenzung)",
                    "1. Die Software wird im Zustand <b>„WIE BESEHEN“ („AS-IS“)</b> ohne jegliche ausdrückliche oder stillschweigende Gewährleistung zur Verfügung gestellt.<br/>"
                    "2. Das Unternehmen haftet nicht für mittelbare, beiläufige oder Folgeschäden (einschließlich entgangenen Gewinns, Betriebsunterbrechungen oder Datenverlust)."
                ),
                (
                    "Artikel 6 (Vertragsstrafe und Schadensersatz)",
                    "Verletzt der Benutzer vorsätzlich oder grob fahrlässig die Bestimmungen des Artikels 4 (Unzulässige Handlungen), so hat er unverzüglich eine <b>Vertragsstrafe in Höhe des 5-fachen regulären Listenpreises der kommerziellen Lizenz</b> an das Unternehmen zu entrichten, unbeschadet weitergehender Schadensersatzansprüche."
                ),
                (
                    "Artikel 7 (Anwendbares Recht und Gerichtsstand)",
                    "Dieser Vertrag unterliegt dem Recht der Republik Korea. Für alle Streitigkeiten aus oder im Zusammenhang mit diesem Vertrag ist das <b>für den Hauptsitz der DragonRPA Co., Ltd. zuständige Gericht in der Republik Korea (Bezirksgericht Seoul Central)</b> als erstinstanzliches Gericht ausschließlich zuständig."
                )
            ],
            "footer": "Bekanntmachung: 2026.09.11 | Inkrafttreten: 2026.09.11<br/>DragonRPA Co., Ltd. | CEO: Lee Jeong-yong | Kontakt: 77.victor.lee@gmail.com",
            "dialog_title": "Endbenutzer-Lizenzvertrag (EULA) - DragonRPA Co., Ltd.",
            "btn_close": "Schließen",
            "btn_copy": "📋 Alles kopieren",
            "copied_toast": "EULA-Inhalt in die Zwischenablage kopiert."
        },
        "es": {
            "title": "Contrato de Licencia de Usuario Final de DragonRPA (EULA)",
            "subtitle": "Acuerdo de Licencia de Usuario Final para Manual Studio | DragonRPA Co., Ltd.",
            "preamble": "El presente Contrato de Licencia de Usuario Final (\"Contrato\" o \"EULA\") es un acuerdo legalmente vinculante entre <b>DragonRPA Co., Ltd.</b> (\"Compañía\") y cualquier persona física o jurídica (\"Usuario\") que descargue, copie, instale o utilice el software <b>'Manual Studio'</b> (\"Software\"). La descarga, instalación o uso del Software implica la aceptación plena de las condiciones aquí estipuladas.",
            "articles": [
                (
                    "Artículo 1 (Objeto)",
                    "El objeto del presente Contrato es otorgar al Usuario una licencia no exclusiva e intransferible para el uso del Software desarrollado por la Compañía, así como regular los derechos y obligaciones de ambas partes."
                ),
                (
                    "Artículo 2 (Propiedad Intelectual y Titularidad)",
                    "1. Todos los derechos de autor, patentes, marcas registradas, secretos comerciales y demás derechos de propiedad intelectual relativos al Software, documentación, código fuente, binarios, gráficos y diseño UI/UX pertenecen exclusivamente a <b>DragonRPA Co., Ltd.</b> de conformidad con la Ley de Propiedad Intelectual de la República de Corea y tratados internacionales.<br/>"
                    "2. La provisión del Software bajo este Contrato no implica transferencia de propiedad, concediendo únicamente una <b>licencia de uso limitada (License)</b> dentro de los términos acordados."
                ),
                (
                    "Artículo 3 (Alcance y Condiciones de la Licencia)",
                    "1. <b>[Licencia de Evaluación / Prueba (Trial)]</b>: La versión de prueba se proporciona de forma gratuita exclusivamente para evaluación no comercial y verificación de funciones durante el periodo de vigencia especificado (hasta el 31 de diciembre de 2026). Queda prohibido su uso continuado tras el vencimiento sin una licencia comercial válida.<br/>"
                    "2. <b>[Licencia Comercial]</b>: La licencia comercial regular autoriza la instalación y ejecución en un único equipo de hardware determinado por clave de licencia (1PC-1Key Bloqueo por Nodo)."
                ),
                (
                    "Artículo 4 (Conductas Prohibidas - Prohibición de Ingeniería Inversa y Redistribución)",
                    "El Usuario tiene estrictamente prohibido realizar cualquiera de los siguientes actos, incurriendo en responsabilidades civiles y penales en caso de infracción:<br/>"
                    "1. <b>Prohibición de ingeniería inversa</b>: Descompilar (Decompile), desensamblar (Disassemble) o realizar ingeniería inversa para obtener el código fuente o algoritmos.<br/>"
                    "2. <b>Prohibición de vulneración de seguridad</b>: Eludir, alterar o crackear mecanismos de verificación de licencias (HWID, protección contra manipulación de reloj o claves criptográficas).<br/>"
                    "3. <b>Prohibición de redistribución no autorizada y reventa</b>: Vender, alquilar, sublicenciar o distribuir el Software en redes públicas sin autorización previa por escrito.<br/>"
                    "4. <b>Prohibición de eliminación de avisos legales</b>: Modificar o eliminar marcas, logotipos o avisos de derechos de autor y vigencia de prueba."
                ),
                (
                    "Artículo 5 (Exclusión de Garantías y Límite de Responsabilidad)",
                    "1. El Software se suministra <b>\"TAL CUAL\" (\"AS-IS\")</b> sin garantías de ningún tipo, expresas o implícitas, en cuanto a idoneidad para un fin determinado o funcionamiento libre de errores.<br/>"
                    "2. La Compañía no será responsable por daños indirectos, imprevistos o consecuentes (pérdida de beneficios comerciales, interrupción del negocio o pérdida de datos)."
                ),
                (
                    "Artículo 6 (Cláusula Penal e Indemnización)",
                    "En caso de infracción dolosa o por negligencia grave del Artículo 4, el Usuario deberá <b>abonar de inmediato a la Compañía una cláusula penal equivalente a 5 (cinco) veces el precio oficial de la licencia comercial</b>, sin perjuicio de la reclamación íntegra por los daños y perjuicios reales causados."
                ),
                (
                    "Artículo 7 (Ley Aplicable y Jurisdicción Exclusiva)",
                    "El presente Contrato se regirá e interpretará conforme a las leyes de la República de Corea. Cualquier litigio o controversia será sometido a la <b>jurisdicción exclusiva del tribunal correspondiente a la sede principal de DragonRPA Co., Ltd. (Tribunal de Distrito Central de Seúl)</b>."
                )
            ],
            "footer": "Fecha de publicación: 2026.09.11 | Fecha de entrada en vigor: 2026.09.11<br/>DragonRPA Co., Ltd. | Director Ejecutivo: Lee Jeong-yong | Contacto: 77.victor.lee@gmail.com",
            "dialog_title": "Contrato de Licencia de Usuario Final (EULA) - DragonRPA Co., Ltd.",
            "btn_close": "Cerrar",
            "btn_copy": "📋 Copiar todo",
            "copied_toast": "Contenido del EULA copiado al portapapeles."
        },
        "fr": {
            "title": "Contrat de Licence Utilisateur Final DragonRPA (EULA)",
            "subtitle": "Contrat de Licence Utilisateur Final pour Manual Studio | DragonRPA Co., Ltd.",
            "preamble": "Le présent Contrat de Licence Utilisateur Final (« Contrat » ou « EULA ») constitue un accord juridiquement contraignant entre <b>DragonRPA Co., Ltd.</b> (« Société ») et toute personne physique ou morale (« Utilisateur ») téléchargeant, installant, copiant ou utilisant le logiciel <b>'Manual Studio'</b> (« Logiciel »). Le téléchargement, l'installation ou l'utilisation du Logiciel vaut acceptation pleine et entière des présentes conditions.",
            "articles": [
                (
                    "Article 1 (Objet)",
                    "Le présent Contrat a pour objet d'accorder à l'Utilisateur une licence d'utilisation non exclusive et non transférable du Logiciel développé par la Société et de définir les droits et obligations des parties."
                ),
                (
                    "Article 2 (Propriété Intellectuelle et Titularité)",
                    "1. Tous les droits d'auteur, brevets, marques, secrets commerciaux et autres droits de propriété intellectuelle afférents au Logiciel, à la documentation, au code source, aux fichiers binaires, aux graphiques et à l'interface UI/UX sont la propriété exclusive de <b>DragonRPA Co., Ltd.</b>, conformément à la législation de la République de Corée et aux conventions internationales.<br/>"
                    "2. La fourniture du Logiciel n'emporte aucun transfert de propriété, ne conférant qu'un <b>droit d'usage limité (Licence)</b> dans les conditions stipulées."
                ),
                (
                    "Article 3 (Étendue de la Licence et Conditions)",
                    "1. <b>[Licence d'Évaluation / Essai (Trial)]</b>: La version d'évaluation fournie par la Société est accordée à titre gratuit exclusivement pour un examen non commercial et des tests fonctionnels durant la période de validité fixée (jusqu'au 31 décembre 2026). Toute utilisation continue après expiration sans licence commerciale est strictement prohibée.<br/>"
                    "2. <b>[Licence Commerciale]</b>: Une licence commerciale régulière autorise l'installation et l'exécution sur un seul appareil matériel désigné par clé de licence (1PC-1Key Verrouillage par Nœud)."
                ),
                (
                    "Article 4 (Actes Interdits - Rétro-ingénierie et Diffusion Non Autorisée)",
                    "Il est strictement interdit à l'Utilisateur de commettre les actes suivants sous peine de poursuites civiles et pénales:<br/>"
                    "1. <b>Interdiction de rétro-ingénierie</b>: Décompiler (Decompile), désassembler (Disassemble) ou effectuer toute rétro-ingénierie pour extraire le code source ou les algorithmes.<br/>"
                    "2. <b>Interdiction de falsification des mécanismes de sécurité</b>: Contourner, modifier ou pirater les systèmes de vérification de licence (HWID, protection de l'horloge, clés de chiffrement).<br/>"
                    "3. <b>Interdiction de redistribution et revente non autorisées</b>: Vendre, louer, sous-licencier ou diffuser le Logiciel sur des réseaux publics sans autorisation écrite préalable de la Société.<br/>"
                    "4. <b>Interdiction de suppression des mentions de réserve</b>: Modifier ou supprimer les marques, logos ou mentions de droit d'auteur et de période d'essai intégrés au Logiciel."
                ),
                (
                    "Article 5 (Limitation de Garantie et Exonération de Responsabilité)",
                    "1. Le Logiciel est fourni <b>« EN L'ÉTAT » (« AS-IS »)</b> sans aucune garantie expresse ou tacite relative à son aptitude à un usage particulier ou à l'absence d'erreurs.<br/>"
                    "2. La Société décline toute responsabilité pour les préjudices indirects, accessoires ou consécutifs (perte de bénéfices commerciaux, interruption d'activité ou perte de données)."
                ),
                (
                    "Article 6 (Clause Pénale et Dommages-Intérêts)",
                    "En cas de violation intentionnelle ou par négligence grave de l'Article 4, l'Utilisateur sera tenu de <b>verser immédiatement à la Société, à titre de clause pénale forfaitaire, une somme correspondant à 5 (cinq) fois le prix officiel de la licence commerciale</b>, sans préjudice du droit de la Société d'exiger la réparation intégrale du préjudice réel subi."
                ),
                (
                    "Article 7 (Droit Applicable et Attribution de Juridiction)",
                    "Le présent Contrat est régi et interprété conformément aux lois de la République de Corée. Tout litige relatif au présent Contrat sera soumis à la <b>compétence exclusive du tribunal du ressort du siège social de DragonRPA Co., Ltd. (Tribunal du District Central de Séoul)</b> en première instance."
                )
            ],
            "footer": "Date de publication: 2026.09.11 | Date d'entrée en vigueur: 2026.09.11<br/>DragonRPA Co., Ltd. | PDG: Lee Jeong-yong | Contact: 77.victor.lee@gmail.com",
            "dialog_title": "Contrat de Licence Utilisateur Final (EULA) - DragonRPA Co., Ltd.",
            "btn_close": "Fermer",
            "btn_copy": "📋 Tout copier",
            "copied_toast": "Contenu du CLUF copié dans le presse-papiers."
        },
        "pt": {
            "title": "Contrato de Licença de Usuário Final DragonRPA (EULA)",
            "subtitle": "Termos de Licença de Usuário Final para Manual Studio | DragonRPA Co., Ltd.",
            "preamble": "O presente Contrato de Licença de Usuário Final (\"Contrato\" ou \"EULA\") é um acordo legalmente vinculativo entre a <b>DragonRPA Co., Ltd.</b> (\"Empresa\") e qualquer pessoa física ou jurídica (\"Usuário\") que baixe, instale, copie ou utilize o software <b>'Manual Studio'</b> (\"Software\"). Ao baixar, instalar ou utilizar o Software, o Usuário concorda com todos os termos e condições deste instrumento.",
            "articles": [
                (
                    "Artigo 1º (Objetivo)",
                    "O objetivo deste Contrato é conceder ao Usuário uma licença não exclusiva e intransferível de uso do Software desenvolvido pela Empresa, estabelecendo os direitos e obrigações mútuos."
                ),
                (
                    "Artigo 2º (Propriedade Intelectual e Titularidade)",
                    "1. Todos os direitos autorais, patentes, marcas comerciais, segredos industriais e demais direitos de propriedade intelectual relativos ao Software, documentação, código-fonte, binários, gráficos e design de UI/UX pertencem com exclusividade à <b>DragonRPA Co., Ltd.</b>, nos termos da legislação da República da Coreia e de tratados internacionais.<br/>"
                    "2. O fornecimento do Software não representa cessão de propriedade, conferindo unicamente uma <b>licença limitada de uso (License)</b> sob as condições estipuladas."
                ),
                (
                    "Artigo 3º (Escopo e Condições da Licença)",
                    "1. <b>[Licença de Avaliação / Teste (Trial)]</b>: A versão de teste disponibilizada pela Empresa destina-se exclusivamente a testes funcionais e avaliação não comercial durante o período de vigência estipulado (até 31 de dezembro de 2026). O uso contínuo após o vencimento sem licença comercial é expressamente proibido.<br/>"
                    "2. <b>[Licença Comercial]</b>: A licença comercial regular autoriza a instalação e execução em uma única máquina física designada por chave de licença (1PC-1Key Bloqueio por Nó)."
                ),
                (
                    "Artigo 4º (Atos Proibidos - Vedação à Engenharia Reversa e Redistribuição)",
                    "O Usuário não praticará nenhum dos seguintes atos, sujeitando-se às penalidades civis e criminais cabíveis:<br/>"
                    "1. <b>Vedação à engenharia reversa</b>: Descompilar (Decompile), desmontar (Disassemble) ou realizar engenharia reversa para extrair código-fonte ou algoritmos.<br/>"
                    "2. <b>Vedação à manipulação de segurança</b>: Burlar, alterar ou violar travas de licença (HWID, proteção de data/hora ou chaves criptográficas).<br/>"
                    "3. <b>Vedação à redistribuição não autorizada e revenda</b>: Vender, alugar, sublicenciar ou disponibilizar o Software em redes públicas sem prévia autorização por escrito.<br/>"
                    "4. <b>Vedação à remoção de avisos legais</b>: Alterar ou suprimir marcas, logotipos ou avisos de direitos autorais e de período de avaliação."
                ),
                (
                    "Artigo 5º (Exclusão de Garantias e Limitação de Responsabilidade)",
                    "1. O Software é fornecido <b>\"NO ESTADO EM QUE SE ENCONTRA\" (\"AS-IS\")</b>, sem qualquer garantia expressa ou implícita quanto à adequação a finalidades específicas ou operação isenta de erros.<br/>"
                    "2. A Empresa não se responsabiliza por quaisquer danos indiretos, incidentais ou emergentes (perda de lucros comerciais, interrupção de atividades ou perda de dados)."
                ),
                (
                    "Artigo 6º (Cláusula Penal e Indenização)",
                    "Havendo descumprimento doloso ou com culpa grave do Artigo 4º, o Usuário deverá <b>pagar imediatamente à Empresa, a título de cláusula penal punitiva, quantia equivalente a 5 (cinco) vezes o valor oficial da licença comercial</b>, sem prejuízo da indenização integral por perdas e danos reais."
                ),
                (
                    "Artigo 7º (Legislação Aplicável e Foro de Eleição)",
                    "Este Contrato é regido pelas leis da República da Coreia. Fica eleito com exclusividade o <b>foro da sede principal da DragonRPA Co., Ltd. (Tribunal do Distrito Central de Seul, República da Coreia)</b> para dirimir quaisquer litígios oriundos deste Contrato."
                )
            ],
            "footer": "Data de divulgação: 2026.09.11 | Data de vigência: 2026.09.11<br/>DragonRPA Co., Ltd. | Diretor Executivo: Lee Jeong-yong | Contato: 77.victor.lee@gmail.com",
            "dialog_title": "Contrato de Licença de Usuário Final (EULA) - DragonRPA Co., Ltd.",
            "btn_close": "Fechar",
            "btn_copy": "📋 Copiar tudo",
            "copied_toast": "Conteúdo do EULA copiado para a área de transferência."
        },
        "ru": {
            "title": "Лицензионное соглашение с конечным пользователем DragonRPA (EULA)",
            "subtitle": "Лицензионное соглашение для Manual Studio | DragonRPA Co., Ltd.",
            "preamble": "Настоящее Лицензионное соглашение с конечным пользователем («Соглашение» или «EULA») представляет собой юридически обязательный договор между <b>DragonRPA Co., Ltd.</b> («Компания») и любым физическим или юридическим лицом («Пользователь»), осуществляющим загрузку, установку, копирование или использование программы <b>'Manual Studio'</b> («Программное обеспечение»). Загрузка, установка или использование Программного обеспечения означает полное согласие Пользователя со всеми условиями настоящего Соглашения.",
            "articles": [
                (
                    "Статья 1 (Предмет соглашения)",
                    "Настоящее Соглашение предоставляет Пользователю неисключительную, не подлежащую передаче лицензию на использование Программного обеспечения, разработанного Компанией, и определяет взаимные права и обязанности сторон."
                ),
                (
                    "Статья 2 (Интеллектуальная собственность и права владения)",
                    "1. Все авторские права, патенты, товарные знаки, ноу-хау и иные права интеллектуальной собственности на Программное обеспечение, документацию, исходный код, бинарные файлы, графику и интерфейс UI/UX принадлежат исключительно <b>DragonRPA Co., Ltd.</b> в соответствии с законодательством Республики Корея и международными договорами.<br/>"
                    "2. Предоставление Программного обеспечения не означает передачу права собственности, а предоставляет лишь <b>ограниченное право использования (Лицензию)</b> на оговоренных условиях."
                ),
                (
                    "Статья 3 (Объем лицензии и условия)",
                    "1. <b>[Ознакомительная / Пробная лицензия (Trial)]</b>: Пробная версия предоставляется Компанией бесплатно исключительно для некоммерческого тестирования функций и оценки в течение установленного срока (до 31 декабря 2026 года). Использование после истечения срока без коммерческой лицензии строго запрещено.<br/>"
                    "2. <b>[Коммерческая лицензия (Commercial License)]</b>: Официальная коммерческая лицензия разрешает установку и запуск только на одном указанном аппаратном компьютере по лицензионному ключу (1PC-1Key с аппаратной привязкой)."
                ),
                (
                    "Статья 4 (Запрещенные действия - Обратная разработка и распространение)",
                    "Пользователю строго запрещается совершать следующие действия под угрозой гражданской и уголовной ответственности:<br/>"
                    "1. <b>Запрет обратной разработки</b>: Декомпиляция (Decompile), дизассемблирование (Disassemble) или реверс-инжиниринг с целью извлечения исходного кода или алгоритмов.<br/>"
                    "2. <b>Запрет обхода механизмов защиты</b>: Обход, модификация или взлом средств проверки лицензии (HWID, защита системных часов, ключи шифрования).<br/>"
                    "3. <b>Запрет несанкционированного распространения и перепродажи</b>: Продажа, сдача в аренду, сублицензирование или размещение Программного обеспечения в открытом доступе в сети Интернет без письменного согласия Компании.<br/>"
                    "4. <b>Запрет удаления уведомлений об авторских правах</b>: Изменение или удаление товарных знаков, логотипов и правовых уведомлений об авторских правах или сроках пробного периода."
                ),
                (
                    "Статья 5 (Отказ от гарантий и ограничение ответственности)",
                    "1. Программное обеспечение предоставляется на условиях <b>«КАК ЕСТЬ» («AS-IS»)</b> без каких-либо явных или подразумеваемых гарантий пригодности для конкретных целей или безошибочной работы.<br/>"
                    "2. Компания не несет ответственности за любые косвенные, случайные или сопутствующие убытки (включая упущенную выгоду, перерыв в деятельности или потерю данных)."
                ),
                (
                    "Статья 6 (Неустойка и возмещение убытков)",
                    "При умышленном или грубо неосторожном нарушении Статьи 4 Пользователь обязуется <b>незамедлительно выплатить Компании штрафную неустойку в размере 5-кратной официальной стоимости коммерческой лицензии</b>, а также в полном объеме возместить фактически понесенные Компанией убытки."
                ),
                (
                    "Статья 7 (Применимое право и исключительная подсудность)",
                    "Настоящее Соглашение регулируется и толкуется в соответствии с законодательством Республики Корея. Все споры, возникающие из настоящего Соглашения, подлежат <b>исключительному рассмотрению в суде по месту нахождения головного офиса DragonRPA Co., Ltd. (Центральный районный суд Сеула)</b> в качестве суда первой инстанции."
                )
            ],
            "footer": "Дата объявления: 2026.09.11 | Дата вступления в силу: 2026.09.11<br/>DragonRPA Co., Ltd. | Генеральный директор: Ли Чон Ён (Lee Jeong-yong) | Контакт: 77.victor.lee@gmail.com",
            "dialog_title": "Лицензионное соглашение (EULA) - DragonRPA Co., Ltd.",
            "btn_close": "Закрыть",
            "btn_copy": "📋 Копировать всё",
            "copied_toast": "Текст EULA скопирован в буфер обмена."
        }
    }

    @classmethod
    def normalize_locale(cls, locale_code: str) -> str:
        """Normalize locale string to 2-letter lowercase code."""
        if not locale_code:
            return "ko"
        loc = locale_code.strip().lower()
        if "_" in loc:
            loc = loc.split("_")[0]
        if "-" in loc:
            loc = loc.split("-")[0]
        if loc in cls._DATA:
            return loc
        return "en" if "en" in cls._DATA else "ko"

    @classmethod
    def get_supported_locales(cls) -> Dict[str, str]:
        """Return supported locale mapping."""
        return dict(cls.SUPPORTED_LOCALES)

    @classmethod
    def get_eula_html(cls, locale_code: str = "ko") -> str:
        """
        Generate structured, beautifully styled HTML for the given locale.
        """
        loc = cls.normalize_locale(locale_code)
        data = cls._DATA.get(loc, cls._DATA["en"])

        html_parts = []
        html_parts.append(f'<h3 style="color:#0F172A; margin-bottom:4px; font-size:15px;">{data["title"]}</h3>')
        html_parts.append(f'<p style="color:#64748B; font-size:11px; margin-top:0; margin-bottom:8px;">{data["subtitle"]}</p>')
        html_parts.append('<hr style="border:0; border-top:1px solid #CBD5E1; margin:8px 0;"/>')
        html_parts.append(f'<p style="line-height:1.6; margin-bottom:12px;">{data["preamble"]}</p>')

        for title, content in data["articles"]:
            # Highlight Article 6 (Liquidated damages 5x)
            is_article_6 = "6" in title or "第6条" in title or "6조" in title or "6º" in title or "Artikel 6" in title or "Article 6" in title or "Artículo 6" in title
            if is_article_6:
                html_parts.append(f'<h4 style="color:#B91C1C; margin-top:16px; margin-bottom:4px; font-size:12.5px;">⚠️ {title}</h4>')
                html_parts.append(
                    f'<div style="background-color:#FEF2F2; border-left:4px solid #EF4444; padding:8px 12px; margin:6px 0; border-radius:4px; line-height:1.6;">'
                    f'{content}'
                    f'</div>'
                )
            else:
                html_parts.append(f'<h4 style="color:#1E40AF; margin-top:14px; margin-bottom:4px; font-size:12.5px;">{title}</h4>')
                html_parts.append(f'<p style="line-height:1.6; margin-top:2px; margin-bottom:8px;">{content}</p>')

        html_parts.append('<hr style="border:0; border-top:1px solid #CBD5E1; margin:12px 0 8px 0;"/>')
        html_parts.append(f'<p style="font-size:10.5px; color:#64748B; line-height:1.5;">{data["footer"]}</p>')

        return "\n".join(html_parts)

    @classmethod
    def get_eula_plain(cls, locale_code: str = "ko") -> str:
        """
        Generate plain text version suitable for clipboard or console/export.
        """
        loc = cls.normalize_locale(locale_code)
        data = cls._DATA.get(loc, cls._DATA["en"])

        def clean_html(text: str) -> str:
            t = text.replace("<br/>", "\n").replace("<br>", "\n")
            t = t.replace("<b>", "").replace("</b>", "")
            return t

        lines = []
        lines.append("=" * 72)
        lines.append(data["title"])
        lines.append(data["subtitle"])
        lines.append("=" * 72)
        lines.append("")
        lines.append(clean_html(data["preamble"]))
        lines.append("")

        for title, content in data["articles"]:
            lines.append("-" * 50)
            lines.append(title)
            lines.append("-" * 50)
            lines.append(clean_html(content))
            lines.append("")

        lines.append("=" * 72)
        lines.append(clean_html(data["footer"]))
        lines.append("=" * 72)

        return "\n".join(lines)

    @classmethod
    def get_dialog_title(cls, locale_code: str = "ko") -> str:
        """Return localized dialog title."""
        loc = cls.normalize_locale(locale_code)
        return cls._DATA.get(loc, cls._DATA["en"]).get("dialog_title", "EULA")

    @classmethod
    def get_ui_labels(cls, locale_code: str = "ko") -> Dict[str, str]:
        """Return localized UI action labels."""
        loc = cls.normalize_locale(locale_code)
        d = cls._DATA.get(loc, cls._DATA["en"])
        return {
            "btn_close": d.get("btn_close", "Close"),
            "btn_copy": d.get("btn_copy", "Copy All"),
            "copied_toast": d.get("copied_toast", "Copied to clipboard.")
        }
