"""アプリ・ファイルの起動処理"""

import os
import webbrowser


def launch(item: dict) -> bool:
    """
    アイテムを起動する。
    .url の場合はブラウザで開く。それ以外は os.startfile。
    """
    target = item.get("target", "")
    source = item.get("source_path", "")

    if not target and not source:
        return False

    try:
        # URL の場合はブラウザで開く
        if target.startswith("http://") or target.startswith("https://"):
            webbrowser.open(target)
            return True

        # .lnk ファイルがあればそれを直接実行（引数等が保持される）
        if source and source.lower().endswith(".lnk") and os.path.isfile(source):
            os.startfile(source)
            return True

        # ターゲットが存在すればそれを起動
        if target and os.path.exists(target):
            os.startfile(target)
            return True

        # フォールバック: source_path を起動
        if source and os.path.exists(source):
            os.startfile(source)
            return True

    except Exception as e:
        print(f"[DeskShelf] Launch error: {e}")
        return False

    return False
