import re
from typing import Any


def parse_event(data: dict) -> dict:
    """
    把 NapCat 传来的原始事件整理成统一结构。
    data: NapCat 发来的整包字典数据
    """
    return {
        "post_type": data.get("post_type"),
        "message_type": data.get("message_type"),
        "group_id": data.get("group_id"),
        "user_id": data.get("user_id"),
        "message": data.get("message"),
        "raw_message": data.get("raw_message", ""),
    }


def is_group_message(parsed: dict) -> bool:
    """
    判断是不是群消息。
    只有 post_type 是 message 且 message_type 是 group，才说明它是群消息。
    """
    return (
        parsed.get("post_type") == "message"
        and parsed.get("message_type") == "group"
    )


def extract_text(parsed: dict) -> str | None:
    """
    从消息中提取纯文本内容。
    兼容：
    1. string 模式（CQ码字符串）
    2. array 模式（消息段列表）
    """
    message = parsed.get("message")

    if isinstance(message, str):
        text = message.strip()
        text = re.sub(r"\[CQ:reply,[^\]]*\]", "", text)
        text = re.sub(r"\[CQ:at,[^\]]*\]", "", text)
        text = text.strip()
        return text or None

    if isinstance(message, list):
        text_parts = []
        for segment in message:
            if segment.get("type") == "text":
                text_value = segment.get("data", {}).get("text", "")
                text_parts.append(text_value)
        full_text = "".join(text_parts).strip()
        return full_text or None

    return None


def extract_reply_id(message: Any) -> str | None:
    """
    提取被回复消息的 message_id。
    """
    if isinstance(message, list):
        for segment in message:
            if segment.get("type") == "reply":
                reply_id = segment.get("data", {}).get("id")
                if reply_id is not None:
                    return str(reply_id)
        return None

    if isinstance(message, str):
        match = re.search(r"\[CQ:reply,id=(-?\d+)\]", message)
        if match:
            return match.group(1)

    return None


def extract_image_urls(message: Any) -> list[str]:
    """
    从消息中提取图片地址。
    """
    image_urls = []

    if isinstance(message, list):
        for segment in message:
            if segment.get("type") == "image":
                image_data = segment.get("data", {})
                image_url = image_data.get("url") or image_data.get("file")
                if image_url:
                    image_urls.append(image_url)
        return image_urls

    if isinstance(message, str):
        matches = re.finditer(r"\[CQ:image,[^\]]*url=([^,\]]+)", message)
        for match in matches:
            image_urls.append(match.group(1))

    return image_urls
