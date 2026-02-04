from pathlib import Path
from typing import Literal, Optional, Tuple

import pymupdf
from pymupdf import Page

from pdf_image_converter import PDFImageConverter
from type import Anchor, AnchorPos


class PDFAnnotator:
    def __init__(
        self,
        pdf_path: str | Path,
        anchor: Anchor | AnchorPos = Anchor.BOTTOM_LEFT,
        margin_frac: float = 1 / 10,
        offset: Tuple[int, int] = (10, 10),
        zoom: float = 2.0,
    ):
        self.pdf = Path(pdf_path).resolve()
        self.anchor = Anchor(anchor)
        self.margin_frac = margin_frac
        self.offset = offset
        self.zoom = zoom
        self._validate()

    def annotate_and_render_pages(
        self,
    ) -> bytes:
        doc = pymupdf.open(self.pdf)

        try:
            # Annotate all pages
            for page in doc:
                assert isinstance(page, Page)
                self._annotate_page(page)
            # Return annotated PDF as bytes
            return doc.tobytes()
        finally:
            doc.close()

    def _annotate_and_save(
        self,
        method: Literal["pdf", "image"] = "image",
        output_path: Optional[str | Path] = None,
    ) -> str:
        data = self.annotate_and_render_pages()
        output_path = self.get_output_path(path, method)
        if method == "pdf":
            if not isinstance(data, (bytes, bytearray)):
                raise ValueError("Expected PDF data to be bytes")
            output_path.write_bytes(data)
            return output_path.as_posix()
        elif method == "image":
            PDFImageConverter().save_to_images(
                data, output_path, pdf_name=self.pdf.stem
            )
        return output_path.as_posix()

    def _annotate_page(
        self,
        page: Page,
    ):
        if page.rotation != 0:
            page.set_rotation(0)

        rect = page.rect
        cx, cy = self._get_annotation_coords(
            (rect.width, rect.height),
            self.margin_frac,
            self.offset,
            self.anchor,
        )

        radius = rect.width * self.margin_frac

        # draw circle
        page.draw_circle(
            center=(cx, cy),
            radius=radius,
        )

        # draw centered number
        box_size = radius
        label_rect = pymupdf.Rect(
            cx - box_size,
            cy - box_size,
            cx + box_size,
            cy + box_size,
        )

        page.insert_textbox(
            label_rect,
            str(page.number),
            fontsize=radius,
            align=pymupdf.TEXT_ALIGN_CENTER,
        )

    def _get_annotation_coords(
        self,
        size: tuple[int, int],
        margin_frac: float = 1 / 10,
        offset: tuple[int, int] = (10, 10),
        anchor: Anchor = Anchor.BOTTOM_LEFT,
    ) -> Tuple[float, float]:
        width, height = size
        x_off, y_off = offset

        match anchor.value:
            case "top-left":
                cx = width * margin_frac + x_off
                cy = height * margin_frac + y_off
            case "top-right":
                cx = width - (width * margin_frac) - x_off
                cy = height * margin_frac + y_off
            case "bottom-left":
                cx = width * margin_frac + x_off
                cy = height - (height * margin_frac) - y_off
            case "bottom-right":
                cx = width - (width * margin_frac) - x_off
                cy = height - (height * margin_frac) - y_off
            case _:
                raise ValueError(f"Invalid anchor: {anchor}")
        return cx, cy

    def get_output_path(
        self,
        path: Optional[str | Path] = None,
        method: Literal["image", "pdf"] = "image",
    ) -> Path:
        if path:
            return Path(path).resolve()
        if method == "pdf":
            output_path = self.pdf.with_name(f"{self.pdf.stem}_annotated.pdf")
        elif method == "image":
            output_path = self.pdf.with_name(f"{self.pdf.stem}_annotated_pages")
            output_path.mkdir(parents=True, exist_ok=True)

        return output_path

    def _validate(self):
        if not self.pdf.exists():
            raise FileNotFoundError(f"PDF Path {self.pdf} does not exist")


if __name__ == "__main__":
    path = "data/Lecture_02_03.pdf"
    output = Path(r"src\data\images").resolve()
    PDFAnnotator(path, anchor="bottom-left", margin_frac=1 / 20)._annotate_and_save(
        method="image"
    )
