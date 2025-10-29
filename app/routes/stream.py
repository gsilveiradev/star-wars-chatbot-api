import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

from app.clients.bedrock import get_bedrock_client
from app.config import settings
from app.llm.core import (
    build_messages_from_user,
    build_payload,
    bedrock_invoke,
    resolve_tools_sync,
)
from app.models import UserQuery

logger = logging.getLogger(__name__)
router = APIRouter()
bedrock = get_bedrock_client()
MODEL_ID = settings.bedrock_model_id

def bedrock_stream(payload: Dict[str, Any]):
    resp = bedrock.invoke_model_with_response_stream(
        modelId=MODEL_ID,
        body=json.dumps(payload),
        accept="application/json",
        contentType="application/json",
    )
    stream = resp.get("body")
    for event in stream:
        if "chunk" not in event:
            continue
        data = json.loads(event["chunk"]["bytes"].decode("utf-8"))
        if data.get("type") == "content_block_delta":
            delta = data.get("delta", {})
            if delta.get("type") == "text_delta":
                yield delta.get("text", "")
        elif data.get("type") == "message_stop":
            break

@router.post("/stream")
async def stream_with_claude(user_query: UserQuery):
    def sse_gen():
        try:
            messages = build_messages_from_user(user_query.user_input)

            # FIRST non-stream call to get quick text
            first_result = bedrock_invoke(build_payload(messages))

            # quick text BEFORE any tool_use
            first_content = first_result.get("content", [])
            for block in first_content:
                if block.get("type") == "text":
                    yield f"data: {json.dumps({'delta': block.get('text', '')})}\n\n"
                else:
                    break  # stop when first non-text (tool_use) appears

            # resolve tools synchronously (shared helper)
            messages, tools_used, last_result = resolve_tools_sync(messages)

            # tell client about tools
            if tools_used:
                yield f"data: {json.dumps({'tool_event': {'used': True, 'names': tools_used}})}\n\n"
            else:
                yield f"data: {json.dumps({'tool_event': {'used': False}})}\n\n"

            # FINAL streaming call (no "stream": true in body)
            stream_payload = build_payload(messages)
            for token in bedrock_stream(stream_payload):
                yield f"data: {json.dumps({'delta': token})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.exception("SSE stream failed")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        sse_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )