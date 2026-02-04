from pathlib import Path
from pdf_page_extractor import State
import json
from utils import save_base64_image
path = Path("output.json").resolve()
data = State.model_validate(json.loads(path.read_text()))
save_base64_image(data.parsed[-1].pdf_bytes, "data_output.pdf")