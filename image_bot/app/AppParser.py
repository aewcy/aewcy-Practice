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

    为什么要单独写这个函数？
    因为 NapCat 的 message 有两种常见情况：
    1. 直接就是字符串，例如: "搜图"
    2. 是消息段列表，例如:
       [
           {"type": "reply", "data": {"id": "123"}},
           {"type": "text", "data": {"text": "搜图"}}
       ]
    从消息中提取纯文本内容。
    兼容：
    1. string 模式（CQ码字符串）
    2. array 模式（消息段列表）
    """
    message = parsed.get("message")

    # 情况1：string 模式
    if isinstance(message, str):
        text = message.strip()

        # 去掉 reply CQ码
        text = re.sub(r"\[CQ:reply,[^\]]*\]", "", text)

        # 如果以后有 at，也顺便去掉
        text = re.sub(r"\[CQ:at,[^\]]*\]", "", text)

        text = text.strip()
        return text or None

    # 情况2：array 模式
    if isinstance(message, list):
        text_parts = []

        for segment in message:
            if segment.get("type") == "text":
                text_value = segment.get("data", {}).get("text", "")
                text_parts.append(text_value)

        full_text = "".join(text_parts).strip()
        return full_text or None

    # 情况2：message 是列表，列表里每一项都是一个“消息段”
    if isinstance(message, list):
        text_parts = []

        for segment in message:
            # segment 表示“列表中的当前这一小段消息”
            # 例如可能是 reply 段、text 段、image 段
            if segment.get("type") == "text":
                text_value = segment.get("data", {}).get("text", "")
                text_parts.append(text_value)

        full_text = "".join(text_parts).strip()
        return full_text or None

    return None


def extract_reply_id(message: Any) -> str | None:
    """
    提取被回复消息的 message_id。

    参数 message 不再是整个 parsed，
    而是 parsed["message"] 这部分内容。

    为什么类型写 Any？
    因为 message 可能是字符串，也可能是列表。
    Any 的意思就是：这里先允许多种类型传进来。
    """
    # 情况1：message 是消息段列表
    if isinstance(message, list):
        for segment in message:
            if segment.get("type") == "reply":
                reply_id = segment.get("data", {}).get("id")
                if reply_id is not None:
                    return str(reply_id)
        return None

    # 情况2：message 是 CQ 码字符串
    if isinstance(message, str):
        match = re.search(r"\[CQ:reply,id=(-?\d+)\]", message)
        if match:
            return match.group(1)

    return None


def extract_image_urls(message: Any) -> list[str]:
    """
    从消息中提取图片地址。

    为什么返回 list[str] 而不是一个字符串？
    因为一条消息里有可能不止一张图，所以统一返回“图片地址列表”。
    即使只有一张图，也返回例如:
    ["https://xxx.com/abc.jpg"]
    """
    image_urls = []

    # 情况1：message 是消息段列表
    if isinstance(message, list):
        for segment in message:
            if segment.get("type") == "image":
                image_data = segment.get("data", {})

                # 有的实现把图片地址放在 url
                # 有的实现可能放在 file
                image_url = image_data.get("url") or image_data.get("file")

                if image_url:
                    image_urls.append(image_url)

        return image_urls

    # 情况2：message 是 CQ 码字符串
    if isinstance(message, str):
        matches = re.finditer(r"\[CQ:image,[^\]]*url=([^,\]]+)", message)
        for match in matches:
            image_urls.append(match.group(1))

    return image_urls