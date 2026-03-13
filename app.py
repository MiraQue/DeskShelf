"""DeskShelf メインウインドウ"""

import os
import threading
from datetime import datetime, timezone
import customtkinter as ctk
from PIL import Image

from desktop_reader import scan_desktop
from icon_extractor import get_icon, _create_default_icon
from launcher import launch
from config import load_config, save_config

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "icons")
ALL_TAG = "All"
ICON_SIZE = 24
ROW_HEIGHT = 26
STAR_CHARS = ["\u2606", "\u2605", "\u2605\u2605", "\u2605\u2605\u2605"]  # 0=☆, 1~3=★

# 多言語テキスト
LANG = {
    "ja": {
        "topmost_on": "\U0001f4cc \u6700\u524d\u9762 ON",
        "topmost_off": "\U0001f4cc \u6700\u524d\u9762 OFF",
        "refresh": "\u21bb \u66f4\u65b0",
        "tag": "\U0001f3f7 Tag",
        "more": "\u25bc \u3082\u3063\u3068\u898b\u308b ({n}\u4ef6)...",
        "collapse": "\u25b2 \u305f\u305f\u3080",
    },
    "en": {
        "topmost_on": "\U0001f4cc Topmost ON",
        "topmost_off": "\U0001f4cc Topmost OFF",
        "refresh": "\u21bb Refresh",
        "tag": "\U0001f3f7 Tag",
        "more": "\u25bc More ({n})...",
        "collapse": "\u25b2 Collapse",
    },
}


class DeskShelfApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config = load_config()
        self.lang = self.config.get("lang", "ja")
        self.icon_images = {}
        self.items = []
        self.current_tag = ALL_TAG
        self._loading = False
        self._more_expanded = False

        self._setup_window()
        self._setup_theme()
        self._build_ui()
        self._load_desktop_items()
        self._restore_position()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── ウインドウ設定 ──

    def _setup_window(self):
        self.title("DeskShelf")
        win = self.config["window"]
        self.geometry(f"{win.get('width', 280)}x400")
        if win.get("always_on_top", True):
            self.attributes("-topmost", True)
        opacity = win.get("opacity", 1.0)
        if opacity < 1.0:
            self.attributes("-alpha", opacity)
        self.minsize(200, 120)
        max_w = win.get("max_width", 360)
        self.maxsize(max_w, 2000)
        # カスタムアイコン設定（タイトルバー + タスクバー）
        ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "deskshelf.ico")
        if os.path.isfile(ico_path):
            self.after(50, lambda: self.iconbitmap(ico_path))

    def _setup_theme(self):
        theme = self.config["window"].get("theme", "system")
        ctk.set_appearance_mode(theme if theme in ("dark", "light") else "system")
        ctk.set_default_color_theme("blue")

    # ── UI構築 ──

    def _t(self, key, **kwargs):
        """現在の言語でテキスト取得"""
        txt = LANG.get(self.lang, LANG["ja"]).get(key, key)
        return txt.format(**kwargs) if kwargs else txt

    def _build_ui(self):
        btn_font = ctk.CTkFont(size=10)
        small_font = ctk.CTkFont(size=11)
        btn_h = 24

        # ── ツールバー上段: テーマ + 言語 + Tag ──
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=4, pady=(4, 0))

        self._theme_btn = ctk.CTkButton(
            row1, text="", width=btn_h, height=btn_h, font=ctk.CTkFont(size=14),
            fg_color=("gray85", "gray22"), hover_color=("gray75", "gray32"),
            text_color=("gray30", "#FFD43B"),
            border_width=1, border_color=("gray70", "gray40"),
            corner_radius=btn_h // 2, command=self._toggle_theme,
        )
        self._theme_btn.pack(side="left", padx=(0, 4))
        self._update_theme_button()

        # 言語セグメントコントロール
        seg_w = 92
        lang_frame = ctk.CTkFrame(
            row1, fg_color=("gray80", "gray25"), corner_radius=8,
            width=seg_w, height=btn_h,
        )
        lang_frame.pack(side="left")
        lang_frame.pack_propagate(False)
        lang_font = ctk.CTkFont(size=9, weight="bold")

        self._lang_btn_ja = ctk.CTkButton(
            lang_frame, text="\u65e5\u672c\u8a9e", width=48, height=btn_h - 4,
            font=lang_font, corner_radius=6,
            command=lambda: self._set_lang("ja"),
        )
        self._lang_btn_ja.pack(side="left", padx=(2, 0), pady=2)

        self._lang_btn_en = ctk.CTkButton(
            lang_frame, text="EN", width=36, height=btn_h - 4,
            font=lang_font, corner_radius=6,
            command=lambda: self._set_lang("en"),
        )
        self._lang_btn_en.pack(side="left", padx=(0, 2), pady=2)
        self._update_lang_segment()

        self._tag_btn = ctk.CTkButton(
            row1, text=self._t("tag"), width=52, height=btn_h, font=btn_font,
            corner_radius=6, command=self._open_tag_manager,
        )
        self._tag_btn.pack(side="right", padx=2)

        # ── ツールバー下段: 最前面 + 更新 ──
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=4, pady=(2, 0))

        self._pin_btn = ctk.CTkButton(
            row2, text="", height=btn_h, font=btn_font,
            corner_radius=6, command=self._toggle_topmost,
        )
        self._pin_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))
        self._update_pin_button()

        self._refresh_btn = ctk.CTkButton(
            row2, text=self._t("refresh"), height=btn_h, font=btn_font,
            corner_radius=6, command=self._refresh,
        )
        self._refresh_btn.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # ── タグタブ（横スクロール） ──
        self.tab_frame = ctk.CTkScrollableFrame(
            self, orientation="horizontal", height=32,
            fg_color=("gray90", "gray17"), corner_radius=6,
            scrollbar_button_color=("gray70", "gray35"),
            scrollbar_button_hover_color=("gray60", "gray45"),
        )
        self.tab_frame.pack(fill="x", padx=4, pady=(3, 0))
        self._tab_buttons = {}

        # ── リスト表示 ──
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=2, pady=2)

    # ── ソート ──

    def _get_star(self, name: str) -> int:
        return self.config.get("stars", {}).get(name, 0)

    def _set_star(self, name: str, level: int):
        stars = self.config.setdefault("stars", {})
        if level == 0:
            stars.pop(name, None)
        else:
            stars[name] = level
        save_config(self.config)

    def _sort_items(self, items: list[dict]) -> list[dict]:
        """星の数(降順) → 最終使用日時(降順) → 名前(昇順)"""
        usage = self.config.get("usage", {})

        def key(item):
            name = item["name"]
            star = self._get_star(name)
            last = usage.get(name, {}).get("last", "")
            last_ts = _ts_to_int(last) if last else 0
            return (-star, -last_ts, name.lower())

        return sorted(items, key=key)

    # ── テーマ / 言語切替 ──

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "dark" if current == "Light" else "light"
        ctk.set_appearance_mode(new_mode)
        self.config["window"]["theme"] = new_mode
        save_config(self.config)
        self._update_theme_button()

    def _update_theme_button(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        # 現在の状態を表示: 太陽=ライト中、月=ダーク中
        self._theme_btn.configure(
            text="\U0001f319" if is_dark else "\u2600",
            text_color=("#A0B4F0", "#A0B4F0") if is_dark else ("#E8A000", "#E8A000"),
        )

    def _set_lang(self, lang: str):
        if self.lang == lang:
            return
        self.lang = lang
        self.config["lang"] = lang
        save_config(self.config)
        self._update_lang_segment()
        self._update_pin_button()
        self._refresh_btn.configure(text=self._t("refresh"))
        self._tag_btn.configure(text=self._t("tag"))
        self._render_list()

    def _update_lang_segment(self):
        active_fg = ("#6366F1", "#7C3AED")
        inactive_fg = "transparent"
        active_text = "white"
        inactive_text = ("gray40", "gray65")
        if self.lang == "ja":
            self._lang_btn_ja.configure(fg_color=active_fg, text_color=active_text, hover_color=("#5558E6", "#6D2FCC"))
            self._lang_btn_en.configure(fg_color=inactive_fg, text_color=inactive_text, hover_color=("gray70", "gray35"))
        else:
            self._lang_btn_ja.configure(fg_color=inactive_fg, text_color=inactive_text, hover_color=("gray70", "gray35"))
            self._lang_btn_en.configure(fg_color=active_fg, text_color=active_text, hover_color=("#5558E6", "#6D2FCC"))

    # ── タグタブ ──

    def _rebuild_tabs(self):
        for w in self.tab_frame.winfo_children():
            w.destroy()
        self._tab_buttons.clear()
        tags = [ALL_TAG] + self.config.get("tag_order", [])
        for tag in tags:
            is_active = (tag == self.current_tag)
            btn = ctk.CTkButton(
                self.tab_frame, text=tag, height=24, width=0,
                font=ctk.CTkFont(size=10, weight="bold" if is_active else "normal"),
                fg_color=("#3B8ED0", "#1F6AA5") if is_active else ("gray78", "gray30"),
                text_color=("white", "white") if is_active else ("gray10", "gray90"),
                hover_color=("#5EAEE8", "#2A80B8") if is_active else ("gray68", "gray40"),
                corner_radius=12,
                command=lambda t=tag: self._switch_tag(t),
            )
            btn.pack(side="left", padx=2, pady=1)
            self._tab_buttons[tag] = btn

    def _switch_tag(self, tag: str):
        self.current_tag = tag
        self._more_expanded = False
        self._rebuild_tabs()
        self._render_list()

    # ── データ読み込み ──

    def _load_desktop_items(self):
        self.items = scan_desktop()
        self._rebuild_tabs()
        self._render_list_placeholders()
        self._load_icons_async()

    def _refresh(self):
        if self._loading:
            return
        self.items = scan_desktop()
        self._rebuild_tabs()
        self._render_list_placeholders()
        self._load_icons_async()

    # ── フィルタ ──

    def _get_filtered_items(self) -> list[dict]:
        if self.current_tag == ALL_TAG:
            return self.items
        tags_map = self.config.get("tags", {})
        return [it for it in self.items if self.current_tag in tags_map.get(it["name"], [])]

    # ── リスト描画 ──

    def _render_list_placeholders(self):
        self._render_items(use_cache=False)

    def _render_list(self):
        self._render_items(use_cache=True)

    def _render_items(self, use_cache: bool):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        if not use_cache:
            self.icon_images.clear()

        filtered = self._get_filtered_items()
        sorted_items = self._sort_items(filtered)
        visible_count = self.config.get("visible_count", 30)

        visible = sorted_items[:visible_count]
        hidden = sorted_items[visible_count:]

        for item in visible:
            ctk_img = self._get_or_create_image(item, use_cache)
            self._create_row(self.scroll_frame, item, ctk_img)

        if hidden:
            self._render_more_section(hidden, use_cache)

    def _render_more_section(self, items: list[dict], use_cache: bool):
        sep = ctk.CTkFrame(self.scroll_frame, height=1, fg_color=("gray75", "gray40"))
        sep.pack(fill="x", padx=4, pady=(4, 0))

        n = len(items)
        label = self._t("more", n=n) if not self._more_expanded else self._t("collapse")
        ctk.CTkButton(
            self.scroll_frame, text=label,
            height=22, font=ctk.CTkFont(size=10),
            fg_color="transparent", hover_color=("gray85", "gray25"),
            text_color=("gray40", "gray60"), anchor="w",
            command=self._toggle_more,
        ).pack(fill="x", padx=1)

        if self._more_expanded:
            for item in items:
                ctk_img = self._get_or_create_image(item, use_cache)
                self._create_row(self.scroll_frame, item, ctk_img)

    def _toggle_more(self):
        self._more_expanded = not self._more_expanded
        self._render_list()

    def _get_or_create_image(self, item: dict, use_cache: bool):
        if use_cache:
            ctk_img = self.icon_images.get(item["name"])
            if ctk_img:
                return ctk_img
        placeholder = _create_default_icon(item["name"], ICON_SIZE)
        ctk_img = ctk.CTkImage(light_image=placeholder, dark_image=placeholder, size=(ICON_SIZE, ICON_SIZE))
        self.icon_images[item["name"]] = ctk_img
        return ctk_img

    def _create_row(self, parent, item: dict, ctk_img):
        """1行: [star_btn] [icon + name_btn]"""
        name = item["name"]
        star = self._get_star(name)

        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=0, pady=0)

        # 星ボタン（左端、固定幅）
        star_text = STAR_CHARS[star]
        star_btn = ctk.CTkButton(
            row_frame, text=star_text, width=20, height=ROW_HEIGHT,
            font=ctk.CTkFont(size=9),
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=("goldenrod", "gold") if star > 0 else ("gray70", "gray50"),
            corner_radius=0,
            command=lambda n=name: self._cycle_star(n),
        )
        star_btn.pack(side="left", padx=0)

        # アイコン+名前ボタン（残り領域）
        # 長い名前は切り詰め（ウインドウ幅に収まるように）
        max_chars = 28
        display = name if len(name) <= max_chars else name[:max_chars - 1] + "..."

        name_btn = ctk.CTkButton(
            row_frame, image=ctk_img, text=display,
            anchor="w", height=ROW_HEIGHT,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"),
            corner_radius=4,
            command=lambda it=item: self._on_click(it),
        )
        name_btn.pack(side="left", fill="x", expand=True, padx=0)
        name_btn._ds_item_name = name

        # ホバーでフルネーム表示
        if len(name) > max_chars:
            name_btn.bind("<Enter>", lambda e, n=name: self.title(f"DeskShelf - {n}"))
            name_btn.bind("<Leave>", lambda e: self.title("DeskShelf"))

    def _cycle_star(self, name: str):
        """星を 0→1→2→3→0 でサイクル"""
        current = self._get_star(name)
        new_level = (current + 1) % 4
        self._set_star(name, new_level)
        self._render_list()

    # ── アイコン非同期読み込み ──

    def _load_icons_async(self):
        self._loading = True

        def worker():
            for item in self.items:
                if not self._loading:
                    break
                try:
                    pil_img = get_icon(item, CACHE_DIR, ICON_SIZE)
                    self.after(0, self._update_icon, item["name"], pil_img)
                except Exception:
                    pass
            self._loading = False

        threading.Thread(target=worker, daemon=True).start()

    def _update_icon(self, name: str, pil_img: Image.Image):
        try:
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(ICON_SIZE, ICON_SIZE))
            self.icon_images[name] = ctk_img
            self._update_icon_in_tree(self.scroll_frame, name, ctk_img)
        except Exception:
            pass

    def _update_icon_in_tree(self, parent, name: str, ctk_img):
        for widget in parent.winfo_children():
            if getattr(widget, "_ds_item_name", None) == name:
                widget.configure(image=ctk_img)
                return True
            if hasattr(widget, "winfo_children") and widget.winfo_children():
                if self._update_icon_in_tree(widget, name, ctk_img):
                    return True
        return False

    # ── クリック ──

    def _on_click(self, item: dict):
        launch(item)
        self._record_usage(item["name"])

    def _record_usage(self, name: str):
        """使用回数と最終日時を記録（起動時に1回書くだけ、軽い）"""
        usage = self.config.setdefault("usage", {})
        u = usage.get(name, {"count": 0, "last": ""})
        u["count"] = u.get("count", 0) + 1
        u["last"] = datetime.now(timezone.utc).isoformat()
        usage[name] = u
        save_config(self.config)

    # ── タグ管理 ──

    def _open_tag_manager(self):
        import json
        win = ctk.CTkToplevel(self)
        win.title("Tag Manager")
        win.geometry("400x500")
        win.attributes("-topmost", True)
        win.grab_set()

        # ローカルコピーで作業（Cancel時に破棄するため）
        local_tag_order = list(self.config.get("tag_order", []))
        local_tags = json.loads(json.dumps(self.config.get("tags", {})))

        top = ctk.CTkFrame(win, fg_color="transparent")
        top.pack(anchor="w", padx=8, pady=(8, 4))

        new_tag_entry = ctk.CTkEntry(top, placeholder_text="New tag...", width=140)
        new_tag_entry.pack(side="left", padx=(0, 4))

        current_tag_var = ctk.StringVar(value=local_tag_order[0] if local_tag_order else "")
        tag_selector = ctk.CTkOptionMenu(top, variable=current_tag_var, values=local_tag_order if local_tag_order else ["(none)"], width=110)
        tag_selector.pack(side="left", padx=2)

        check_vars = {}

        def refresh_sel():
            tag_selector.configure(values=local_tag_order if local_tag_order else ["(none)"])
            if local_tag_order and current_tag_var.get() not in local_tag_order:
                current_tag_var.set(local_tag_order[0])

        def add_tag():
            n = new_tag_entry.get().strip()
            if n and n not in local_tag_order:
                local_tag_order.append(n)
                refresh_sel()
                new_tag_entry.delete(0, "end")

        def del_tag():
            t = current_tag_var.get()
            if t and t != "(none)" and t in local_tag_order:
                local_tag_order.remove(t)
                for v in local_tags.values():
                    if t in v:
                        v.remove(t)
                refresh_sel()
                load_items()

        ctk.CTkButton(top, text="Add", width=36, command=add_tag).pack(side="left", padx=1)
        ctk.CTkButton(top, text="Del", width=36, fg_color="firebrick", hover_color="darkred", command=del_tag).pack(side="left", padx=1)

        ctk.CTkLabel(win, text="Select tag, then check items:", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=16, pady=(2, 1))

        list_frame = ctk.CTkScrollableFrame(win)
        list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        def load_items(*_a):
            for w in list_frame.winfo_children():
                w.destroy()
            check_vars.clear()
            t = current_tag_var.get()
            if not t or t == "(none)":
                return
            for item in self.items:
                var = ctk.BooleanVar(value=(t in local_tags.get(item["name"], [])))
                check_vars[item["name"]] = var
                ctk.CTkCheckBox(list_frame, text=item["name"], variable=var, font=ctk.CTkFont(size=11), height=22).pack(anchor="w", padx=4, pady=0)

        current_tag_var.trace_add("write", load_items)
        load_items()

        def save_tags():
            t = current_tag_var.get()
            if t and t != "(none)":
                for n, v in check_vars.items():
                    local_tags.setdefault(n, [])
                    if v.get() and t not in local_tags[n]:
                        local_tags[n].append(t)
                    elif not v.get() and t in local_tags[n]:
                        local_tags[n].remove(t)
            # ローカルコピーを本体に反映
            self.config["tag_order"] = local_tag_order
            self.config["tags"] = local_tags
            save_config(self.config)
            self._rebuild_tabs()
            self._render_list()
            win.destroy()

        bf = ctk.CTkFrame(win, fg_color="transparent")
        bf.pack(fill="x", padx=8, pady=(0, 6))
        ctk.CTkButton(bf, text="Save", width=80, command=save_tags).pack(side="right", padx=4)
        ctk.CTkButton(bf, text="Cancel", width=60, fg_color="gray50", command=win.destroy).pack(side="right", padx=4)

    # ── その他 ──

    def _toggle_topmost(self):
        current = self.config["window"].get("always_on_top", True)
        self.config["window"]["always_on_top"] = not current
        self.attributes("-topmost", not current)
        self._update_pin_button()

    def _update_pin_button(self):
        is_pinned = self.config["window"].get("always_on_top", True)
        if is_pinned:
            self._pin_btn.configure(text=self._t("topmost_on"), fg_color=("#3B8ED0", "#1F6AA5"))
        else:
            self._pin_btn.configure(text=self._t("topmost_off"), fg_color="gray50")

    def _restore_position(self):
        win = self.config["window"]
        x, y = win.get("x"), win.get("y")
        if x is not None and y is not None:
            if -5000 < x < 10000 and -5000 < y < 10000:
                self.geometry(f"+{x}+{y}")
                self.after(100, self._clamp_to_screen)

    def _clamp_to_screen(self):
        try:
            x, y = self.winfo_x(), self.winfo_y()
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            if x > sw + 2000 or y > sh + 2000 or x < -3000 or y < -3000:
                self.geometry("+100+100")
        except Exception:
            pass

    def _on_close(self):
        self._loading = False
        try:
            self.config["window"]["x"] = self.winfo_x()
            self.config["window"]["y"] = self.winfo_y()
            max_w = self.config["window"].get("max_width", 500)
            self.config["window"]["width"] = min(self.winfo_width(), max_w)
            save_config(self.config)
        except Exception:
            pass
        self.destroy()


def _ts_to_int(ts: str) -> int:
    try:
        return int(datetime.fromisoformat(ts).timestamp())
    except Exception:
        return 0
