"""DeskShelf — エントリーポイント"""

import sys
import os
import ctypes

# タスクバーアイコンを独自に設定するために必要（Pythonデフォルトアイコンを上書き）
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("patlas.deskshelf")
except Exception:
    pass

# パス解決は config.py の ASSETS_DIR / CONFIG_DIR で行う

from app import DeskShelfApp


def main():
    app = DeskShelfApp()
    app.mainloop()


if __name__ == "__main__":
    main()
