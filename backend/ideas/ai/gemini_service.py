import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

BUSINESS_EXTRACTION_SCHEMA = {
    "language": "string (English | Hindi | Marathi | Auto)",
    "business_type": "string — normalized business type in English",
    "sector": "string — one of: food_processing, textiles_apparel, beauty_wellness, agriculture, dairy, handicrafts, retail, education, technology, manufacturing, services, healthcare, other",
    "location": "string — city, district, state, or 'Not specified'",
    "capital": "integer or null — amount in INR, null if not mentioned",
    "target_customers": "array of strings",
    "skills": "array of strings",
    "experience": "string — 'Not specified' if unknown",
    "business_stage": "string — one of: idea, startup, growth, established",
    "goal": "string — summarized goal in English",
    "keywords": "array of strings — relevant keywords for matching",
    "required_support": "array of strings — what support the user needs",
    "is_vague": "boolean — true if idea is too vague to extract meaningful info",
    "follow_up_questions": "array of strings — 2-3 follow-up questions if is_vague is true, else empty array"
}

EXTRACTION_PROMPT = """You are NariNiti's AI business advisor helping Indian women entrepreneurs.

The user has described their business idea. Extract structured information from it.

USER INPUT:
{user_input}

Extract and return ONLY a valid JSON object with these exact fields:
{schema}

RULES:
1. Detect the language (English, Hindi, or Marathi) from the input
2. Normalize business_type and sector to English for database matching
3. Extract capital as integer INR (e.g., "50 हजार" → 50000, "2 lakh" → 200000)
4. If information is not mentioned, use null for numbers or "Not specified" for strings
5. If the idea is too vague (e.g., "I want to start a business"), set is_vague=true and provide 2-3 follow-up questions
6. Keywords should be in English and useful for scheme/mentor matching
7. Do NOT invent information not present in the input
8. Return ONLY the JSON, no markdown, no explanation

SECTOR MAPPING GUIDE:
- Cooking, food, masala, tiffin, pickle, snacks → food_processing
- Tailoring, stitching, clothing, fashion → textiles_apparel
- Beauty, salon, makeup, mehendi → beauty_wellness
- Farming, vegetables, flowers → agriculture
- Dairy, milk, ghee → dairy
- Handicrafts, pottery, weaving, embroidery → handicrafts
- Shop, store, selling products → retail
- Tuition, coaching, training → education
- Software, IT, digital → technology
- Any physical product manufacturing → manufacturing
"""


def extract_business_profile(user_input: str) -> dict:
    """
    Use Gemini to extract structured business profile from user text.
    Returns dict with business profile data.
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.warning('GEMINI_API_KEY not set — using fallback extraction')
        return _fallback_extraction(user_input)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = EXTRACTION_PROMPT.format(
            user_input=user_input,
            schema=json.dumps(BUSINESS_EXTRACTION_SCHEMA, indent=2, ensure_ascii=False)
        )

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1024,
            )
        )

        raw_text = response.text.strip()
        # Strip markdown code blocks if present
        if raw_text.startswith('```'):
            raw_text = raw_text.split('```')[1]
            if raw_text.startswith('json'):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        result = json.loads(raw_text)
        result['raw_response'] = raw_text
        return _validate_and_normalise(result)

    except json.JSONDecodeError as e:
        logger.error(f'Gemini returned invalid JSON: {e}')
        # Retry with stricter instruction
        return _retry_extraction(user_input, api_key)
    except Exception as e:
        logger.error(f'Gemini extraction error: {e}')
        return _fallback_extraction(user_input)


def transcribe_audio_with_gemini(audio_bytes: bytes, mime_type: str = 'audio/webm') -> dict:
    """
    Use Gemini multimodal to transcribe audio and extract business profile.
    Returns dict with transcription + business profile.
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {'transcription': '', 'error': 'GEMINI_API_KEY not configured', 'profile': _fallback_extraction('')}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = """Listen to this audio. The speaker is an Indian woman describing her business idea.

Step 1: Transcribe exactly what she said (in the original language — Hindi, Marathi, or English).
Step 2: Extract the business information.

Return ONLY a JSON object with these fields:
{
  "transcription": "exact transcription of the audio",
  "language": "English|Hindi|Marathi",
  "business_type": "normalized business type in English",
  "sector": "one of: food_processing, textiles_apparel, beauty_wellness, agriculture, dairy, handicrafts, retail, education, technology, manufacturing, services, healthcare, other",
  "location": "location mentioned or Not specified",
  "capital": null or integer INR,
  "target_customers": [],
  "skills": [],
  "experience": "Not specified",
  "business_stage": "idea|startup|growth|established",
  "goal": "goal in English",
  "keywords": [],
  "required_support": [],
  "is_vague": false,
  "follow_up_questions": []
}"""

        audio_part = {'mime_type': mime_type, 'data': audio_bytes}
        response = model.generate_content([prompt, audio_part])

        raw_text = response.text.strip()
        if raw_text.startswith('```'):
            raw_text = raw_text.split('```')[1]
            if raw_text.startswith('json'):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        result = json.loads(raw_text)
        transcription = result.pop('transcription', '')
        return {
            'transcription': transcription,
            'profile': _validate_and_normalise(result),
        }

    except Exception as e:
        logger.error(f'Gemini audio transcription error: {e}')
        return {'transcription': '', 'error': str(e), 'profile': _fallback_extraction('')}


def _retry_extraction(user_input: str, api_key: str) -> dict:
    """Second attempt with even stricter JSON-only instruction."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""Return ONLY a JSON object, no text, no markdown.
Input: {user_input}
JSON:
{{"language":"English","business_type":"","sector":"other","location":"Not specified","capital":null,"target_customers":[],"skills":[],"experience":"Not specified","business_stage":"idea","goal":"","keywords":[],"required_support":[],"is_vague":false,"follow_up_questions":[]}}
Now fill the values based on the input above. Return only valid JSON."""

        response = model.generate_content(prompt)
        raw = response.text.strip().lstrip('```json').lstrip('```').rstrip('```').strip()
        result = json.loads(raw)
        return _validate_and_normalise(result)
    except Exception:
        return _fallback_extraction(user_input)


def _validate_and_normalise(data: dict) -> dict:
    """Ensure all required fields exist with correct types."""
    valid_sectors = [
        'food_processing', 'textiles_apparel', 'beauty_wellness', 'agriculture',
        'dairy', 'handicrafts', 'retail', 'education', 'technology',
        'manufacturing', 'services', 'healthcare', 'other'
    ]
    valid_stages = ['idea', 'startup', 'growth', 'established']

    return {
        'language': str(data.get('language', 'English')),
        'business_type': str(data.get('business_type', '') or ''),
        'sector': data.get('sector', 'other') if data.get('sector') in valid_sectors else 'other',
        'location': str(data.get('location', 'Not specified') or 'Not specified'),
        'capital': int(data['capital']) if data.get('capital') and str(data['capital']).isdigit() else (
            int(data['capital']) if isinstance(data.get('capital'), (int, float)) and data['capital'] else None
        ),
        'target_customers': list(data.get('target_customers') or []),
        'skills': list(data.get('skills') or []),
        'experience': str(data.get('experience', 'Not specified') or 'Not specified'),
        'business_stage': data.get('business_stage', 'idea') if data.get('business_stage') in valid_stages else 'idea',
        'goal': str(data.get('goal', '') or ''),
        'keywords': list(data.get('keywords') or []),
        'required_support': list(data.get('required_support') or []),
        'is_vague': bool(data.get('is_vague', False)),
        'follow_up_questions': list(data.get('follow_up_questions') or []),
        'raw_response': data.get('raw_response', ''),
    }


def _fallback_extraction(user_input: str) -> dict:
    """Simple keyword-based fallback when Gemini is unavailable."""
    text = user_input.lower()
    sector = 'other'
    if any(w in text for w in ['masala', 'food', 'cook', 'tiffin', 'pickle', 'snack', 'मसाल', 'खाना', 'जेवण']):
        sector = 'food_processing'
    elif any(w in text for w in ['tailoring', 'stitch', 'cloth', 'fashion', 'सिलाई', 'कपडे', 'शिवणकाम']):
        sector = 'textiles_apparel'
    elif any(w in text for w in ['beauty', 'salon', 'makeup', 'mehendi', 'ब्यूटी']):
        sector = 'beauty_wellness'
    elif any(w in text for w in ['farm', 'vegetable', 'flower', 'शेती', 'खेती']):
        sector = 'agriculture'
    elif any(w in text for w in ['dairy', 'milk', 'ghee', 'दूध', 'डेयरी']):
        sector = 'dairy'
    elif any(w in text for w in ['craft', 'handicraft', 'pottery', 'weav', 'हस्तकला', 'विणकाम']):
        sector = 'handicrafts'

    # Language detection
    language = 'English'
    if any('\u0900' <= c <= '\u097f' for c in user_input):
        # Devanagari detected — try Marathi vs Hindi keywords
        marathi_words = ['मला', 'आहे', 'करायचे', 'माझ्या', 'आणि', 'सुरू']
        hindi_words = ['मुझे', 'मैं', 'करना', 'चाहती', 'शुरू', 'है']
        m_count = sum(1 for w in marathi_words if w in user_input)
        h_count = sum(1 for w in hindi_words if w in user_input)
        language = 'Marathi' if m_count >= h_count else 'Hindi'

    return {
        'language': language,
        'business_type': 'Business (AI unavailable — manual review needed)',
        'sector': sector,
        'location': 'Not specified',
        'capital': None,
        'target_customers': [],
        'skills': [],
        'experience': 'Not specified',
        'business_stage': 'idea',
        'goal': user_input[:200],
        'keywords': [sector],
        'required_support': [],
        'is_vague': False,
        'follow_up_questions': [],
        'raw_response': '',
    }
