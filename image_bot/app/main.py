from fastapi import FastAPI, Request,Body
from AppParser import parse_event, is_group_message,extract_text
from AppDispatcher import dispatch_command
from AppOnebot_api import send_group_message

app = FastAPI() 

@app.get("/")
async def root():
    return{"message":"bot backend is runing"}

@app.post("/onebot/event")
# async def receive_event(request: Request):
#     data = await request.json()
#     print("get_event:",data)
#     return {"ok":True}

async def receive_event(data: dict = Body(...)):
    parsed = parse_event(data)

    print("原始事件：", data)
    print("解析结果：", parsed)

    if is_group_message(parsed):
        print("这是群消息")

        command = extract_text(parsed)
        print("提取文本命令：", command)
        reply = dispatch_command(command)
        print("响应：", reply)
        if reply:
            group_id = parsed.get("group_id")
            if group_id is not None:
                send_group_message(group_id, reply)
    else:
        print("这不是群消息")

    return {"ok": True} 
