import re

def parse_event(data:dict) -> dict:
    return{
        "post_type": data.get("post_type"),
        "message_type": data.get("message_type"),
        "group_id": data.get("group_id"),
        "user_id": data.get("user_id"),
        "message": data.get("message"),
    }


def is_group_message(parsed:dict) -> bool:
    return(
        parsed.get("post_type") == "message" and
        parsed.get("message_type") == "group"
    )

def extract_text(parsed:dict) -> str:
    message = parsed.get("message")

    if not isinstance(message, str):
        return None
    
    message = message.strip()

    if not message:
        return None
    
    return message

def extract_reply_id(parsed:dict) -> str | None:
    if not message:
        return None
    
    message = message.strip()
    if match:
        return match.group(1)
    return None