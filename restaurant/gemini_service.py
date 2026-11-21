import time

from django.conf import settings
from google import genai
from google.genai import types


class GeminiError(Exception):
    pass


def ask_gemini(prompt, system=None, max_tokens=1000):
    """Send a prompt to Gemini. Retries once, then tries the backup model."""
    if not settings.GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY is not set in the .env file.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    models = [settings.GEMINI_MODEL]
    if settings.GEMINI_FALLBACK_MODEL and settings.GEMINI_FALLBACK_MODEL != settings.GEMINI_MODEL:
        models.append(settings.GEMINI_FALLBACK_MODEL)

    last_error = None
    for model in models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        max_output_tokens=max_tokens,
                    ),
                )
                return (response.text or "").strip()
            except Exception as exc:
                last_error = exc
                time.sleep(1)
    raise GeminiError(str(last_error)) from last_error