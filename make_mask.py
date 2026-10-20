from pathlib import Path
from PIL import Image, ImageOps
from rembg import remove, new_session

INPUT_DIR = Path("manual")
MASK_DIR = Path("manual-mask")

MASK_DIR.mkdir(exist_ok=True)

session = new_session("birefnet-general")

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}

for path in INPUT_DIR.iterdir():
    if not path.is_file() or path.suffix.lower() not in SUPPORTED:
        continue

    print(f"Маска: {path.name}")

    original = Image.open(path)
    original = ImageOps.exif_transpose(original).convert("RGB")

    cutout = remove(
        original,
        session=session
    ).convert("RGBA")

    alpha = cutout.getchannel("A")

    mask_path = MASK_DIR / f"{path.stem}_mask.png"

    alpha.save(mask_path)

    print(f"  -> {mask_path}")