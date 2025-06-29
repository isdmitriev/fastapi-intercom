import os
from openai import OpenAI, AsyncOpenAI, ChatCompletion
from dotenv import load_dotenv
import json
from typing import Dict, List
from models.models import UserMessage
from models.custom_exceptions import APPException
from openai._exceptions import OpenAIError

load_dotenv()


class OpenAITranslatorService:
    def __init__(self):
        try:
            self.open_ai_client = OpenAI(api_key=os.getenv("OPENAPI_KEY"))
            self.client_async = AsyncOpenAI(api_key=os.getenv("OPENAPI_KEY"))
        except OpenAIError as open_ai_error:
            full_exception_name = (
                f"{type(open_ai_error).__module__}.{type(open_ai_error).__name__}"
            )
            exception_message: str = str(open_ai_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="OpenAITranslatorService_Init",
                params={},
            )
            raise app_exception
        except Exception as e:
            raise e

    async def translate_message_from_english_to_hindi_async(
        self, message: str
    ) -> str | None:
        promt = """You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India. Your task is to translate the following English message into Hindi (हिन्दी) while preserving the exact meaning and making it easy to understand for a native Hindi speaker.

CRITICAL TRANSLATION REQUIREMENTS:
1. **TRANSLATE EVERYTHING**: You MUST translate ALL words into Hindi, including technical terms like "Transactions History", "Payment Provider", "Finance Team", etc. Do NOT leave ANY English words untranslated.

2. **Technical Terms Translation Guide**:
   - Transactions History → लेन-देन का इतिहास
   - Finance Team → वित्त टीम 
   - Payment Provider → भुगतान प्रदाता
   - Processing → प्रसंस्करण
   - Verifying → सत्यापन
   - Completed → पूर्ण

3. **Gender Specifications**:
   - The message is written by a **female customer support agent** - use appropriate **feminine grammatical forms** (feminine verb endings like '-ी' instead of masculine '-ा' when the agent refers to herself)
   - The message is addressed **to a male player** - use **respectful masculine forms** when addressing him (जी, आप, किया है, बताया गया है, etc.)

4. **Tone Requirements**:
   - Maintain friendly and professional customer service tone
   - Use respectful language appropriate for Indian customers
   - Ensure clarity for Hindi-speaking gambling/betting platform users

5. **ZERO TOLERANCE**: Any English word remaining in the translation is considered an ERROR. Every single term must be in Hindi.

REMEMBER: Complete Hindi translation with NO English words remaining is mandatory."""
        promt2 = """You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India. Your task is to translate the following English message into Hindi (हिन्दी) while preserving the exact meaning and making it easy to understand for a native Hindi speaker.

Important: The message is written by a **female customer support agent**, so please use appropriate **feminine grammatical forms and gender markers** in Hindi where applicable (such as feminine verb endings like '-ी' instead of masculine '-ा' when referring to the writer).

The message is being sent **to a male player**, so please use **respectful and appropriate masculine forms** when addressing the recipient (such as using "किया है", "बताया गया है", etc. when referring to the player).

Maintain a friendly and professional tone, ensuring clarity for the player. If the message contains casino or betting-related terms, translate them in a way that Hindi-speaking players commonly understand.
"""
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
        translated_text = response.choices[0].message.content
        result = translated_text.strip('"')

        return result

    async def translate_message_from_english_to_bengali_async(
        self, message: str
    ) -> str | None:
        current_promt = """You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India. Your task is to translate the following English message into Bengali (বাংলা) while preserving the exact meaning and making it easy to understand for a native Bengali speaker.

CRITICAL TRANSLATION REQUIREMENTS:
1. **TRANSLATE EVERYTHING**: You MUST translate ALL words into Bengali, including technical terms like "Transactions History", "Payment Provider", "Finance Team", etc. Do NOT leave ANY English words untranslated.

2. **Technical Terms Bengali Translation Guide**:
   - Transactions History → লেনদেনের ইতিহাস (lendenor itihaas)
   - Finance Team → অর্থ বিভাগ (ortho bibhag) / ফিন্যান্স টিম (finance team)
   - Payment Provider → পেমেন্ট প্রদানকারী (payment prodankaari)
   - Processing → প্রক্রিয়াকরণ (prokriyakoron)
   - Verifying → যাচাইকরণ (yachaaikoron)
   - Completed → সম্পূর্ণ (shompurno)

3. **Gender and Respect Specifications**:
   - The message is written by a **female customer support agent** - use appropriate **feminine grammatical forms** in Bengali
   - The message is addressed **to a male player** - use **respectful forms** like আপনি (apni), আপনার (apnar), etc.

4. **Tone Requirements**:
   - Maintain friendly and professional customer service tone
   - Use respectful Bengali language appropriate for customer service
   - Ensure clarity for Bengali-speaking gambling/betting platform users
   - Use formal/respectful Bengali (শুদ্ধ বাংলা) mixed with commonly understood terms

5. **ZERO TOLERANCE**: Any English word remaining in the translation is considered an ERROR. Every single term must be in Bengali script (বাংলা).

REMEMBER: Complete Bengali translation with NO English words remaining is mandatory. Use Bengali script only."""

        promt2 = """You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from Bangladesh and India. Your task is to translate the following English message into Bengali (বাংলা) while preserving the exact meaning and making it easy to understand for a native Bengali speaker.

Important: The message is written by a female customer support agent, so please use appropriate feminine grammatical forms and gender-specific markers in Bengali where applicable.

The message is being sent to a male player. While Bengali verbs generally do not change based on gender, please use respectful and context-appropriate masculine addressing forms when relevant (e.g., choice of pronouns, honorifics, and polite expressions).

Maintain a friendly and professional tone, ensuring clarity for the player. If the message contains casino or betting-related terms, translate them in a way that Bengali-speaking players commonly understand.
"""
        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": current_promt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0,
        )
        translated_text = response.choices[0].message.content
        result = translated_text.strip('"')

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

    async def translate_message_from_english_to_hinglish_async_v2(
        self, message: str
    ) -> str | None:
        prompt = f"""You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India and Bangladesh. Your task is to translate the following English message into **Hinglish (Romanized Hindi)**, ensuring that the translation is written **entirely in the Latin alphabet** (English letters).

The translation must **not use Devanagari script** (हिंदी). Instead, it should be written in **a natural, easy-to-read Romanized Hindi style** that native Hindi speakers commonly use in chat or casual writing.

Make sure that no extra symbols (such as exclamation marks, commas, or other punctuation marks) are added unless they are part of the original message.

Maintain a **friendly and professional tone**, ensuring clarity for the player. If the message contains casino or betting-related terms, translate them in a way that Indian players commonly understand.

Example:
- **English:** "Your bet has been placed successfully."
- - **Correct Hinglish:** "Aapka bet successfully lag gaya hai."
- - **Incorrect (Devanagari):** "आपका बेट सफलतापूर्वक लग गया है।"

Now, translate the following message into **Hinglish (Romanized Hindi) only**:

"{message}"
"""

        promt2 = f"""You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India and Bangladesh. Your task is to translate the following English message into **Hinglish (Romanized Hindi)**, ensuring that the translation is written **entirely in the Latin alphabet** (English letters). The translation must **not use Devanagari script** (हिंदी). Instead, it should be written in **a natural, easy-to-read Romanized Hindi style** that native Hindi speakers commonly use in chat or casual writing.

CRITICAL TRANSLATION REQUIREMENTS:
1. **TRANSLATE EVERYTHING INTO HINGLISH**: You MUST convert ALL words into Hinglish format, including technical terms. Do NOT leave pure English technical terms untranslated - convert them to Hindi concepts written in Roman script.

2. **Technical Terms Hinglish Guide**:
   - Transactions History → len-den ka history / transaction ka itihaas
   - Finance Team → finance ki team / paisa wali team  
   - Payment Provider → payment karne wala / payment company
   - Processing → process ho raha hai
   - Verifying → verify kar rahe hain / check kar rahe hain
   - Completed → complete ho gaya / poora ho gaya

3. **ZERO TOLERANCE RULE**: Any pure English technical term remaining untranslated is considered an ERROR. Everything must be in natural Hinglish format using Roman script only.

Important: The note is written by a **female support agent**, so the tone and style should reflect that. The message is being sent **to a male player**, so please use **masculine grammatical forms and respectful male-addressing style in Hindi** where applicable (aap, aapko, aapne, etc.).

Make sure that no extra symbols (such as exclamation marks, commas, or other punctuation marks) are added unless they are part of the original message. Maintain a **friendly and professional tone**, ensuring clarity for the player.

Example: 
- **English:** "Your bet has been placed successfully."
- **Correct Hinglish:** "Aapka bet successfully lag gaya hai."
- **Incorrect (Devanagari):** "आपका बेट सफलतापूर्वक लग गया है।"

REMEMBER: Complete Hinglish conversion with natural Hindi-English mixing in Roman script is mandatory.

Now, translate the following message into **Hinglish (Romanized Hindi) only**, using **masculine forms** where appropriate: "{message}"""
        current_promt = """You are an AI assistant for the customer support team of an online casino and sports betting platform, handling conversations with players from India. Your task is to translate the following English message into Hinglish (Hindi written in Roman script) while preserving the exact meaning and making it natural for Indian English speakers.

CRITICAL TRANSLATION REQUIREMENTS:
1. **TRANSLATE EVERYTHING INTO HINGLISH**: You MUST convert ALL words into Hinglish format. Do NOT leave pure English technical terms untranslated - convert them to Hindi concepts written in Roman script.

2. **Technical Terms Hinglish Guide**:
   - Transactions History → len-den ka history / transaction ka history
   - Finance Team → finance ki team / paisa wali team  
   - Payment Provider → payment karne wala / payment company
   - Processing → process ho raha hai
   - Verifying → verify kar rahe hain
   - Completed → complete ho gaya / poora ho gaya

3. **Gender Specifications**:
   - The message is written by a **female customer support agent** - use appropriate **feminine markers** in Hinglish (main, mujhe, maine, etc. with feminine context)
   - The message is addressed **to a male player** - use **respectful masculine forms** (aap, aapko, aapne, etc.)

4. **Hinglish Style Requirements**:
   - Mix Hindi grammar with Roman script naturally
   - Use common Hinglish expressions (kar sakte hain, ho jayega, etc.)
   - Keep it conversational and familiar to Indian users
   - Use respectful terms like "aap", "ji" where appropriate

5. **ZERO TOLERANCE**: Any pure English technical term remaining untranslated is considered an ERROR. Everything must be in natural Hinglish format.

REMEMBER: Complete Hinglish conversion with natural Hindi-English mixing is mandatory."""

        response = await self.client_async.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "system", "content": promt2}],
            temperature=0.2,
        )
        translated_text = response.choices[0].message.content
        result = translated_text.strip('"')
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
        translated_text = response.choices[0].message.content
        result = translated_text.strip('"')

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
        translated_text = response.choices[0].message.content
        result = translated_text.strip('"')

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
        translated_text = response.choices[0].message.content
        result = translated_text.strip('"')

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

    async def detect_language_async_v2(self, message: str):
        prompt = f"""
            Determine the language of the given text. The possible options are:
            - 'Hindi' – if the text is written in Devanagari script (e.g., 'नमस्ते, मेरी समस्या है...').
            - 'Hinglish' – if the text is written in the Latin alphabet but represents Hindi words phonetically (e.g., 'namaste, meri samasya hai...').
            - 'English' – if the text is standard English (e.g., 'Hello, I have a problem...').
            - 'Bengali' – if the text is written in Bengali script (বাংলা).
            - 'Uncertain' – if the language is unclear or mixed in a way that makes identification difficult.

            Return only the name of the language from the list above. Do not provide explanations or additional text.

            Text: {message}
            Language:
            """
        response = await self.client_async.chat.completions.create(
            # model="gpt-4",
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=10,
            temperature=0,
        )
        result = response.choices[0].message.content.strip()
        return result
