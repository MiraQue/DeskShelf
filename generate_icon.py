"""DeskShelf アプリアイコンを生成するワンショットスクリプト"""

from PIL import Image, ImageDraw
import os


def generate_icon():
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for sz in sizes:
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        pad = max(1, sz // 16)
        r = max(2, sz // 8)

        # 背景: 木目風の温かいブラウン
        bg_color = (62, 50, 42, 245)
        draw.rounded_rectangle(
            [pad, pad, sz - pad - 1, sz - pad - 1],
            radius=r,
            fill=bg_color,
        )

        margin = max(3, sz // 7)
        shelf_color = (160, 120, 80, 255)      # 棚板の色（木目ブラウン）
        shelf_edge = (120, 85, 55, 255)         # 棚板の前面（少し濃い）
        shelf_h = max(2, sz // 12)              # 棚板の厚み
        shelf_front = max(1, sz // 24)          # 棚板前面の厚み

        # 棚を3段描く（上から: 物が乗る場所の下に板）
        shelf_positions = [0.30, 0.55, 0.80]

        for sy in shelf_positions:
            y = int(sz * sy)
            # 棚板上面
            draw.rectangle(
                [margin, y, sz - margin - 1, y + shelf_h - 1],
                fill=shelf_color,
            )
            # 棚板前面（少し濃い影）
            draw.rectangle(
                [margin, y + shelf_h, sz - margin - 1, y + shelf_h + shelf_front - 1],
                fill=shelf_edge,
            )

        # 左右の側板
        side_w = max(1, sz // 20)
        side_color = (130, 95, 65, 255)
        top_y = int(sz * 0.12)
        bottom_y = int(sz * 0.80) + shelf_h + shelf_front
        draw.rectangle([margin - side_w, top_y, margin - 1, bottom_y], fill=side_color)
        draw.rectangle([sz - margin, top_y, sz - margin + side_w - 1, bottom_y], fill=side_color)

        # 棚の上にアイテム（カラフルな小さい四角）を配置
        item_colors = [
            (100, 180, 230, 255),  # 青
            (230, 160, 80, 255),   # オレンジ
            (120, 195, 130, 255),  # 緑
            (210, 100, 110, 255),  # 赤
            (180, 140, 200, 255),  # 紫
        ]
        item_sz = max(2, sz // 9)
        item_gap = max(1, sz // 18)
        inner_left = margin + max(1, sz // 20)

        # 各段にアイテムを置く
        items_per_row = [3, 2, 2]
        for row_idx, sy in enumerate(shelf_positions):
            y_base = int(sz * sy) - item_sz - max(1, sz // 32)
            n = items_per_row[row_idx]
            for i in range(n):
                x = inner_left + i * (item_sz + item_gap)
                color = item_colors[(row_idx * 3 + i) % len(item_colors)]
                draw.rounded_rectangle(
                    [x, y_base, x + item_sz - 1, y_base + item_sz - 1],
                    radius=max(1, sz // 40),
                    fill=color,
                )

        images.append(img)

    # .ico として保存
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(out_dir, exist_ok=True)
    ico_path = os.path.join(out_dir, "deskshelf.ico")
    images[-1].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[:-1])
    print(f"Icon saved: {ico_path}")

    # PNG版も保存
    png_path = os.path.join(out_dir, "deskshelf.png")
    images[-1].save(png_path, "PNG")
    print(f"PNG saved: {png_path}")


if __name__ == "__main__":
    generate_icon()
