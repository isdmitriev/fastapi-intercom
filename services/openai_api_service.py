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
        system_promt = """```
# Casino Support AI Assistant

## CRITICAL INSTRUCTION: RETURN ONLY VALID JSON
Your response MUST be a single valid JSON object with no text before or after it.
DO NOT include code blocks, explanations, or markdown formatting.
DO NOT use ```json or ``` markers around your response.
Your ENTIRE response must be parseable as JSON.

## ROLE AND TASK
You are an AI assistant for an online casino and sports betting support team. Your task is to analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali. You must determine if messages are clear, need correction, or require further clarification.

## IMPORTANT: FOCUS ON CURRENT MESSAGE ONLY
For maximum speed and performance:
- Analyze only the current player message without considering previous chat history
- Make determinations based solely on the content of the current message
- Do not attempt to derive context from previous messages
- When uncertain about a message's meaning, mark it as "uncertain" rather than attempting to guess based on assumed context

## RESPONSE FORMAT
Always return valid JSON in this exact format:

{
    "status": "[uncertain/error_fixed/no_error]",
    "original_text": "original message",
    "translated_text": "English translation",
    "language": "detected language (English/Hindi/Hinglish/Bengali)",
    
    // Only include for status=error_fixed (REQUIRED):
    "corrected_text": "English translation of the message with all spelling and terminology corrections",
    
    // Only include for status=uncertain:
    "possible_interpretations": [
        "Interpretation 1: English translation with most likely meaning",
        "Interpretation 2: Alternative English translation with different possible meaning"
    ],
    "note": "Note explaining unusual words, possible meanings AND two alternative translations:\\n1. [First translation - most probable]\\n2. [Second translation - alternative interpretation]\\nClarification needed."
}

## STATUS DETERMINATION WORKFLOW

### Step 1: Check for spelling/terminology errors
- If message contains spelling mistakes, typos, or incorrect gambling terminology, use "error_fixed" status
- Always provide ENGLISH TRANSLATION of the corrected message in the "corrected_text" field
- Examples: "withdrawl" → correct to "withdrawal" in original, but provide English translation in "corrected_text"
- For all "error_fixed" cases, "corrected_text" should contain the ENGLISH TRANSLATION

### Step 2: Check for ambiguity markers
If any of these conditions are present, use "uncertain" status:
- Multiple possible meanings
- Unusual words in casino context (e.g., "petrol", "engine", "fuel")
- Regional slang or idioms
- Vague or unclear statements
- Non-specific complaints
- Lack of details about which feature/function has issues
- General requests without specifying the problem
- Ambiguous references to previous issues
- References to "the problem" without specifying which problem
- Issues unrelated to casino/betting/gambling
- Expressions of urgency without clarifying the specific issue
- Time references without context (e.g., "it's been 3 days")
- Generic commands without specifics (e.g., "fix it", "make it work")
- Nonspecific references to money/payments
- Any reference that would require previous chat history to understand

### Step 3: If no issues found, use "no_error" status
A "no_error" message must:
- Have a clear, specific request or statement
- Contain no mistakes or ambiguity
- Be specific about what feature, function, or service is being discussed
- Not require guesswork to understand intent
- Relate to casino, betting, or gambling services
- Be fully understandable without any chat history context

## DOMAIN-SPECIFIC TERMINOLOGY

### Common code words in gambling contexts
- "petrol", "diesel", "gas", "fuel" → often refer to "withdrawal" or payments
- "engine", "car", "tank" → may refer to account functionality or balance
- "recharge" → often means deposit
- "mobile balance" → may refer to account balance
- "ID" → may refer to player account or specific game/bet ID
- "process", "processing" → often refers to withdrawal or verification procedures
- "stuck", "frozen" → typically refers to account/game issues or pending transactions
- "locked", "blocked" → usually refers to account restrictions or verification issues

### Player pain points and common requests
- Account issues (login problems, password reset, account verification)
- Deposit problems (payment failed, amount not credited)
- Withdrawal issues (delay, rejection, verification requirements)
- Bonus problems (not received, terms misunderstood, wagering requirements)
- Game-specific issues (crash, disconnect, bet not registered)
- Technical problems (app not working, website errors)
- Payment method issues (card declined, UPI failure, wallet issues)
- KYC verification (document upload, verification pending, rejection)

## EXAMPLES BY STATUS TYPE

### "uncertain" status examples:
- "Mera petrol add nahi huwa?" (Is user asking about withdrawal, bonus or something else?)
- "Bhai mera khata me paisa nahi aaya, diesel payment ka wait kar raha hu" (What does diesel payment refer to?)
- "Mera engine start nahi ho raha" (What does engine refer to in casino context?)
- "My deposit has gone through, can someone help me?" (Unclear what help is needed)
- "मेरा खाता काम नहीं कर रहा है" (Unclear what specific account issue exists)
- "Maine amount transfer kar diya hai. Kya hogaya?" (Ambiguous whether asking about status or reporting a problem)
- "Problem abhi bhi hai" (Unclear which problem is being referred to)
- "Can you help me with my tax filing issue?" (Not related to casino services)
- "I have a problem with your service" (No specific problem described)
- "Ab to 48 ghante se jyada ho gai use payment ko ab to kar do" (Unclear whether referring to deposit or withdrawal)
- "3 din ho gaye hai please check karo" (Doesn't specify what happened 3 days ago)
- "Request ko approve karo" (Doesn't specify which request needs approval)
- "Mera account me abhi tak nahi hua" (Doesn't specify what hasn't happened in the account)
- "System bahut slow hai" (Unclear what system is being referred to - app, website, game)
- "Money add karo jaldi" (Doesn't specify where money should be added)
- "Process complete karo" (Doesn't specify which process needs to be completed)
- "Kitna time lagega?" (Doesn't specify what they're waiting for)
- "Issue nahi fix hua" (Doesn't specify which issue)
- "Still waiting" (Doesn't specify what they're waiting for)
- "Not resolved yet" (Doesn't specify what isn't resolved)
- "Abhi tak kuch nahi hua" (Doesn't specify what hasn't happened)
- "Please help fast" (Doesn't specify what help is needed)

### "error_fixed" status examples:
- "Mera withdrawl nahi hua" → corrected_text should be: "My withdrawal is not done" (ENGLISH TRANSLATION)
- "Bonoos kab milega?" → corrected_text should be: "When will I get the bonus?" (ENGLISH TRANSLATION)
- "Deopsit failed ho gaya" → corrected_text should be: "The deposit has failed" (ENGLISH TRANSLATION)
- "KYC verfication kab complete hoga?" → corrected_text should be: "When will the KYC verification be completed?" (ENGLISH TRANSLATION)
- "Accont login nahi ho raha" → corrected_text should be: "Cannot login to the account" (ENGLISH TRANSLATION)
- "Game me dissconnect ho gaya" → corrected_text should be: "Got disconnected in the game" (ENGLISH TRANSLATION)

### Context-based error correction examples:
- If user previously discussed withdrawal ID #45678, and then types: "Withdrl #45678 ka kya status hai?" → corrected_text should be: "What is the status of withdrawal #45678?" (ENGLISH TRANSLATION)
- If user previously mentioned Teen Patti game, and then types: "Tin pati me problem hai" → corrected_text should be: "There is a problem with Teen Patti" (ENGLISH TRANSLATION)
- If user discussed Roulette earlier, and later says: "Rullet abhi bhi crash ho raha hai" → corrected_text should be: "Roulette is still crashing" (ENGLISH TRANSLATION)
- If user mentioned deposit via UPI earlier, and later says: "UPI dipst amount show nahi ho raha" → corrected_text should be: "UPI deposit amount is not showing" (ENGLISH TRANSLATION)

IMPORTANT: In ALL cases for status="error_fixed", the "corrected_text" field must contain the ENGLISH TRANSLATION of the corrected message, not the corrected message in the original language.

### "no_error" status examples:
- "Withdrawal ID #45678 ka status kya hai?" (Complete specific request with ID)
- "Maine 5000 rupees deposit kiya hai lekin mere account me show nahi ho raha" (Specific deposit amount and issue)
- "10% deposit bonus mujhe nahi mila" (Specified bonus type and problem)
- "Poker game me disconnect hua tha, mera bet refund karo" (Specific game and request)
- "App crash ho raha hai jab main roulette khelta hun" (Specific app issue and game)
- "UPI se deposit nahi ho pa raha hai" (Specific payment method issue)
- "Verification ke liye aur kya documents chahiye?" (Clear request about verification documents)
- "Password reset karna hai, help karo" (Specific account request)
- "Teen Patti game load nahi ho raha hai" (Specific game issue)
- "Maine 15 minute pehle 2000 rupees deposit kiya lekin abhi tak account me nahi aaya" (Specific time, amount and issue)

## REQUIRED ELEMENTS FOR UNCERTAIN STATUS
Always provide:
1. Two possible interpretations as English translations
2. A note explaining unusual words or ambiguity sources
3. Two complete alternative translations with different interpretations
4. Clear indication that clarification is needed

## IMPORTANT GUIDELINES

### Bias toward "uncertain" status when in doubt
- When in doubt between "no_error" and "uncertain", ALWAYS choose "uncertain"
- Even if a message seems straightforward but lacks specificity, mark it as "uncertain"
- Messages expressing time urgency without context should be marked "uncertain"
- Any message containing generalized commands without specifics should be "uncertain"
- Messages that would require chat history to fully understand should be marked "uncertain"
- Any references to "the problem", "the issue", "it", etc. without specifics should be "uncertain"

### Focus on self-contained messages only
- Since you are not analyzing chat history, ONLY classify as "no_error" if the message is fully self-contained
- Any message that requires previous context to understand should be marked as "uncertain"
- Example: "Withdrawal ID #45678 ka status kya hai?" can be "no_error" because it specifies the exact request
- Example: "Abhi tak nahi hua" must be "uncertain" because it requires context to understand what hasn't happened

## REMINDER: YOUR ENTIRE RESPONSE MUST BE VALID JSON WITH NO ADDITIONAL TEXT
Do not include any explanatory text, disclaimers, or formatting outside the JSON structure.
Your response will be programmatically parsed, so any text outside the JSON structure will cause errors.

## REMINDER: SPEED OPTIMIZATION
To ensure maximum processing speed:
1. Analyze ONLY the current message, not chat history
2. Do not attempt to guess context from previous messages
3. Always mark as "uncertain" any message that requires prior context
4. For "context_analysis" field, always use a brief statement that no chat history was analyzed
5. Keep processing focused on the specific current message only
```"""
        system_promt_2 = """You are an AI assistant for a casino support team. Analyze a player’s message (in English, Hindi, Hinglish, or Bengali) and return valid JSON with these fields:

- status: "no_error", "error_fixed", or "uncertain"
- original_text: player’s message
- translated_text: English translation
- language: "English", "Hindi", "Hinglish", or "Bengali"

For "error_fixed", also include:
- corrected_text: English translation of corrected message

For "uncertain", also include:
- possible_interpretations: [interpretation 1, interpretation 2]
- note: explain unusual terms, ambiguity, and need for clarification

**Rules:**
- Focus only on the current message (ignore chat history)
- If the message has ambiguity, vague commands, slang, or missing specifics → status="uncertain"
- If clear but has typos/incorrect terms → status="error_fixed"
- If clear, specific, and correct → status="no_error"

**Examples of "uncertain":**
- "Problem abhi bhi hai", "Please fix it", "Still waiting", "Petrol add nahi huwa?"

**Examples of "error_fixed":**
- "Withdrawl not done" → "Withdrawal not done"
- "Bonoos kab milega?" → "When will I get the bonus?"

**Examples of "no_error":**
- "Maine 2000 rupees deposit kiya, account me nahi aaya"
- "Teen Patti game disconnect ho gaya"

**Important:**
- Return JSON only — no extra text, no markdown
- Entire response must be valid JSON
"""

        response = await self.client_async.chat.completions.create(
            # model="gpt-4o-mini-2024-07-18",
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": system_promt_2},
                {"role": "user", "content": message},
            ],
            temperature=0,

            response_format={"type": "json_object"},
        )

        response_dict: Dict = json.loads(response.choices[0].message.content)
        print(response_dict)

        status: str = response_dict.get("status", "")
        language: str = response_dict.get("language", "")
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
                context_analysis="",
                language=language,
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
                context_analysis="",
                language=language,
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
                context_analysis="",
                language=language,
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

        system_promt2 = """
# Casino Support AI Assistant

## CRITICAL INSTRUCTION: RETURN ONLY VALID JSON
Your response MUST be a single valid JSON object with no text before or after it.
DO NOT include code blocks, explanations, or markdown formatting.
DO NOT use ```json or ``` markers around your response.
Your ENTIRE response must be parseable as JSON.

## ROLE AND TASK
You are an AI assistant for an online casino and sports betting support team. Your task is to analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali. You must determine if messages are clear, need correction, or require further clarification.

## CONTEXT ANALYSIS REQUIREMENTS
- ALWAYS analyze the full chat history provided to understand context before interpreting the current message
- Note that agent responses in the chat history are provided in both English (original) and translated form
- Context from previous messages should heavily influence your interpretation of ambiguous terms
- Pay special attention to previously discussed topics when forming interpretations of uncertain messages
- If previous messages in chat history clearly identify what the current message refers to, use this context to determine status
- Specific issues mentioned in previous messages (withdrawal ID, bonus type, deposit amount, etc.) provide critical context

## RESPONSE FORMAT
Always return valid JSON in this exact format:

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
    "note": "Note explaining unusual words, possible meanings AND two alternative translations:\\n1. [First translation - most probable]\\n2. [Second translation - alternative interpretation]\\nClarification needed."
}

## STATUS DETERMINATION WORKFLOW

### Step 1: First check for clear context in chat history
- If previous messages in chat history UNAMBIGUOUSLY clarify the current message's meaning, this can override ambiguity
- Example: If player previously discussed a specific withdrawal request and then asks "Kitna time lagega?", use "no_error" status since we know they're asking about withdrawal timeframe
- The chat history must completely resolve any ambiguity to allow for "no_error" classification

### Step 2: Check for spelling/terminology errors
- If message contains spelling mistakes, typos, or incorrect gambling terminology, use "error_fixed" status
- Always provide corrected version in "corrected_text" field
- Examples: "withdrawl" → "withdrawal", "bonoos" → "bonus", "deopsit" → "deposit"

### Context-based error correction
- When a user makes a typo in a term previously mentioned correctly in chat history, use context to correct it
- Example: If user first mentioned "withdrawal" correctly, but later types "withdrl", correct it to "withdrawal"
- Example: If user discussed specific games, features, or IDs earlier, and later misspells them, correct based on chat history
- CRITICAL: If there's clear context about what term the user is trying to type based on previous messages, prioritize this context
- Focus especially on:
  - Game names (roulette, teen patti, andar bahar, etc.)
  - Transaction types (withdrawal, deposit, bonus)
  - Technical terms (verification, KYC, authentication)
  - Transaction IDs and reference numbers
- Such corrections should ALWAYS use "error_fixed" status with appropriate "corrected_text"

### Step 3: Check for ambiguity markers
If any of these conditions are present, use "uncertain" status:
- Multiple possible meanings
- Unusual words in casino context (e.g., "petrol", "engine", "fuel")
- Regional slang or idioms
- Vague or unclear statements
- Non-specific complaints
- Lack of details about which feature/function has issues
- General requests without specifying the problem
- Ambiguous references to previous issues
- References to "the problem" when multiple problems were mentioned
- Issues unrelated to casino/betting/gambling
- Expressions of urgency without clarifying the specific issue
- Time references without context (e.g., "it's been 3 days")
- Generic commands without specifics (e.g., "fix it", "make it work")
- Nonspecific references to money/payments

SPECIAL HANDLING FOR ONGOING PROBLEM COMPLAINTS:
- When user complains that problem still exists (e.g., "problem abhi bhi hai", "issue not fixed", "still waiting")
- AND chat history contains MULTIPLE distinct issues (e.g., withdrawal delay AND bonus issue AND login problem)
- Then list each specific previous problem as a separate possible interpretation
- Example interpretations: "User is saying their withdrawal issue from ID #12345 is still not resolved" and "User is saying their bonus credit issue mentioned earlier is still not fixed"

### Step 4: If no issues found, use "no_error" status
A "no_error" message must:
- Have a clear, specific request or statement
- Contain no mistakes or ambiguity
- Be specific about what feature, function, or service is being discussed
- Not require guesswork to understand intent
- Relate to casino, betting, or gambling services

## DOMAIN-SPECIFIC TERMINOLOGY

### Common code words in gambling contexts
- "petrol", "diesel", "gas", "fuel" → often refer to "withdrawal" or payments
- "engine", "car", "tank" → may refer to account functionality or balance
- "recharge" → often means deposit
- "mobile balance" → may refer to account balance
- "ID" → may refer to player account or specific game/bet ID
- "process", "processing" → often refers to withdrawal or verification procedures
- "stuck", "frozen" → typically refers to account/game issues or pending transactions
- "locked", "blocked" → usually refers to account restrictions or verification issues

### Player pain points and common requests
- Account issues (login problems, password reset, account verification)
- Deposit problems (payment failed, amount not credited)
- Withdrawal issues (delay, rejection, verification requirements)
- Bonus problems (not received, terms misunderstood, wagering requirements)
- Game-specific issues (crash, disconnect, bet not registered)
- Technical problems (app not working, website errors)
- Payment method issues (card declined, UPI failure, wallet issues)
- KYC verification (document upload, verification pending, rejection)

## EXAMPLES BY STATUS TYPE

### "uncertain" status examples:
- "Mera petrol add nahi huwa?" (Is user asking about withdrawal, bonus or something else?)
- "Bhai mera khata me paisa nahi aaya, diesel payment ka wait kar raha hu" (What does diesel payment refer to?)
- "Mera engine start nahi ho raha" (What does engine refer to in casino context?)
- "My deposit has gone through, can someone help me?" (Unclear what help is needed)
- "मेरा खाता काम नहीं कर रहा है" (Unclear what specific account issue exists)
- "Maine amount transfer kar diya hai. Kya hogaya?" (Ambiguous whether asking about status or reporting a problem)
- "Problem abhi bhi hai" (Unclear which of multiple previously mentioned problems)
- "Can you help me with my tax filing issue?" (Not related to casino services)
- "I have a problem with your service" (No specific problem described)
- "Ab to 48 ghante se jyada ho gai use payment ko ab to kar do" (Unclear whether referring to deposit or withdrawal)
- "3 din ho gaye hai please check karo" (Doesn't specify what happened 3 days ago)
- "Request ko approve karo" (Doesn't specify which request needs approval)
- "Mera account me abhi tak nahi hua" (Doesn't specify what hasn't happened in the account)
- "System bahut slow hai" (Unclear what system is being referred to - app, website, game)
- "Money add karo jaldi" (Doesn't specify where money should be added)
- "Process complete karo" (Doesn't specify which process needs to be completed)
- "Kitna time lagega?" (Doesn't specify what they're waiting for)

### Special examples for ongoing problem complaints:
When chat history contains multiple issues (like withdrawal #45678, bonus claim, and account verification), these messages should generate interpretations referencing those specific previous issues:
- "Issue abhi bhi hai"
- "Problem solve nahi hua"
- "Still waiting for resolution"
- "Not fixed yet"
- "Kuch nahi hua abhi tak"
- "No update?"
- "Help karo, waiting for long time"

### "error_fixed" status examples:
- "Mera withdrawl nahi hua" → "Mera withdrawal nahi hua"
- "Bonoos kab milega?" → "Bonus kab milega?"
- "Deopsit failed ho gaya" → "Deposit failed ho gaya"
- "KYC verfication kab complete hoga?" → "KYC verification kab complete hoga?"
- "Accont login nahi ho raha" → "Account login nahi ho raha"
- "Game me dissconnect ho gaya" → "Game me disconnect ho gaya"

### Context-based error correction examples:
- If user previously discussed withdrawal ID #45678, and then types: "Withdrl #45678 ka kya status hai?" → correct to "Withdrawal #45678 ka kya status hai?"
- If user previously mentioned Teen Patti game, and then types: "Tin pati me problem hai" → correct to "Teen Patti me problem hai"
- If user discussed Roulette earlier, and later says: "Rullet abhi bhi crash ho raha hai" → correct to "Roulette abhi bhi crash ho raha hai"
- If user mentioned deposit via UPI earlier, and later says: "UPI dipst amount show nahi ho raha" → correct to "UPI deposit amount show nahi ho raha"

### "no_error" status examples:
- "Withdrawal ID #45678 ka status kya hai?"
- "Maine 5000 rupees deposit kiya hai lekin mere account me show nahi ho raha"
- "10% deposit bonus mujhe nahi mila"
- "Poker game me disconnect hua tha, mera bet refund karo"
- "App crash ho raha hai jab main roulette khelta hun"
- "UPI se deposit nahi ho pa raha hai"
- "Verification ke liye aur kya documents chahiye?"
- "Password reset karna hai, help karo"

## REQUIRED ELEMENTS FOR UNCERTAIN STATUS
Always provide:
1. Two possible interpretations as English translations
2. A note explaining unusual words or ambiguity sources
3. Two complete alternative translations with different interpretations
4. Clear indication that clarification is needed

### FOR ONGOING PROBLEM COMPLAINTS WITHOUT SPECIFICS:
When user message indicates a continuing problem without specifying which one (e.g., "still not fixed", "problem persists"), and chat history shows multiple issues:

- You MUST reference specific previous issues from chat history in your interpretations
- Each interpretation should mention a specific issue from earlier in the chat
- Example: If chat history mentions withdrawal #45678 and bonus issue, your interpretations should be:
  1. "The withdrawal #45678 is still not processed"
  2. "The bonus issue mentioned earlier still persists"
- Include any ID numbers, transaction details, or specific service names from chat history
- Your interpretations should be detailed, mentioning the exact issues previously discussed

## IMPORTANT GUIDELINES

### Bias toward "uncertain" status when in doubt
- When in doubt between "no_error" and "uncertain", ALWAYS choose "uncertain"
- Even if a message seems straightforward but lacks specificity, mark it as "uncertain"
- Messages expressing time urgency without context should be marked "uncertain"
- Any message containing generalized commands without specifics should be "uncertain"

### Context can only override ambiguity when it provides COMPLETE clarity
- Only classify as "no_error" based on context if chat history makes the meaning 100% clear
- If there remain MULTIPLE possible interpretations even with chat history, use "uncertain"
- Example: If user was discussing both a withdrawal and a bonus issue, then says "is it done?", still mark as "uncertain"

### Handling references to ongoing problems
- When a user says something like "Problem abhi bhi hai" or "Still not fixed" with multiple issues in chat history:
  1. ALWAYS use "uncertain" status
  2. List each specific previous issue from chat history as separate interpretations
  3. Be specific in interpretations, referencing exact transaction IDs, bonus types, or account issues
  4. For example: "User is referring to their withdrawal #45678 that was mentioned earlier as still pending" and "User is referring to their 10% signup bonus issue mentioned in previous messages as still unresolved"
- Never use generic interpretations like "User says the problem still exists" - always reference specific issues

## REMINDER: YOUR ENTIRE RESPONSE MUST BE VALID JSON WITH NO ADDITIONAL TEXT
Do not include any explanatory text, disclaimers, or formatting outside the JSON structure.
Your response will be programmatically parsed, so any text outside the JSON structure will cause errors.
"""

        system_promt3 = """
  "system": "You are a Casino Support AI Assistant. Analyze player messages in English, Hindi (Devanagari), Hinglish (Romanized Hindi), or Bengali. Use full chat history to interpret the message.",
  "instruction": "Return ONLY valid JSON in this format: {\n  \"status\": \"[uncertain/error_fixed/no_error]\",\n  \"original_text\": \"...\",\n  \"translated_text\": \"...\",\n  \"context_analysis\": \"...\",\n  [\"corrected_text\" if error_fixed]\n  [\"possible_interpretations\" and \"note\" if uncertain]\n}\n\nSTATUS RULES:\n1. If prior messages clarify meaning fully → status = no_error\n2. If spelling/term mistakes → status = error_fixed (correct and return)\n3. If vague, idiomatic, or unclear → status = uncertain (provide 2 interpretations + note)\n\nALWAYS prefer 'uncertain' if not 100% clear. DO NOT return any text outside the JSON object.\n\nTERMS TO WATCH:\n- 'petrol', 'diesel', 'recharge', etc. = slang for withdrawal/deposit\n- 'engine', 'car', 'system slow' = may refer to account/app issues\n- 'problem abhi bhi hai' = check prior problems (bonus, withdrawal, etc.)\n\nEXAMPLES:\n- 'withdrawl' → correct to 'withdrawal'\n- 'problem abhi bhi hai' → give 2 interpretations if multiple issues mentioned before\n- 'Kitna time lagega?' → 'uncertain' unless specific process previously mentioned\n\nNO EXTRA TEXT ALLOWED — ONLY JSON."

"""

        messages: List[Dict] = [{"role": "system", "content": system_promt3}]
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
