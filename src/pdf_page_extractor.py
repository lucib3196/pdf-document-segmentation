from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from type import PDFInput, PageRange
from typing import List
from pdf_annotator import PDFAnnotator
from pathlib import Path
from pdf_llm import PDFMultiModalLLM
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from pdf_seperator import PDFSeperator
from pydantic import field_serializer
import base64

load_dotenv()


class SectionBreakDown(BaseModel):
    title: str = Field(
        description="Short, descriptive title identifying the derivation or section."
    )
    description: str = Field(
        description="Brief summary of the derivation, stating what is being derived and its purpose, without adding interpretation beyond the source material."
    )
    page_range: PageRange = Field(
        description="Inclusive start and end pages where the derivation appears in the lecture material."
    )


class CleanedSection(SectionBreakDown):
    pdf_bytes: bytes | None = None

    @field_serializer("pdf_bytes")
    def serialize_pdf_bytes(self, value: bytes):

        return base64.b64encode(value).decode("ascii")


class Sections(BaseModel):
    sections: List[SectionBreakDown]


model = init_chat_model(model="gpt-4o", model_provider="openai")


class State(BaseModel):
    pdf: PDFInput
    prompt: str
    pdf_bytes: List[bytes] = []
    raw_output: List[SectionBreakDown] = []
    parsed: List[CleanedSection] = []

    @field_serializer("pdf_bytes")
    def serialize_pdf_bytes(self, value: list[bytes]):

        return [base64.b64encode(b).decode("ascii") for b in value]


def prepare_pdf(state: State):
    state.pdf = Path(state.pdf)
    if not state.pdf.exists():
        raise ValueError("PDF path cannot be resolved")
    pdf_bytes = PDFAnnotator(state.pdf).annotate_and_render_pages()
    return {"pdf_bytes": pdf_bytes}


def get_sections(state: State):
    llm = PDFMultiModalLLM(
        prompt=state.prompt,
        image_bytes=state.pdf_bytes,
        model=model,
    )
    result = llm.invoke(Sections)
    parsed = Sections.model_validate(result)
    return {"raw_output": parsed.sections}


def seperate_pages(state: State):
    parsed: list[CleanedSection] = []

    separator = PDFSeperator(pdf_path=state.pdf)

    for section in state.raw_output:
        cleaned = CleanedSection(**section.model_dump())

        page_range = section.page_range
        cleaned.pdf_bytes = separator.extract_page_range(
            start=page_range.start_page,
            end=page_range.end_page,
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
    result = graph.invoke(
        State(
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
