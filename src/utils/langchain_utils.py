from pathlib import Path
from typing import Any
from langgraph.graph.state import CompiledStateGraph
from .image_utils import write_image_data


def save_graph_visualization(
    graph: CompiledStateGraph | Any,
    folder_path: str | Path,
    filename: str,
):
    try:
        image_bytes = graph.get_graph().draw_mermaid_png()
        save_path = write_image_data(image_bytes, folder_path, filename)
        print(f"✅ Saved graph visualization at: {save_path}")
    except ValueError:
        raise
    except Exception as error:
        print(f"❌ Graph visualization failed: {error}")
