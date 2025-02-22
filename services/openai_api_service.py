import os
from openai import OpenAI, AsyncOpenAI, ChatCompletion
from dotenv import load_dotenv
import json
from typing import Dict, List
from models.models import UserMessage, MessageError, MessageAlternative

load_dotenv()


class OpenAIService:
    def __init__(self):
        self.open_ai_client = OpenAI(api_key=os.getenv("OPENAPI_KEY"))
        self.client_async = AsyncOpenAI(api_key=os.getenv("OPENAPI_KEY"))

    def detect_language(self, message: str) -> str | None:
        response = self.open_ai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник, который определяет язык текста. Отвечай только кодом языка (например, 'en', 'hi', 'bn').",
                },
                {"role": "user", "content": f"Какой это язык? {message}"},
            ],
            max_tokens=5,
        )

        result = response.choices[0].message.content.strip()
        return result

    async def detect_language_async(self, message: str) -> str | None:
        response: ChatCompletion = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник, который определяет язык текста. Отвечай только кодом языка (например, 'en', 'hi', 'bn').",
                },
                {"role": "user", "content": f"Какой это язык? {message}"},
            ],
            max_tokens=5,
        )
        result = response.choices[0].message.content.strip()
        return result

    def translate_message_from_hindi_to_english(self, message: str) -> str | None:
        response = self.open_ai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты переводчик, который переводит текст с индийских языков (например, хинди, бенгальский, тамильский) на английский.",
                },
                {"role": "user", "content": f"Переведи на английский: {message}"},
            ],
            max_tokens=100,
        )
        result = response.choices[0].message.content.strip()

        return result

    async def translate_message_from_hindi_to_english_async(
        self, message: str
    ) -> str | None:
        response: ChatCompletion = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты переводчик, который переводит текст с индийских языков (например, хинди, бенгальский, тамильский) на английский.",
                },
                {"role": "user", "content": f"Переведи на английский: {message}"},
            ],
            max_tokens=100,
        )
        result: str = response.choices[0].message.content.strip()
        return result

    def translate_message_from_english_to_hindi(self, message: str) -> str | None:
        response = self.open_ai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты переводчик, который переводит текст с английских языков на индийский.",
                },
                {
                    "role": "user",
                    "content": f"Переведи на индийский,отправь мне только сам перевод: {message}",
                },
            ],
        )
        result = response.choices[0].message.content.strip()

        return result

    async def translate_message_from_bengali_to_english_async(
        self, message: str
    ) -> str | None:
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты переводчик, который переводит текст с индийских языков (например, хинди, бенгальский, тамильский) на английский.",
                },
                {"role": "user", "content": f"Переведи на английский: {message}"},
            ],
            max_tokens=100,
        )
        result: str = response.choices[0].message.content.strip()
        return result

    async def translate_message_from_english_to_bengali_async(
        self, message: str
    ) -> str | None:
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты переводчик, который переводит текст с английских языков на бенгальский.",
                },
                {"role": "user", "content": f"Переведи на бенгальский: {message}"},
            ],
            max_tokens=100,
        )
        result: str = response.choices[0].message.content.strip()
        return result

    async def translate_message_from_english_to_hindi_async(
        self, message: str
    ) -> str | None:
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты переводчик, который переводит текст с английских языков на индийский.",
                },
                {"role": "user", "content": f"Переведи на индийский: {message}"},
            ],
        )
        result = response.choices[0].message.content.strip()

        return result

    async def analyze_message_with_correction(self, message: str, language: str):

        promt = """
You are an AI assistant for an online casino and sports betting support team.

Analyze the following message based on the gambling and betting context.

- If there are no errors, return only the English translation.
- If there are errors and you are confident in the correction, return the error and the corrected version.
- If you are unsure about the correction, provide two alternative corrections.

The message language will be provided as an input parameter.

Return the response in the following JSON format:

{
  "original_message": "<input message>",
  "language": "<detected language>",
  "status": "<status of the message processing (no_error, error_fixed, error_uncertain)>",
  "issues": [
    {
      "error": "<description of the issue>",
      "suggested_correction": "<corrected text>",
      "alternatives": ["<alternative correction 1>", "<alternative correction 2>"]
    }
  ],
  "corrected_message_hindi": "<fully corrected version in Hindi (if applicable)>",
  "corrected_message_english": "<English translation of the corrected message>",
  "translation_only": "<English translation if no errors were found>"
}
"""

        response = await self.client_async.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": promt,
                },
                {
                    "role": "user",
                    "content": f"Language: {language}\nMessage: {message}",
                },
            ],
        )
        try:
            response_dict: Dict = json.loads(response.choices[0].message.content)
            status: str = response_dict.get("status", "")
            language: str = response_dict.get("language", "")
            original_message: str = response_dict.get("original_message", "")

            if status == "no_error":
                translated_message: str = response_dict.get("translation_only", "")

                return UserMessage(
                    status=status,
                    message_language=language,
                    errors=[],
                    corrected_message_origin=original_message,
                    corrected_message_en=translated_message,
                    original_message=original_message,
                )
            elif status == "error_fixed":
                issues: List[Dict] = response_dict.get("issues", [])
                corrected_message_english: str = response_dict.get(
                    "corrected_message_english", ""
                )
                corrected_message_origin: str = response_dict.get(
                    "corrected_message_origin", ""
                )
                errors: List[MessageError] = []
                for issue in issues:
                    original: str = issue.get("error", {}).get("original", "")
                    english: str = issue.get("error", {}).get("english", "")
                    suggested_correction_en: str = issue.get(
                        "suggested_correction", {}
                    ).get("english", "")
                    suggested_correction_origin: str = issue.get(
                        "suggested_correction", {}
                    ).get("original", "")
                    errors.append(
                        MessageError(
                            original=original,
                            english=english,
                            suggested_correction_en=suggested_correction_en,
                            suggested_correction_origin=suggested_correction_origin,
                            alternatives=[],
                        )
                    )
                return UserMessage(
                    errors=errors,
                    status=status,
                    original_message=original_message,
                    corrected_message_en=corrected_message_english,
                    message_language=language,
                    corrected_message_origin=corrected_message_origin,
                )
            elif status == "error_uncertain":
                corrected_message_english = response_dict.get(
                    "corrected_message_english",''
                )
                corrected_message_origin = response_dict.get(
                    "corrected_message_origin",''
                )

                issues: List[Dict] = response_dict.get("issues", [])
                errors: List[MessageError] = []
                for issue in issues:
                    alternatives_result: List[MessageAlternative] = []
                    alternatives: List[Dict] = issue.get("alternatives", [])
                    for alternative in alternatives:
                        alternatives_result.append(
                            MessageAlternative(
                                original=alternative.get("original"),
                                english=alternative.get("english"),
                            )
                        )
                    original: str = issue.get("error", {}).get("original", "")
                    english: str = issue.get("error", {}).get("english", "")
                    errors.append(
                        alternatives=alternatives_result,
                        original=original,
                        english=english,
                        suggested_correction_en="",
                        suggested_correction_origin="",
                    )
                return UserMessage(
                    errors=errors,
                    status=status,
                    original_message=original_message,
                    corrected_message_en=corrected_message_english,
                    message_language=language,
                    corrected_message_origin=corrected_message_origin,
                )

        except:
            return None
