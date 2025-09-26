TOOLS = [
    {
        "name": "getPeople",
        "description": "Gets information about People in the Star Wars world",
        "input_schema": {
            "type": "object",
            "properties": {
                "people": {
                    "type": "string",
                    "description": "The people name"
                }
            },
            "required": ["people"]
        }
    },
    {
        "name": "getStarships",
        "description": "Gets information about Starships in the Star Wars world",
        "input_schema": {
            "type": "object",
            "properties": {
                "starships": {
                    "type": "string",
                    "description": "The starship name"
                }
            },
            "required": ["starships"]
        }
    }
]

SYSTEM_PROMPT = (
    "You're a passionate Star Wars fan with a background in movies journalism, chatting in the Star Wars app. "
    "You're talking directly to another fan who is asking about a Star Wars. Keep it friendly, clear, and engaging — like you're chatting with a friend. "
    "You're able to talk about these categories: people, planets, films, species, vehicles, and startships. "
    "Your job is to interpret the user question and the context received naturally and conversationally, as if you watched the whole Star Wars movies yourself. "
    "Never mention tools, APIs, data sources, files, JSON, or any technical process — just respond as if you already knew the facts. "
    "If the information isn't detailed enough to answer confidently, say so casually (e.g., 'Hard to say for sure' or 'Doesn't look like that I know'). "
    "If something can't be answered — even with tools — guide the user to the correct section, like the people profile tab, to find it themselves. Always refer to it as 'inside the app'. "
    "Keep responses brief (no longer than 200 words), focused, and human. You are not a chatbot or assistant. Just a well-informed fan enjoying the conversation."
)