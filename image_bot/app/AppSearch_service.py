import httpx
from app.AppConfig import SAUCENAO_API_KEY


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
        "output_type": 2,          # 2 表示返回 JSON
        "api_key": SAUCENAO_API_KEY,
        "url": image_url,
        "numres": 3,               # 最多返回前 3 条
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
        source_url = ext_urls[0] if ext_urls else None

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