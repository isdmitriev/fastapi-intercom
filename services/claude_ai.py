from anthropic import AsyncAnthropic
import os
from dotenv import load_dotenv
import json
from typing import Dict, List
from models.models import UserMessage
from services.redis_cache_service import MessagesCache
from models.models import ConversationMessages, ConversationMessage

load_dotenv()


class ClaudeService:
    def __init__(self, messages_cache_service: MessagesCache):
        self.client = AsyncAnthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        self.messages_cache_service = messages_cache_service

    async def analyze_message_with_correction(self, message: str, conversation_id: str):
        system_promt = """# Casino Support AI Assistant

## CRITICAL INSTRUCTION: RETURN ONLY VALID JSON
Your response MUST be a single valid JSON object with no text before or after it.
DO NOT include code blocks, explanations, or markdown formatting.
DO NOT use ```json or ``` markers around your response.
Your ENTIRE response must be parseable as JSON.

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

The goal is to ensure agents have complete information before responding to player inquiries, so err on the side of marking messages as "uncertain" whenever specific details are missing.

## REMINDER: YOUR ENTIRE RESPONSE MUST BE VALID JSON WITH NO ADDITIONAL TEXT
Do not include any explanatory text, disclaimers, or formatting outside the JSON structure.
Your response will be programmatically parsed, so any text outside the JSON structure will cause errors."""

        try:
            messages: List[Dict] = []
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

            response = await self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1024,
                system=system_promt,

                messages=[
                    {"role": 'user', "content": f"CURRENT MESSAGE: {message}"}],
            )

            response_dict: Dict = json.loads(response.content[0].text)

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
