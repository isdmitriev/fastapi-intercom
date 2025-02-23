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

    async def analyze_message_with_correction(self, message: str):
        response = await self.client_async.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI assistant for an online casino and sports betting support team. 
                           Your task is to analyze the player's message written in Hindi, Bengali, or Hinglish. 
                           Identify any spelling mistakes, incorrect word choices, slang, or unclear meanings based on the gambling and betting context.

                           ### Rules:
                           - If the message is correct, return it as is.
                           - If there is a clear mistake, correct it and explain why.
                           - If you are unsure, provide two possible interpretations and an explanation in English.
                           - Always include an English translation of the corrected message (if applicable).

                           ### Response Format (Always return JSON):
                           {
                             "status": "ok" | "corrected" | "uncertain",
                             "original_message": "<original message>",
                             "corrected_message": "<corrected message, if applicable>",
                             "correction_reason": "<reason for correction, if applicable>",
                             "translated_message": "<English translation of the corrected message, if applicable>",
                             "possible_interpretations": ["<interpretation 1>", "<interpretation 2>"] (if uncertain),
                             "note": "<internal note for the support agent, if uncertain>",
                             "explanation": "<detailed explanation in English>"
                           }
                           """
                },
                {"role": "user", "content": message}
            ],
            temperature=0.2,

        )


        response_dict: Dict = json.loads(response.choices[0].message.content)
        print(response_dict)
        # status: str = response_dict.get("status", "")
        # language: str = response_dict.get("language", "")
        # original_message: str = response_dict.get("original_message", "")
        #
        # if status == "no_error":
        #     translated_message: str = response_dict.get("translation_only", "")
        #     return UserMessage(
        #         status=status,
        #         message_language=language,
        #         errors=[],
        #         corrected_message_origin=original_message,
        #         corrected_message_en=translated_message,
        #         original_message=original_message,
        #     )
        #
        # elif status == "error_fixed":
        #     issues: List[Dict] = response_dict.get("
        #     corrected_message_english: str = response_dict.get(
        #         "corrected_message_english", ""
        #     )
        #     corrected_message_origin: str = response_dict.get(
        #         "corrected_message_origin", ""
        #     )
        #     errors: List[MessageError] = []
        #     for issue in issues:
        #         original: str = issue.get("original", "")
        #         english: str = issue.get("english", "")
        #         error_description = issue.get("error_in_english", "")
        #
        #         errors.append(
        #             MessageError(
        #                 original=original,
        #                 english=english,
        #                 error_description=error_description,
        #             )
        #         )
        #     return UserMessage(
        #         errors=errors,
        #         status=status,
        #         original_message=original_message,
        #         corrected_message_en=corrected_message_english,
        #         message_language=language,
        #         corrected_message_origin=corrected_message_origin,
        #     )
        # elif status == "error_uncertain":
        #     issues: List[Dict] = response_dict.get("issues", [])
        #     corrected_message_english: str = response_dict.get(
        #         "corrected_message_english", ""
        #     )
        #     corrected_message_origin: str = response_dict.get(
        #         "corrected_message_origin", ""
        #     )
        #     errors: List[MessageError] = []
        #     for issue in issues:
        #         original: str = issue.get("original", "")
        #         english: str = issue.get("english", "")
        #         error_description = issue.get("error_in_english", "")
        #
        #         errors.append(
        #             MessageError(
        #                 original=original,
        #                 english=english,
        #                 error_description=error_description,
        #             )
        #         )
        #     return UserMessage(
        #         errors=errors,
        #         status=status,
        #         original_message=original_message,
        #         corrected_message_en=corrected_message_english,
        #         message_language=language,
        #         corrected_message_origin=corrected_message_origin,
        #     )
        #
        # else:
        #     return None
