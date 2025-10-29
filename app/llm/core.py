from __future__ import annotations
import json
import asyncio
from typing import Dict, Any, List, Tuple

import httpx

from app.clients.bedrock import get_bedrock_client
from app.config import settings
from app.llm.chat import SYSTEM_PROMPT, TOOLS
from app.tools import swapi

bedrock = get_bedrock_client()
MODEL_ID = settings.bedrock_model_id

# ---------- Message helpers (content blocks) ----------
def user_text(text: str) -> Dict[str, Any]:
    return {"role": "user", "content": [{"type": "text", "text": text}]}

def assistant_blocks(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"role": "assistant", "content": blocks}

def user_tool_results(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"role": "user", "content": blocks}

def find_tool_uses(resp_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [b for b in resp_json.get("content", []) if b.get("type") == "tool_use"]

# ---------- Bedrock wrappers ----------
def bedrock_invoke(payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(payload),
        accept="application/json",
        contentType="application/json",
    )
    return json.loads(resp["body"].read().decode("utf-8"))

def build_messages_from_user(user_input: str) -> List[Dict[str, Any]]:
    return [user_text(user_input)]

def build_payload(messages: List[Dict[str, Any]], *, max_tokens: int | None = None) -> Dict[str, Any]:
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "system": SYSTEM_PROMPT,
        "tools": TOOLS,
        "messages": messages,
        "max_tokens": max_tokens or settings.max_tokens,
        "temperature": 0.2,
    }

# ---------- Tool resolution (async) ----------
async def _run_tools_once(tool_uses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run one batch of tool_uses concurrently and return tool_result blocks."""
    if not tool_uses:
        return []
    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        async def one(tu: Dict[str, Any]) -> Dict[str, Any]:
            name = tu.get("name")
            args = tu.get("input", {})
            res_obj = await swapi.run_tool(name, args, base_url=settings.sw_api_base, client=client)
            return {
                "type": "tool_result",
                "tool_use_id": tu["id"],
                "content": json.dumps(res_obj) if not isinstance(res_obj, str) else res_obj,
            }
        results = await asyncio.gather(*(one(tu) for tu in tool_uses))
    return results

def resolve_tools_sync(messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, Any]]:
    """
    Resolve all tool calls (possibly multiple rounds) synchronously (for /chat or before streaming).
    Returns: (updated_messages, tools_used, last_nonstream_result)
    """
    tools_used: List[str] = []
    # initial non-stream request
    payload = build_payload(messages)
    result = bedrock_invoke(payload)

    while True:
        tool_uses = find_tool_uses(result)
        if not tool_uses:
            # no more tools; return
            return messages, tools_used, result

        # record names for telemetry/UX
        tools_used.extend([tu.get("name") for tu in tool_uses if tu.get("name")])

        # run tools (async) inside sync flow
        tool_result_blocks = asyncio.run(_run_tools_once(tool_uses))

        # extend transcript: assistant (with tool_use blocks) + user (tool_result blocks)
        messages.extend([
            assistant_blocks(result.get("content", [])),
            user_tool_results(tool_result_blocks),
        ])

        # ask again
        payload = build_payload(messages)
        result = bedrock_invoke(payload)