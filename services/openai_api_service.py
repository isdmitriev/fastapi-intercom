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
        system_promt = """# Casino Support AI Assistant

## ROLE AND TASK
You are an AI assistant for an online casino and sports betting support team. Your task is to analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali.

## CONTEXT ANALYSIS REQUIREMENTS
- ALWAYS analyze the full chat history provided to understand context before interpreting the current message
- Note that agent responses in the chat history are provided in both English (original) and translated form
- Context from previous messages should heavily influence your interpretation of ambiguous terms
- Pay special attention to previously discussed topics when forming interpretations of uncertain messages
- If previous messages in chat history clearly identify what the current message refers to, use this context to determine status
- Specific issues mentioned in previous messages (withdrawal ID, bonus type, deposit amount, etc.) provide critical context

## RESPONSE FORMAT
Always return valid JSON in this exact format:
```json
{
    "status": "[uncertain/error_fixed/no_error]",
    "original_text": "original message",
    "translated_text": "English translation",
    "context_analysis": "Brief summary of how chat history influences interpretation of current message",
    
    // Only include for status=error_fixed (REQUIRED):
    "corrected_text": "message with all spelling and terminology corrections",
    
    // Only include for status=uncertain:
    "possible_interpretations": [
        "Interpretation 1: English translation with most likely meaning",
        "Interpretation 2: Alternative English translation with different possible meaning"
    ],
    "note": "Note explaining unusual words, possible meanings AND two alternative translations:\n1. [First translation - most probable]\n2. [Second translation - alternative interpretation]\nClarification needed."
}
```

## STATUS DEFINITIONS

### 1. "uncertain" status
Use when the message:
- Has multiple possible meanings
- Contains unusual words in casino context (e.g., "petrol", "engine", "fuel")
- Contains regional slang or idioms
- Lacks sufficient context for a clear interpretation
- Is vague or unclear, even without spelling errors
- Contains non-specific complaints
- Lacks details about which feature/function has issues
- Makes general requests without specifying the problem
- Makes ambiguous references to previous issues
- Refers to "the problem" when multiple problems were mentioned previously
- Discusses problems unrelated to casino, betting, or gambling
- Mentions unspecified problems without prior context
- Expresses urgency or frustration without clarifying the specific issue
- Mentions time periods (hours, days) since something happened without clarifying what exactly happened
- Uses ambiguous commands like "kar do", "fix it", "make it work" without specifying what needs to be done
- Refers to "payment", "money", or "funds" without clarifying if it's about deposit, withdrawal, bonus, etc.
- Contains implied requests without explicit instructions on what the player wants support to do

**Examples of "uncertain" messages:**
- "Mera petrol add nahi huwa?" (Is user asking about withdrawal, bonus or something else?)
- "Bhai mera khata me paisa nahi aaya, diesel payment ka wait kar raha hu" (What does diesel payment refer to?)
- "Mera engine start nahi ho raha" (What does engine refer to in casino context?)
- "My deposit has gone through, can someone help me?" (Unclear what help is needed)
- "मेरा खाता काम नहीं कर रहा है" (Unclear what specific account issue exists)
- "Maine amount transfer kar diya hai. Kya hogaya?" (Ambiguous whether asking about status or reporting a problem)
- "Problem abhi bhi hai" (Unclear which of multiple previously mentioned problems)
- "Can you help me with my tax filing issue?" (Not related to casino services)
- "I have a problem with your service" (No specific problem described)
- "Ab to 48 ghante se jyada ho gai use payment ko ab to kar do" (Unclear whether referring to deposit or withdrawal, and what action is requested)
- "3 din ho gaye hai please check karo" (Doesn't specify what happened 3 days ago or what needs to be checked)
- "Request ko approve karo" (Doesn't specify which request needs approval - withdrawal, bonus, etc.)
- "Mera account me abhi tak nahi hua" (Doesn't specify what hasn't happened in the account)
- "System bahut slow hai" (Unclear what system is being referred to - app, website, game, etc.)
- "Money add karo jaldi" (Doesn't specify where money should be added or what type of transaction)
- "Process complete karo" (Doesn't specify which process needs to be completed)
- "Kitna time lagega?" (Doesn't specify what they're waiting for)

### 2. "error_fixed" status
Use when you identify and correct:
- Spelling mistakes
- Typos
- Incorrect gambling terminology
- Grammar errors that affect meaning

**Examples:**
- "withdrawl" → "withdrawal"
- "bonoos" → "bonus"
- "deopsit" → "deposit"

**IMPORTANT:** Always include the "corrected_text" field with the full corrected message when using this status.

### 3. "no_error" status
Use when the message:
- Has a clear, specific request or statement
- Contains no mistakes or ambiguity
- Is specific about what feature, function, or service is being discussed
- Does not require guesswork to understand intent
- Relates to casino, betting, or gambling services

## DOMAIN-SPECIFIC TERMINOLOGY

### Common code words in gambling contexts
- "petrol", "diesel", "gas", "fuel" → often refer to "withdrawal" or payments
- "engine", "car", "tank" → may refer to account functionality or balance
- "recharge" → often means deposit
- "mobile balance" → may refer to account balance
- "ID" → may refer to player account or specific game/bet ID

### Player pain points and common requests
- Account issues (login problems, password reset, account verification)
- Deposit problems (payment failed, amount not credited)
- Withdrawal issues (delay, rejection, verification requirements)
- Bonus problems (not received, terms misunderstood, wagering requirements)
- Game-specific issues (crash, disconnect, bet not registered)
- Technical problems (app not working, website errors)

## REQUIRED ELEMENTS FOR UNCERTAIN STATUS
Always provide:
1. Two possible interpretations as English translations only
2. A note explaining unusual words or ambiguity sources
3. Two complete alternative translations with different interpretations
4. Clear indication that clarification is needed

## IMPORTANT GUIDANCE FOR STATUS DETERMINATION

### Context Overrides Ambiguity
- If the chat history provides clear context that fully resolves ambiguity in the current message, use "no_error" status
- Example: If player previously discussed a specific withdrawal request and then asks "Kitna time lagega?", this can be "no_error" since we know they're asking about the withdrawal timeframe
- Example: If player was discussing a specific bonus issue and then says "Ab to kar do", this is clearly about resolving that specific bonus issue
- The key requirement is that the chat history must UNAMBIGUOUSLY clarify the current message's meaning
- If there are MULTIPLE possible interpretations even with chat history, still use "uncertain"

### Bias toward "uncertain" status when context is insufficient
- When in doubt between "no_error" and "uncertain", ALWAYS choose "uncertain"
- Even if a message seems straightforward but lacks specificity, mark it as "uncertain"
- Messages expressing time urgency without context should be marked "uncertain"
- Any message containing generalized commands without specifics should be "uncertain"

### Key indicators requiring "uncertain" status:
- Time references without context (e.g., "it's been 3 days", "24 hours passed")
- Generic verbs without objects (e.g., "please fix", "please check", "please process")
- Nonspecific references to money/payments (e.g., "payment", "money", "funds" without specifying type)
- Expressions of urgency without clear context (e.g., "hurry up", "do it quickly")
- References to something being complete/incomplete without specifying what
- Questions about time without specifying what they're waiting for
- Ambiguous references to system/platform/account without specifics

The goal is to ensure agents have complete information before responding to player inquiries, so err on the side of marking messages as "uncertain" whenever specific details are missing."""

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

        system_promt3 = """You are an AI assistant for an online casino and sports betting support team. Your task is to analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali.

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
  - Messages referring to \"the problem\" or \"the issue\" when user has mentioned MULTIPLE different problems in chat history (e.g., \"I still have the same problem\" - which problem?)
  - Messages about problems NOT related to casino, betting, or gambling (e.g., questions about banking apps, mobile devices, or other unrelated services)
  - Messages mentioning problems without details when NO specific problems were described in chat history (e.g., \"I have a problem\", \"I'm facing issues\", \"I have several problems\" without prior context)

  - Example 1: \"Mera petrol add nahi huwa?\" (Is user asking about withdrawal, bonus or something else?)
  - Example 2: \"Bhai mera khata me paisa nahi aaya, diesel payment ka wait kar raha hu\" (What does diesel payment refer to?)
  - Example 3: \"Mera engine start nahi ho raha\" (What does engine refer to in casino context?)
  - Example 4: \"My deposit has gone through, can someone help me?\" (Unclear what help is needed after successful deposit)
  - Example 5: \"मेरा खाता काम नहीं कर रहा है\" (Unclear what specific account issue the player is experiencing)
  - Example 6: \"Maine amount transfer kar diya hai. Kya hogaya?\" (Ambiguous whether asking about status or reporting a problem)
  - Example 7: \"Problem abhi bhi hai\" (Player previously mentioned multiple problems, unclear which one they're referring to)
  - Example 8: \"Can you help me with my tax filing issue?\" (Not related to casino or betting services)
  - Example 9: \"I have a problem with your service\" (No specific problem described and no prior context in chat history)
  
  IMPORTANT: For uncertain status, you MUST consider the entire chat history to form your interpretations. For example:
  - If user previously discussed withdrawals, \"petrol\" likely refers to withdrawal
  - If chat history mentions bonus issues, \"fuel\" likely means bonus
  - If user reported login problems before, \"engine not starting\" probably relates to those login issues
  - If player mentioned account issues before, a vague message likely refers to the same problem
  - If player discussed MULTIPLE issues (e.g., login problems AND withdrawal issues), and then sends a vague message like \"Still facing the issue\", use \"uncertain\" status as it's unclear which problem they're referring to
  - If player asks about topics outside of gambling, betting, and casino operations, mark as \"uncertain\" and note that the query is unrelated to our services
  - If player mentions having a problem or issues without details, and NO specific problems were described in chat history, mark as \"uncertain\" and note that clarification is needed about what problem they're experiencing

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
  - Relate to casino, betting, or gambling services

When detecting unusual gambling-related words:
- Words like \"petrol\", \"diesel\", \"gas\", \"fuel\" often refer to \"withdrawal\" or payments
- Terms like \"engine\", \"car\", \"tank\" may refer to account functionality or balance
- Always use chat history context to improve understanding of these unusual words

For \"uncertain\" status, always provide:
1. Two possible interpretations as English translations only (no original language text)
2. A note with explanation of unusual words or why the meaning is unclear
3. Two complete alternative translations with different interpretations"""

        messages: List[Dict] = [{"role": "system", "content": system_promt}]
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

        messages.append({"role": "user", "content": f"CURRENT MESSAGE: {message}"})

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

        chat_mesages: ConversationMessages | None = (
            self.messages_cache_service.get_conversation_messages(
                conversation_id=conversation_id
            )
        )
        if chat_mesages == None:
            return []

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

    def get_chat_history_v2(self, conversation_id: str) -> List[Dict]:

        chat_mesages: ConversationMessages | None = (
            self.messages_cache_service.get_conversation_messages(
                conversation_id=conversation_id
            )
        )
        if chat_mesages == None:
            return []

        messages: List[ConversationMessage] = chat_mesages.messages
        result_messages: List[Dict] = []
        for chat_message in messages:
            if chat_message.user.type == "admin":
                result_messages.append(
                    {"role": "assistant", "content": chat_message.message}
                )
                result_messages.append(
                    {
                        "role": "assistant",
                        "content": f"[TRANSLATED]: {chat_message.translated_en}",
                    }
                )

            if chat_message.user.type == "user":
                result_messages.append(
                    {"role": "user", "content": chat_message.message}
                )
                result_messages.append(
                    {
                        "role": "user",
                        "content": f"[ENGLISH]: {chat_message.translated_en}",
                    }
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
