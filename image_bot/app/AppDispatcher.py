from app.AppParser import extract_reply_id, extract_image_urls
from app.AppOnebot_api import get_msg
from app.AppSearch_service import search_image_by_saucenao
from app.AppManga_service import search_manga_by_image


def normalize_command(command: str | None) -> str | None:
    """
    作用：
    - 对命令做标准化
    - 清理不可见字符、换行、空格干扰
    - 让“看起来一样”的命令，真正变成一样

    为什么需要它？
    因为当前日志里已经出现了：
    - 屏幕显示是“搜漫画”
    - 但代码没有进入“搜漫画”分支
    这很像是命令里混入了隐藏字符。
    """
    if command is None:
        return None

    text = str(command)

    # 去掉常见不可见字符
    text = text.replace("\u200b", "")   # 零宽空格
    text = text.replace("\ufeff", "")   # BOM
    text = text.replace("\u00a0", " ")  # 不换行空格

    # 去掉首尾空白
    text = text.strip()

    # 把中间所有空白也压掉，防止“搜 漫画”这种情况
    text = "".join(text.split())

    return text or None


async def _get_reply_image_url(parsed: dict) -> tuple[str | None, str | None]:
    """
    从当前命令消息中，取出“被回复的那张图片”的 URL。

    返回值说明：
    - 成功: (image_url, None)
    - 失败: (None, 错误提示文本)
    """
    reply_id = extract_reply_id(parsed.get("message"))
    print("_get_reply_image_url -> reply_id:", reply_id)

    if not reply_id:
        return None, "请先回复一张图片，再发送命令"

    original_msg_data = await get_msg(reply_id)
    print("_get_reply_image_url -> original_msg_data:", original_msg_data)

    if not original_msg_data:
        return None, "获取被回复消息失败"

    image_urls = extract_image_urls(original_msg_data.get("message"))
    print("_get_reply_image_url -> image_urls:", image_urls)

    if not image_urls:
        return None, "引用的那条消息里没有图片"

    return image_urls[0], None


async def dispatch_command(command: str | None, parsed: dict) -> str | None:
    """
    根据用户发来的命令，决定执行哪种功能。
    """
    raw_command = command
    command = normalize_command(command)

    print("dispatch -> raw_command:", repr(raw_command))
    print("dispatch -> normalized_command:", repr(command))

    if not command:
        return None

    if command == ".ping":
        return "pong"

    if command == ".list":
        return "当前可用命令：.ping, .list, 搜图, 搜漫画"

    if command == "我爱你":
        return "我也爱你喵"

    if command in {"搜图", ".搜图"}:
        image_url, error_message = await _get_reply_image_url(parsed)
        if error_message:
            return error_message

        search_result = await search_image_by_saucenao(image_url)
        print("dispatch -> search_result:", search_result)

        if not search_result:
            return "搜图失败，或者没有找到结果"

        similarity = search_result.get("similarity", "未知")
        title = search_result.get("title", "未知")
        source_url = search_result.get("source_url", "无")
        index_name = search_result.get("index_name", "未知")

        return (
            f"搜图结果：\n"
            f"相似度：{similarity}\n"
            f"标题：{title}\n"
            f"来源：{source_url}\n"
            f"索引：{index_name}"
        )

    if command in {"搜漫画", ".搜漫画"}:
        image_url, error_message = await _get_reply_image_url(parsed)
        if error_message:
            return error_message

        manga_result = await search_manga_by_image(image_url)
        print("dispatch -> manga_result:", manga_result)

        if not manga_result:
            return "没有识别到明确的漫画结果"

        similarity = manga_result.get("similarity", "未知")
        title = manga_result.get("title", "未知")
        source_url = manga_result.get("source_url", "无")
        index_name = manga_result.get("index_name", "未知")

        return (
            f"搜漫画结果：\n"
            f"相似度：{similarity}\n"
            f"标题：{title}\n"
            f"来源：{source_url}\n"
            f"索引：{index_name}"
        )

    # 临时调试出口：防止未知命令静默
    return f"未识别命令：原始={raw_command!r}，规范化后={command!r}"