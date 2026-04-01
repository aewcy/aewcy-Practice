import asyncio
from app.AppOnebot_api import get_reply_image_url as _get_reply_image_url
from app.AppManga_service import search_manga_by_image
from app.AppSearch_service import search_image_by_saucenao
from app.AppJm_handler import handle_jm, handle_jmzip
from psutil import cpu_percent, virtual_memory


AVAILABLE_COMMANDS = [
    ("搜漫画 / .搜漫画", "搜索被回复图片的漫画来源"),
    ("搜图 / .搜图", "搜索被回复图片的图片来源"),
    (".jm [本子ID]", "下载本子并打包为 PDF/ZIP"),
    (".jmzip [本子ID]", "获取已缓存本子的压缩包"),
    (".list", "显示本帮助列表"),
    (".ping", "查看服务器 CPU/内存状态"),
]


async def dispatch_command(command: str, parsed: dict) -> str:

    if command in {"搜漫画", ".搜漫画"}:
        image_url, error_message = await _get_reply_image_url(parsed)
        if error_message:
            return error_message

        manga_result = await search_manga_by_image(image_url)
        print("dispatch -> manga_result:", manga_result)

        if not manga_result:
            return "搜漫画失败：没有拿到可用候选结果"

        similarity = manga_result.get("similarity", "未知")
        title = manga_result.get("title", "未知")
        source_url = manga_result.get("source_url", "无")
        index_name = manga_result.get("index_name", "未知")
        manga_id = manga_result.get("manga_id", "未知")
        total_pages = manga_result.get("total_pages", "未知")
        native_title = manga_result.get("native_title")
        note = manga_result.get("note")

        lines = [
            "搜漫画结果：",
            f"相似度：{similarity}",
            f"标题：{title}",
            f"来源：{source_url}",
            f"索引：{index_name}",
        ]

        if manga_result.get("source") == "nhentai":
            lines.append(f"作品ID：{manga_id}")
            lines.append(f"页数：{total_pages}")

        if native_title:
            lines.append(f"原生标题：{native_title}")

        if note:
            lines.append(f"说明：{note}")

        return "\n".join(lines)

    if command in {"搜图", ".搜图"}:
        image_url, error_message = await _get_reply_image_url(parsed)
        if error_message:
            return error_message

        search_result = await search_image_by_saucenao(image_url)
        print("dispatch -> search_result:", search_result)

        if not search_result:
            return "搜图失败：没有找到结果"

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

    user_id = str(parsed.get("user_id", ""))
    group_id = parsed.get("group_id")

    if command.startswith(".jm "):
        if not group_id:
            return "该命令仅限群聊使用"
        parts = command.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return "请注意格式：.jm [本子ID]，例如 .jm 472537"
        asyncio.create_task(handle_jm(user_id, group_id, parts[1]))
        return ""

    if command.startswith(".jmzip "):
        if not group_id:
            return "该命令仅限群聊使用"
        parts = command.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return "请注意格式：.jmzip [本子ID]，例如 .jmzip 472537"
        asyncio.create_task(handle_jmzip(user_id, group_id, parts[1]))
        return ""

    if command == ".list":
        lines = ["可用指令："]
        for cmd, desc in AVAILABLE_COMMANDS:
            lines.append(f"  {cmd} - {desc}")
        return "\n".join(lines)

    if command == ".ping":
        cpu = cpu_percent(interval=0.5)
        mem = virtual_memory()
        return f"pong\nCPU: {cpu}%\n内存: {mem.percent}%"

    return ""
