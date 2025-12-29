from typing import Any
import json
from pathlib import Path

from agents import FunctionTool, RunContextWrapper
from pydantic import BaseModel, Field

class CodeJsonTool(BaseModel):
    prompt_number: int = Field(..., description="Prompt number from the context")
    prompt: str = Field(..., description="IFC/BIM query prompt extracted from the context")
    code: str = Field(
        ..., description="markdown python blocks -> ```python ... ``` with the viktor application"
    )

async def create_json_func(ctx: RunContextWrapper[Any], args: str) -> str:
    payload = CodeJsonTool.model_validate_json(args)

    output_dir = Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"prompt_{payload.prompt_number}.json"
    output_path.write_text(json.dumps(payload.model_dump(), indent=2), encoding="utf-8")
    return str(output_path)

create_json = FunctionTool(
    name="create_json",
    description="Generate a json based on the resulting generated code",
    params_json_schema=CodeJsonTool.model_json_schema(),
    on_invoke_tool=create_json_func,
)
