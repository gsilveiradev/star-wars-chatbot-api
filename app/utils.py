import orjson
from app.config import settings

UNWANTED_KEYS = {"created", "edited", "url"}

def truncate_json(obj, limit=3000):
    cleaned = remove_keys_recursively(obj, UNWANTED_KEYS)
    raw = orjson.dumps(cleaned)
    if len(raw) <= limit:
        return raw.decode()
    return raw[:limit].decode("utf-8", errors="ignore")

def remove_keys_recursively(obj, keys_to_remove):
    """
    Recursively remove keys from dictionaries and lists.
    """
    if isinstance(obj, dict):
        return {
            k: remove_keys_recursively(v, keys_to_remove)
            for k, v in obj.items()
            if k not in keys_to_remove
        }
    elif isinstance(obj, list):
        return [remove_keys_recursively(item, keys_to_remove) for item in obj]
    else:
        return obj



def estimate_tokens(text: str) -> int:
    """rough token estimation (1 token ≈ 4 characters)."""
    return int(len(text) / 4)


def get_bedrock_usage(model_id, input_text, output_text, call_type):
    tokens_input = estimate_tokens(input_text)
    tokens_output = estimate_tokens(output_text)
    total_tokens = tokens_input + tokens_output

    # Claude Sonnet 3.5 pricing
    cost_input = (tokens_input / 1000) * 0.003
    cost_output = (tokens_output / 1000) * 0.015
    total_cost = cost_input + cost_output

    return {
        "bedrock.model_id": model_id,
        "bedrock.call_type": call_type,
        "bedrock.tokens_input": tokens_input,
        "bedrock.tokens_output": tokens_output,
        "bedrock.total_tokens": total_tokens,
        "bedrock.estimated_cost": round(total_cost, 6),
        "bedrock.estimated_input_cost": round(cost_input, 6),
        "bedrock.estimated_output_cost": round(cost_output, 6),
        "bedrock.input_text": input_text,
        "bedrock.output_text": output_text,
    }