from pathlib import Path
from PIL import Image, ImageOps

CURRENT = Path("current")
OUTPUT = Path("output")

OUTPUT.mkdir(exist_ok=True)

files = [p for p in CURRENT.iterdir() if p.is_file()]

originals = [
    p for p in files
    if p.suffix.lower() in {".jpg", ".jpeg", ".webp"}
]

pngs = [
    p for p in files
    if p.suffix.lower() == ".png"
]

if len(originals) != 1:
    raise RuntimeError(
        f"В current должен быть ровно один исходник. Найдено: {len(originals)}"
    )

if len(pngs) != 1:
    raise RuntimeError(
        f"В current должен быть ровно один PNG от ChatGPT. Найдено: {len(pngs)}"
    )

original_path = originals[0]
edited_path = pngs[0]

original = Image.open(original_path)
original = ImageOps.exif_transpose(original)

target_size = original.size
target_ext = original_path.suffix.lower()

edited = Image.open(edited_path).convert("RGBA")

# Белая подложка
white = Image.new("RGBA", edited.size, (255, 255, 255, 255))
edited = Image.alpha_composite(white, edited).convert("RGB")

# Масштабируем только пропорционально
edited.thumbnail(target_size, Image.Resampling.LANCZOS)

canvas = Image.new("RGB", target_size, (255, 255, 255))

x = (target_size[0] - edited.width) // 2
y = (target_size[1] - edited.height) // 2

canvas.paste(edited, (x, y))

output_path = OUTPUT / original_path.name

if target_ext in {".jpg", ".jpeg"}:
    canvas.save(
        output_path,
        "JPEG",
        quality=95,
        subsampling=0
    )
elif target_ext == ".webp":
    canvas.save(output_path, "WEBP", quality=95)

print(f"Готово: {output_path}")