import requests
from AppConfig import NAPCAT_API_URL

def send_group_message(group_id: int, message: str) -> None:
    url = f"{NAPCAT_API_URL}/api/v1/send_group_message"
    payload = {
        "group_id": group_id,
        "message": message
    }

    try:
        resp = requests.post(url, json=payload,timeout=10)
        print(f"[真实发送] status:{resp.status_code}, body:{resp.text}")
    except Exception as e:
        print(f"[发送失败] error:{e}")