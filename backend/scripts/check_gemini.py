"""Make a short Gemini request after GEMINI_API_KEY is set in backend/.env."""

from core.config import settings
from google import genai


if not settings.GEMINI_API_KEY:
    raise SystemExit("Set GEMINI_API_KEY in backend/.env, then run this check again.")

client = genai.Client(api_key=settings.GEMINI_API_KEY)
interaction = client.interactions.create(
    model=settings.GEMINI_MODEL,
    input="Reply with the single word OK.",
)
print(f"{settings.GEMINI_MODEL} responded: {interaction.output_text}")
