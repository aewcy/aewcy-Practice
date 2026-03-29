import httpx
from app.AppConfig import NAPCAT_API_URL

async def send_group_message(group_id: int, message: str) -> None:
    url = f"{NAPCAT_API_URL}/send_group_msg"
    payload = {
        "group_id": group_id,
        "message": message
    }
    TOKEN = "cSMsJS8cowszL9eH" 
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }


    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload,timeout=10,headers=headers)
        print(f"[真实发送] status:{resp.status_code}, body:{resp.text}")
    except Exception as e:
        print(f"[发送失败] error:{e}")


# 在 send_group_msg 函数下面加上这个新函数
async def get_msg(message_id: str) -> dict | None:
    """根据 message_id 获取完整的消息体"""
    url = f"{NAPCAT_API_URL}/get_msg"
    payload = {
        "message_id": message_id
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=5)
            data = resp.json()
            if data.get("status") == "ok":
                return data.get("data")
    except Exception as e:
        print(f"[获取消息失败] error:{e}")
    return None