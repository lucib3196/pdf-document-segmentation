from pathlib import Path
from typing import List, Type
from typing import Generic, TypeVar, List
import base64

from pydantic import BaseModel, field_serializer, Field
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from type import PDFInput, PageRange
from pdf_annotator import PDFAnnotator
from pdf_llm import PDFMultiModalLLM
from pdf_seperator import PDFSeperator


load_dotenv()


class Section(BaseModel):
    """
    Base class for any structured unit extracted from a document.
    This should contain ONLY semantic fields produced by the LLM.
    """

    page_range: PageRange


T = TypeVar("T", bound=Section)


class ListOutput(BaseModel, Generic[T]):
    items: List[T]


class ParsedUnit(
    BaseModel,
    Generic[T],
):
    """
    A semantic unit enriched with pipeline-generated artifacts.
    """

    data: T
    pdf_bytes: bytes | None = None

    @field_serializer("pdf_bytes")
    def serialize_pdf_bytes(self, value: bytes):
        return base64.b64encode(value).decode("ascii")


model = init_chat_model(model="gpt-4o", model_provider="openai")


class State(BaseModel, Generic[T]):
    # --- Inputs ---
    pdf: PDFInput
    prompt: str
    pdf_images: list[bytes] = []

    # --- Schema configuration ---
    output_schema: Type[ListOutput[T]] = Field(exclude=True)
    raw_output: List[T] = []

    parsed: list[ParsedUnit[T]] = Field(default_factory=list, exclude=False)

    @field_serializer("pdf_images")
    def serialize_pdf_bytes(self, value: list[bytes]):

        return [base64.b64encode(b).decode("ascii") for b in value]


def prepare_pdf(state: State):
    state.pdf = Path(state.pdf)
    if not state.pdf.exists():
        raise ValueError("PDF path cannot be resolved")
    pdf_images = PDFAnnotator(state.pdf).annotate_and_render_pages()
    return {"pdf_images": pdf_images}


def get_sections(state: State):
    llm = PDFMultiModalLLM(
        prompt=state.prompt,
        image_bytes=state.pdf_images,
        model=model,
    )
    result = llm.invoke(state.output_schema)
    result = state.output_schema.model_validate(result)
    return {"raw_output": result.items}


def seperate_pages(state: State[T]):
    parsed = []
    separator = PDFSeperator(image_bytes=state.pdf_images)
    for unit in state.raw_output:
        page_range = getattr(unit, "page_range", None)
        if page_range is None:
            raise ValueError("Unit does not define a page_range")
        cleaned = ParsedUnit[T](
            data=unit,
            pdf_bytes=separator.extract_page_range(
                start=page_range.start_page - 1,
                end=page_range.end_page - 1,
            ),
        )
        parsed.append(cleaned)
    return {"parsed": parsed}


graph = StateGraph(State)
graph.add_node(prepare_pdf)
graph.add_node(get_sections)
graph.add_node(seperate_pages)

graph.add_edge(START, "prepare_pdf")
graph.add_edge("prepare_pdf", "get_sections")
graph.add_edge("get_sections", "seperate_pages")
graph.add_edge("seperate_pages", END)
graph = graph.compile()


if __name__ == "__main__":
    path = "data/Lecture_02_03.pdf"

    class MySection(Section, BaseModel):
        title: str
        description: str

    class MySections(ListOutput[MySection]):
        items: List[MySection]

    result = graph.invoke(
        State(
            output_schema=MySections,
            pdf=path,
            prompt="""You are tasked with analyzing the provided lecture material.
Identify and extract all sections that contain mathematical derivations.
Each derivation must be clearly separated into its own section and include the start and end page (or location) where the derivation appears.
Only include content that is part of a derivation; do not summarize or explain beyond what is explicitly shown. For the page range, the lecture is annotated with a page number circled on the bottom left corner use this as the primary indexing of the pages""",
        )
    )
    result = State.model_validate(result)
    from utils import to_serializable
    import json

    output = Path("output.json").resolve()
    output.write_text(json.dumps(to_serializable(result)))
