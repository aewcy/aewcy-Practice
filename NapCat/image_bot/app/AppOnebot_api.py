import os
import httpx
from app.AppConfig import NAPCAT_API_URL, NAPCAT_TOKEN, PUBLIC_BASE_URL


def build_headers() -> dict:
    """
    给 NapCat API 请求构造请求头。
    如果配置了 token，就带上 Authorization。
    """
    if NAPCAT_TOKEN:
        return {"Authorization": f"Bearer {NAPCAT_TOKEN}"}
    return {}


async def send_group_message(group_id: int, message: str) -> None:
    """
    发送群消息。
    group_id: 群号
    message: 要发送的文本内容
    """
    url = f"{NAPCAT_API_URL}/send_group_msg"
    payload = {
        "group_id": group_id,
        "message": message,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=build_headers(),
                timeout=10
            )
            print("[send_group_message] status:", response.status_code)
            print("[send_group_message] body:", response.text[:200])
    except Exception as e:
        print("[send_group_message] error:", e)


async def get_msg(message_id: str | int) -> dict | None:
    """
    根据 message_id 获取某条历史消息的详细内容。
    message_id: 消息编号，可以是字符串，也可以是整数
    return: 如果成功，返回 NapCat 返回的 data 部分；失败返回 None
    """
    url = f"{NAPCAT_API_URL}/get_msg"
    payload = {
        "message_id": int(message_id)
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=build_headers(),
                timeout=10
            )
            print("[get_msg] status:", response.status_code)
            print("[get_msg] body:", response.text[:200])

            result = response.json()

            if result.get("status") == "ok":
                return result.get("data")

            return None

    except Exception as e:
        print("[get_msg] error:", e)
        return None


async def get_reply_image_url(parsed: dict) -> tuple[str | None, str | None]:
    """
    从被回复消息中提取图片 URL。
    返回 (image_url, error_message)。成功时 error_message 为 None，失败时 image_url 为 None。
    """
    from app.AppParser import extract_reply_id, extract_image_urls

    reply_id = extract_reply_id(parsed.get("message"))
    if not reply_id:
        return None, "未找到回复 ID，请在消息中引用（回复）一张图片"

    replied_msg = await get_msg(reply_id)
    if not replied_msg:
        return None, f"无法获取被回复消息 {reply_id} 的内容"

    replied_message = replied_msg.get("message")
    image_urls = extract_image_urls(replied_message)

    if not image_urls:
        return None, "被回复的消息中没有找到图片"

    return image_urls[0], None


def build_public_file_url(file_path: str) -> str:
    """
    把容器内文件路径转换为 FastAPI 可公开访问的 URL。
    例如：
    /workspace/cache/jm_download/903485102/86632/86632.pdf
    ->
    http://192.168.61.128:8000/public/903485102/86632/86632.pdf
    """
    prefix = "/workspace/cache/jm_download/"
    normalized = file_path.replace("\\", "/")

    if not normalized.startswith(prefix):
        raise ValueError(f"文件路径不在公开目录下: {file_path}")

    relative_path = normalized[len(prefix):]
    return f"{PUBLIC_BASE_URL}/public/{relative_path}"


async def upload_group_file(group_id: int, file_path: str) -> dict | None:
    """
    上传文件到群文件列表。
    这里不传 base64，不传 multipart，不传本地路径。
    直接传 FastAPI 暴露出来的 HTTP 下载地址。
    """
    url = f"{NAPCAT_API_URL}/upload_group_file"
    file_name = os.path.basename(file_path)

    if not os.path.exists(file_path):
        print("[upload_group_file] file not found:", file_path)
        return None

    try:
        public_url = build_public_file_url(file_path)
    except Exception as e:
        print("[upload_group_file] build_public_file_url error:", e)
        return None

    payload = {
        "group_id": group_id,
        "file": public_url,
        "name": file_name,
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                url,
                json=payload,
                headers=build_headers(),
            )
            print("[upload_group_file] status:", response.status_code)
            print("[upload_group_file] payload:", payload)
            print("[upload_group_file] body:", response.text[:500])

            result = response.json()
            if result.get("status") == "ok":
                return result.get("data")

            return None

    except Exception as e:
        print("[upload_group_file] error:", e)
        return None


async def get_group_root_files(group_id: int) -> list[dict]:
    """
    获取群根目录文件列表。
    """
    url = f"{NAPCAT_API_URL}/get_group_root_files"
    payload = {"group_id": group_id}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=build_headers(),
                timeout=10
            )
            print("[get_group_root_files] status:", response.status_code)
            print("[get_group_root_files] body:", response.text[:200])
            result = response.json()
            if result.get("status") == "ok":
                return result.get("data", {}).get("files", [])
            return []
    except Exception as e:
        print("[get_group_root_files] error:", e)
        return []


async def upload_to_fileio(file_path: str) -> str | None:
    """
    将文件上传到 file.io，返回下载 URL。失败返回 None。
    """
    url = "https://file.io/"
    file_name = os.path.basename(file_path)

    if not os.path.exists(file_path):
        print("[upload_to_fileio] file not found:", file_path)
        return None

    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                response = await client.post(url, files=files)

        print("[upload_to_fileio] status:", response.status_code)
        print("[upload_to_fileio] final_url:", str(response.url))
        print("[upload_to_fileio] headers location:", response.headers.get("location"))
        print("[upload_to_fileio] body:", response.text[:300])

        if response.status_code != 200:
            return None

        result = response.json()
        if result.get("success") is True:
            return result.get("link")

        return None

    except Exception as e:
        print("[upload_to_fileio] error:", e)
        return None

async def upload_group_file_by_url(group_id: int, file_url: str, file_name: str) -> dict | None:
    """
    通过下载 URL 将文件上传到群文件列表。
    """
    url = f"{NAPCAT_API_URL}/upload_group_file"
    payload = {
        "group_id": group_id,
        "uri": file_url,
        "name": file_name,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                json=payload,
                headers=build_headers()
            )
            print("[upload_group_file_by_url] status:", response.status_code)
            print("[upload_group_file_by_url] body:", response.text[:200])
            result = response.json()
            if result.get("status") == "ok":
                return result.get("data")
            return None
    except Exception as e:
        print("[upload_group_file_by_url] error:", e)
        return None

async def delete_group_file(group_id: int, file_id: str, busid: int) -> bool:
    """
    删除群文件。
    """
    url = f"{NAPCAT_API_URL}/delete_group_file"
    payload = {
        "group_id": group_id,
        "file_id": file_id,
        "busid": busid,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                json=payload,
                headers=build_headers(),
            )
            print("[delete_group_file] status:", response.status_code)
            print("[delete_group_file] body:", response.text[:300])

            result = response.json()
            return result.get("status") == "ok"

    except Exception as e:
        print("[delete_group_file] error:", e)
        return False