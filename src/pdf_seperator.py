from pathlib import Path
import pymupdf
from type import PDFInput, BaseOutput
from typing import Sequence, Iterable


class PDFSeperator:
    def __init__(
        self,
        pdf_path: PDFInput | None = None,
        pdf_bytes: Sequence[bytes] | None = None,
        image_bytes: Sequence[bytes] | None = None,
        pdf_name: str | None = "input_pdf",
    ):
        self.pdf_name = pdf_name
        if pdf_path is None and pdf_bytes is None and image_bytes is None:
            raise ValueError(
                "Either pdf_path or image_bytes or pdf_bytes must be provided"
            )
        if pdf_path is not None and pdf_bytes is not None and image_bytes is None:
            raise ValueError("Provide only one of pdf_path or image_bytes")

        if pdf_path is not None:
            self.pdf = pymupdf.open(pdf_path).tobytes()
        elif pdf_bytes:
            self.pdf = pdf_bytes
        elif image_bytes:
            self.pdf = self.images_to_pdf(image_bytes)

        else:
            raise ValueError("Unexpected Error Occured")

    def extract_page_range(self, start: int, end: int) -> bytes:
        src = pymupdf.open(stream=self.pdf, filetype="pdf")
        dst = pymupdf.open()
        dst.insert_pdf(src, from_page=start, to_page=end, rotate=0)
        return dst.tobytes()

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

    def _extract_and_save(self, start: int, end: int, output_dir: str | Path) -> str:
        output_dir = Path(output_dir).resolve()
        if not output_dir.exists():
            raise ValueError("Failed to extract pdf path {output_dir} does not exist")
        output_path = output_dir / (f"{self.pdf_name}_extracted_{start}_{end}.pdf")
        output_path.write_bytes(self.extract_page_range(start, end))
        return output_path.as_posix()


if __name__ == "__main__":
    path = r"data\Lecture_02_03.pdf"
    PDFSeperator(path)._extract_and_save(1, 3, output_dir="./data")
