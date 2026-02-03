from pathlib import Path
import base64
from typing import Sequence, List
from type import ImageInput


class ImagePayloadBuilder:
    @staticmethod
    def _to_bytes(data: ImageInput) -> bytes:
        if isinstance(data, (bytes, bytearray, memoryview)):
            return bytes(data)
        path = Path(data)
        if not path.exists():
            raise FileNotFoundError(f"Image path not found: {path}")
        return path.read_bytes()

    @staticmethod
    def encode(data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    @classmethod
    def prepare_llm_payload(
        cls,
        payload: Sequence[ImageInput],
        mime: str = "image/jpeg",
    ) -> List[dict[str, str | dict[str, str]]]:
        payload = [cls._to_bytes(p) for p in payload]
        return [
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{cls.encode(p)}"},
            }
            for p in payload
        ]
