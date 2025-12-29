import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import agent


def test_runs_first_prompt_and_generates_json(tmp_path: Path) -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is required for this integration test.")

    evals_path = Path(__file__).resolve().parents[1] / "test" / "evals.json"
    prompts = agent.load_prompts(evals_path)
    first_prompt = prompts[0][1]

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        import asyncio

        asyncio.run(agent.run_prompts(prompts=[("test1", first_prompt)]))
    finally:
        os.chdir(original_cwd)

    output_path = tmp_path / "prompt_1.json"
    assert output_path.exists(), "Expected prompt_1.json to be created."


def _run_agent_demo() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is required to run the agent demo.")

    evals_path = Path(__file__).resolve().parents[1] / "test" / "evals.json"
    prompts = agent.load_prompts(evals_path)
    first_prompt = prompts[0][1]

    original_cwd = Path.cwd()
    try:
        os.chdir(Path.cwd())
        import asyncio

        asyncio.run(agent.run_prompts(prompts=[("test1", first_prompt)]))
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    _run_agent_demo()
