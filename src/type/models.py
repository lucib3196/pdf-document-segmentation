from pydantic import BaseModel


class BaseOutput(BaseModel):
    data: str


class PageRange(BaseModel):
    start_page: int
    end_page: int


