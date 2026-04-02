from fastapi import FastAPI, Request, Body, Response
from pathlib import Path
from fastapi.staticfiles import StaticFiles


from app.AppParser import parse_event, is_group_message, extract_text, extract_reply_id, extract_image_urls
from app.AppDispatcher import dispatch_command
from app.AppOnebot_api import send_group_message
from app.AppConfig import ALLOW_GROUP_IDS


app = FastAPI()

PUBLIC_DIR = Path("/workspace/cache/jm_download")
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")

@app.get("/metrics")
async def dummy_metrics():
    # 随便返回一点什么，或者返回纯文本，打发监控工具
    return Response(content="ok", media_type="text/plain")

@app.get("/")
async def root():
    return{"message":"bot backend is runing"}

@app.post("/onebot/event")
async def receive_event(data: dict = Body(...)):
    parsed = parse_event(data)

    print("原始事件：", data)
    print("解析结果：", parsed)
    print("提取文本：", extract_text(parsed))
    print("reply_id:", extract_reply_id(parsed.get("message")))

    if not is_group_message(parsed):
        print("这不是群消息")
        return {"ok": True}
    else:
        print("这是群消息")

    group_id = parsed.get("group_id")
    if group_id is None:
        print("没有 group_id")
        return {"ok": True}
    
    if ALLOW_GROUP_IDS and group_id not in ALLOW_GROUP_IDS:
        print(f"群 {group_id} 不在白名单中，忽略")
        return {"ok": True}

    command = extract_text(parsed)
    print("提取文本命令：", command)
    print("提取文本命令 repr：", repr(command))
    
    reply = await dispatch_command(command,parsed)
    print("响应：", reply)
    if reply:
        await send_group_message(group_id, reply)

    return {"ok": True} 
