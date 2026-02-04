from type import PDFInput, ImageExt
import pymupdf
from typing import List, Optional, Iterable
from pathlib import Path


class PDFImageConverter:
    def convert_to_images(
        self, pdf: PDFInput, zoom: float = 0.2, ext: ImageExt = "png"
    ) -> List[bytes]:
        if isinstance(PDFInput, (bytes, bytearray, memoryview)):
            doc = pymupdf.open(stream=PDFInput, filetype="pdf")
        else:
            doc = pymupdf.open(pdf)
        matrix = pymupdf.Matrix(zoom, zoom)
        image_bytes = [page.get_pixmap(matrix=matrix).tobytes(ext) for page in doc]
        doc.close()
        return image_bytes

    def save_to_images(
        self,
        pdf: PDFInput,
        output_path: str | Path,
        pdf_name: str | None = None,
        ext: ImageExt = "png",
        start: int = 0,
    ) -> None:

        if pdf_name is None:
            if isinstance(pdf, (str, Path)):
                pdf_name = Path(pdf).stem
            else:
                raise ValueError("pdf_name must be provided when pdf is not a path")

        output_path = self._validate(output_path)
        data = self.convert_to_images(pdf)
        for i, b in enumerate(data, start=start):
            out = output_path / f"{pdf_name}_page_{i}.{ext}"
            out.write_bytes(b)

    def images_to_pdf(self, images: Iterable[bytes]) -> bytes:
        doc = pymupdf.open()
        for img_bytes in images:
            img_doc = pymupdf.open(stream=img_bytes, filetype="png")
            rect = img_doc[0].rect
            page = doc.new_page(width=rect.width, height=rect.height)
            page.insert_image(rect, stream=img_bytes)
            img_doc.close()
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    def _validate(self, path: str | Path) -> Path:
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Failed to validate pdf {path} cannot be resolved")
        return path
