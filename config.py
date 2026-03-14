"""設定の読み書き"""

import json
import os
import sys

DEFAULT_CONFIG = {
    "window": {
        "x": None,
        "y": None,
        "width": 280,
        "max_width": 500,
        "always_on_top": True,
        "theme": "system",
        "opacity": 1.0,
    },
    "lang": "ja",
    "icon_size": 48,
    "visible_count": 30,  # 折りたたみ前に表示する件数
    "tags": {},
    "tag_order": [],
    "stars": {},   # { "item_name": 1~3 }  重要度（0=なし）
    "usage": {},   # { "item_name": {"count": N, "last": "ISO timestamp"} }
}

# ユーザーデータ: %APPDATA%/DeskShelf/ (ユーザーごとに独立)
CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "DeskShelf")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# アセット(アイコン等): PyInstaller展開先 or スクリプトディレクトリ
if getattr(sys, "frozen", False):
    ASSETS_DIR = os.path.join(sys._MEIPASS, "data")
else:
    ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load_config() -> dict:
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config = json.loads(json.dumps(DEFAULT_CONFIG))
            for key in DEFAULT_CONFIG:
                if key in saved:
                    if isinstance(DEFAULT_CONFIG[key], dict):
                        config[key] = {**DEFAULT_CONFIG[key], **saved[key]}
                    else:
                        config[key] = saved[key]
            return config
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(config: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
