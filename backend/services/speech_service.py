import os
import re

from groq import Groq

from backend.config import GROQ_API_KEY

LANG_MAP = {
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "hi": "Hindi",
    "en": "English",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "ur": "Urdu",
    "pa": "Punjabi",
}


def _detect_code_mixed(native_text, detected_language):
    has_english = bool(re.search(r"[a-zA-Z]{3,}", native_text))
    has_non_latin = bool(re.search(r"[^\x00-\x7F]", native_text))
    if has_english and has_non_latin and detected_language != "English":
        code_mix_label = {
            "Telugu": "Tinglish",
            "Hindi": "Hinglish",
            "Tamil": "Tanglish",
            "Kannada": "Kanglish",
            "Malayalam": "Manglish",
        }
        return code_mix_label.get(detected_language, f"{detected_language}-English Mix")
    return detected_language


def transcribe_audio(audio_path, language_hint=None):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing from .env! Capture Conversation requires Groq.")

    client = Groq(api_key=GROQ_API_KEY)

    whisper_params = {"model": "whisper-large-v3", "response_format": "verbose_json"}
    if language_hint:
        whisper_params["language"] = language_hint

    with open(audio_path, "rb") as file_obj:
        native_result = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), file_obj.read()), **whisper_params
        )

    native_text = native_result.text.strip()
    whisper_lang_code = language_hint or getattr(native_result, "language", None)
    detected_language = LANG_MAP.get(whisper_lang_code, whisper_lang_code or "Unknown")
    detected_language = _detect_code_mixed(native_text, detected_language)

    if detected_language == "English":
        english_text = native_text
    else:
        translation_prompt = f"""Translate the following {detected_language} text into natural, fluent English.
This is a financial conversation about topics like SIP, EMI, loans, mutual funds, and investments.
Preserve all financial terms, numbers, and proper nouns exactly as spoken.
Return ONLY the English translation, nothing else.

Text to translate:
{native_text}"""

        translation_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": translation_prompt}],
            temperature=0.1,
        )
        english_text = translation_response.choices[0].message.content.strip()

    return {
        "native_text": native_text,
        "english_text": english_text,
        "detected_language": detected_language,
    }
