from pathlib import Path
from typing import Optional, Sequence, Type

import pymupdf
from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.chat_models import init_chat_model
from type import PDFInput, BaseOutput
from image_payload_builder import ImagePayloadBuilder


class PDFMultiModalLLM:
    def __init__(
        self,
        *,
        prompt: str,
        model: BaseChatModel,
        pdf_path: PDFInput | None = None,
        image_bytes: Sequence[bytes] | None = None,
    ):
        if pdf_path is None and image_bytes is None:
            raise ValueError("Either pdf_path or image_bytes must be provided")
        if pdf_path is not None and image_bytes is not None:
            raise ValueError("Provide only one of pdf_path or image_bytes")

        self.prompt = prompt
        self.builder = ImagePayloadBuilder()
        self.llm = model

        if pdf_path is not None:
            self.pdf_bytes = self._load_pdf_as_images(pdf_path)
        elif image_bytes:
            self.pdf_bytes = list(image_bytes)
        else:
            raise ValueError("Unexpected Error Occured")

    def _load_pdf_as_images(self, pdf_path: PDFInput) -> list[bytes]:
        """
        Convert PDF pages to image bytes.
        """
        doc = pymupdf.open(pdf_path)
        images: list[bytes] = []

        for page in doc:
            pix = page.get_pixmap(dpi=150)
            images.append(pix.tobytes("png"))
        doc.close()
        return images

    def prepare_payload(
        self,
    ):
        image_payload = self.builder.prepare_llm_payload(self.pdf_bytes)
        message = {
            "role": "user",
            "content": [{"type": "text", "text": self.prompt}, *image_payload],
        }
        return message

    def invoke(
        self,
        output_model: Optional[Type[BaseModel]] = BaseOutput,
    ):
        message = self.prepare_payload()
        if output_model:
            chain = self.llm.with_structured_output(schema=output_model)
            return chain.invoke([message])
        else:
            return self.llm.invoke([message])

    async def ainvoke(
        self,
        output_model: Optional[Type[BaseModel]] = BaseOutput,
    ):
        message = self.prepare_payload()
        if output_model:
            chain = self.llm.with_structured_output(
                schema=output_model,
            )
            return chain.ainvoke([message])
        else:
            return self.llm.ainvoke([message])


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    path = "data/Lecture_02_03.pdf"
    output = Path(r"src\data\images").resolve()
    model = init_chat_model(model="gpt-4o", model_provider="openai")
    data = PDFMultiModalLLM(
        prompt="What is in the image", pdf_path=path, model=model
    ).invoke()
    print(data)
