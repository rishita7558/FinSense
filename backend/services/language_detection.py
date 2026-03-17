from langdetect import detect
import re

def detect_language(text):
    text_lower = text.lower()
    
    # Common Hindi/Hinglish structural words
    hinglish_markers = ["hai", "hoon", "tha", "mera", "kya", "kar", "raha", "yeh", "woh", "kaise"]
    
    hindi_word_count = sum(1 for word in hinglish_markers if re.search(r'\b' + word + r'\b', text_lower))
    
    # Basic heuristic: if it contains english financial terms but also contains Hindi structural words, it's Hinglish
    has_english = bool(re.search(r'[a-z]', text_lower))
    
    # 1. Phonetic/Unicode Hard-Checks for Indian Regional Scripts
    # Instead of guessing based on vocabulary, check the actual unicode block of the alphabet
    if re.search('[\u0C00-\u0C7F]', text):
        return "Telugu"
    elif re.search('[\u0C80-\u0CFF]', text):
        return "Kannada"
    elif re.search('[\u0B80-\u0BFF]', text):
        return "Tamil"
    elif re.search('[\u0D00-\u0D7F]', text):
        return "Malayalam"
    elif re.search('[\u0900-\u097F]', text) and not has_english:
        return "Hindi"

    # 2. Heuristics fallback for Latin code-mixed Hinglish
    if hindi_word_count >= 1 and has_english:
        return "Hinglish (Code-Mixed)"
        
    # 3. Final Fallback to langdetect
    try:
        lang_code = detect(text)
        language_map = {
            "en": "English", "hi": "Hindi", "mr": "Marathi", "bn": "Bengali", 
            "te": "Telugu", "ta": "Tamil", "gu": "Gujarati", "kn": "Kannada", 
            "ml": "Malayalam", "ur": "Urdu", "pa": "Punjabi"
        }
        return language_map.get(lang_code, lang_code.upper())
    except:
        return "Unknown"