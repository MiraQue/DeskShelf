[**English**](README.en.md) | 日本語

# DeskShelf

> ウインドウに埋もれたデスクトップを、いつでも手元に。

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6)

DeskShelf は、デスクトップのショートカットやファイルを常に最前面に浮かぶ小さなウインドウに表示するフローティングランチャーです。
ブラウザやエディタでデスクトップが見えなくても、DeskShelf からワンクリックで起動できる「浮かぶ棚」。

クラウド不要。データはすべてローカルに保存されます。

---

## 機能一覧

| 機能 | 説明 |
|------|------|
| **デスクトップアイコン表示** | Desktop + Public Desktop の .lnk / .url / .exe を自動読み取り |
| **ワンクリック起動** | クリックでアプリ・URLを起動。使用回数と最終使用日時を記録 |
| **Always on Top** | 最前面表示のON/OFF切り替え |
| **星レーティング** | 0〜3段階の重要度。よく使うアプリを上位に |
| **自動ソート** | 星の数 → 最終使用日時 → 名前で自動並べ替え |
| **タグ管理** | タグの作成・削除・割り当て。タブで絞り込み |
| **ダーク / ライトテーマ** | ワンクリックで切り替え。設定は自動保存 |
| **日本語 / 英語 切り替え** | セグメントコントロールで言語切り替え |
| **折りたたみ表示** | 上位30件を表示、残りは「もっと見る」で展開 |
| **マルチモニター対応** | ウインドウ位置の保存・復元。範囲外検知でフォールバック |
| **アイコン自動抽出** | Win32 API + PIL で .lnk / .exe からアイコンを取得 |
| **カスタムアプリアイコン** | 棚デザインの独自アイコン。タスクバーにも表示 |

---

## クイックスタート

### 1. ダウンロード＆インストール

**git を使う場合:**
```bash
git clone https://github.com/MiraQue/DeskShelf.git
cd DeskShelf
pip install -r requirements.txt
```

**git を使わない場合:**
1. [こちら](https://github.com/MiraQue/DeskShelf/archive/refs/heads/master.zip) から ZIP をダウンロード
2. 展開して、フォルダ内でコマンドプロンプトを開く
3. `pip install -r requirements.txt` を実行

> Python 3.9以上 + Windows 10/11 が必要です。

### 2. 起動

```bash
python main.py
```

デスクトップのショートカットが自動的に読み込まれ、フローティングウインドウが表示されます。

### 3. 使い方

- アイコンをクリック → アプリ/URLが起動
- 星をクリック → 重要度を変更（0〜3段階）
- タグタブで絞り込み、Tag ボタンでタグを管理

---

## UI構成

```
┌─────────────────────────────┐
│  [棚アイコン] DeskShelf  ─ □ ×│
├─────────────────────────────┤
│ [☀] [日本語|EN]    [Tag]   │  ← 上段ツールバー
│ [📌 最前面 ON] [↻ 更新]     │  ← 下段ツールバー
├─────────────────────────────┤
│ [All] [AI] [メタバース] [>>] │  ← タグタブ（横スクロール）
├─────────────────────────────┤
│ ★★★ [icon] Antigravity      │
│ ★★★ [icon] Blender 5.0      │
│ ★   [icon] Discord           │
│ ...                           │
│ ▼ もっと見る (54件)...        │
└─────────────────────────────┘
```

---

## プロジェクト構成

```
DeskShelf/
├── main.py              # エントリーポイント（AppUserModelID設定）
├── app.py               # メインウインドウ（CustomTkinter）
├── desktop_reader.py    # デスクトップのショートカット読み取り
├── icon_extractor.py    # Win32 APIでアイコン画像を抽出
├── launcher.py          # アプリ起動処理
├── config.py            # 設定の読み書き
├── generate_icon.py     # アプリアイコン生成スクリプト
├── requirements.txt     # Python依存パッケージ
└── data/
    ├── deskshelf.ico    # アプリアイコン（.ico）
    └── deskshelf.png    # アプリアイコン（.png）

ユーザーデータ保存先: %APPDATA%\DeskShelf\
├── config.json          # ユーザー設定（初回起動時に自動生成）
└── cache/icons/         # 抽出したアイコンのキャッシュ
```

---

## 技術スタック

- **言語**: Python 3.9+
- **GUI**: CustomTkinter（モダンUI、Always on Top対応）
- **アイコン抽出**: ctypes (shell32/gdi32) + PIL（64bit安全）
- **ショートカット解析**: win32com（.lnk のターゲット・アイコン情報を取得）
- **設定保存**: ローカルJSONファイル

---

## 動作環境

| 項目 | 要件 |
|------|------|
| OS | Windows 10 / 11 |
| Python | 3.9 以上 |
| 依存パッケージ | customtkinter, pywin32, Pillow |

> Windows専用アプリです。デスクトップのショートカット読み取りとアイコン抽出にWindows APIを使用しています。

---

## ライセンス

MIT License. 詳細は [LICENSE](LICENSE) を参照してください。
