import os
import re
from groq import Groq
from backend.config import GROQ_API_KEY

LANG_MAP = {
    "te": "Telugu", "ta": "Tamil", "kn": "Kannada", "ml": "Malayalam",
    "hi": "Hindi", "en": "English", "mr": "Marathi", "bn": "Bengali",
    "gu": "Gujarati", "ur": "Urdu", "pa": "Punjabi"
}

def transcribe_audio(audio_path, language_hint=None):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing from .env! Cannot perform transcription.")

    client = Groq(api_key=GROQ_API_KEY)

    # ──────────────────────────────────────────────────────────
    # STEP 1: Native transcription using the FULL Whisper model
    # The `language` parameter FORCES Whisper to transcribe in
    # the correct script — this is the #1 accuracy booster.
    # ──────────────────────────────────────────────────────────
    whisper_params = {
        "model": "whisper-large-v3",
        "response_format": "verbose_json"
    }
    
    # If user selected a language, force Whisper to use it
    if language_hint:
        whisper_params["language"] = language_hint
    
    with open(audio_path, "rb") as file_obj:
        native_result = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), file_obj.read()),
            **whisper_params
        )
    
    native_text = native_result.text.strip()
    
    # Use Whisper's detected language or the user's hint
    whisper_lang_code = language_hint or getattr(native_result, 'language', None)
    detected_language = LANG_MAP.get(whisper_lang_code, whisper_lang_code or "Unknown")

    # ──────────────────────────────────────────────────────────
    # STEP 1.5: Detect code-mixing (Tinglish, Hinglish, etc.)
    # ──────────────────────────────────────────────────────────
    has_english = bool(re.search(r'[a-zA-Z]{3,}', native_text))
    has_non_latin = bool(re.search(r'[^\x00-\x7F]', native_text))
    
    is_code_mixed = has_english and has_non_latin and detected_language != "English"
    
    if is_code_mixed:
        code_mix_label = {
            "Telugu": "Tinglish", "Hindi": "Hinglish", "Tamil": "Tanglish",
            "Kannada": "Kanglish", "Malayalam": "Manglish"
        }
        detected_language = code_mix_label.get(detected_language, f"{detected_language}-English Mix")

    # ──────────────────────────────────────────────────────────
    # STEP 1.75: LLM Transcription Cleanup (regional languages)
    # Whisper sometimes outputs garbled script for Dravidian
    # languages. LLaMa-3 cleans up the native text.
    # ──────────────────────────────────────────────────────────
    if detected_language not in ["English", "Unknown"] and not is_code_mixed:
        cleanup_prompt = f"""The following is a Whisper-generated transcription in {detected_language}.
It may contain incorrectly mixed scripts, broken words, or transliteration errors.
Clean it up: output ONLY the corrected {detected_language} text in proper native script.
Do NOT translate to English. Keep the meaning identical.
If the text is already correct, return it as-is.

Text: {native_text}"""

        cleanup_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": cleanup_prompt}],
            temperature=0.1
        )
        native_text = cleanup_response.choices[0].message.content.strip()

    # ──────────────────────────────────────────────────────────
    # STEP 2: English translation via LLaMa-3 70B
    # ──────────────────────────────────────────────────────────
    if detected_language == "English":
        english_text = native_text
    elif is_code_mixed:
        translation_prompt = f"""The following text is CODE-MIXED speech ({detected_language}) containing both English words and regional language words written together.
Translate the ENTIRE text into clean, fluent English. Keep English words as-is and translate only the non-English parts.
This is a financial conversation about SIP, EMI, loans, mutual funds, investments, interest rates, etc.
Preserve all financial terms, numbers, and proper nouns exactly.
Return ONLY the English translation, nothing else.

Text:
{native_text}"""

        translation_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": translation_prompt}],
            temperature=0.1
        )
        english_text = translation_response.choices[0].message.content.strip()
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
            temperature=0.1
        )
        english_text = translation_response.choices[0].message.content.strip()

    return {
        "native_text": native_text,
        "english_text": english_text,
        "detected_language": detected_language
    }