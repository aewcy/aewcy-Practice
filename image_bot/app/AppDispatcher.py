from app.AppParser import extract_reply_id, extract_image_urls
from app.AppOnebot_api import get_msg


async def dispatch_command(command: str | None, parsed: dict) -> str | None:
    """
    根据用户发来的命令，决定执行哪种功能。
    command: 提取出来的纯文本命令，比如 ".ping"、"搜图"
    parsed: parse_event() 之后得到的消息字典
    """
    if not command:
        return None

    command = command.strip()

    if command == ".ping":
        return "pong"

    if command == ".list":
        return "当前可用命令：.ping, .list, 搜图"

    if command == "我爱你":
        return "我也爱你喵"

    if command in {"搜图", ".搜图"}:
        # 第一步：从当前这条“搜图”消息里提取 reply_id
        reply_id = extract_reply_id(parsed.get("message"))
        print("dispatch -> reply_id:", reply_id)

        if not reply_id:
            return "请先回复一张图片，再发送“搜图”"

        # 第二步：根据 reply_id 获取被回复的原消息
        original_msg_data = await get_msg(reply_id)
        print("dispatch -> original_msg_data:", original_msg_data)

        if not original_msg_data:
            return "获取被回复消息失败"

        # 第三步：从原消息里提取图片地址
        image_urls = extract_image_urls(original_msg_data.get("message"))
        print("dispatch -> image_urls:", image_urls)

        if not image_urls:
            return "引用的那条消息里没有图片"

        # 先不接 SauceNAO，先验证到这里是否通了
        return f"已拿到图片地址：{image_urls[0]}"

    return None