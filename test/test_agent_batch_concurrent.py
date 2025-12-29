import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from factory import agent


def _get_free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def _server_health_ok(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/health", timeout=1) as resp:
            return resp.read().decode("utf-8").strip() == "OK"
    except Exception:
        return False


def _wait_for_server(host: str, port: int, timeout_s: float = 10.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _server_health_ok(host, port):
            return
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for MCP server at {host}:{port}.")


def test_run_prompts_concurrent_batches(tmp_path: Path) -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is required for this integration test.")

    evals_path = Path(__file__).resolve().parents[1] / "test" / "evals.json"
    prompts = agent.load_prompts(evals_path)[:4]

    host = os.getenv("MCP_HOST", "127.0.0.1")
    port_env = os.getenv("MCP_PORT")
    port = int(port_env) if port_env else _get_free_port(host)
    os.environ["MCP_HOST"] = host
    os.environ["MCP_PORT"] = str(port)

    server_proc = None
    if not _server_health_ok(host, port):
        server_path = Path(__file__).resolve().parents[1] / "factory" / "viktor-mcp" / "server.py"
        server_env = os.environ.copy()
        server_proc = subprocess.Popen(
            [sys.executable, str(server_path)],
            env=server_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            _wait_for_server(host, port)
        except Exception:
            server_proc.terminate()
            try:
                stdout, stderr = server_proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                stdout, stderr = server_proc.communicate(timeout=2)
            raise RuntimeError(
                "Failed to start MCP server.\n"
                f"stdout: {stdout}\n"
                f"stderr: {stderr}"
            )

    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    original_cwd = Path.cwd()
    try:
        os.chdir(output_dir)
        asyncio.run(agent.run_prompts_concurrent(prompts=prompts, max_concurrency=2))
    finally:
        os.chdir(original_cwd)
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait(timeout=5)

    generated = list(output_dir.glob("prompt_*.json"))
    assert generated, "Expected at least one prompt_*.json to be created."
    for output_path in generated:
        payload = output_path.read_text(encoding="utf-8").strip()
        assert payload, f"{output_path} was empty."
        data = json.loads(payload)
        assert data.get("prompt_number"), f"{output_path} missing prompt_number."
        assert data.get("prompt"), f"{output_path} missing prompt."
        assert data.get("code"), f"{output_path} missing code."


if __name__ == "__main__":
    test_run_prompts_concurrent_batches(Path.cwd())
