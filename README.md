# Kindle to PDF App

Kindle for PCアプリで開いている本を自動でスクリーンショット撮影し、PDF化するPythonアプリケーションです。

## 目次

- [概要](#概要)
- [主な機能](#主な機能)
- [システム要件](#システム要件)
- [インストール](#インストール)
- [使い方](#使い方)
- [プロジェクト構造](#プロジェクト構造)
- [設定オプション](#設定オプション)
- [トラブルシューティング](#トラブルシューティング)
- [開発者向け情報](#開発者向け情報)
- [ライセンス](#ライセンス)

---

## 概要

このアプリケーションは、Kindle for PCで開いている本を自動的にページめくりしながらスクリーンショットを撮影し、1つのPDFファイルにまとめます。

### 主な特徴

- **完全自動化**: Kindleアプリの起動から、ページめくり、スクリーンショット撮影、PDF生成まで全自動
- **モダンなUI**: CustomTkinterを使用したiOSライクなデザイン
- **柔軟な設定**: 手動・自動領域検出、ページターン方向の選択、各種タイミング調整
- **マルチモニター対応**: 複数のモニター環境でも正常に動作
- **ダークモード対応**: システムの外観設定に自動適応

---

## 主な機能

### 1. Kindle自動起動
- Kindle for PCを自動的に検索・起動
- 既に起動している場合は既存のウィンドウを使用
- マルチモニター環境でのウィンドウ検出

### 2. 領域検出
- **自動検出**: OpenCVを使用して本のページ領域を自動検出
- **手動選択**: マウスで範囲をドラッグして指定可能
- テストキャプチャ機能でプレビュー確認

### 3. ページターン
- **自動方向検出**: 画像ハッシュ比較により、左→右、右→左を自動判定
- **手動方向指定**: LtoR（英語の本）、RtoL（日本語の漫画）を選択可能
- **終了検出**: 連続して同じページが検出されたら自動終了

### 4. 画像最適化
- グレースケール変換でファイルサイズ削減
- PNGまたはJPEG形式を選択可能
- JPEG品質調整（0-100）

### 5. PDF生成
- 複数の画像を1つのPDFに統合
- img2pdfライブラリを使用した高速処理
- 自動的に出力フォルダを開く

---

## システム要件

### 必須環境

- **OS**: Windows 10/11
- **Python**: 3.8以上（開発時: 3.11.7）
- **Kindle for PC**: Amazon公式アプリ
- **メモリ**: 4GB以上推奨
- **ディスク空き容量**: 1ページあたり約2MB × ページ数

### 必須ソフトウェア

- [Kindle for PC](https://www.amazon.co.jp/kindle-dbs/fd/kcp)（無料）
- Amazonアカウント（Kindleにログイン済み）

---

## インストール

### 方法1: 実行ファイル（推奨）

1. `dist/KindleToPdfApp_new/`フォルダ全体を任意の場所にコピー
2. `KindleToPdfApp.exe`をダブルクリックで起動

### 方法2: ソースコードから実行

```bash
# リポジトリをクローン
git clone <repository-url>
cd kindle-to-pdf-app

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化（Windows）
.\venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# アプリケーションを起動
python main.py
```

### 方法3: 自分でビルド

```bash
# 依存パッケージをインストール済みの場合
pyinstaller KindleToPdfApp.spec

# 実行ファイルは dist/KindleToPdfApp/ に生成されます
```

---

## 使い方

### 基本的な手順

1. **アプリを起動**
   - `KindleToPdfApp.exe`を実行

2. **Kindleで本を開く**
   - Kindle for PCを起動（自動起動も可能）
   - 本を開いて**最初のページ**に移動
   - 本のページを2-3回クリックしてフォーカスを確保

3. **設定を確認**
   - Target Region: `Automatic`（推奨）
   - Page Turn Direction: `Automatic`（失敗する場合は`LtoR`または`RtoL`を選択）
   - Max Pages: キャプチャするページ数（デフォルト: 100）
   - Page Turn Delay: 3秒（推奨）

4. **自動化を開始**
   - 「Start」ボタンをクリック
   - 自動化中はマウスやキーボードを操作しない

5. **完了後**
   - PDF生成完了のダイアログが表示される
   - 「Open Folder」ボタンで出力先フォルダを開く

### ページターン方向について

| 設定 | 説明 | 使用例 |
|------|------|--------|
| **Automatic** | 自動検出（推奨） | ほとんどの本 |
| **LtoR** (→) | 左から右へ | 英語の本、横書きの日本語 |
| **RtoL** (←) | 右から左へ | 漫画、縦書きの日本語 |

### ホットキー

- **Ctrl + Q**: 自動化を緊急停止（グローバルホットキー）

---

## プロジェクト構造

```
kindle-to-pdf-app/
├── main.py                          # エントリーポイント
├── requirements.txt                 # 依存パッケージ一覧
├── KindleToPdfApp.spec             # PyInstallerビルド設定
├── config.json                      # ユーザー設定ファイル（自動生成）
│
├── src/                            # ソースコード
│   ├── app.py                      # アプリケーション初期化
│   ├── config_manager.py           # 設定の読み書き
│   ├── hotkey_listener.py          # グローバルホットキー処理
│   ├── utils.py                    # ユーティリティ関数
│   │
│   ├── automation/                 # 自動化モジュール
│   │   ├── automation_coordinator.py  # 自動化の統括管理
│   │   ├── kindle_controller.py       # Kindle操作（起動、フォーカス、ページめくり）
│   │   └── pdf_converter.py           # PDF生成処理
│   │
│   └── gui/                        # GUI関連
│       ├── main_window.py          # メインウィンドウ
│       └── region_selector.py      # 領域選択ツール
│
├── dist/                           # ビルド済み実行ファイル
│   └── KindleToPdfApp_new/
│       ├── KindleToPdfApp.exe      # メイン実行ファイル
│       └── _internal/              # 依存ライブラリ
│
└── build/                          # ビルド時の一時ファイル
```

### 主要モジュールの説明

#### `src/automation/automation_coordinator.py`
自動化処理全体を統括するコーディネーター。

**主要機能:**
- ディスクスペースチェック
- スリープ防止機能
- Kindleウィンドウの管理
- スクリーンショット撮影の制御
- 一時/停止/再開機能
- PDF生成の起動

**主要メソッド:**
```python
def run(self, pages, optimize_images, page_turn_direction, ...):
    """自動化のメイン処理"""

def pause(self):
    """自動化を一時停止"""

def resume(self):
    """自動化を再開"""

def stop(self):
    """自動化を停止"""
```

#### `src/automation/kindle_controller.py`
Kindle for PCの制御を担当。

**主要機能:**
- Kindle.exeの検索と起動
- ウィンドウの検出とアクティベート
- フルスクリーンモード切り替え
- ページ領域の自動検出（OpenCV使用）
- ページターン方向の自動判定
- マルチモニター対応

**主要メソッド:**
```python
def find_kindle_exe(self):
    """標準的なインストール場所からKindle.exeを検索"""

def start_kindle_app(self):
    """Kindleアプリを起動"""

def launch_and_activate_kindle(self):
    """Kindleを起動してフルスクリーンに"""

def get_book_region(self, kindle_win):
    """OpenCVで本のページ領域を検出"""

def determine_page_turn_direction(self, kindle_win):
    """画像ハッシュ比較でページめくり方向を判定"""
```

**定数:**
```python
DEFAULT_KINDLE_STARTUP_DELAY = 10      # Kindle起動待機時間（秒）
DEFAULT_PAGE_TURN_DELAY = 3            # ページめくり待機時間（秒）
MIN_BOOK_REGION_SIZE = 0.15            # 最小領域サイズ（15%）
HASH_DIFF_THRESHOLD = 5.0              # ページ変化検出の閾値
```

#### `src/automation/pdf_converter.py`
画像からPDFを生成。

**主要機能:**
- 画像の最適化（グレースケール、リサイズ）
- PNG/JPEG形式のサポート
- img2pdfを使用した高速変換

**主要メソッド:**
```python
def create_pdf_from_images(self, image_files, output_folder,
                          output_filename, optimize_images,
                          image_format, jpeg_quality):
    """画像リストからPDFを生成"""

def optimize_image(self, image_path, output_path,
                  image_format, jpeg_quality):
    """画像を最適化"""
```

#### `src/gui/main_window.py`
CustomTkinterを使用したメインGUI。

**主要機能:**
- 設定フォーム（左パネル）
- コントロールボタン（右パネル）
- プレビュー表示
- プログレスバー
- アクティビティログ

**レイアウト:**
```
┌─────────────────────────────────────────┐
│  [Settings]            [Control Panel]  │
│  ┌──────────┐         ┌──────────────┐ │
│  │Target    │         │ Warnings     │ │
│  │Region    │         │ ⚠ Tips       │ │
│  │          │         ├──────────────┤ │
│  │Actions   │         │ [Start] [Stop]│ │
│  │          │         ├──────────────┤ │
│  │Output    │         │ Progress Bar │ │
│  │          │         ├──────────────┤ │
│  │Delays    │         │ Preview      │ │
│  │          │         ├──────────────┤ │
│  └──────────┘         │ Activity Log │ │
│                       └──────────────┘ │
└─────────────────────────────────────────┘
```

#### `src/gui/region_selector.py`
画面上でマウスドラッグして領域を選択するツール。

**使い方:**
1. 半透明のオーバーレイが表示される
2. マウスでドラッグして矩形を描く
3. マウスを離すと選択完了
4. ESCキーでキャンセル

#### `src/config_manager.py`
設定の永続化を担当。

**設定ファイル:** `config.json`

**デフォルト設定:**
```json
{
    "pages": 100,
    "optimize_images": true,
    "page_turn_delay": 3,
    "kindle_startup_delay": 10,
    "window_activation_delay": 3,
    "fullscreen_delay": 3,
    "navigation_delay": 7,
    "page_turn_direction": "Automatic",
    "region_detection_mode": "Automatic",
    "manual_capture_region": null,
    "output_folder": "Kindle_PDFs",
    "output_filename": "My_Kindle_Book.pdf",
    "image_format": "PNG",
    "jpeg_quality": 90,
    "end_detection_sensitivity": 3
}
```

#### `src/hotkey_listener.py`
グローバルホットキー（Ctrl+Q）の監視。

**機能:**
- 別スレッドでキーボード監視
- アプリがバックグラウンドでも動作
- 自動化を緊急停止可能

---

## 設定オプション

### Target Region（ターゲット領域）

| 設定 | 説明 | 使用例 |
|------|------|--------|
| **Automatic Detection** | OpenCVで自動検出 | 通常の本（推奨） |
| **Manual Selection** | マウスで範囲指定 | 特殊なレイアウト |

### Action Parameters（アクション設定）

| 設定 | 説明 | デフォルト | 推奨値 |
|------|------|-----------|--------|
| **Page Turn Direction** | ページめくり方向 | Automatic | 失敗時はLtoR/RtoL |
| **Max Pages** | 最大ページ数 | 100 | 本のページ数に合わせる |
| **End Detect Sensitivity** | 終了検出感度 | 3 | 3-5（連続同一ページ数） |

### Output Settings（出力設定）

| 設定 | 説明 | デフォルト |
|------|------|-----------|
| **Output Folder** | 保存先フォルダ | Kindle_PDFs |
| **Filename** | PDFファイル名 | My_Kindle_Book.pdf |
| **Image Format** | 画像形式 | PNG |
| **JPEG Quality** | JPEG品質 | 90 |
| **Optimize Images** | 画像最適化 | ON |

### Delay Settings（遅延設定）

| 設定 | 説明 | デフォルト | 推奨範囲 |
|------|------|-----------|----------|
| **Page Turn** | ページめくり後の待機 | 3秒 | 3-5秒 |
| **Kindle Startup** | Kindle起動待機 | 10秒 | 10-15秒 |
| **Window Activation** | ウィンドウアクティベート | 3秒 | 3-5秒 |
| **Fullscreen Toggle** | フルスクリーン切替 | 3秒 | 3-5秒 |
| **Go to Home** | ホームキー押下後 | 7秒 | 5-10秒 |

---

## トラブルシューティング

### 問題1: Kindleアプリが起動しない

**症状:**
```
Error: Could not find Kindle.exe in standard installation locations.
```

**原因:**
- Kindle for PCがインストールされていない
- 非標準の場所にインストールされている

**解決策:**
1. [Kindle for PC](https://www.amazon.co.jp/kindle-dbs/fd/kcp)をインストール
2. 手動でKindleを起動してログイン
3. 本を開いてからアプリを再試行

---

### 問題2: ページターン方向が検出できない

**症状:**
```
Error: Could not determine page turn direction.
Screen did not change significantly.
RIGHT arrow diff: 0.00, LEFT arrow diff: 0.00
```

**原因:**
- Kindleウィンドウにフォーカスがない
- 本がライブラリ画面のまま
- キーボード入力が届いていない

**解決策:**

1. **手動でフォーカスを確保:**
   - Kindleの本のページを2-3回クリック
   - 本が確実に開いていることを確認

2. **Page Turn Directionを手動設定:**
   - 英語の本: `LtoR` を選択
   - 日本語の漫画: `RtoL` を選択

3. **Page Turn Delayを増やす:**
   - 3秒 → 4秒または5秒に設定

4. **Kindleを再起動:**
   - Kindleアプリを完全に閉じる
   - 再度起動して本を開く

---

### 問題3: 領域検出が失敗する

**症状:**
```
Warning: Dynamic detection failed
Using full-window fallback method...
```

**原因:**
- 本のレイアウトが特殊
- OpenCVの検出閾値に引っかかる

**解決策:**

1. **Manual Selection modeに切り替え:**
   - Target Region: `Manual Selection` を選択
   - 「Select Area」ボタンをクリック
   - マウスで本のページ領域をドラッグ

2. **Test Captureで確認:**
   - 「Test Capture」ボタンで正しく撮影できるか確認
   - プレビューに本のページが表示されればOK

---

### 問題4: ページが重複する

**症状:**
- 同じページが複数回撮影される
- ページがスキップされる

**原因:**
- Page Turn Delayが短すぎる
- Kindleのページめくりアニメーションが遅い

**解決策:**

1. **Page Turn Delayを増やす:**
   - 3秒 → 5秒に設定

2. **End Detect Sensitivityを調整:**
   - デフォルト3 → 5に増やす
   - 連続して同じページが5回検出されたら終了

---

### 問題5: PDFファイルが巨大になる

**症状:**
- PDFファイルが数百MB以上になる

**原因:**
- Optimize Imagesがオフ
- PNG形式で保存している

**解決策:**

1. **Optimize Imagesをオン:**
   - チェックボックスを有効化
   - グレースケール変換＋リサイズが適用される

2. **JPEG形式に変更:**
   - Image Format: `JPEG` を選択
   - JPEG Quality: 70-85に設定

---

### 問題6: マルチモニター環境で動作しない

**症状:**
- Kindleウィンドウが検出されない
- マウスが正しい位置に移動しない

**原因:**
- セカンダリモニターにKindleがある
- 座標計算が正しくない

**解決策:**

1. **Kindleをプライマリモニターに移動:**
   - Kindleウィンドウをメインモニターにドラッグ

2. **ログを確認:**
   - Activity Logに表示される座標を確認
   - `Window position: (x, y)` が正しいか確認

3. **最新版を使用:**
   - マルチモニター対応が改善されています

---

### 問題7: スリープモードに入る

**症状:**
- 自動化中にPCがスリープする

**原因:**
- 長時間の自動化でスリープタイマーが作動

**解決策:**

- アプリが自動的にスリープ防止機能を有効化します
- それでもスリープする場合:
  1. Windows設定 → 電源とスリープ
  2. スリープタイマーを「なし」に設定

---

## 開発者向け情報

### 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd kindle-to-pdf-app

# 仮想環境を作成
python -m venv venv
.\venv\Scripts\activate

# 開発用依存パッケージをインストール
pip install -r requirements.txt
```

### 依存パッケージ

主要なパッケージ:

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| **customtkinter** | 5.2.2 | モダンなGUI |
| **opencv-python** | 4.9.0.80 | 画像処理、領域検出 |
| **pillow** | 12.1.0 | 画像操作 |
| **mss** | 9.0.1 | スクリーンショット |
| **pyautogui** | 0.9.54 | キーボード/マウス制御 |
| **pygetwindow** | 0.0.9 | ウィンドウ管理 |
| **img2pdf** | 0.4.4 | PDF変換 |
| **keyboard** | 0.13.5 | グローバルホットキー |
| **numpy** | 1.26.4 | 数値計算 |

ビルド用:
- **pyinstaller** | 6.17.0 | 実行ファイル生成

### ビルド方法

```bash
# 標準ビルド
pyinstaller KindleToPdfApp.spec

# クリーンビルド
pyinstaller KindleToPdfApp.spec --clean

# 実行ファイルは dist/KindleToPdfApp/ に生成
```

### ディレクトリ構成の詳細

```
src/
├── app.py                          # アプリ初期化、CustomTkinter設定
├── config_manager.py               # JSON設定の読み書き
├── hotkey_listener.py              # keyboard使用、別スレッドで監視
├── utils.py                        # 一時ディレクトリ作成・削除
│
├── automation/
│   ├── automation_coordinator.py  # 全体統括、スリープ防止、進捗管理
│   ├── kindle_controller.py       # pygetwindow, pyautogui, OpenCV使用
│   └── pdf_converter.py           # Pillow, img2pdf使用
│
└── gui/
    ├── main_window.py             # CustomTkinter、PIL.ImageTk使用
    └── region_selector.py         # tkinter（オーバーレイ用）
```

### コーディング規約

- **命名規則:**
  - クラス: PascalCase（例: `KindleController`）
  - 関数/変数: snake_case（例: `get_book_region`）
  - 定数: UPPER_SNAKE_CASE（例: `DEFAULT_PAGE_TURN_DELAY`）

- **コメント:**
  - 日本語コメント推奨
  - 複雑なロジックには詳細な説明を記載

- **エラーハンドリング:**
  - 外部システム（Kindle、ファイル操作）との連携は必ずtry-exceptで囲む
  - ユーザーに分かりやすいエラーメッセージを表示

### テスト方法

```bash
# 手動テスト
python main.py

# 特定のモジュールをテスト
python -c "from src.automation.kindle_controller import KindleController; kc = KindleController(); print(kc.find_kindle_exe())"

# ビルド後のテスト
cd dist/KindleToPdfApp
./KindleToPdfApp.exe
```

### デバッグのヒント

1. **ログを確認:**
   - GUIの「Activity Log」に詳細なログが表示される
   - ウィンドウ座標、ハッシュ値、検出結果などを確認

2. **Test Capture機能:**
   - 領域検出が正しいか確認
   - プレビュー画像で視覚的に確認可能

3. **PyInstallerの警告:**
   - ビルド時の`WARNING`は通常無視してOK
   - WindowsのシステムDLL（bcrypt.dll等）は実行時に自動解決される

4. **マルチスレッド:**
   - `automation.run()`は別スレッドで実行される
   - GUIコールバックは`master.after(0, callback)`で実行

### 貢献方法

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

---

## よくある質問（FAQ）

### Q1: Kindleの本は全部PDFにできますか？

**A:** 技術的には可能ですが、以下の点に注意してください：
- **著作権**: 個人利用の範囲内で使用してください
- **DRM**: Kindleの本自体はDRM保護されていますが、このアプリはスクリーンショットを撮るだけなのでDRMの制限は受けません
- **用途**: バックアップや個人的なアーカイブ目的での使用を推奨

### Q2: Mac/Linuxでも動きますか？

**A:** 現時点ではWindows専用です。理由：
- `pygetwindow`がWindows専用
- Kindle for PCがWindows専用
- 将来的にはクロスプラットフォーム対応を検討

### Q3: Kindle以外のアプリでも使えますか？

**A:** コードを少し修正すれば可能です：
- `kindle_controller.py`のウィンドウタイトル検索を変更
- ページめくりのキーバインドを調整
- プルリクエスト歓迎！

### Q4: 処理時間はどれくらいかかりますか？

**A:** ページ数と設定によります：
- **100ページの本**: 約5-7分
- **計算式**: (Page Turn Delay + アニメーション時間) × ページ数
- **高速化**: Page Turn Delayを短くする（ただし検出精度は低下）

### Q5: エラーが出ても途中から再開できますか？

**A:** 現在は未対応ですが、回避策：
1. エラー時のページ番号をメモ
2. Kindleでそのページまで移動
3. Max Pagesを残りページ数に設定
4. 別のファイル名で再実行
5. 後でPDFを結合

### Q6: 商用利用は可能ですか？

**A:** このアプリ自体はオープンソースですが：
- Kindleの本の著作権を尊重してください
- 商用目的での本のPDF化は著作権法に違反する可能性があります
- 個人利用の範囲内での使用を推奨します

---

## 既知の問題

1. **OneDriveフォルダ内での動作:**
   - OneDrive同期フォルダ内で実行すると、一時ファイルの削除時にエラーが出る場合があります
   - 回避策: ローカルドライブで実行

2. **高DPI環境:**
   - 150%以上のスケーリング環境では座標がずれる場合があります
   - 回避策: 100%スケーリングを使用、またはManual Selection modeで手動指定

3. **Kindleのアップデート:**
   - Kindleアプリのメジャーアップデートでウィンドウタイトルやレイアウトが変わる可能性があります
   - 問題が発生したらissueを報告してください

---

## 更新履歴

### v1.3.0 (2026-01-11)
- **🖥️ マルチモニター対応強化:** セカンドモニターでKindleを開いていても正確に領域選択が可能
- **🎯 領域選択UIの大幅改善:**
  - ドラッグ中に選択範囲が明るく表示される視覚的フィードバック
  - 選択後の確認ダイアログでやり直しが簡単に
  - Kindleウィンドウを自動的に前面に表示
- **🔍 dHashアルゴリズム導入:** より堅牢なページめくり検出（閾値: 1.5→10.0）
- **🐛 デバッグ機能追加:** `debug_capture_*.png`を自動保存してトラブルシューティングを容易に
- **⏸️ スマート停止確認:** 目標ページ未達成時に停止確認ダイアログを表示
- **📊 UI最適化:** プレビュー縮小（300x400→200x250）、ログ拡大（150px→200px）
- **📁 便利なデフォルト設定:**
  - 出力フォルダー: Downloadsフォルダに自動設定
  - ファイル名: 今日の日付（yyyymmdd.pdf）に自動設定
- **📝 コード整理:** constants.py、config_validator.pyで設定管理を一元化

### v1.2.0 (2026-01-09)
- ページターン検出の大幅改善
- ウィンドウフォーカスの強化（3回クリック、ESCキーテスト）
- キーボード入力の信頼性向上（keyDown/keyUp使用）
- GUIにヘルプテキストと警告メッセージを追加
- Page Turn Delayのデフォルトを3秒に変更

### v1.1.0 (2026-01-09)
- CustomTkinterに移行、iOSライクなモダンUIに刷新
- Kindle自動起動機能の改善
- マルチモニター対応強化
- 詳細なエラーメッセージとログ出力

### v1.0.0 (2026-01-09)
- 初回リリース
- 基本的な自動化機能
- 自動/手動領域検出
- PNG/JPEG出力対応
- グローバルホットキー（Ctrl+Q）

---

## ライセンス

このプロジェクトはオープンソースです。

**注意事項:**
- このアプリは個人利用を目的としています
- Kindleの本の著作権を尊重してください
- 本のPDF化は個人的なバックアップ目的での使用を推奨します
- 商用利用や再配布には著作権者の許可が必要です

---

## サポート

問題が発生した場合:

1. **このREADMEのトラブルシューティングセクションを確認**
2. **Activity Logを確認して詳細なエラー情報を取得**
3. **GitHubのissueで報告:**
   - エラーメッセージ全文
   - Activity Logの内容
   - 使用環境（Windows version、Kindle version）
   - 再現手順

---

## 謝辞

このプロジェクトは以下のオープンソースライブラリを使用しています:

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - モダンなGUIフレームワーク
- [OpenCV](https://opencv.org/) - 画像処理
- [PyAutoGUI](https://github.com/asweigart/pyautogui) - GUI自動化
- [img2pdf](https://gitlab.mister-muffin.de/josch/img2pdf) - PDF生成
- [MSS](https://github.com/BoboTiG/python-mss) - 高速スクリーンショット

すべての開発者とコントリビューターに感謝します。

---

## 連絡先

- **GitHub**: [Repository URL]
- **Issues**: [Issues URL]

---

**免責事項:** このアプリケーションは教育目的で作成されました。使用は自己責任で行ってください。著作権法を遵守し、個人利用の範囲内で使用してください。
