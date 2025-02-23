import random

from services.intercom_api_service import IntercomAPIService
import asyncio

intercom_client: IntercomAPIService = IntercomAPIService()


async def dialog_process():
    user_id: str = "6798a0c79645a8b3711b89d3"
    admin_id: str = "8028082"

    status, data = intercom_client.create_conversation(
        user_id=user_id, message="मेरी वेबसाइट में समस्या आ रही है।"
    )
    new_conversatin_id: str = data.get("conversation_id", "")
    intercom_client.attach_admin_to_conversation(
        admin_id=admin_id, conversation_id=new_conversatin_id
    )
    await asyncio.sleep(random.uniform(3, 5))
    status, data = await intercom_client.add_admin_note_to_conversation_async(
        conversation_id=new_conversatin_id, admin_id=admin_id, note="i will help you"
    )
    await asyncio.sleep(random.uniform(3, 5))

    status, data = await intercom_client.add_user_replied_to_conversation(
        conversation_id=new_conversatin_id,
        user_id=user_id,
        message="আমি পেমেন্ট করতে অসমর্থ।",
    )

    await asyncio.sleep(random.uniform(3, 5))
    status, data = await intercom_client.add_admin_note_to_conversation_async(
        conversation_id=new_conversatin_id,
        admin_id=admin_id,
        note="Can you describe the problem in more detail?",
    )


async def main():
    dialogs = [dialog_process() for _ in range(4)]

    await asyncio.gather(*dialogs)


asyncio.run(main())
