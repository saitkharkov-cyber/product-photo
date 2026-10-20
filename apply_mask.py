from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

INPUT_DIR = Path("manual")
MASK_DIR = Path("manual-mask")
OUTPUT_DIR = Path("manual-output")

OUTPUT_DIR.mkdir(exist_ok=True)

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def save_result(image, source_path, output_path):
    ext = source_path.suffix.lower()

    if ext in {".jpg", ".jpeg"}:
        image.convert("RGB").save(
            output_path,
            "JPEG",
            quality=95,
            subsampling=0
        )

    elif ext == ".png":
        image.save(output_path, "PNG")

    elif ext == ".webp":
        image.convert("RGB").save(
            output_path,
            "WEBP",
            quality=95
        )


for source_path in INPUT_DIR.iterdir():
    if (
        not source_path.is_file()
        or source_path.suffix.lower() not in SUPPORTED
    ):
        continue

    mask_path = MASK_DIR / f"{source_path.stem}_mask.png"

    if not mask_path.exists():
        print(f"Нет маски: {source_path.name}")
        continue

    print(f"Обработка: {source_path.name}")

    original = Image.open(source_path)
    original = ImageOps.exif_transpose(original).convert("RGB")

    alpha = Image.open(mask_path).convert("L")

    if alpha.size != original.size:
        raise RuntimeError(
            f"Размер маски не совпадает: {alpha.size} != {original.size}"
        )

    # лёгкая коррекция товара
    product = ImageEnhance.Brightness(original).enhance(1.08)
    product = ImageEnhance.Contrast(product).enhance(1.05)
    product = ImageEnhance.Color(product).enhance(1.02)

    product_rgba = product.convert("RGBA")
    product_rgba.putalpha(alpha)

    # лёгкая тень
    width, height = original.size
    base = min(width, height)

    blur = max(5, int(base * 0.006))
    offset_x = max(2, int(base * 0.002))
    offset_y = max(8, int(base * 0.010))

    shadow_alpha = alpha.filter(
        ImageFilter.GaussianBlur(blur)
    )

    shadow_alpha = shadow_alpha.point(
        lambda p: int(p * 0.18)
    )

    shadow = Image.new(
        "RGBA",
        original.size,
        (0, 0, 0, 0)
    )
    shadow.putalpha(shadow_alpha)

    shadow_layer = Image.new(
        "RGBA",
        original.size,
        (0, 0, 0, 0)
    )

    shadow_layer.alpha_composite(
        shadow,
        dest=(offset_x, offset_y)
    )

    # сборка
    canvas = Image.new(
        "RGBA",
        original.size,
        (255, 255, 255, 255)
    )

    canvas = Image.alpha_composite(
        canvas,
        shadow_layer
    )

    canvas = Image.alpha_composite(
        canvas,
        product_rgba
    )

    result = canvas.convert("RGB")

    output_path = OUTPUT_DIR / source_path.name

    save_result(
        result,
        source_path,
        output_path
    )

    print(f"  -> {output_path}")

print("Готово.")