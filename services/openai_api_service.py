import os
from openai import OpenAI, AsyncOpenAI, ChatCompletion
from dotenv import load_dotenv
import json
from typing import Dict, List
from models.models import UserMessage
from models.custom_exceptions import APPException
from openai._exceptions import OpenAIError
from services.redis_cache_service import MessagesCache
from models.models import ConversationMessages, ConversationMessage

load_dotenv()


class OpenAIService:
    def __init__(self, messages_cache_service: MessagesCache):
        try:
            self.open_ai_client = OpenAI(api_key=os.getenv("OPENAPI_KEY"))
            self.client_async = AsyncOpenAI(api_key=os.getenv("OPENAPI_KEY"))
            self.messages_cache_service = messages_cache_service
        except OpenAIError as open_ai_error:
            full_exception_name = (
                f"{type(open_ai_error).__module__}.{type(open_ai_error).__name__}"
            )
            exception_message: str = str(open_ai_error)
            app_exception: APPException = APPException(
                message=exception_message,
                ex_class=full_exception_name,
                event_type="OpenAIService_Init",
                params={},
            )
            raise app_exception
        except Exception as e:
            raise e

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
        system_promt = """You are an AI assistant for an online casino and sports betting support team. Your task is to analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali.

Always return JSON with the following structure:
{
    \"status\": \"[uncertain/error_fixed/no_error]\",
    \"original_text\": \"original message\",
    \"translated_text\": \"English translation\",
    
    // Only for status=uncertain:
    \"possible_interpretations\": [
        \"corrected version (Most likely meaning explanation)\",
        \"original version (Alternative meaning explanation)\"
    ],
    \"note\": \"Note explaining unusual words, possible meanings and need for clarification\"
}

Status codes:
- \"uncertain\": When you're less than 95% confident about message meaning
- \"error_fixed\": When you found and corrected mistakes
- \"no_error\": When message is clear and no corrections needed

When detecting messages with typos or misspellings:
- Correct common substitutions (e.g., "withdrawl" → "withdrawal", "bonuss" → "bonus")
- Fix incorrect word combinations (e.g., "with drawl" → "withdrawal")
- Handle digit/letter confusion (e.g., "b0nus" → "bonus")
- Correct phonetic spelling mistakes (e.g., "vishdraal" → "withdrawal")
- Fix incorrect gambler terminology (e.g., "jackpot machine" → "slot machine")

Example responses:

1. For uncertain meaning:
{
    \"status\": \"uncertain\",
    \"original_text\": \"Mujhe mera petrol nahi mila abhi tak\",
    \"translated_text\": \"I haven't received my petrol yet\",
    \"possible_interpretations\": [
        \"Mujhe mera bonus nahi mila abhi tak (Most likely: The player is talking about a withdrawal that was not credited)\",
        \"Mujhe mera petrol nahi mila abhi tak (Unclear meaning, might refer to cashback or bonus-related request)\"
    ],
    \"note\": \"The player used the word 'petrol', which is unusual in a betting-casino-related request. Possible meanings:\\n1. Withdrawal not credited\\n2. Cashback or external bonus-related request\\nClarification needed.\"
}

2. For corrected message:
{
    \"status\": \"error_fixed\",
    \"original_text\": \"मैंने विथड्रवल के लिए अप्लाई किया लेकिन पैसा नहीं मिला\",
    \"translated_text\": \"I applied for withdrawal but haven't received the money\"
}

3. For clear message:
{
    \"status\": \"no_error\",
    \"original_text\": \"I want to withdraw my bonus\",
    \"translated_text\": \"I want to withdraw my bonus\"
}"""

        response = await self.client_async.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": system_promt},
                {"role": "user", "content": message},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        response_dict: Dict = json.loads(response.choices[0].message.content)

        status: str = response_dict.get("status", "")
        if status == "no_error":
            original_text: str = response_dict.get("original_text", "")
            translated_text: str = response_dict.get("translated_text", "")
            return UserMessage(
                status=status,
                original_text=original_text,
                translated_text=translated_text,
                note=None,
                corrected_text=original_text,
                possible_interpretations=[],
            )
        elif status == "error_fixed":
            original_text: str = response_dict.get("original_text", "")
            translated_text: str = response_dict.get("translated_text", "")
            corrected_text: str = response_dict.get("corrected_text", "")
            return UserMessage(
                status=status,
                original_text=original_text,
                translated_text=translated_text,
                note=None,
                corrected_text=corrected_text,
                possible_interpretations=[],
            )
        elif status == "uncertain":
            original_text: str = response_dict.get("original_text", "")
            translated_text: str = response_dict.get("translated_text", "")
            note: str = response_dict.get("note", "")
            interpretations: List[str] = response_dict.get(
                "possible_interpretations", []
            )
            return UserMessage(
                status=status,
                original_text=original_text,
                translated_text=translated_text,
                possible_interpretations=interpretations,
                note=note,
                corrected_text="",
            )
        else:
            return None

    async def analyze_message_with_correction_v3(
            self, message: str, conversation_id: str
    ):
        system_promt = """You are an AI assistant for an online casino and sports betting support team. Your task is to analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali.

IMPORTANT: You must carefully analyze the chat history provided to understand the context before interpreting the current message. Agent responses in the chat history are provided in both English (original) and translated form. 

When forming possible interpretations for uncertain messages, ALWAYS consider what topics were previously discussed in the chat history. This context should significantly influence your interpretations of ambiguous terms.

ALWAYS return JSON in this format:
{
    \"status\": \"[uncertain/error_fixed/no_error]\",
    \"original_text\": \"original message\",
    \"translated_text\": \"English translation\",
    \"context_analysis\": \"Brief summary of how chat history influences interpretation of current message\",
    
    // Only for status=error_fixed (REQUIRED FOR ERROR_FIXED STATUS):
    \"corrected_text\": \"message with all spelling and terminology corrections\",
    
    // Only for status=uncertain:
    \"possible_interpretations\": [
        \"Interpretation 1: English translation with most likely meaning\",
        \"Interpretation 2: Alternative English translation with different possible meaning\"
    ],
    \"note\": \"Note explaining unusual words, possible meanings AND two alternative translations:\\n1. [First translation - most probable]\\n2. [Second translation - alternative interpretation]\\nClarification needed.\"
}

### Status codes:
- **\"uncertain\"** → When the message has **multiple possible meanings**, unusual words (like \"petrol\", \"engine\", \"fuel\" in casino context), slang, or lacks context for a clear answer.
  - Example 1: \"Mera petrol add nahi huwa?\" (Is user asking about withdrawal, bonus or something else?)
  - Example 2: \"Bhai mera khata me paisa nahi aaya, diesel payment ka wait kar raha hu\" (What does diesel payment refer to?)
  - Example 3: \"Mera engine start nahi ho raha\" (What does engine refer to in casino context?)
  
  IMPORTANT: For uncertain status, you MUST consider the entire chat history to form your interpretations. For example:
  - If user previously discussed withdrawals, \"petrol\" likely refers to withdrawal
  - If chat history mentions bonus issues, \"fuel\" likely means bonus
  - If user reported login problems before, \"engine not starting\" probably relates to those login issues

- **\"error_fixed\"** → When you find and correct **spelling mistakes, typos, or wrong gambling terminology**.
  - Example: \"withdrawl\" → \"withdrawal\"
  - Example: \"bonoos\" → \"bonus\"
  - Example: \"deopsit\" → \"deposit\"
  YOU MUST ALWAYS include the \"corrected_text\" field for status=\"error_fixed\". 
  For example, if original message is \"Bhai maine 1000 ruppe ka deopsit kiya hai lekin mera bonoos nhi mila\", 
  then corrected_text should be \"Bhai maine 1000 rupee ka deposit kiya hai lekin mera bonus nahi mila\"

- **\"no_error\"** → When the message is **fully clear** with no mistakes or ambiguity.

When detecting unusual gambling-related words:
- Words like \"petrol\", \"diesel\", \"gas\", \"fuel\" often refer to \"withdrawal\" or payments
- Terms like \"engine\", \"car\", \"tank\" may refer to account functionality or balance
- Always use chat history context to improve understanding of these unusual words

For \"uncertain\" status, always provide:
1. Two possible interpretations as English translations only (no original language text)
2. A note with explanation of unusual words
3. Two complete alternative translations with different interpretations"""

        system_promt2 = """You are an AI assistant for an online casino and sports betting support team. Your task is to analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali.

IMPORTANT: You must carefully analyze the chat history provided to understand the context before interpreting the current message. Agent responses in the chat history are provided in both English (original) and translated form. 

When forming possible interpretations for uncertain messages, ALWAYS consider what topics were previously discussed in the chat history. This context should significantly influence your interpretations of ambiguous terms.

ALWAYS return JSON in this format:
{
    \"status\": \"[uncertain/error_fixed/no_error]\",
    \"original_text\": \"original message\",
    \"translated_text\": \"English translation\",
    \"context_analysis\": \"Brief summary of how chat history influences interpretation of current message\",
    
    // Only for status=error_fixed (REQUIRED FOR ERROR_FIXED STATUS):
    \"corrected_text\": \"message with all spelling and terminology corrections\",
    
    // Only for status=uncertain:
    \"possible_interpretations\": [
        \"Interpretation 1: English translation with most likely meaning\",
        \"Interpretation 2: Alternative English translation with different possible meaning\"
    ],
    \"note\": \"Note explaining unusual words, possible meanings AND two alternative translations:\\n1. [First translation - most probable]\\n2. [Second translation - alternative interpretation]\\nClarification needed.\"
}

### Status codes:
- **\"uncertain\"** → When the message has **multiple possible meanings**, unusual words (like \"petrol\", \"engine\", \"fuel\" in casino context), slang, or lacks context for a clear answer. ALSO use this status when message meaning is vague or unclear, even if there are no spelling errors or unusual words. This includes:
  - Messages with non-specific complaints (e.g., \"My account is not working\")
  - Messages lacking details about which specific feature/function has issues
  - General requests for help without specifying the problem
  - Messages with ambiguous references to previous issues

  - Example 1: \"Mera petrol add nahi huwa?\" (Is user asking about withdrawal, bonus or something else?)
  - Example 2: \"Bhai mera khata me paisa nahi aaya, diesel payment ka wait kar raha hu\" (What does diesel payment refer to?)
  - Example 3: \"Mera engine start nahi ho raha\" (What does engine refer to in casino context?)
  - Example 4: \"My deposit has gone through, can someone help me?\" (Unclear what help is needed after successful deposit)
  - Example 5: \"मेरा खाता काम नहीं कर रहा है\" (Unclear what specific account issue the player is experiencing)
  - Example 6: \"Maine amount transfer kar diya hai. Kya hogaya?\" (Ambiguous whether asking about status or reporting a problem)
  
  IMPORTANT: For uncertain status, you MUST consider the entire chat history to form your interpretations. For example:
  - If user previously discussed withdrawals, \"petrol\" likely refers to withdrawal
  - If chat history mentions bonus issues, \"fuel\" likely means bonus
  - If user reported login problems before, \"engine not starting\" probably relates to those login issues
  - If player mentioned account issues before, a vague message likely refers to the same problem

- **\"error_fixed\"** → When you find and correct **spelling mistakes, typos, or wrong gambling terminology**.
  - Example: \"withdrawl\" → \"withdrawal\"
  - Example: \"bonoos\" → \"bonus\"
  - Example: \"deopsit\" → \"deposit\"
  YOU MUST ALWAYS include the \"corrected_text\" field for status=\"error_fixed\". 
  For example, if original message is \"Bhai maine 1000 ruppe ka deopsit kiya hai lekin mera bonoos nhi mila\", 
  then corrected_text should be \"Bhai maine 1000 rupee ka deposit kiya hai lekin mera bonus nahi mila\"

- **\"no_error\"** → When the message is **fully clear** with no mistakes or ambiguity. For a message to qualify as \"no_error\", it must:
  - Have a clear, specific request or statement
  - Not contain any vague references to problems
  - Be specific about what feature, function, or service is being discussed
  - Not require guesswork to understand the player's intention

When detecting unusual gambling-related words:
- Words like \"petrol\", \"diesel\", \"gas\", \"fuel\" often refer to \"withdrawal\" or payments
- Terms like \"engine\", \"car\", \"tank\" may refer to account functionality or balance
- Always use chat history context to improve understanding of these unusual words

For \"uncertain\" status, always provide:
1. Two possible interpretations as English translations only (no original language text)
2. A note with explanation of unusual words or why the meaning is unclear
3. Two complete alternative translations with different interpretations"""

        system_promt3 = """You are an AI assistant for an online casino and sports betting support team. Your task is to analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali.\n\nIMPORTANT: You MUST carefully analyze the chat history before interpreting the current message. Agent responses in the chat history are provided in both English (original) and translated form.\n\nWhen forming possible interpretations for uncertain messages, ALWAYS consider what topics were previously discussed in the chat history. Context significantly influences ambiguous terms.\n\nALWAYS return a valid JSON object in this format:\n{\n    \"status\": \"[uncertain/error_fixed/no_error]\",\n    \"original_text\": \"original message\",\n    \"translated_text\": \"English translation\",\n    \"context_analysis\": \"Brief summary of how chat history influences interpretation of current message\",\n    \n    // Only for status=error_fixed (REQUIRED FOR ERROR_FIXED STATUS):\n    \"corrected_text\": \"message with all spelling and terminology corrections\",\n    \n    // Only for status=uncertain:\n    \"possible_interpretations\": [\n        \"Interpretation 1: English translation with most likely meaning\",\n        \"Interpretation 2: Alternative English translation with different possible meaning\"\n    ],\n    \"note\": \"Note explaining unusual words, possible meanings AND two alternative translations:\\n1. [First translation - most probable]\\n2. [Second translation - alternative interpretation]\\nClarification needed.\"\n}\n\n### Status Codes:\n- **\"uncertain\"** → When the message has **multiple possible meanings**, unusual words (like \"petrol\", \"engine\", \"fuel\" in a casino context), slang, or lacks context for a clear answer. ALSO use this status when message meaning is vague or unclear, even if there are no spelling errors. Examples:\n  - \"Mera petrol add nahi huwa?\" (Is user asking about withdrawal, bonus or something else?)\n  - \"Mera engine start nahi ho raha\" (Does \"engine\" refer to account login, balance, or something else?)\n  - \"My deposit has gone through, can someone help me?\" (Unclear what help is needed)\n  - \"मेरा खाता काम नहीं कर रहा है\" (Unclear what specific account issue the player is experiencing)\n\n  **NEW RULE:** If the chat history indicates a specific problem, assume new vague messages relate to the same issue.\n  - If user previously discussed withdrawals, \"petrol\" likely refers to withdrawal.\n  - If chat history mentions bonus issues, \"fuel\" likely means bonus.\n  - If player mentioned account issues before, a vague message likely refers to the same problem.\n\n- **\"error_fixed\"** → When you find and correct **spelling mistakes, typos, or wrong gambling terminology**.\n  - Example: \"withdrawl\" → \"withdrawal\"\n  - Example: \"bonoos\" → \"bonus\"\n  - Example: \"deopsit\" → \"deposit\"\n  **YOU MUST ALWAYS include the \"corrected_text\" field for status=\"error_fixed\".**\n\n- **\"no_error\"** → When the message is **fully clear** with no mistakes or ambiguity. A message qualifies as \"no_error\" if:\n  - It has a clear, specific request or statement.\n  - It does not contain vague references to problems.\n  - It is specific about what feature, function, or service is being discussed.\n  - It does not require guesswork to understand the player's intention.\n  **NEW RULE:** If a short message is unclear by itself but chat history makes its meaning obvious, it can still be \"no_error\".\n\n**Additional Rules for Handling Slang & New Terms:**\n- Words like \"petrol\", \"diesel\", \"gas\", \"fuel\" often refer to \"withdrawal\" or payments.\n- Terms like \"engine\", \"car\", \"tank\" may refer to account functionality or balance.\n- If a new slang term is encountered with no clear meaning, mark as \"uncertain\" and request clarification.\n\n**STRICT FORMAT ENFORCEMENT:**\n- **You MUST return a valid JSON object.**\n- **Do NOT provide explanations or additional text outside the JSON response.**\n- **If meaning is ambiguous, always provide TWO alternative interpretations.**\n- **If fixing errors, only correct spelling and terminology—do not change meaning.**"""

        messages: List[Dict] = [{"role": "system", "content": system_promt2}]
        chat_history: List[Dict] = self.get_chat_history(
            conversation_id=conversation_id
        )
        for message_chat in chat_history:
            messages.append(
                {
                    "role": message_chat.get("role"),
                    "content": message_chat.get("content"),
                }
            )

        messages.append({"role": "user", "content": f"CURRENT MESSAGE:{message}"})

        try:
            response = await self.client_async.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            response_dict: Dict = json.loads(response.choices[0].message.content)

            status: str = response_dict.get("status", "")
            if status == "no_error":
                original_text: str = response_dict.get("original_text", "")
                translated_text: str = response_dict.get("translated_text", "")
                context_analysis = response_dict.get("context_analysis", "")
                return UserMessage(
                    status=status,
                    original_text=original_text,
                    translated_text=translated_text,
                    note=None,
                    corrected_text=original_text,
                    possible_interpretations=[],
                    context_analysis=context_analysis,
                )
            elif status == "error_fixed":
                original_text: str = response_dict.get("original_text", "")
                translated_text: str = response_dict.get("translated_text", "")
                corrected_text: str = response_dict.get("corrected_text", "")
                context_analysis: str = response_dict.get("context_analysis", "")
                return UserMessage(
                    status=status,
                    original_text=original_text,
                    translated_text=translated_text,
                    note=None,
                    corrected_text=corrected_text,
                    possible_interpretations=[],
                    context_analysis=context_analysis,
                )
            elif status == "uncertain":
                original_text: str = response_dict.get("original_text", "")
                translated_text: str = response_dict.get("translated_text", "")
                note: str = response_dict.get("note", "")
                interpretations: List[str] = response_dict.get(
                    "possible_interpretations", []
                )
                context_analysis = response_dict.get("context_analysis", "")
                return UserMessage(
                    status=status,
                    original_text=original_text,
                    translated_text=translated_text,
                    possible_interpretations=interpretations,
                    note=note,
                    corrected_text="",
                    context_analysis=context_analysis,
                )
            else:
                return None

        except Exception as e:
            raise e

    def get_chat_history(self, conversation_id: str) -> List[Dict]:

        chat_mesages: ConversationMessages = self.messages_cache_service.get_conversation_messages(
            conversation_id=conversation_id
        )

        messages: List[ConversationMessage] = chat_mesages.messages
        result_messages: List[Dict] = []
        for chat_message in messages:
            if chat_message.user.type == "admin":
                result_messages.append(
                    {"role": "assistant", "content": chat_message.message}
                )

            if chat_message.user.type == "user":
                result_messages.append(
                    {"role": "user", "content": chat_message.message}
                )

        return result_messages

    async def analyze_message_with_correction_async_v2(self, message: str):
        promt = """You are an AI assistant for an online casino and sports betting support team. Your task is to analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali.

Always return JSON with the following structure:
{
    \"status\": \"[uncertain/error_fixed/no_error]\",
    \"original_text\": \"original message\",
    \"translated_text\": \"English translation\",
    
    // Only for status=uncertain:
    \"possible_interpretations\": [
        \"corrected version (Most likely meaning explanation)\",
        \"original version (Alternative meaning explanation)\"
    ],
    \"note\": \"Note explaining unusual words with possible meanings AND two alternative translations:\\n1. [First translation - most probable]\\n2. [Second translation - alternative interpretation]\\nClarification needed.\"
}

Status codes:
- \"uncertain\": When you're less than 95% confident about message meaning
- \"error_fixed\": When you found and corrected mistakes
- \"no_error\": When message is clear and no corrections needed

Example for uncertain message:
{
    \"status\": \"uncertain\",
    \"original_text\": \"Bhai site par login nahi ho pa raha hai, mera engine start hi nahi ho raha, password dalte hi petrol khatam ho jata hai\",
    \"translated_text\": \"Brother, I cannot log in to the site, my engine is not starting, as soon as I enter the password, petrol runs out\",
    \"possible_interpretations\": [
        \"Bhai site par login nahi ho pa raha hai, mera page load hi nahi ho raha, password dalte hi session expire ho jata hai (Most likely: The player is experiencing a technical issue where the site fails to load after password entry)\",
        \"Bhai site par login nahi ho pa raha hai, mera engine start hi nahi ho raha, password dalte hi petrol khatam ho jata hai (Unclear meaning, might refer to connection issues or error messages during login)\"
    ],
    \"note\": \"The player used the words 'engine' and 'petrol', which are unusual in a casino login context. Possible meanings:\\n1. Website/app not loading properly after password entry\\n2. Session expiring or connection dropping during login\\nAlternative translations:\\n1. 'Brother, I cannot log in to the site, the page doesn't load, session expires right after entering password'\\n2. 'Brother, I cannot log in to the site, the application crashes, an error appears right after entering password'\\nClarification needed.\"
}"""

        response = await self.client_async.chat.completions.create(
            model="gpt-4",  # Используй нужную модель
            messages=[
                {"role": "system", "content": promt},
                {"role": "user", "content": message},
            ],
            temperature=0,
        )
        response_dict: Dict = json.loads(response.choices[0].message.content)
        print(response_dict)
