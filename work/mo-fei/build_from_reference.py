from __future__ import annotations

from collections import deque
from pathlib import Path
from statistics import median
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
SOURCE = WORK / "source" / "reference.jpg"
RUN = WORK / "run"
OUT = ROOT / "outputs"
CELL_W, CELL_H = 192, 208
COL_BOUNDS = [96, 253, 410, 568, 725, 883, 1040, 1198, 1355, 1512, 1670, 1828]
ROW_BOUNDS = [133, 273, 413, 553, 693, 833, 973, 1113, 1241]
ROW_CONTENT = [(149, 263), (289, 399), (428, 540), (568, 680), (705, 814), (843, 954), (978, 1089), (1114, 1227)]
ACTION_NAMES = ["idle", "walk", "run", "drag", "working", "waiting", "sleep", "happy", "angry", "fail", "down"]
DIR_NAMES = ["up", "up-right", "right", "down-right", "down", "down-left", "left", "up-left"]


def clean_cell(image: Image.Image, direction: int, action: int) -> Image.Image:
    x0, x1 = COL_BOUNDS[action] + 3, COL_BOUNDS[action + 1] - 3
    y0, y1 = ROW_CONTENT[direction]
    crop = image.crop((x0, y0, x1, y1)).convert("RGB")
    w, h = crop.size
    px = crop.load()
    border = []
    for x in range(w):
        border.extend((px[x, 0], px[x, h - 1]))
    for y in range(h):
        border.extend((px[0, y], px[w - 1, y]))
    key = tuple(int(median(c[i] for c in border)) for i in range(3))

    def distance(c):
        return sum((c[i] - key[i]) ** 2 for i in range(3)) ** 0.5

    # Only erase key-like pixels connected to the crop boundary. This protects dark hair and clothes.
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.extend(((x, 0), (x, h - 1)))
    for y in range(h):
        q.extend(((0, y), (w - 1, y)))
    while q:
        x, y = q.popleft()
        idx = y * w + x
        if seen[idx] or distance(px[x, y]) > 31:
            continue
        seen[idx] = 1
        if x: q.append((x - 1, y))
        if x + 1 < w: q.append((x + 1, y))
        if y: q.append((x, y - 1))
        if y + 1 < h: q.append((x, y + 1))

    out = crop.convert("RGBA")
    opx = out.load()
    for y in range(h):
        for x in range(w):
            # Source is a JPEG contact sheet; discard the entire safety band where grid compression lives.
            if x < 10 or x >= w - 10 or y < 8 or y >= h - 8:
                opx[x, y] = (0, 0, 0, 0)
                continue
            if seen[y * w + x]:
                d = distance(px[x, y])
                if d <= 13:
                    opx[x, y] = (0, 0, 0, 0)
                else:
                    alpha = max(0, min(255, int((d - 13) / 18 * 255)))
                    # Suppress the gray JPEG fringe while preserving antialiasing.
                    r, g, b = px[x, y]
                    opx[x, y] = (r, g, b, alpha)
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    return out


def fit(sprite: Image.Image, max_w=174, max_h=166) -> Image.Image:
    scale = min(max_w / sprite.width, max_h / sprite.height, 1.55)
    nw, nh = max(1, round(sprite.width * scale)), max(1, round(sprite.height * scale))
    resized = sprite.resize((nw, nh), Image.Resampling.NEAREST)
    # A light pixel-safe sharpening offsets JPEG softness without redrawing details.
    rgb = resized.convert("RGB").filter(ImageFilter.UnsharpMask(radius=0.55, percent=115, threshold=3))
    rgb.putalpha(resized.getchannel("A"))
    return rgb


def place(sprite: Image.Image, dx=0, dy=0, baseline=188) -> Image.Image:
    frame = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    fitted = fit(sprite)
    x = (CELL_W - fitted.width) // 2 + dx
    y = baseline - fitted.height + dy
    frame.alpha_composite(fitted, (x, y))
    return frame


def save_frames(states):
    frames_root = RUN / "frames"
    for state, frames in states.items():
        folder = frames_root / state
        folder.mkdir(parents=True, exist_ok=True)
        for i, frame in enumerate(frames):
            frame.save(folder / f"{i:02d}.png")


def compose(states, look_frames):
    specs = ["idle", "running-right", "running-left", "waving", "jumping", "failed", "waiting", "running", "review"]
    atlas = Image.new("RGBA", (CELL_W * 8, CELL_H * 11), (0, 0, 0, 0))
    for row, state in enumerate(specs):
        for col, frame in enumerate(states[state]):
            atlas.alpha_composite(frame, (col * CELL_W, row * CELL_H))
    # v2 reserves idle row column 6 as the explicit neutral/deadzone still.
    atlas.alpha_composite(states["idle"][0], (6 * CELL_W, 0))
    for i, frame in enumerate(look_frames):
        row, col = 9 + i // 8, i % 8
        atlas.alpha_composite(frame, (col * CELL_W, row * CELL_H))
    final = RUN / "final"
    final.mkdir(parents=True, exist_ok=True)
    atlas.save(final / "spritesheet-extended.png")
    atlas.save(final / "spritesheet-extended.webp", lossless=True, method=6)
    return atlas


def make_preview(atlas):
    labels = ["待机", "向右移动", "向左移动", "开心/招手", "跳跃", "失败/低头", "等待", "工作", "生气/检查", "视线 000–157.5°", "视线 180–337.5°"]
    scale = 0.5
    thumb_w, thumb_h = round(CELL_W * scale), round(CELL_H * scale)
    left = 150
    sheet = Image.new("RGBA", (left + thumb_w * 8 + 20, thumb_h * 11 + 20), "#252525")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for row, label in enumerate(labels):
        draw.text((8, 10 + row * thumb_h + 42), label, fill="white", font=font)
        for col in range(8):
            cell = atlas.crop((col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H))
            cell = cell.resize((thumb_w, thumb_h), Image.Resampling.NEAREST)
            sheet.alpha_composite(cell, (left + col * thumb_w, 10 + row * thumb_h))
    OUT.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(OUT / "ye-xiu-contact-sheet.png", quality=95)


image = Image.open(SOURCE)
sprites = [[clean_cell(image, d, a) for a in range(11)] for d in range(8)]

# Every animation uses only poses from the user's sheet. Pixel offsets create loop cadence without changing identity.
states = {
    "idle": [place(sprites[0][0], dy=o) for o in (0, -1, -2, -1, 0, 1)],
    "running-right": [place(sprites[2][a], dx=x, dy=y) for a, x, y in [(1,-5,0),(2,-3,-2),(3,-1,0),(2,1,-3),(1,3,0),(2,5,-2),(3,3,0),(1,0,1)]],
    "running-left": [place(ImageOps.mirror(sprites[2][a]), dx=x, dy=y) for a, x, y in [(1,5,0),(2,3,-2),(3,1,0),(2,-1,-3),(1,-3,0),(2,-5,-2),(3,-3,0),(1,0,1)]],
    "waving": [place(sprites[0][a], dy=y) for a, y in [(0,0),(7,-2),(0,0),(7,-1)]],
    "jumping": [place(sprites[0][a], dy=y) for a, y in [(0,0),(7,-12),(7,-24),(7,-12),(0,0)]],
    "failed": [place(sprites[0][a], dy=y) for a, y in [(8,0),(8,1),(9,3),(9,5),(10,7),(6,7),(10,7),(9,4)]],
    "waiting": [place(sprites[0][a], dy=y) for a, y in [(5,0),(5,-1),(0,0),(5,-1),(5,0),(0,1)]],
    "running": [place(sprites[0][4], dy=y) for y in (0,-1,0,-1,0,1)],
    "review": [place(sprites[0][a], dy=y) for a, y in [(8,0),(0,0),(8,-1),(0,0),(10,1),(8,0)]],
}

# User-approved hover easter eggs. Codex exposes 16 fixed pointer-direction slots but no
# per-pet random event hook, so each slot receives a different source-grounded reaction.
# The sequence intentionally covers wave/happy/jump/angry/fail/prone/sleep/down twice,
# using alternate supplied directions while preserving the exact face and clothing art.
hover_specs = [
    (0, 7, 0, 0),    # wave / happy
    (0, 7, 0, -24),  # jump
    (0, 8, 0, 0),    # angry
    (0, 9, 0, 3),    # fail
    (2, 3, 0, 5),    # prone / dragged
    (0, 6, 0, 5),    # sleep
    (0, 10, 0, 5),   # head down
    (2, 7, 0, -2),   # side happy
    (4, 7, 0, 0),    # back happy
    (5, 7, 0, -20),  # diagonal jump
    (6, 8, 0, 0),    # left angry
    (6, 9, 0, 3),    # left fail
    (6, 3, 0, 5),    # left prone
    (6, 6, 0, 5),    # left sleep
    (6, 10, 0, 5),   # left head down
    (7, 7, 0, -2),   # other diagonal happy
]
look_frames = [place(sprites[d][a], dx=x, dy=y) for d, a, x, y in hover_specs]
save_frames(states)
atlas = compose(states, look_frames)
make_preview(atlas)
print(RUN / "final" / "spritesheet-extended.webp")
print(OUT / "ye-xiu-contact-sheet.png")
