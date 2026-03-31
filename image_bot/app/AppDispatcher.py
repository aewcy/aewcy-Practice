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