import httpx
from app.AppConfig import SAUCENAO_API_KEY


def _contains_keywords(text: str | None, keywords: list[str]) -> bool:
    if not text:
        return False
    lower_text = str(text).lower()
    return any(keyword in lower_text for keyword in keywords)


def is_manga_candidate(search_result: dict | None) -> bool:
    if not search_result:
        return False

    keywords = [
        "manga",
        "comic",
        "doujin",
        "doujinshi",
        "nhentai",
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


def _build_candidate(best_result: dict) -> dict:
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


async def search_image_candidates_by_saucenao(image_url: str) -> list[dict]:
    """
    返回 SauceNAO 前 10 条候选结果，给搜漫画分支使用。
    """
    if not SAUCENAO_API_KEY:
        print("[SauceNAO] API key 未配置")
        return []

    url = "https://saucenao.com/search.php"

    params = {
        "output_type": 2,
        "api_key": SAUCENAO_API_KEY,
        "url": image_url,
        "numres": 10,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, params=params)

            print("[SauceNAO] status:", response.status_code)
            print("[SauceNAO] body:", response.text[:1000])

            if response.status_code != 200:
                return []

            result = response.json()

        results = result.get("results", [])
        if not results:
            return []

        return [_build_candidate(item) for item in results[:3]]

    except Exception as e:
        print("[SauceNAO] error:", e)
        return []


async def search_image_by_saucenao(image_url: str) -> dict | None:
    """
    保持给“搜图”用：默认取第一条候选。
    """
    candidates = await search_image_candidates_by_saucenao(image_url)
    return candidates[0] if candidates else None