from pathlib import Path
from typing import List, Literal, Tuple
import pymupdf
from pymupdf import Document, Page, Rect, Point
from enum import Enum

AnchorPos = Literal["top-left", "top-right", "bottom-right", "bottom-left"]


class Anchor(str, Enum):
    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"


class PDFAnnotator:
    def __init__(
        self,
        pdf_path: str | Path,
        anchor: Anchor | AnchorPos = Anchor.BOTTOM_LEFT,
        margin_frac: float = 1 / 10,
        offset: Tuple[int, int] = (10, 10),
    ):
        self.pdf = Path(pdf_path).resolve()
        self.anchor = Anchor(anchor)
        self.margin_frac = margin_frac
        self.offset = offset

    def _to_image_bytes(self, zoom: float = 2.0):
        doc = pymupdf.open(self.pdf)
        image_bytes: List[bytes] = []
        for page_num in range(len(doc)):
            page: Page = doc.load_page(page_num)
            matrix = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix)
            image_bytes.append(pix.tobytes("png"))
        doc.close()
        return image_bytes

    def _annotate_pages(self):
        doc = pymupdf.open(self.pdf)
        for page_num in range(len(doc)):
            page: Page = doc.load_page(page_num)
            self._get_draw(page)
            pix = page.get_pixmap(dpi=150)

            pix.save("debug_page.png")

    def _get_draw(
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

    def _validate(self):
        if not self.pdf.exists():
            raise FileNotFoundError(f"PDF Path {self.pdf} does not exist")


if __name__ == "__main__":
    path = "src/data/Lecture_02_03.pdf"
    PDFAnnotator(path, anchor="bottom-left", margin_frac=1 / 20)._annotate_pages()
