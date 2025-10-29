from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from app.llm.core import (
    build_messages_from_user,
    build_payload,
    bedrock_invoke,
    resolve_tools_sync,
)
from app.models import UserQuery

router = APIRouter()

@router.post("/chat")
def chat_with_ai(user_query: UserQuery) -> Dict[str, Any]:
    try:
        # 1) start transcript
        messages = build_messages_from_user(user_query.user_input)

        # 2) resolve tools (sync loop that internally uses asyncio for HTTP tools)
        messages, tools_used, last_result = resolve_tools_sync(messages)

        # 3) final non-stream answer
        #    You might already have assistant text in last_result if stop_reason != "tool_use".
        #    To be explicit, do one more non-stream call with the full transcript (optional).
        final_payload = build_payload(messages)
        final_result = bedrock_invoke(final_payload)

        text = next(
            (c.get("text") for c in final_result.get("content", []) if c.get("type") == "text"),
            "Unable to give an answer"
        )

        return {
            "response": text,
            "tool": {
                "used_tool": int(bool(tools_used)),
                "names": tools_used,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))