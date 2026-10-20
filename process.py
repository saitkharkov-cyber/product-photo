from pathlib import Path

from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from rembg import remove, new_session


INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")

OUTPUT_DIR.mkdir(exist_ok=True)

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}

MASK_MAX_SIDE = 1600

# Расширение маски
MASK_EXPAND = 3

# Смягчение края маски
MASK_FEATHER = 1.2

session = new_session("birefnet-general")


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
        image.save(
            output_path,
            "PNG"
        )

    elif ext == ".webp":
        image.convert("RGB").save(
            output_path,
            "WEBP",
            quality=95
        )


def improve_mask(alpha):
    # Лёгкое расширение маски:
    # MaxFilter увеличивает белую область наружу
    expand_size = MASK_EXPAND * 2 + 1

    alpha = alpha.filter(
        ImageFilter.MaxFilter(expand_size)
    )

    # Очень мягкий feather края
    if MASK_FEATHER > 0:
        alpha = alpha.filter(
            ImageFilter.GaussianBlur(MASK_FEATHER)
        )

    return alpha


def make_mask(original):
    width, height = original.size

    mask_source = original.copy()

    if max(width, height) > MASK_MAX_SIDE:
        scale = MASK_MAX_SIDE / max(width, height)

        mask_size = (
            max(1, round(width * scale)),
            max(1, round(height * scale))
        )

        mask_source = mask_source.resize(
            mask_size,
            Image.Resampling.LANCZOS
        )

        print(
            f"  Маска считается на: "
            f"{mask_size[0]}x{mask_size[1]}"
        )

    cutout_small = remove(
        mask_source,
        session=session
    ).convert("RGBA")

    alpha_small = cutout_small.getchannel("A")

    # Возвращаем маску к размеру оригинала
    if alpha_small.size != original.size:
        alpha = alpha_small.resize(
            original.size,
            Image.Resampling.LANCZOS
        )
    else:
        alpha = alpha_small

    # Страховка от подрезания светлых краёв
    alpha = improve_mask(alpha)

    return alpha


def make_shadow(alpha, size):
    width, height = size
    base = min(width, height)

    shadow_blur = max(
        5,
        int(base * 0.006)
    )

    shadow_offset_x = max(
        2,
        int(base * 0.002)
    )

    shadow_offset_y = max(
        8,
        int(base * 0.010)
    )

    shadow_alpha = alpha.filter(
        ImageFilter.GaussianBlur(
            shadow_blur
        )
    )

    shadow_alpha = shadow_alpha.point(
        lambda p: int(p * 0.22)
    )

    shadow = Image.new(
        "RGBA",
        size,
        (0, 0, 0, 0)
    )

    shadow.putalpha(
        shadow_alpha
    )

    shadow_layer = Image.new(
        "RGBA",
        size,
        (0, 0, 0, 0)
    )

    shadow_layer.alpha_composite(
        shadow,
        dest=(
            shadow_offset_x,
            shadow_offset_y
        )
    )

    return shadow_layer


def process_image(source_path):
    print()
    print(f"Обработка: {source_path.name}")

    original = Image.open(source_path)

    original = ImageOps.exif_transpose(
        original
    ).convert("RGB")

    original_size = original.size

    print(
        f"  Оригинал: "
        f"{original_size[0]}x{original_size[1]}"
    )

    alpha = make_mask(original)

    # Коррекция только товара
    product_rgb = original.copy()

    product_rgb = ImageEnhance.Brightness(
        product_rgb
    ).enhance(1.08)

    product_rgb = ImageEnhance.Contrast(
        product_rgb
    ).enhance(1.05)

    product_rgb = ImageEnhance.Color(
        product_rgb
    ).enhance(1.02)

    product_rgb = ImageEnhance.Sharpness(
        product_rgb
    ).enhance(1.03)

    product_rgba = product_rgb.convert(
        "RGBA"
    )

    product_rgba.putalpha(
        alpha
    )

    # Тень
    shadow_layer = make_shadow(
        alpha,
        original_size
    )

    # Белый фон
    canvas = Image.new(
        "RGBA",
        original_size,
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

    print(
        f"  Готово: "
        f"{output_path.name}"
    )


def main():
    files = [
        p
        for p in INPUT_DIR.iterdir()
        if (
            p.is_file()
            and p.suffix.lower()
            in SUPPORTED
        )
    ]

    if not files:
        print("В папке input нет изображений.")
        return

    print(
        f"Найдено изображений: "
        f"{len(files)}"
    )

    for path in files:
        output_path = OUTPUT_DIR / path.name

        if output_path.exists():
            print(
                f"Пропуск: {path.name} — уже готово"
            )
            continue

        try:
            process_image(path)

        except MemoryError:
            print(
                f"  ОШИБКА {path.name}: "
                f"не хватило оперативной памяти"
            )

        except Exception as e:
            print(
                f"  ОШИБКА {path.name}: "
                f"{e}"
            )

    print()
    print("Обработка завершена.")


if __name__ == "__main__":
    main()