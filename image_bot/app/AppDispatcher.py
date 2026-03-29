from app.AppParser import extract_reply_id
from app.AppOnebot_api import get_msg

async def dispatch_command(command:str | None,parsed:dict) -> str | None:
    if not command:
        return None
    
    command = command.strip()

    if command == ".ping":
        return "pong"
    
    if command == ".list":
        return "当前可用命令：.ping, .list"
    
    if "搜图" in command:
        raw_message = parsed.get("message","")

        reply_id = extract_reply_id(raw_message)
        if not reply_id:
            return "无参考图喵"
        
        original_msg = await get_msg(reply_id)
        if not original_msg_data:
            return "找不到图片，可能是原消息太久远了喵"
        
        return f"获得参考图：{original_msg_data['message']}"

    return None