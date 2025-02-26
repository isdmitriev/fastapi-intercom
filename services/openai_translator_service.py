import os
from openai import OpenAI, AsyncOpenAI, ChatCompletion
from dotenv import load_dotenv
import json
from typing import Dict, List
from models.models import UserMessage

load_dotenv()


class OpenAITranslatorService:
    def __init__(self):
        self.open_ai_client = OpenAI(api_key=os.getenv("OPENAPI_KEY"))
        self.client_async = AsyncOpenAI(api_key=os.getenv("OPENAPI_KEY"))

    async def translate_message_from_english_to_hindi_async(
            self, message: str
    ) -> str | None:
        promt = "You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India. Your task is to translate the following English message into Hindi (हिन्दी) while preserving the exact meaning and making it easy to understand for a native Hindi speaker. Maintain a friendly and professional tone, ensuring clarity for the player. If the message contains casino or betting-related terms, translate them in a way that Hindi-speaking players commonly understand."
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": promt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip()

        return result

    async def translate_message_from_english_to_bengali_async(
            self, message: str
    ) -> str | None:
        promt = "You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from Bangladesh and India. Your task is to translate the following English message into Bengali (বাংলা) while preserving the exact meaning and making it easy to understand for a native Bengali speaker. Maintain a friendly and professional tone, ensuring clarity for the player. If the message contains casino or betting-related terms, translate them in a way that Bengali-speaking players commonly understand"
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": promt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip()

        return result

    async def translate_message_from_english_to_hinglish_async(
            self, message: str
    ) -> str | None:
        promt = "You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India and Bangladesh. Your task is to translate the following English message into Romanized Hindi (Hinglish) while preserving the exact meaning and making it easy to understand for a native Hindi speaker. Maintain a friendly and professional tone, ensuring clarity for the player. If the message contains casino or betting-related terms, translate them in a way that Indian players commonly understand."
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": promt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip()

        return result

    async def translate_message_from_bengali_to_english_async(
            self, message: str
    ) -> str | None:
        promt = "You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from Bangladesh and India. Your task is to translate the following Bengali (বাংলা) message into English while preserving the exact meaning and making it easy to understand for a native English speaker. Maintain a friendly and professional tone, ensuring clarity for the player. If the message contains casino or betting-related terms, translate them in a way that English-speaking players commonly understand."
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": promt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip()

        return result

    async def translate_message_from_hindi_to_english_async(
            self, message: str
    ) -> str | None:
        promt = "You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India. Your task is to translate the following Hindi (हिंदी) message into English while preserving the exact meaning and making it easy to understand for a native English speaker. Maintain a friendly and professional tone, ensuring clarity for the player. If the message contains casino or betting-related terms, translate them in a way that English-speaking players commonly understand."
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": promt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip()

        return result

    async def translate_message_from_hinglish_to_english_async(
            self, message: str
    ) -> str | None:
        promt = "You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India. Your task is to translate the following Hinglish (a mix of Hindi and English) message into proper English while preserving the exact meaning and making it easy to understand for a native English speaker. Maintain a friendly and professional tone, ensuring clarity for the player. If the message contains casino or betting-related terms, translate them in a way that English-speaking players commonly understand. Also, ensure that informal or slang expressions are appropriately adapted for clarity and professionalism."
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": promt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip()

        return result

    async def detect_language_async(self, message: str) -> str | None:
        promt = """You are an AI assistant for an online casino and sports betting customer support team. Your task is to determine the language of a player's message.

Please identify the language as one of the following:
- English: Messages written entirely in English
- Hindi: Messages written in Devanagari script (example: मेरी पेमेंट में प्रॉब्लम है)
- Hinglish: Messages written using Latin/Roman alphabet but containing Hindi words or sentence structure, often mixed with English words (examples: "Meri payment mein problem hai", "Yaar mera account freeze ho gaya hai", "Kitna balance bacha hai check karo please")
- Bengali: Messages written in Bengali script (example: আমার পেমেন্ট নিয়ে সমস্যা আছে)
- Uncertain: If you cannot confidently determine the language

IMPORTANT: Pay special attention to the writing system. If the message uses Latin/Roman alphabet but contains Hindi vocabulary or grammar mixed with English words, classify it as Hinglish, NOT Hindi.

Return ONLY the language name without explanation."""

        response = await self.client_async.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": promt},
                {"role": "user", "content": message},
            ],
            temperature=0,
        )
        result = response.choices[0].message.content.strip()

        return result
