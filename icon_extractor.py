"""ショートカットからアイコンを抽出するモジュール"""

import os
import ctypes
import ctypes.wintypes
from PIL import Image, ImageDraw, ImageFont

shell32 = ctypes.windll.shell32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# argtypes / restype を正しく設定（64bitハンドル対応）
gdi32.CreateCompatibleDC.argtypes = [ctypes.wintypes.HDC]
gdi32.CreateCompatibleDC.restype = ctypes.wintypes.HDC
gdi32.DeleteDC.argtypes = [ctypes.wintypes.HDC]
gdi32.DeleteObject.argtypes = [ctypes.wintypes.HGDIOBJ]
gdi32.GetDIBits.argtypes = [
    ctypes.wintypes.HDC, ctypes.wintypes.HBITMAP,
    ctypes.c_uint, ctypes.c_uint,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
]
user32.GetDC.argtypes = [ctypes.wintypes.HWND]
user32.GetDC.restype = ctypes.wintypes.HDC
user32.ReleaseDC.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.HDC]
user32.DestroyIcon.argtypes = [ctypes.wintypes.HICON]
user32.GetIconInfo.argtypes = [ctypes.wintypes.HICON, ctypes.c_void_p]
shell32.ExtractIconExW.argtypes = [
    ctypes.wintypes.LPCWSTR, ctypes.c_int,
    ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_uint,
]
shell32.ExtractIconExW.restype = ctypes.c_uint


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.wintypes.DWORD),
        ("biWidth", ctypes.wintypes.LONG),
        ("biHeight", ctypes.wintypes.LONG),
        ("biPlanes", ctypes.wintypes.WORD),
        ("biBitCount", ctypes.wintypes.WORD),
        ("biCompression", ctypes.wintypes.DWORD),
        ("biSizeImage", ctypes.wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.wintypes.LONG),
        ("biYPelsPerMeter", ctypes.wintypes.LONG),
        ("biClrUsed", ctypes.wintypes.DWORD),
        ("biClrImportant", ctypes.wintypes.DWORD),
    ]


class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", ctypes.wintypes.BOOL),
        ("xHotspot", ctypes.wintypes.DWORD),
        ("yHotspot", ctypes.wintypes.DWORD),
        ("hbmMask", ctypes.c_void_p),   # c_void_p で64bit安全
        ("hbmColor", ctypes.c_void_p),
    ]


def _extract_icon_from_file(file_path: str, icon_index: int = 0, size: int = 48) -> Image.Image | None:
    if not file_path or not os.path.isfile(file_path):
        return None
    try:
        large = (ctypes.c_void_p * 1)()
        small = (ctypes.c_void_p * 1)()
        count = shell32.ExtractIconExW(file_path, icon_index, large, small, 1)
        if count == 0:
            return None
        hicon = large[0] or small[0]
        if not hicon:
            return None
        try:
            return _hicon_to_image(hicon, size)
        finally:
            user32.DestroyIcon(hicon)
            other = small[0] if large[0] else large[0]
            if other and other != hicon:
                user32.DestroyIcon(other)
    except Exception:
        return None


def _hicon_to_image(hicon, size: int = 48) -> Image.Image | None:
    icon_info = ICONINFO()
    if not user32.GetIconInfo(hicon, ctypes.byref(icon_info)):
        return None
    hdc = None
    hdc_mem = None
    try:
        hdc = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc)
        if not icon_info.hbmColor:
            return None
        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        gdi32.GetDIBits(hdc_mem, icon_info.hbmColor, 0, 0, None, ctypes.byref(bmi), 0)
        w, h = bmi.biWidth, abs(bmi.biHeight)
        if w == 0 or h == 0:
            return None
        bmi.biBitCount = 32
        bmi.biCompression = 0
        bmi.biHeight = -h
        bmi.biSizeImage = w * h * 4
        buf = ctypes.create_string_buffer(bmi.biSizeImage)
        gdi32.GetDIBits(hdc_mem, icon_info.hbmColor, 0, h, buf, ctypes.byref(bmi), 0)
        img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
        return img.resize((size, size), Image.LANCZOS)
    except Exception:
        return None
    finally:
        if hdc_mem:
            gdi32.DeleteDC(hdc_mem)
        if hdc:
            user32.ReleaseDC(0, hdc)
        if icon_info.hbmMask:
            gdi32.DeleteObject(icon_info.hbmMask)
        if icon_info.hbmColor:
            gdi32.DeleteObject(icon_info.hbmColor)


def _load_ico_file(ico_path: str, size: int = 48) -> Image.Image | None:
    """PILで .ico ファイルを直接読み込む"""
    try:
        img = Image.open(ico_path)
        img = img.convert("RGBA")
        return img.resize((size, size), Image.LANCZOS)
    except Exception:
        return None


def get_icon(item: dict, cache_dir: str, size: int = 48) -> Image.Image:
    os.makedirs(cache_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in item["name"])
    cache_path = os.path.join(cache_dir, f"{safe_name}.png")

    if os.path.isfile(cache_path):
        try:
            return Image.open(cache_path).copy()
        except Exception:
            pass

    img = None

    # 1. icon_location / target / source_path から .ico を直接開く
    for key in ("icon_location", "target", "source_path"):
        p = item.get(key, "")
        if p and p.lower().endswith(".ico") and os.path.isfile(p):
            img = _load_ico_file(p, size)
            if img:
                break

    # 2. ExtractIconExW で .exe / .dll / .lnk から抽出
    if img is None:
        for path_key, idx in [
            ("icon_location", item.get("icon_index", 0)),
            ("target", 0),
            ("source_path", 0),
        ]:
            p = item.get(path_key, "")
            if p and os.path.isfile(p):
                img = _extract_icon_from_file(p, idx, size)
                if img:
                    break

    # 3. フォールバック
    if img is None:
        img = _create_default_icon(item["name"], size)

    try:
        img.save(cache_path, "PNG")
    except Exception:
        pass
    return img


def _create_default_icon(name: str, size: int = 48) -> Image.Image:
    img = Image.new("RGBA", (size, size), (100, 100, 120, 200))
    draw = ImageDraw.Draw(img)
    initial = name[0].upper() if name else "?"
    try:
        font = ImageFont.truetype("segoeui.ttf", size // 2)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initial, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) // 2, (size - th) // 2 - bbox[1]), initial, fill=(255, 255, 255, 255), font=font)
    return img
