from collections import deque
from pathlib import Path
from PIL import Image, ImageChops, ImageStat


SOURCE = Path(__file__).parent / "source" / "reference.jpg"
OUTPUT = Path(__file__).parent / "run" / "qa" / "ye-xiu-base-preview.png"


def remove_connected_background(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    samples = []
    for x in range(width):
        samples.extend((pixels[x, 0], pixels[x, height - 1]))
    for y in range(height):
        samples.extend((pixels[0, y], pixels[width - 1, y]))
    samples.sort(key=lambda c: sum(c))
    middle = samples[len(samples) // 4 : len(samples) * 3 // 4]
    key = tuple(sum(c[i] for c in middle) // len(middle) for i in range(3))

    def is_background(x: int, y: int) -> bool:
        c = pixels[x, y]
        distance = sum((c[i] - key[i]) ** 2 for i in range(3)) ** 0.5
        return distance <= 24 and max(c) - min(c) <= 14

    visited = bytearray(width * height)
    queue = deque()
    for x in range(width):
        queue.extend(((x, 0), (x, height - 1)))
    for y in range(height):
        queue.extend(((0, y), (width - 1, y)))
    while queue:
        x, y = queue.popleft()
        index = y * width + x
        if visited[index] or not is_background(x, y):
            continue
        visited[index] = 1
        if x:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))

    rgba = rgb.convert("RGBA")
    alpha = Image.new("L", (width, height), 255)
    alpha_pixels = alpha.load()
    for y in range(height):
        for x in range(width):
            if visited[y * width + x]:
                alpha_pixels[x, y] = 0
    rgba.putalpha(alpha)
    bbox = rgba.getbbox()
    if bbox:
        rgba = rgba.crop(bbox)
    return rgba


source = Image.open(SOURCE)
# First action cell in the first direction row: the clearest neutral/front identity.
cell = source.crop((103, 141, 255, 269))
sprite = remove_connected_background(cell)
sprite = sprite.resize((sprite.width * 2, sprite.height * 2), Image.Resampling.NEAREST)
canvas = Image.new("RGBA", (192, 208), (0, 0, 0, 0))
canvas.alpha_composite(sprite, ((192 - sprite.width) // 2, 208 - sprite.height - 20))
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUTPUT)
print(OUTPUT)
