from pathlib import Path
import base64


def save_base64_image(b64_data: str, output_path: str | Path) -> Path:
    """
    Decode a base64-encoded image and save it to disk.

    Args:
        b64_data: Base64-encoded image string (no data URI prefix).
        output_path: Path where the image will be saved.

    Returns:
        Path to the saved image.
    """
    output_path = Path(output_path).resolve()

    image_bytes = base64.b64decode(b64_data)
    output_path.write_bytes(image_bytes)

    return output_path


def write_image_data(image_bytes: bytes, folder_path: str | Path, filename: str) -> str:
    try:
        path = Path(folder_path).resolve()
        path.mkdir(exist_ok=True)
        save_path = path / filename

        if save_path.suffix != ".png":
            raise ValueError(
                "Suffix allowed is only PNG either missing or nnot allowed"
            )
        save_path.write_bytes(image_bytes)
        return save_path.as_posix()
    except Exception as e:
        raise ValueError(f"Could not save image {str(e)}")
