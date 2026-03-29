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
            print("[send_group_message] body:", response.text)
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
            print("[get_msg] body:", response.text)

            result = response.json()

            if result.get("status") == "ok":
                return result.get("data")

            return None

    except Exception as e:
        print("[get_msg] error:", e)
        return None