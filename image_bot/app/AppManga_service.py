import httpx
from app.AppSearch_service import search_image_by_saucenao, is_manga_candidate
from app.AppConfig import NHENTAI_API_BASE


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


async def fetch_nhentai_details(manga_id: str | int) -> dict | None:
    """调用详情补全接口获取漫画详情"""
    url = f"{NHENTAI_API_BASE}/{manga_id}"
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"[fetch_nhentai_details] error: {e}")
    return None


def _extract_nhentai_id(search_result: dict) -> str | None:
    """从搜图结果中尝试提取详情 ID"""
    raw_data = search_result.get("raw_data", {})
    data_part = raw_data.get("data", {})

    nh_id = data_part.get("nhentai_id")
    if nh_id:
        return str(nh_id)

    source_url = search_result.get("source_url") or ""
    if "nhentai.net/g/" in source_url:
        return source_url.split("/g/")[-1].strip("/")

    return None


async def search_manga_by_image(image_url: str) -> dict | None:
    """
    搜漫画流程：
    1. 先用 SauceNAO 搜图
    2. 尝试从结果里提取详情 ID
    3. 如果详情补全成功，返回补全版漫画结果
    4. 如果补全失败，也返回一个“基础版漫画结果”
    """
    search_result = await search_image_by_saucenao(image_url)
    print("[search_manga_by_image] search_result:", search_result)

    if not search_result:
        return None

    nh_id = _extract_nhentai_id(search_result)
    print("[search_manga_by_image] nh_id:", nh_id)

    if nh_id:
        detail = await fetch_nhentai_details(nh_id)
        print("[search_manga_by_image] detail:", detail)

        if detail:
            return {
                "source": "detail_api",
                "manga_id": nh_id,
                "title": detail.get("title", {}).get("english") or search_result.get("title"),
                "native_title": detail.get("title", {}).get("japanese"),
                "total_pages": detail.get("num_pages"),
                "similarity": search_result.get("similarity"),
                "index_name": search_result.get("index_name"),
                "source_url": search_result.get("source_url") or f"https://nhentai.net/g/{nh_id}",
                "note": "已拿到详情补全结果",
            }

    candidate = is_manga_candidate(search_result)
    print("[search_manga_by_image] candidate:", candidate)

    return {
        "source": "generic_manga_search",
        "title": search_result.get("title"),
        "source_url": search_result.get("source_url"),
        "similarity": search_result.get("similarity"),
        "index_name": search_result.get("index_name"),
        "raw_data": search_result.get("raw_data"),
        "is_candidate": candidate,
        "note": "未拿到详情补全，先返回基础搜图结果",
    }