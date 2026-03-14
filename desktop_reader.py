"""デスクトップのショートカット・ファイルを読み取るモジュール"""

import os
import ctypes
import win32com.client

# CSIDL定数（GUIDより確実）
_CSIDL_DESKTOP = 0x0010           # ユーザーデスクトップ
_CSIDL_COMMON_DESKTOP = 0x0019    # パブリックデスクトップ


def _get_folder_path(csidl: int) -> str | None:
    """SHGetFolderPathW でシステムフォルダのパスを取得する"""
    buf = ctypes.create_unicode_buffer(260)
    hr = ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, buf)
    if hr == 0 and buf.value:
        return buf.value
    return None


def get_desktop_path() -> str:
    """ユーザーのデスクトップパスを取得する（OneDrive同期対応）"""
    path = _get_folder_path(_CSIDL_DESKTOP)
    if path and os.path.isdir(path):
        return path
    return os.path.join(os.environ["USERPROFILE"], "Desktop")


def get_public_desktop_path() -> str:
    """パブリックデスクトップのパスを取得する"""
    path = _get_folder_path(_CSIDL_COMMON_DESKTOP)
    if path and os.path.isdir(path):
        return path
    return os.path.join(os.environ["PUBLIC"], "Desktop")


def resolve_lnk(lnk_path: str) -> dict | None:
    """
    .lnk ファイルを解析してリンク先情報を返す。
    Returns: {"name", "target", "icon_location", "icon_index", "description"}
    """
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        name = os.path.splitext(os.path.basename(lnk_path))[0]
        return {
            "name": name,
            "target": shortcut.Targetpath,
            "icon_location": shortcut.IconLocation.split(",")[0].strip(),
            "icon_index": int(shortcut.IconLocation.split(",")[-1].strip() or 0),
            "description": shortcut.Description or "",
            "source_path": lnk_path,
        }
    except Exception:
        return None


def resolve_url(url_path: str) -> dict | None:
    """
    .url ファイルを解析してURL情報を返す。
    """
    try:
        name = os.path.splitext(os.path.basename(url_path))[0]
        url = ""
        icon_file = ""
        with open(url_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("URL="):
                    url = line[4:]
                elif line.startswith("IconFile="):
                    icon_file = line[9:]
        return {
            "name": name,
            "target": url,
            "icon_location": icon_file,
            "icon_index": 0,
            "description": "",
            "source_path": url_path,
        }
    except Exception:
        return None


def _collect_desktop_paths() -> list[str]:
    """重複を除いた全デスクトップパスを返す（OneDrive + ローカル + パブリック）"""
    paths = []
    seen = set()

    for p in [
        get_desktop_path(),                                      # Windows API（OneDrive側になる場合あり）
        os.path.join(os.environ["USERPROFILE"], "Desktop"),      # ローカル固定パス
        get_public_desktop_path(),                               # パブリック
    ]:
        rp = os.path.normcase(os.path.realpath(p))
        if rp not in seen and os.path.isdir(p):
            seen.add(rp)
            paths.append(p)

    return paths


def scan_desktop() -> list[dict]:
    """
    デスクトップ上のショートカット・実行ファイルをスキャンして一覧を返す。
    OneDrive同期デスクトップ・ローカルデスクトップ・パブリックデスクトップを全て読む。
    """
    items = []
    seen_names = set()

    for desktop_path in _collect_desktop_paths():
        if not os.path.isdir(desktop_path):
            continue
        for entry in os.listdir(desktop_path):
            full_path = os.path.join(desktop_path, entry)
            if not os.path.isfile(full_path):
                continue

            ext = os.path.splitext(entry)[1].lower()
            item = None

            if ext == ".lnk":
                item = resolve_lnk(full_path)
            elif ext == ".url":
                item = resolve_url(full_path)
            elif ext in (".exe", ".bat", ".cmd"):
                name = os.path.splitext(entry)[0]
                item = {
                    "name": name,
                    "target": full_path,
                    "icon_location": full_path,
                    "icon_index": 0,
                    "description": "",
                    "source_path": full_path,
                }

            if item and item["name"] not in seen_names:
                seen_names.add(item["name"])
                items.append(item)

    items.sort(key=lambda x: x["name"].lower())
    return items
