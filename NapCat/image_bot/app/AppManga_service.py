import re
import httpx
from app.AppSearch_service import (
    search_image_candidates_by_saucenao,
    is_manga_candidate,
)
from app.AppConfig import NHENTAI_API_BASE


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


async def fetch_nhentai_details(manga_id: str | int) -> dict | None:
    """直接调用 nHentai API 获取漫画详情"""
    url = f"{NHENTAI_API_BASE}/{manga_id}"
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
            response = await client.get(url)
            print("[fetch_nhentai_details] status:", response.status_code)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"[fetch_nhentai_details] error: {e}")
    return None


def _collect_candidate_urls(candidate: dict) -> list[str]:
    """
    把一条候选里所有可能有用的 URL 都收集起来。
    """
    urls = []

    source_url = candidate.get("source_url")
    if source_url:
        urls.append(source_url)

    raw_result = candidate.get("raw_data", {})
    data_part = raw_result.get("data", {})

    ext_urls = data_part.get("ext_urls", [])
    if isinstance(ext_urls, list):
        for url in ext_urls:
            if url and url not in urls:
                urls.append(url)

    source = data_part.get("source")
    if source and source not in urls:
        urls.append(source)

    return urls


def _extract_nhentai_id_from_url(url: str) -> str | None:
    match = re.search(r"nhentai\.net/g/(\d+)", url)
    if match:
        return match.group(1)
    return None


def _extract_nhentai_id(candidate: dict) -> str | None:
    """
    从候选结果中尽可能多地尝试提取 gallery id。
    """
    raw_result = candidate.get("raw_data", {})
    data_part = raw_result.get("data", {})

    nh_id = data_part.get("nhentai_id")
    if nh_id:
        return str(nh_id)

    for url in _collect_candidate_urls(candidate):
        parsed_id = _extract_nhentai_id_from_url(url)
        if parsed_id:
            return parsed_id

    return None


def _manga_score(candidate: dict) -> int:
    """
    给候选打分，分越高越像漫画结果。
    """
    score = 0

    if is_manga_candidate(candidate):
        score += 3

    urls = _collect_candidate_urls(candidate)
    url_text = " ".join(urls).lower()

    if "nhentai" in url_text:
        score += 6
    if "doujin" in url_text:
        score += 3
    if "manga" in url_text or "comic" in url_text:
        score += 2

    index_name = str(candidate.get("index_name", "")).lower()
    if "manga" in index_name or "doujin" in index_name or "comic" in index_name:
        score += 3

    try:
        similarity = float(candidate.get("similarity", 0))
        if similarity >= 80:
            score += 2
        elif similarity >= 60:
            score += 1
    except Exception:
        pass

    return score


async def search_manga_by_image(image_url: str) -> dict | None:
    """
    特化版搜漫画：
    1. 先拿 SauceNAO 前 3 条候选
    2. 对候选逐条打分
    3. 优先尝试从高分候选里提取详情 ID
    4. 如果补全失败，也返回最像漫画的候选，而不是直接 None
    """
    candidates = await search_image_candidates_by_saucenao(image_url)
    print("[search_manga_by_image] candidates:", candidates)

    if not candidates:
        return None

    scored_candidates = sorted(
        candidates,
        key=lambda item: (_manga_score(item), float(item.get("similarity") or 0)),
        reverse=True,
    )

    print("[search_manga_by_image] scored_candidates:", scored_candidates)

    for candidate in scored_candidates:
        nh_id = _extract_nhentai_id(candidate)
        print("[search_manga_by_image] trying nh_id:", nh_id, "candidate:", candidate)

        if not nh_id:
            continue

        detail = await fetch_nhentai_details(nh_id)
        print("[search_manga_by_image] detail:", detail)

        if detail:
            return {
                "source": "nhentai",
                "manga_id": nh_id,
                "title": detail.get("title", {}).get("english") or candidate.get("title"),
                "native_title": detail.get("title", {}).get("japanese"),
                "tags": [t.get("name") for t in detail.get("tags", []) if t.get("type") == "tag"],
                "total_pages": detail.get("num_pages"),
                "similarity": candidate.get("similarity"),
                "index_name": candidate.get("index_name"),
                "source_url": f"https://nhentai.net/g/{nh_id}",
                "note": "已命中详情接口",
            }

    best_candidate = scored_candidates[0]
    return {
        "source": "generic_manga_candidate",
        "title": best_candidate.get("title"),
        "source_url": best_candidate.get("source_url"),
        "similarity": best_candidate.get("similarity"),
        "index_name": best_candidate.get("index_name"),
        "note": "未命中详情接口，返回最佳漫画候选",
        "raw_data": best_candidate.get("raw_data"),
    }