"""デスクトップのショートカット・ファイルを読み取るモジュール"""

import os
import win32com.client


def get_desktop_path() -> str:
    """ユーザーのデスクトップパスを取得する"""
    return os.path.join(os.environ["USERPROFILE"], "Desktop")


def get_public_desktop_path() -> str:
    """パブリックデスクトップのパスを取得する"""
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


def scan_desktop() -> list[dict]:
    """
    デスクトップ上のショートカット・実行ファイルをスキャンして一覧を返す。
    ユーザーデスクトップとパブリックデスクトップの両方を読む。
    """
    items = []
    seen_names = set()

    for desktop_path in [get_desktop_path(), get_public_desktop_path()]:
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
