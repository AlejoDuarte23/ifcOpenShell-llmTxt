# factory/agent.py
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from agents import Agent, Runner, ItemHelpers, WebSearchTool, ModelSettings
from agents.mcp import MCPServerSse
from openai.types import Reasoning
from openai.types.responses import ResponseTextDeltaEvent

from .tools import create_json

load_dotenv()

INSTRUCTIONS = (
    "You are a coding assistant for the VIKTOR SDK. "
    "ALWAYS use the MCP tools to learn the VIKTOR SDK syntax when needed. "
    "Before creating the code, use MCP tools so you understand the available VIKTOR components. "
    "When asked to produce a VIKTOR app, call create_json. "
    "The user input includes PROMPT_NUMBER. When calling create_json, set prompt_number to PROMPT_NUMBER. "
    "Do not include placeholders. Provide fully runnable code."
)

def load_prompts(evals_path: Path = Path("test/evals.json")) -> list[tuple[str, str]]:
    with open(evals_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        (name, entry["prompt"])
        for name, entry in data.items()
        if isinstance(entry, dict) and entry.get("prompt")
    ]

def format_input(prompt_number: int, name: str, prompt: str) -> str:
    return f"PROMPT_NUMBER: {prompt_number}\nPROMPT_NAME: {name}\n\n{prompt}\n"

async def run_prompts_concurrent(
    prompts: list[tuple[str, str]],
    max_concurrency: int = 5,
) -> None:
    if "OPENAI_API_KEY" not in os.environ:
        raise EnvironmentError("Set OPENAI_API_KEY first.")

    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    sse_url = f"http://{host}:{port}/sse"

    semaphore = asyncio.Semaphore(max_concurrency)
    print_lock = asyncio.Lock()

    async with MCPServerSse(
        name="DataServer",
        params={"url": sse_url, "timeout": 30},
        cache_tools_list=True,
    ) as server:
        agent = Agent(
            name="VIKTOR-Helper",
            instructions=INSTRUCTIONS,
            model="gpt-5.2",
            mcp_servers=[server],
            tools=[WebSearchTool(), create_json],
            model_settings=ModelSettings(reasoning=Reasoning(effort="high")),
        )

        async def run_one(i: int, name: str, prompt: str) -> None:
            async with semaphore:
                token_buffer: list[str] = []
                final_buffer: list[str] = []

                result = Runner.run_streamed(agent, input=format_input(i, name, prompt))
                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        token_buffer.append(event.data.delta or "")
                        continue

                    if event.type == "run_item_stream_event":
                        it = event.item
                        if it.type == "message_output_item":
                            final_buffer.append(ItemHelpers.text_message_output(it))

                async with print_lock:
                    print(f"\n=== Final Answer ({name}) ===")
                    print(("".join(final_buffer).strip()) if final_buffer else ("".join(token_buffer).strip()))

        await asyncio.gather(*(run_one(i, n, p) for i, (n, p) in enumerate(prompts, start=1)))
