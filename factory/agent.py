import asyncio
import json
import os

from pathlib import Path

from dotenv import load_dotenv

from agents import Agent, Runner, ItemHelpers, WebSearchTool, ModelSettings
from agents.mcp import MCPServerStdio
from openai.types import Reasoning

from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel
from .tools import create_json 

load_dotenv()

DATA_SERVER_DIR = (Path(__file__).parent / "viktor-mcp").resolve()


tool = create_json


data_server = MCPServerStdio(
    name="DataServer",
    cache_tools_list=True,
    params={"command": "uv", "args": ["run", "server.py"], "cwd": str(DATA_SERVER_DIR)},
)


assistant = Agent(
    name="VIKTOR-Helper",
    instructions=(
        "You are a coding assistant for the VIKTOR SDK. "
        "ALWAYS use the MCP tools to learn the VIKTOR SDK syntax when needed. "
        "Before creating the code try to use more tools so you have a complete undersating of the Viktor Components"
        "When asked to produce a VIKTOR app, call the 'create_json'. "
        "Do not include placeholders. Provide fully runnable code."
        "you have also websearch capabilties if the IFCopenShell context is not enought you can search for the documentation"
        "No need to print the code to the user use the tool at then to generate file notify the user the steps your are taking at at then let the user know  end you have generate the results"
    ),
    model="gpt-5.2",
    mcp_servers=[data_server],
    tools=[WebSearchTool() ,tool],
    model_settings=ModelSettings(reasoning=Reasoning(effort="low"))
)

def load_prompts(evals_path: Path = Path("test/evals.json")) -> list[tuple[str, str]]:
    with open(evals_path, "r", encoding="utf-8") as evals_file:
        evals_data = json.load(evals_file)

    return [
        (name, entry["prompt"])
        for name, entry in evals_data.items()
        if isinstance(entry, dict) and entry.get("prompt")
    ]


async def run_prompts(
    prompts: list[tuple[str, str]],
    runner: type[Runner] = Runner,
    assistant_instance: Agent = assistant,
    server: MCPServerStdio = data_server,
) -> None:
    async with server:
        for name, prompt in prompts:
            print(f"\n=== Running {name} ===\n", flush=True)
            token_buffer: list[str] = []
            final_buffer: list[str] = []

            result = runner.run_streamed(assistant_instance, input=prompt)

            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    chunk = event.data.delta or ""
                    token_buffer.append(chunk)
                    print(chunk, end="", flush=True)
                    continue

                if event.type == "run_item_stream_event":
                    it = event.item
                    if it.type == "message_output_item":
                        msg_text = ItemHelpers.text_message_output(it)
                        final_buffer.append(msg_text)
                    elif it.type == "tool_call_item":
                        try:
                            args_str = getattr(it.raw_item, "arguments", "") or ""
                            args_len = len(args_str) if isinstance(args_str, str) else -1
                            print(f"\n[tool called] {it.raw_item.name} args_len={args_len}\n", flush=True)  # type: ignore
                        except Exception:
                            print(f"\n[tool called] {getattr(it.raw_item, 'name', '<unknown>')}\n", flush=True)  # type: ignore

            print(f"\n\n=== Final Answer ({name}) ===")
            if final_buffer:
                print("".join(final_buffer).strip())
            else:
                print("".join(token_buffer).strip())


async def main() -> None:
    if "OPENAI_API_KEY" not in os.environ:
        raise EnvironmentError("Set OPENAI_API_KEY first.")

    prompts = load_prompts()
    await run_prompts(prompts)


if __name__ == "__main__":
    asyncio.run(main())
