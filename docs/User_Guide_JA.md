# Manual Studio v1.4.0 ユーザーガイド
> **PowerPoint マニュアル作成自動化ソリューション • DragonRPA Co.**
> *Official Release Build v1.4.0 | (주)드래곤알피에이 (DragonRPA Co., Ltd.)*

---

## 📌 1. 主な機能
Manual Studio は、画面キャプチャから 10 種類の注釈編集、社内 PPT テンプレートの適用、スライド自動生成までをワンストップで完結する業務標準化ソフトウェアです。

![Manual Studio Main Window Interface](images/guide_main_window.png)

---

## ⚡ 2. ショートカットと即時キャプチャ

| ショートカット | 機能名 | 説明 |
| :--- | :--- | :--- |
| **`F9`** | 固定座標キャプチャ | 指定された画面領域を即座にキャプチャ |
| **`Shift + F9`** | 範囲指定キャプチャ | マウスを離すと Enter キー入力待機なしで即座に確定 |
| **`F8`** | 追加部分キャプチャ | サブウィンドウやダイアログを追加切り抜きしてオーバーレイ配置 |
| **`F10`** | PPT スライド生成 | PowerPoint に新スライドを作成し、クリップボードにも転送 |
| **`Ctrl + S`** | プロジェクト保存 | 元画像とベクター注釈データを `.mcs.json` に完全保存 |
| **`Ctrl + Z`** | 元に戻す | 直前の編集操作をロールバック |


> **Tip**: Shift+F9 또는 F8 캡처 시, 마우스 드래그를 마치고 손을 떼는 순간(Mouse Release) 엔터키 입력 대기 없이 즉시 확정되어 캔버스에 안착됩니다.

---

## 🎨 3. 10 種の専門注釈ツール

1. **① 番号スタンプ**: クリックするたびにカウントアップする番号スタンプ
2. **①➔ ステップ矢印**: スタンプと一体化した方向指示矢印
3. **↳ 直角エルボー矢印**: 複雑な UI を迂回して指示する直角矢印（Tab キーで経路切替）
4. **↗ 直線矢印**: 正確なポイント指示を行うベクトル矢印
5. **🔲 強調ボックス**: メニューや入力欄を囲む枠線または半透明塗りつぶしボックス
6. **🌫 モザイクぼかし**: 個人情報やパスワードをドラッグで即座に目隠し
7. **💬 説明吹き出し**: 引き出し線の位置を自由に調整できる丸角吹き出し
8. **🔤 テキストラベル**: メイリオ(Meiryo)や Yu Gothic に対応した見やすいテキスト
9. **⌨ ショートカットキーバッジ**: キートップを模した立体的なキーバッジ
10. **✨ ワードアート**: 5 種類の高品質プリセットタイトル


![Annotation Tools and Canvas Overview](images/guide_annotations.png)

---

## 📊 4. 社内 PPT マスター連携とスライド作成

- **社内 PPT マスターテンプレート(`.pptx`)の自動適用**:
  - 設定画面でテンプレートファイルを指定すると、スライド作成時に社内ロゴや規定レイアウトが自動的に引き継がれます。
- **スライド幅の自動統一**:
  - 横幅 960px または 16:9 の最適比率で綺麗に配置されます。
- **ステップ番号の一括自動再採番**:
  - `編集 -> 🔢 PPT Step 番号自動再整列` で、全スライドの `Step {n}.` 番号を 1 秒で整列します。


![Settings and Master Template Configuration](images/guide_settings_dialog.png)

---

## 💾 5. 自動保存および障害復旧機能

- **自動保存機能**:
  - 1〜30分の間隔で作業内容をバックグラウンド自動保存。
- **起動時ワンクリック復元**:
  - 突然のシャットダウン後も、再起動時に保存データから作業を即座に再開できます。


---

## 🔑 6. ライセンス登録とウォーターマーク

- **評価版について**:
  - 未認証状態では、クリップボード出力および PPT スライドに 'Manual Studio' の半透明ウォーターマークが表示されます。
- **ライセンスの登録**:
  - `設定 -> 🔑 ライセンス登録` よりハードウェア ID (HWID) を確認し、発行されたシリアルキーを入力して認証するとウォーターマークが解除されます。
- **ライセンス区分**:
  - ① 1コピー永久ライセンス (`MS1P`)
  - ② 1コピー1ヶ月サブスクリプション (`MS1M`)
  - ③ 1コピー1年サブスクリプション (`MS1Y`)
  - ④ エンタープライズボリューム (`MSENT`)
  - ⑤ クローズドネットワーク・サイトライセンス (`MSSITE`)
  - ⑥ 14日評価延長 (`MST14`)


![License Registration Dialog](images/guide_license_dialog.png)

---

## 🌐 7. 多言語対応（日本語フォント対応）
- **9 Supported Global Languages**:
  - 한국어 (Korean - `ko`)
  - English (`en`)
  - 简体中文 (Chinese Simplified - `zh`)
  - 日本語 (Japanese - `ja`)
  - Deutsch (German - `de`)
  - Español (Spanish - `es`)
  - Français (French - `fr`)
  - Português (Portuguese - `pt`)
  - Русский (Russian - `ru`)
- **Font Fallback Chain**:
  - Segoe UI, Microsoft YaHei, Meiryo, Malgun Gothic, Arial, sans-serif

---

## 📮 8. サポート窓口
- **Company**: (주)드래곤알피에이 (DragonRPA Co., Ltd.)
- **CEO & Lead Architect**: 이정용 (Victor Lee)
- **Official Contact**: `77.victor.lee@gmail.com`
- **Copyright**: Copyright © 2026 DragonRPA Co. All rights reserved.
