"""
Client Gemini partagé pour les opérations synchrones de l'assistant (emails de support).
Le pipeline de chat principal est entièrement asynchrone (voir shop/services/gemini_async.py).
"""

from google import genai
from django.conf import settings


_gemini_client = None


def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client
