"""DeskShelf — エントリーポイント"""

import sys
import os
import ctypes

# タスクバーアイコンを独自に設定するために必要（Pythonデフォルトアイコンを上書き）
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("patlas.deskshelf")
except Exception:
    pass

# スクリプトのディレクトリを基準にする
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import DeskShelfApp


def main():
    app = DeskShelfApp()
    app.mainloop()


if __name__ == "__main__":
    main()
