import logging
from typing import Dict, Any

import httpx

logger = logging.getLogger(__name__)

class ToolError(Exception):
    pass

async def _get_json(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
    try:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise ToolError(f"HTTP {e.response.status_code} from {url}") from e
    except httpx.HTTPError as e:
        raise ToolError(f"Network error calling {url}") from e
    except ValueError as e:
        raise ToolError(f"Invalid JSON from {url}") from e

async def get_people_tool(args: Dict[str, Any], *, base_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    q = (args.get("people") or "").strip()
    if not q:
        return {"error": "Missing required input: 'people'"}
    # Ensure single slash and proper query
    url = f"{base_url.rstrip('/')}/people/?search={q}"
    data = await _get_json(client, url)
    return {
        "count": data.get("count", 0),
        "results": data.get("results", []),
        "next": data.get("next"),
        "previous": data.get("previous"),
        "query": q,
        "resource": "people",
    }

async def get_starships_tool(args: Dict[str, Any], *, base_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    q = (args.get("starships") or "").strip()
    if not q:
        return {"error": "Missing required input: 'starships'"}
    url = f"{base_url.rstrip('/')}/starships/?search={q}"
    data = await _get_json(client, url)
    return {
        "count": data.get("count", 0),
        "results": data.get("results", []),
        "next": data.get("next"),
        "previous": data.get("previous"),
        "query": q,
        "resource": "starships",
    }

async def run_tool(name: str, args: Dict[str, Any], *, base_url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        if name == "getPeople":
            return await get_people_tool(args, base_url=base_url, client=client)
        if name == "getStarships":
            return await get_starships_tool(args, base_url=base_url, client=client)
        return {"error": f"Unsupported tool: {name}"}
    except ToolError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception("Tool failed")
        return {"error": f"Tool '{name}' failed: {e}"}