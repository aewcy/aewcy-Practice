import os
import base64
import httpx
from app.AppConfig import NAPCAT_API_URL, NAPCAT_TOKEN


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


async def upload_group_file(group_id: int, file_path: str) -> dict | None:
    """
    上传文件到群文件列表。
    返回上传后的文件信息，失败返回 None。
    先尝试 base64 JSON 格式，失败后自动 fallback 到 multipart。
    """
    url = f"{NAPCAT_API_URL}/upload_group_file"
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode("utf-8")
        payload = {
            "group_id": group_id,
            "file": file_data,
            "name": file_name,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                url,
                json=payload,
                headers=build_headers()
            )
            print("[upload_group_file] status:", response.status_code)
            print("[upload_group_file] body:", response.text[:200])
            result = response.json()
            if result.get("status") == "ok":
                return result.get("data")
    except Exception as e:
        print("[upload_group_file] base64 error:", e)

    # base64 JSON 失败，尝试 multipart fallback
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            data = {"group_id": group_id, "folder": "/"}
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    url,
                    data=data,
                    files=files,
                    headers=build_headers()
                )
                print("[upload_group_file] multipart status:", response.status_code)
                print("[upload_group_file] multipart body:", response.text[:200])
                if response.status_code != 200:
                    print("[upload_group_file] multipart HTTP error:", response.status_code, response.text)
                result = response.json()
                if result.get("status") == "ok":
                    return result.get("data")
    except Exception as e:
        print("[upload_group_file] multipart error:", e)

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


async def delete_group_file(group_id: int, file_id: str, busid: int) -> bool:
    """
    删除群文件。
    """
    url = f"{NAPCAT_API_URL}/delete_group_file"
    payload = {
        "group_id": group_id,
        "file_id": file_id,
        "busid": busid
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=build_headers(),
                timeout=10
            )
            print("[delete_group_file] status:", response.status_code)
            print("[delete_group_file] body:", response.text[:200])
            result = response.json()
            return result.get("status") == "ok"
    except Exception as e:
        print("[delete_group_file] error:", e)
        return False