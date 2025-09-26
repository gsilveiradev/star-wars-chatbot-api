import json, httpx, logging
from fastapi import APIRouter

from app.clients.bedrock import get_bedrock_client
from app.models import UserQuery
from app.utils import truncate_json, get_bedrock_usage
from app.config import settings
from app.llm.chat import SYSTEM_PROMPT, TOOLS

logger = logging.getLogger(__name__)
router = APIRouter()
bedrock = get_bedrock_client()

@router.post("/chat")
async def chat_with_ai(user_query: UserQuery):
    initial_payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"The user asked: {user_query.user_input}"
                        )
                    }
                ]
            }
        ],
        "tools": TOOLS,
        "max_tokens": settings.max_tokens
    }

    response = bedrock.invoke_model(
        modelId=settings.bedrock_model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(initial_payload)
    )

    raw_body = response["body"].read()
    result = json.loads(raw_body)

    bedrock_usage = get_bedrock_usage(
        model_id=settings.bedrock_model_id,
        input_text=json.dumps(initial_payload["messages"]),
        output_text=json.dumps(result),
        call_type="initial"
    )
    logger.info("Bedrock usage", extra=bedrock_usage)


    tool_use = next((c for c in result.get("content", []) if c.get("type") == "tool_use"), None)

    if not tool_use:
        text_response = next(
            (c["text"] for c in result.get("content", []) if c.get("type") == "text"),
            "Unable to give an answer"
        )

        return {
            "response": text_response,
            "tool": {
                "used_tool": 0
            }
        }

    if tool_use["name"] == "getPeople":
        async with httpx.AsyncClient() as client:
            match_resp = await client.get(
                f"{settings.sw_api_base}/people?search={tool_use['input']['people']}"
            )
        tool_output = match_resp.json()
    elif tool_use["name"] == "getStarships":
        async with httpx.AsyncClient() as client:
            match_resp = await client.get(
                f"{settings.sw_api_base}/starships?search={tool_use['input']['starships']}"
            )
        tool_output = match_resp.json()
    else:
        return {"error": f"Unsupported tool: {tool_use['name']}"}

    tool_result_msg = {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use["id"],
                "content": truncate_json(tool_output, limit=10000)
            }
        ]
    }

    tool_use_msg = {
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": tool_use["id"],
                "name": tool_use["name"],
                "input": tool_use["input"]
            }
        ]
    }

    followup_payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": SYSTEM_PROMPT,
        "messages": [
            initial_payload["messages"][0],
            tool_use_msg,
            tool_result_msg
        ],
        "tools": TOOLS,
        "max_tokens": settings.max_tokens
    }

    final_response = bedrock.invoke_model(
        modelId=settings.bedrock_model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(followup_payload)
    )

    raw_final_body = final_response["body"].read()
    final_result = json.loads(raw_final_body)

    bedrock_usage = get_bedrock_usage(
        model_id=settings.bedrock_model_id,
        input_text=json.dumps(followup_payload["messages"]),
        output_text=json.dumps(final_result),
        call_type="followup"
    )
    logger.info("Bedrock usage", extra=bedrock_usage)

    text_response = next(
        (c["text"] for c in final_result.get("content", []) if c.get("type") == "text"),
        "Claude did not return a response."
    )

    return {
        "response": text_response,
        "tool": {
            "used_tool": 1,
            "name": tool_use["name"]
        }
    }
