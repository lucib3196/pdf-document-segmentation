from pathlib import Path
import pymupdf
import base64
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from uuid import UUID
from pydantic import BaseModel
from langgraph.graph.state import CompiledStateGraph


def extract_page_range(input_pdf, start, end, output_pdf):
    src = pymupdf.open(input_pdf)
    dst = pymupdf.open()
    dst.insert_pdf(src, from_page=start, to_page=end)
    dst.save(output_pdf)
    src.close()
    dst.close()
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


def save_graph_visualization(
    graph: CompiledStateGraph | Any,
    folder_path: str | Path,
    filename: str,
):
    try:
        image_bytes = graph.get_graph().draw_mermaid_png()
        save_path = write_image_data(image_bytes, folder_path, filename)

        print(f"✅ Saved graph visualization at: {save_path}")
    except ValueError:
        raise
    except Exception as error:
        print(f"❌ Graph visualization failed: {error}")


def to_serializable(obj: Any) -> Any:
    """
    Recursively convert Pydantic models (and nested dicts/lists thereof)
    into plain Python data structures.
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(v) for v in obj]

    # --- Special cases ---
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Path):
        return obj.as_posix()
    if isinstance(obj, (bytes, bytearray, memoryview)):
        return base64.b64encode(obj).decode("utf-8")
    return obj
