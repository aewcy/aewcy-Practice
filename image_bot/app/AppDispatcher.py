from app.AppParser import extract_reply_id, extract_image_urls
from app.AppOnebot_api import get_msg
from app.AppSearch_service import search_image_by_saucenao, is_manga_candidate


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

        # 第四步：把图片地址交给 SauceNAO
        search_result = await search_image_by_saucenao(image_urls[0])
        print("dispatch -> search_result:", search_result)

        if not search_result:
            return "搜图失败，或者没有找到结果"

        # 第五步：判断这是不是漫画候选
        manga_candidate = is_manga_candidate(search_result)
        print("dispatch -> manga_candidate:", manga_candidate)

        similarity = search_result.get("similarity", "未知")
        title = search_result.get("title", "未知")
        source_url = search_result.get("source_url", "无")
        index_name = search_result.get("index_name", "未知")

        lines = [
            "搜图结果：",
            f"相似度：{similarity}",
            f"标题：{title}",
            f"来源：{source_url}",
            f"索引：{index_name}",
        ]

        if manga_candidate:
            lines.append("类型判断：漫画候选")
            lines.append("后续可进入漫画信息补全流程")
        else:
            lines.append("类型判断：普通图片结果")

        return "\n".join(lines)

    return None