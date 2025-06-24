# utils/openai_utils.py

import openai
import json
from config import OPENAI_API_KEY
import re

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def call_openai_chat_completion(prompt: str, model: str = "gpt-4-1106-preview") -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    content = response.choices[0].message.content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    try:
        return json.loads(content)
    e