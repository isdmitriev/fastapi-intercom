from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from di.di_container import Container
from services.web_hook_processor import WebHookProcessor
from fastapi.encoders import jsonable_encoder

router = APIRouter()


@router.post("/canvas")
async def canvas_handler(request: Request):
    data = await request.json()
    conversation_id = data.get("conversation", {}).get("id", "unknown")

    response = {
        "canvas": {
            "content": {
                "components": [
                    {
                        "type": "button",
                        "id": "send_message",
                        "label": "send message for user",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {"type": "text", "text": "Conversation Language:"},
                    {"type": "text", "text": "Conversation status: stoped"},
                    {
                        "type": "button",
                        "id": "Hinglish",
                        "label": "Force Hinglish",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {
                        "type": "button",
                        "id": "Hindi",
                        "label": "Force Hindi",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {
                        "type": "button",
                        "id": "Bengali",
                        "label": "Force Bengali",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {
                        "type": "button",
                        "id": "!stop",
                        "label": "stop translator service",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                ]
            }
        }
    }

    return JSONResponse(content=response, media_type="application/json")


@router.post("/canvas/action")
async def handle_canvas_action(request: Request):
    conv_language: str = ""
    conv_status: str = "stoped"
    data = await request.json()
    hook_processor: WebHookProcessor = Container.web_hook_processor()

    conversation_id = data.get("conversation", {}).get("id")

    # Получаем ID нажатой кнопки
    clicked_component_id = data.get("component_id")
    components = data.get("current_canvas", {}).get("content", {}).get("components", [])
    label = None
    for component in components:
        if component.get("id") == clicked_component_id:
            label = component.get("label")
            break

    # Логирование или внутренняя логика
    print(
        f"[ACTION] Button clicked: ID='{clicked_component_id}', Label='{label}', Conversation ID={conversation_id}"
    )

    if (
            clicked_component_id == "Hinglish"
            or clicked_component_id == "Hindi"
            or clicked_component_id == "Bengali"
    ):
        conv_language = clicked_component_id
        conv_status = "started"
        last_message: str = (
            hook_processor.messages_cache_service.get_conversation_last_message(
                conversation_id=conversation_id
            )
        )
        hook_processor.messages_cache_service.set_conversation_language(
            conversation_id=conversation_id, language=clicked_component_id
        )
        hook_processor.messages_cache_service.set_conversation_status(
            conversation_d=conversation_id, status="started"
        )

        await hook_processor.start_translation_service(
            conversation_id=conversation_id, message=last_message
        )
    elif clicked_component_id == "!stop":
        conv_status = "stoped"
        conv_language = hook_processor.messages_cache_service.get_conversation_language(
            conversation_id=conversation_id
        )
        hook_processor.messages_cache_service.set_conversation_status(
            conversation_d=conversation_id, status="stoped"
        )
    elif clicked_component_id == "send_message":
        response_form = {
            "canvas": {
                "content": {
                    "components": [
                        {"type": "text", "text": "write message for user"},
                        {
                            "type": "input",
                            "id": "admin_message",
                            "label": "message for user",
                            "placeholder": "message",
                        },
                        {
                            "type": "single-select",
                            "id": "language_choice",
                            "label": "chose user language",
                            "options": [
                                {
                                    "type": "option",
                                    "id": "Hinglish",
                                    "text": "Hinglish",
                                },
                                {"type": "option", "id": "Hindi", "text": "Hindi"},
                                {"type": "option", "id": "Bengali", "text": "Bengali"},
                            ],
                        },
                        {
                            "type": "button",
                            "id": "submit_form",
                            "label": "Submit",
                            "style": "primary",
                            "action": {"type": "submit"},
                            "metadata": {"conversation_id": conversation_id},
                        },
                        {
                            "type": "button",
                            "id": "back",
                            "label": "back",
                            "style": "primary",
                            "action": {"type": "submit"},
                            "metadata": {"conversation_id": conversation_id},
                        },
                    ]
                }
            }
        }

        return JSONResponse(content=response_form, media_type="application/json")
    elif clicked_component_id == "submit_form":
        return await handle_admin_message(data)
    elif clicked_component_id == "back":
        conv_status = hook_processor.messages_cache_service.get_conversation_status(
            conversation_id=conversation_id
        )
        conv_language = hook_processor.messages_cache_service.get_conversation_language(
            conversation_id=conversation_id
        )
        response = {
            "canvas": {
                "content": {
                    "components": [
                        {
                            "type": "button",
                            "id": "send_message",
                            "label": "send message for user",
                            "style": "primary",
                            "action": {"type": "submit"},
                            "metadata": {"conversation_id": conversation_id},
                        },
                        {
                            "type": "text",
                            "text": f"Conversation Language:{conv_language}",
                        },
                        {"type": "text", "text": f"Conversation status:{conv_status}"},
                        {
                            "type": "button",
                            "id": "Hinglish",
                            "label": "Force Hinglish",
                            "style": "primary",
                            "action": {"type": "submit"},
                            "metadata": {"conversation_id": conversation_id},
                        },
                        {
                            "type": "button",
                            "id": "Hindi",
                            "label": "Force Hindi",
                            "style": "primary",
                            "action": {"type": "submit"},
                            "metadata": {"conversation_id": conversation_id},
                        },
                        {
                            "type": "button",
                            "id": "Bengali",
                            "label": "Force Bengali",
                            "style": "primary",
                            "action": {"type": "submit"},
                            "metadata": {"conversation_id": conversation_id},
                        },
                        {
                            "type": "button",
                            "id": "!stop",
                            "label": "stop translator service",
                            "style": "primary",
                            "action": {"type": "submit"},
                            "metadata": {"conversation_id": conversation_id},
                        },
                    ]
                }
            }
        }
        return JSONResponse(content=response, media_type="application/json")

    # Получаем label кнопки по ID

    response = {
        "canvas": {
            "content": {
                "components": [
                    {
                        "type": "button",
                        "id": "send_message",
                        "label": "send message for user",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {"type": "text", "text": f"Conversation Language:{conv_language}"},
                    {"type": "text", "text": f"Conversation status:{conv_status}"},
                    {
                        "type": "button",
                        "id": "Hinglish",
                        "label": "Force Hinglish",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {
                        "type": "button",
                        "id": "Hindi",
                        "label": "Force Hindi",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {
                        "type": "button",
                        "id": "Bengali",
                        "label": "Force Bengali",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {
                        "type": "button",
                        "id": "!stop",
                        "label": "stop translator service",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                ]
            }
        }
    }
    return JSONResponse(content=response, media_type="application/json")


async def handle_admin_message(payload):
    hook_procesor: WebHookProcessor = Container.web_hook_processor()
    admin_id: str = '8459322'
    conversation_id = payload.get("conversation", {}).get("id")
    input_values = payload.get("input_values", {})
    message_text = input_values.get("admin_message")
    selected_language = input_values.get("language_choice")

    conv_status: str = hook_procesor.messages_cache_service.get_conversation_status(conversation_id=conversation_id)
    if (conv_status == 'started'):
        await hook_procesor.send_admin_reply_message(conversation_id=conversation_id, target_language=selected_language,
                                                     admin_id=admin_id, message=message_text, user=None)
        hook_procesor.messages_cache_service.set_conversation_language(conversation_id=conversation_id,
                                                                       language=selected_language)
    if (conv_status == 'stoped'):
        hook_procesor.messages_cache_service.set_conversation_status(conversation_d=conversation_id, status='started')
        hook_procesor.messages_cache_service.set_conversation_language(conversation_id=conversation_id,
                                                                       language=selected_language)
        await hook_procesor.send_admin_reply_message(conversation_id=conversation_id, message=message_text,
                                                     target_language=selected_language,
                                                     admin_id=admin_id, user=None)

    # Пример логирования
    print(f"Conversation ID: {conversation_id}")
    print(f"Selected language: {selected_language}")
    print(f"Message: {message_text}")

    response = {
        "canvas": {
            "content": {
                "components": [
                    {
                        "type": "button",
                        "id": "send_message",
                        "label": "send message for user",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {"type": "text", "text": f"Conversation Language: {selected_language}"},
                    {"type": "text", "text": "Conversation status: started"},
                    {
                        "type": "button",
                        "id": "Hinglish",
                        "label": "Force Hinglish",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {
                        "type": "button",
                        "id": "Hindi",
                        "label": "Force Hindi",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {
                        "type": "button",
                        "id": "Bengali",
                        "label": "Force Bengali",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                    {
                        "type": "button",
                        "id": "!stop",
                        "label": "stop translator service",
                        "style": "primary",
                        "action": {"type": "submit"},
                        "metadata": {"conversation_id": conversation_id},
                    },
                ]
            }
        }
    }
    return JSONResponse(content=response, media_type="application/json")
