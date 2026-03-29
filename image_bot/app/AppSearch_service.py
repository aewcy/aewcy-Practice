import httpx
from app.AppConfig import SAUCENAO_API_KEY


def _contains_keywords(text: str | None, keywords: list[str]) -> bool:
    """
    作用：
    - 判断一段文本里有没有出现指定关键词
    - 这里主要给“漫画候选判断”用

    参数：
    text: 要检查的文本
    keywords: 关键词列表，例如 ["manga", "comic"]

    返回：
    True  -> 命中关键词
    False -> 没命中
    """
    if not text:
        return False

    lower_text = str(text).lower()
    return any(keyword in lower_text for keyword in keywords)


def is_manga_candidate(search_result: dict | None) -> bool:
    """
    作用：
    - 根据 SauceNAO 的搜图结果，粗判断这次是不是“漫画候选”
    - 这里只做“识别入口”，不做具体站点补全

    判断依据：
    1. index_name
    2. source_url
    3. raw_data 里的标题 / 来源字段
    """
    if not search_result:
        return False

    keywords = [
        "manga",
        "comic",
        "doujin",
        "doujinshi",
    ]

    index_name = search_result.get("index_name")
    source_url = search_result.get("source_url")

    raw_result = search_result.get("raw_data", {})
    raw_header = raw_result.get("header", {})
    raw_data = raw_result.get("data", {})

    candidate_texts = [
        index_name,
        source_url,
        raw_header.get("index_name"),
        raw_data.get("title"),
        raw_data.get("eng_name"),
        raw_data.get("jp_name"),
        raw_data.get("source"),
    ]

    for text in candidate_texts:
        if _contains_keywords(text, keywords):
            return True

    return False


async def search_image_by_saucenao(image_url: str) -> dict | None:
    """
    用 SauceNAO 根据图片 URL 搜索来源信息。

    image_url: 要搜索的图片地址
    return:
        成功时返回一个字典，里面包含：
        - similarity: 相似度
        - title: 标题
        - source_url: 来源链接
        - index_name: 索引名称
        - raw_data: 原始结果（方便以后调试）
        失败时返回 None
    """
    if not SAUCENAO_API_KEY:
        print("[SauceNAO] API key 未配置")
        return None

    url = "https://saucenao.com/search.php"

    params = {
        "output_type": 2,
        "api_key": SAUCENAO_API_KEY,
        "url": image_url,
        "numres": 3,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, params=params)

            print("[SauceNAO] status:", response.status_code)
            print("[SauceNAO] body:", response.text[:1000])

            if response.status_code != 200:
                return None

            result = response.json()

        results = result.get("results", [])
        if not results:
            return None

        best_result = results[0]

        header = best_result.get("header", {})
        data = best_result.get("data", {})

        ext_urls = data.get("ext_urls", [])
        source_url = ext_urls[0] if ext_urls else data.get("source")

        title = (
            data.get("title")
            or data.get("eng_name")
            or data.get("jp_name")
            or data.get("source")
            or "未找到标题"
        )

        return {
            "similarity": header.get("similarity"),
            "title": title,
            "source_url": source_url,
            "index_name": header.get("index_name"),
            "raw_data": best_result,
        }

    except Exception as e:
        print("[SauceNAO] error:", e)
        return None