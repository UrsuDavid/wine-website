from pathlib import Path

from PIL import Image


def convert_assets_to_webp(assets_dir: str = "assets") -> None:
    base = Path(assets_dir)
    if not base.exists():
        print(f"Assets directory not found: {base.resolve()}")
        return

    exts = {".png", ".jpg", ".jpeg"}
    converted = 0

    for path in sorted(base.glob("*.*")):
        if path.suffix.lower() not in exts:
            continue

        out_path = path.with_suffix(".webp")

        # Skip if a WebP version already exists so we do not
        # repeatedly re-encode the same image.
        if out_path.exists():
            print(f"Skipping {path.name} (WebP already exists)")
            continue

        try:
            with Image.open(path) as img:
                # Preserve transparency when present; otherwise use RGB
                if img.mode in ("P", "RGBA", "LA"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")

                img.save(out_path, "WEBP", quality=85, method=6)

            converted += 1
            print(f"Converted {path.name} -> {out_path.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to convert {path}: {exc}")

    if converted == 0:
        print("No PNG/JPG assets found to convert.")
    else:
        print(f"Done. Converted {converted} file(s) to WebP.")


if __name__ == "__main__":
    convert_assets_to_webp()
