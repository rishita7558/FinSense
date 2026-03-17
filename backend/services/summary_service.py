import os
from groq import Groq
from backend.config import GROQ_API_KEY

import json

def generate_summary(text):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing from .env! Cannot perform summarization.")

    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""
    You are a professional financial assistant. 
    Analyze this conversation transcript and extract structured insights.
    
    Transcript:
    {text}

    You MUST return ONLY a valid JSON object with the following schema:
    {{
        "topic": "High level financial theme",
        "intent": "The primary goal of the user",
        "decisions": ["Concrete step 1", "Concrete step 2"],
        "risks": ["Financial exposure 1", "Warning 2"]
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    try:
        return json.loads(response.choices[0].message.content)
    except:
        # Fallback if the strict JSON parsing inexplicably fails
        return {"topic": "Unknown", "intent": "Unknown", "decisions": [], "risks": []}