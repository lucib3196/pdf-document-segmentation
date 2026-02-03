from pathlib import Path

from typing import List, Tuple
import pymupdf
from pymupdf import Page
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

    def annotate_and_render_pages(self) -> List[bytes]:
        doc = pymupdf.open(self.pdf)
        image_bytes: List[bytes] = []
        for page_num in range(len(doc)):
            page: Page = doc.load_page(page_num)
            self._annotate_page(page)
            matrix = pymupdf.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=matrix)
            image_bytes.append(pix.tobytes("png"))
        doc.close()
        return image_bytes

    def _annotate_and_save(self) -> str:
        output_path = self.pdf.with_name(f"{self.pdf.stem}_annotated.pdf")
        for b in self.annotate_and_render_pages():
            output_path.write_bytes(b)
        return output_path.as_posix()

    def save_annotated_pages_as_images(self, output_path: Path | str) -> None:
        output_path = Path(output_path).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        for i, img_bytes in enumerate(self.annotate_and_render_pages()):
            out_file = output_path / f"{self.pdf.stem}_page_{i + 1}.png"
            out_file.write_bytes(img_bytes)

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

    def _validate(self):
        if not self.pdf.exists():
            raise FileNotFoundError(f"PDF Path {self.pdf} does not exist")


if __name__ == "__main__":
    path = "data/Lecture_02_03.pdf"
    output = Path(r"src\data\images").resolve()
    PDFAnnotator(
        path, anchor="bottom-left", margin_frac=1 / 20
    ).save_annotated_pages_as_images(output)
