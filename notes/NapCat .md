# 3.26 NapCat部署

今日准备先去弄 NapCat，打算先弄明白这个

制作目的：制作 QQ 机器人，实现预定功能
环境使用的是 CentOS 9
配置库主要为 tmux（复用终端）、xvfb（X Virtual Framebuffer，虚拟的 X 服务器）、xauth（X 服务器的认证工具），以及 SauceNAO 和 nHentai 的 API。

UI 登录 token：

9ee3aa401e54

本地启动：

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

- 通用下载napcat步骤
    - NapCat的作用
        
        NapCat 在本项目主要负责的是连接 QQ 平台，本身并不负责处理逻辑
        只负责接收和发送信息，作为一个上游的接入层
        
        主要做：
        
        登录QQ
                接收 QQ 消息
                提供API接口 
                把收到的时间交给FastAPI后端处理
        
    - 运行环境
        
        Linux　环境
        
        tumx（复用终端）
        
        xvfb（X Virtual Framebuffer，虚拟的X服务器），
        
        xauth（X服务器的认证工具），
        
        Linux QQ 版
        
    - 下载与启动流程
        
        因为主要是用在 Linux 进项机器人部署，所以安装聚焦在 Linux的安装上
        
        通用安装，如需其他安装方式，查看官方文档  [NapCat官方下载文档](https://napneko.github.io/guide/boot/Shell)
        
        ```bash
        curl -o \
        napcat.sh \
        https://nclatest.znin.net/NapNeko/NapCat-Installer/main/script/install.sh \
        && bash napcat.sh
        ```
        
        安装完后会告诉 UI登录 token 密钥 需要记录
        
        - 常规登录方法和使用方法
            - WebUI 登录
                
                查看 Napcat token 登录
                
                找到webui.json 文件，获取文件地址
                
                find -name "webui.json" 
                
                查看 token 登录
                
                cat ./opt/QQ/resources/app/app_launcher/napcat/config/webui.json
                
                配置网络
                
                需要开两个，HTTP 客户端，HTTP服务端
                
                HTTP 客户端，主要作用：把再 QQ 侧发生的事件上报给后端
                
                HTTP 服务端，主要作用：让业务后端反过来控制 QQ 机器人做事情，比如上传文件
                
            
            开启 NapCat，启用复用窗口，启动 QQ
            
            screen -dmS napcat bash -c "xvfb-run -a /root/Napcat/opt/QQ/qq --no-sandbox"
            
            进入 screen
            
            screen -r napcat
            
            强制恢复现有会话
            
            screen -d -r napcat
            
    - 登陆后，关键信息获取
        
        **UI 登录 token**
        
        这个 token 主要用于登录 NapCat 的管理界面。
        
        **NapCat API 地址**
        
        后端要通过这个地址去调用 NapCat 的接口，比如发送群消息、获取历史消息、上传群文件等。
        
        在项目里，这个地址会配置成 `NAPCAT_API_URL`。
        
        **NapCat Token**
        
        如果 NapCat API 开启了鉴权，那么后端在请求 NapCat 时就要带 token。
        
        项目里的 `AppOnebot_api.py` 会通过 `Authorization: Bearer ...` 的方式带上这个值。
        
        **监听端口**
        
        NapCat 自己一般会监听一个端口，而我的 FastAPI 后端则监听另一个端口。
        
        当前项目里后端是 8000 端口，Compose 里也映射了 `8000:8000`。
        
    - 与本项目后端的对接关系
        
        QQ 消息 → NapCat 接收 → FastAPI 后端处理 → NapCat 再把消息发回 QQ
        
        第一层：NapCat 负责接平台
        
        NapCat 负责连接 QQ，接收群消息，提供 OneBot / API 能力。
        
        第二层：FastAPI 负责业务处理
        
        后端入口在 main.py。
        它接收到事件后，会先调用 AppParser.py 解析消息，再调用 AppDispatcher.py 分发到具体业务。
        
        第三层：API 交互层负责回传
        
        后端处理出结果后，再通过 AppOnebot_api.py 去请求 NapCat 的接口，比如：
        
        send_group_message()
        get_msg()
        upload_group_file() 等。
        
        第四层：配置通过 .env 注入
        
        NapCat 的地址、token、群白名单、SauceNAO key 等，不是写死在代码里，而是通过 .env 注入，再由 AppConfig.py 读出来。
        容器启动时，docker-compose.yml 会把 .env 加载进去。
        
    - 常见的问题
        
        1）NapCat 启动了，但后端收不到事件
        
        这种情况通常要先检查：
        
        NapCat 的事件上报地址有没有配对
        FastAPI 后端有没有启动
        main.py 的 /onebot/event 路由能不能访问到
        
        2）API 地址或 token 配错
        
        如果 NAPCAT_API_URL 或 NAPCAT_TOKEN 配错，后端虽然能启动，但调用 NapCat API 时会失败。
        比如发群消息、取回复消息、上传文件这些都依赖它。
        
        3）端口没打通
        
        后端现在使用 8000 端口，对应 Compose 里的 8000:8000。
        如果服务器防火墙、端口映射或者反向代理没配好，就可能访问不到服务。
        
        4）虚拟显示环境没准备好
        
        如果 xvfb、xauth 这些没装好，QQ 客户端可能根本起不来，NapCat 这一层也就没法正常工作。
        
        5）敏感信息泄露
        
        UI token、API token、.env 内容都不应该直接发到公开仓库。
        你的项目里 .env 已经在忽略逻辑范围里，这就是为了避免把这些配置上传出去。
        

- Bot  V1.01
    - 第一个版本主要实现内容
        
        主要实现了
        
        搜索漫画，
        
        搜索图片，
        
        显示服务器 cpu & 内存 占用，
        
        下载JM 漫画，
        
    - 结构图
        
        
        主要分为三部分
        
        app文件，这个文件夹主要存放项目的函数逻辑，命令执行的函数文件，因项目并不复杂，所以并未专门再分文件
        
        cache缓存文件，主要是作为项目缓存，下载文件和临时文件储存地
        
        根目录的其他文件，主要用来存放非业务文件，但负责整个项目跑起来的主要目录
        
        ```yaml
        image_bot/
        ├── app/
        │   ├── init.py
        │   ├── AppConfig.py
        │   ├── AppDispatcher.py
        │   ├── AppJm_downloader.py
        │   ├── AppJm_handler.py
        │   ├── AppJm_tools.py
        │   ├── AppManga_service.py
        │   ├── AppOnebot_api.py
        │   ├── AppParser.py
        │   ├── AppSearch_service.py
        │   └── 
        ├── cache/
        │   └── ! jm_config.yml
        ├── .env
        ├── .gitignore
        ├── docker-compose.yml
        ├── Dockerfile
        ├── main.py
        └── requirements.txt
        ```
        
    - 根目录项目文件（非文件夹内项目文件），含main.py
        
        根目录有app业务文件，cache缓存文件，和非业务项目跑动文件。
        
        - .env主要存储项目的环境变量
            
            ```
            # NapCat API
            NAPCAT_API_URL=http://192.168.61.128:3000
            NAPCAT_TOKEN=cSMsJS8cowszL9eH
            
            #NAPCAT_API_URL用来告诉后端文件，程序后面发群消息，取回复消息，上传群文件，
            都会用这个地址来请求NapCat，对应文件是AppOnebot_api.py
            #NAPCAT_TOKEN 这是NapCat的鉴权token，作用是让后端程序取调动NapCat API
            
            # 允许的群组 ID
            ALLOW_GROUP_IDS=9954621,4531468,54465189,（QQ群号）
            
            #主要负责允许响应 QQ 群的群号白名单
            
            # SauceNAO API Key
            SAUCENAO_API_KEY=xxxx
            
            #SAUCENAO_API_KEY SauceNAO的搜图的 API key ，没有key就无法取调用SauceNAO
            的搜图功能
            
            # nHentai API Base URL
            NHENTAI_API_BASE=https://nhentai.net/api/gallery/
            
            #nHentai API Base URL 这是nHentai的请求api接口，在拿到SauceNAO调回来的
            漫画候选后去补详情与查找
            
            # JM 下载缓存目录
            JM_DOWNLOAD_DIR=/workspace/cache/jm_download
            ```
            
        - .gitignore 告诉git：哪些文件不需要上传到GitHub上面
            
            ```
            __pycache__/
            *.py[cod]
            .env
            cache/jm_download/
            
            #__pycache__/忽略python在运行后生成的缓存文件
            
            #*.py[cod] 通配写法，忽略后缀文件为*.pyc  *.pyo  *.pyd，这些也大多是
            py运行/编译完后的产物，不是核心代码
            
            #.env 效果一样，忽略此文件
            
            #cache/jm_download/ 忽略下载出来的文件目录，这只是运行文件，不是源代码文件
            ```
            
        - docker-compose.yml 定义项目容器如何构建，启动，端口映射，配置注入，缓存目录等
            
            ```
            services:               #表示服务单元（后端）
              bot-backend:          #服务名，用来compose内部标识服务名字
                build: .            #表示 用当前目录下的Dockerfile来构建镜像
                container_name: image_bot_backend   #容器名定义
                ports:              #表示 宿主机8000端口 映射 容器内8000端口
                  - "8000:8000"
                env_file:           #在容器启动时把.env的环境变量加载进去，后续os才能读取配置
                  - .env
                restart: unless-stopped #在容器异常推出后自动重启，除非手动停掉
                volumes:            #把宿主机当前目录下的./cache挂载到/workspace/cache
                  - ./cache:/workspace/cache
                  
            networks:               #表示给compose项目定义了一个桥接网络botnet
              botnet:
                driver: bridge
             
            ```
            
        - Dockerfile Docker的配置过程
            
            ```docker
            FROM python:3.11-slim
            #以 python:3.11-slim 这个官方镜像作为基础镜像
            
            WORKDIR /workspace
            #把容器内的工作目录设置为 /workspace ，后续执行都是以此目录为相对路径
            
            COPY requirements.txt .
            #copy了俩个部分 第一个是 requirements.txt  第二个是 . 意思是把宿主机文件
            复制到 /workspace这个文件下 ，复制结果为 /workspace/requirements.txt
            
            RUN pip install --no-cache-dir -r requirements.txt
            #RUN 构建镜像时执行的命令 ， --no-cache-dir -r 不保留pip缓存，减少镜像体积
            
            COPY . .
            #把宿主机的当前所有文件都复制到 docker的工作文件内，同上文 Copy 一样
            
            RUN mkdir -p /workspace/cache/jm_download
            #在构建镜像时，创建下载目录
            
            EXPOSE 8000
            #声明 容器使用8000端口
            
            CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
            #容器启动后默认执行这段命令，命令为启动uvicorn 运行FastAPI应用
            ```
            
        - main.py
            
            因为是项目函数，放在下一个App项目核心函数讲了
            
        - requirements.txt 告诉运行程序，我们的项目主要是需要什么的库来支撑程序运行
            
            ```
            fastapi==0.110.0
            uvicorn==0.34.0
            python-dotenv
            requests
            httpx
            nonebot-plugin-guild-patch
            psutil
            pillow
            jmcomic
             
            ```
            
    - App项目核心函数
        - main.py (非App文件夹)
            
            ```python
            #模块导入
            from fastapi import FastAPI, Request, Body, Response
            from pathlib import Path
            from fastapi.staticfiles import StaticFiles
            #项目库模块导入
            
            from app.AppParser import parse_event, is_group_message, extract_text, extract_reply_id, extract_image_urls
            from app.AppDispatcher import dispatch_command
            from app.AppOnebot_api import send_group_message
            from app.AppConfig import ALLOW_GROUP_IDS
            #自建模块项目导入 
            ```
            
            ```python
            app = FastAPI()
            #创建整个后端服务实例，后续所有接口都挂在 app 上面
            
            PUBLIC_DIR = Path("/workspace/cache/jm_download")
            #定义路径对象，只想容器里的下载文件
            PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
            #确保路径存在， parents=True 父目录不存在也一起建 ， 
            exist_ok=True目录存在不报错
            
            app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
            #此代码为 下载目录 变成 HTTP 可访问目录
            ```
            
            ```python
            @app.get("/metrics")        
            async def dummy_metrics():
            		# 随便返回一点什么，或者返回纯文本，打发监控工具
                return Response(content="ok", media_type="text/plain")
            ```
            
            ```python
            @app.get("/")
            async def root():
                return{"message":"bot backend is runing"}
            #根目录接口，也是基础的存活检测接口
            ```
            
            ```python
            #main.py文件的核心功能，负责信息的接收与处理
            
            @app.post("/onebot/event") 
            #napcat onebot 程序的默认接口
            async def receive_event(data: dict = Body(...)):
            #将 napcat 推来的信息 JSON 读成 data: dict
                parsed = parse_event(data)
            		#复制一遍data，不对原始包做处理
            		
                print("原始事件：", data)
                print("解析结果：", parsed)
                print("提取文本：", extract_text(parsed))
                print("reply_id:", extract_reply_id(parsed.get("message")))
                #最后俩行分别是提取文本信息和被回复的文本信息
            
                if not is_group_message(parsed):
                    print("这不是群消息")
                    return {"ok": True}
                else:
                    print("这是群消息")
            		#一层过滤，判断是不是群消息
            		
                group_id = parsed.get("group_id")
                if group_id is None:
                    print("没有 group_id")
                    return {"ok": True}
                #二层过滤，判断有没有群号
                
                if ALLOW_GROUP_IDS and group_id not in ALLOW_GROUP_IDS:
                    print(f"群 {group_id} 不在白名单中，忽略")
                    return {"ok": True}
            		#三层过滤，判断是否为群白名单
            		
                command = extract_text(parsed)
                print("提取文本命令：", command)
                print("提取文本命令 repr：", repr(command))
                #提取命令文本，并打印出来以方便后台运维
                
                reply = await dispatch_command(command,parsed)
                print("响应：", reply)
                #主核心，把命令判断发送给AppDispatcher.dispatch_command()
                去做后续分发
                if reply:
                    await send_group_message(group_id, reply)
            		#如果命令响应了并给出结果，既有回复，就发回群里
            		
                return {"ok": True} 
            		#统一返回
            ```
            
        - AppParser.py　　　　　　　　　 Parser 解析器 主要作用是把NapCat上报的事件解释成程序宜处理的结构
            
            ```python
            import re　　　　　　　　　#引用 Py 的正则模块，在文件负责处理 CQ 码字符串 
            from typing import Any    
            	#Any 意思是 参数先不严格限定类型 因为处理message 有时是字符串 或 列表
            ```
            
            ```python
            1 
            """ 
            主要作用是把NapCat传进来的原始时间字典，整理成统一的字段结构，只保留
            核心的6个字段
             """
            def parse_event(data: dict) -> dict:
                return {
                    "post_type": data.get("post_type"),
                    "message_type": data.get("message_type"),
                    "group_id": data.get("group_id"),
                    "user_id": data.get("user_id"),
                    "message": data.get("message"),
                    "raw_message": data.get("raw_message", ""),
                }
                """
                字段分别为 
            	     事件类型   有 "message" 消息事件 "notice" 通知事件 "request"请求事件
            		   消息类型   消息事件的子类型，常见有 "private" 私聊消息 "group" 群消息
            		   QQ群号     
            		   用户QQ号
            		   主要文本信息   
            		   被回复文本信息
                
                """
            ```
            
            ```python
            2
            """
            判断是不是群消息。
            只有 post_type 是 message 且 message_type 是 group，才说明它是群消息。
            """
            def is_group_message(parsed: dict) -> bool:  #返回值是bool
                return (
                    parsed.get("post_type") == "message"
                    and parsed.get("message_type") == "group"
                )
            ```
            
            ```python
            3
            """
            从消息中提取纯文本内容。
            兼容：
            1. string 模式（CQ码字符串）
            2. array 模式（消息段列表）
            """
            def extract_text(parsed: dict) -> str | None:  #返回值可能是 str 或 None
                message = parsed.get("message")
            
                if isinstance(message, str):  #isinstance 判断是否是实例 既是否是字符串
                    text = message.strip()    #去掉首尾空白字符
                    text = re.sub(r"\[CQ:reply,[^\]]*\]", "", text) #正则表达，去掉前缀 只取文本
                    text = re.sub(r"\[CQ:at,[^\]]*\]", "", text) #一样，但去掉@
                    text = text.strip()       #二次去掉首尾空白字符，以防万一
                    return text or None
            
                if isinstance(message, list):
                    text_parts = []
                    for segment in message:
                        if segment.get("type") == "text":    #只有 type是text 字段才进行处理
                            text_value = segment.get("data", {}).get("text", "")
                            text_parts.append(text_value)
                    full_text = "".join(text_parts).strip()  #多段文本 拼接起来
                    return full_text or None 
            
                return None
            ```
            
            ```python
            4
            def extract_reply_id(message: Any) -> str | None:
                """
                提取被回复消息的 message_id。
                """
                if isinstance(message, list):
                    for segment in message:
                        if segment.get("type") == "reply":
                            reply_id = segment.get("data", {}).get("id")
                            if reply_id is not None:
                                return str(reply_id)
                    return None
            
                if isinstance(message, str):
                    match = re.search(r"\[CQ:reply,id=(-?\d+)\]", message)
                    if match:
                        return match.group(1) #捕获到 id 数字后，返回 数字
            
                return None
            ```
            
            ```python
            5
            def extract_image_urls(message: Any) -> list[str]:
                """
                从消息中提取图片地址。
                """
                image_urls = []
            
                if isinstance(message, list):  #判断信息是否为列表类型
                    for segment in message:
                        if segment.get("type") == "image":  #只处理 image 段
                            image_data = segment.get("data", {})  #先取data 避免缺失报错
                            image_url = image_data.get("url") or image_data.get("file")
                            #先尝试拿到 url ，没有就退一步拿 file 
                            if image_url:
                                image_urls.append(image_url)
                    return image_urls
            
                if isinstance(message, str):
                    matches = re.finditer(r"\[CQ:image,[^\]]*url=([^,\]]+)", message)
                    for match in matches:
                        image_urls.append(match.group(1))
            
                return image_urls
            ```
            
        - AooDispatcher.py　　　　　　　 dispatcher 调度员 作用是获取指令后取分配任务给模块函数
            
            ```python
            import asyncio    #异步函数模块
            from app.AppOnebot_api import get_reply_image_url as _get_reply_image_url
            from app.AppManga_service import search_manga_by_image
            from app.AppSearch_service import search_image_by_saucenao
            from app.AppJm_handler import handle_jm, handle_jmzip
            from psutil import cpu_percent, virtual_memory   #给.ping读取系统状态用的
            ```
            
            ```python
            AVAILABLE_COMMANDS = [
                ("搜漫画", "回复图片搜索漫画"),
                ("搜图",   "回复图片以图搜图"),
                (".jm",    "下载本子，格式：.jm [ID]"),
                (".jmzip", "打包下载本子，格式：.jmzip [ID]"),
                (".list",  "显示所有指令"),
                (".ping",  "查看系统状态"),
            ]
            #.list 指令清单
            ```
            
            ```python
            async def dispatch_command(command: str | None, parsed: dict) -> str: 
            ```
            
            ```python
            if command is None:
                return "" 
            ```
            
            ```python
            if command in {"搜漫画", ".搜漫画"}:
                image_url, error_message = await _get_reply_image_url(parsed)
                if error_message:
                    return error_message
            		#有url就继续，没有则返回
            		
                manga_result = await search_manga_by_image(image_url)
                print("dispatch -> manga_result:", manga_result)
            		#把 有图片的 URL 送到 漫画搜索模块 ， 并把结果赋值
            		
                if not manga_result:
                    return "搜漫画失败：没有拿到可用候选结果"
            
                similarity = manga_result.get("similarity", "未知")
                title = manga_result.get("title", "未知")
                source_url = manga_result.get("source_url", "无")
                index_name = manga_result.get("index_name", "未知")
                manga_id = manga_result.get("manga_id", "未知")
                total_pages = manga_result.get("total_pages", "未知")
                native_title = manga_result.get("native_title")
                note = manga_result.get("note")
            		#把结果字典，进行单独赋值，以便后续拆分
            		
                lines = [
                    "搜漫画结果：",
                    f"相似度：{similarity}",
                    f"标题：{title}",
                    f"来源：{source_url}",
                    f"索引：{index_name}",
                ]
            		
                if manga_result.get("source") == "nhentai":
                    lines.append(f"作品ID：{manga_id}")
                    lines.append(f"页数：{total_pages}")
            		#如果来源是 nhentai 则补充专属字段
            		
                if native_title:
                    lines.append(f"原生标题：{native_title}")
                if note:
                    lines.append(f"说明：{note}")
            		#有就补充字段
            		
                return "\n".join(lines)
                #把列表变成多行字符串
            ```
            
            ```python
            if command in {"搜图", ".搜图"}:
                image_url, error_message = await _get_reply_image_url(parsed)
                if error_message:
                    return error_message
            	
            
                search_result = await search_image_by_saucenao(image_url)
                print("dispatch -> search_result:", search_result)
            
                if not search_result:
                    return "搜图失败：没有找到结果"
            
                similarity = search_result.get("similarity", "未知")
                title = search_result.get("title", "未知")
                source_url = search_result.get("source_url", "无")
                index_name = search_result.get("index_name", "未知")
            
                return (
                    f"搜图结果：\n"
                    f"相似度：{similarity}\n"
                    f"标题：{title}\n"
                    f"来源：{source_url}\n"
                    f"索引：{index_name}"
                )
            ```
            
            ```python
            user_id = str(parsed.get("user_id", ""))
            group_id = parsed.get("group_id")
            #获取用户 ID 和群聊 ID
            ```
            
            ```python
            if command.startswith(".jm "): #字符串.startswith(前缀) 用来判断是否为 .jm 开头
                if not group_id:
                    return "该命令仅限群聊使用"
                    
                parts = command.split() 
                #默认按空白分割，遇到空格就切开 .jm 472537 -> [".jm", "472537"]
                
                if len(parts) != 2 or not parts[1].isdigit(): #判断是否被分开和第二段是否为数字
                    return "请注意格式：.jm [本子ID]，例如 .jm 472537"
                    
                asyncio.create_task(handle_jm(user_id, group_id, parts[1])) 
                #创建个task任务，把任务挂事件循环后台
                return ""
                
            ```
            
            ```python
            if command.startswith(".jmzip "):
                if not group_id:
                    return "该命令仅限群聊使用"
                parts = command.split()
                if len(parts) != 2 or not parts[1].isdigit():
                    return "请注意格式：.jmzip [本子ID]，例如 .jmzip 472537"
                asyncio.create_task(handle_jmzip(user_id, group_id, parts[1]))
                return ""
            ```
            
            ```python
            if command == ".list":
                lines = ["可用指令："]
                for cmd, desc in AVAILABLE_COMMANDS:
                    lines.append(f"  {cmd} - {desc}")
                return "\n".join(lines)
            ```
            
            ```python
            if command == ".ping":
                cpu = cpu_percent(interval=0.5)    #取 cup 占用
                mem = virtual_memory()　　　　　　　#取 内存 信息
                return f"pong\nCPU: {cpu}%\n内存: {mem.percent}%"
            
            return ""
            ```
            
        - AppSearch_service.py                        Search_service 搜图模块
            
            ```python
            import httpx　　　#用来发送 http 请求的
            from app.AppConfig import SAUCENAO_API_KEY
            ```
            
            ```python
            def _contains_keywords(text: str | None, keywords: list[str]) -> bool:
                if not text:
                    return False
                lower_text = str(text).lower() #统一转小写
                return any(keyword in lower_text for keyword in keywords) 
            	   #判断是否有有关漫画的关键词出现在其中
            ```
            
            ```python
            def is_manga_candidate(search_result: dict | None) -> bool: #搜图与漫画筛选
                if not search_result:
                    return False
            
                keywords = [
                    "manga",
                    "comic",
                    "doujin",
                    "doujinshi",
                    "nhentai",
                ]
            
                index_name = search_result.get("index_name")
                source_url = search_result.get("source_url")
            
                raw_result = search_result.get("raw_data", {})
                raw_header = raw_result.get("header", {})
                raw_data = raw_result.get("data", {})
            
                candidate_texts = [
                    index_name,
                    source_url,
                    raw_header.get("index_name"),
                    raw_data.get("title"),
                    raw_data.get("eng_name"),
                    raw_data.get("jp_name"),
                    raw_data.get("source"),
                ]
            		#把所有可能暴露“漫画属性”的字段都收集起来
            		
                for text in candidate_texts:
                    if _contains_keywords(text, keywords):
                        return True
            		#候选文本有意向命中关键词，就判定为漫画候选
            		
                return False
            ```
            
            ```python
            def _build_candidate(best_result: dict) -> dict:  
                header = best_result.get("header", {})
                data = best_result.get("data", {})
            
                ext_urls = data.get("ext_urls", [])
                source_url = ext_urls[0] if ext_urls else data.get("source")
            
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
                #通用化外来格式，方便后续函数调用
            ```
            
            ```python
            #核心函数
            async def search_image_candidates_by_saucenao(image_url: str) -> list[dict]:
                """
                返回 SauceNAO 前 10 条候选结果，给搜漫画分支使用。
                """
                if not SAUCENAO_API_KEY:
                    print("[SauceNAO] API key 未配置")
                    return []
            		#检查密钥配置
            		
                url = "https://saucenao.com/search.php"
            
                params = {
                    "output_type": 2,
                    "api_key": SAUCENAO_API_KEY,
                    "url": image_url,
                    "numres": 10,  #希望返回的结果数量
                }
            		#组合查询函数
            		
                try:
                    async with httpx.AsyncClient(timeout=20) as client:
                    #创建一部客户端，总超时时间设置为20秒
                        response = await client.get(url, params=params)
                        #用client身份 去 get 网页
            
                        print("[SauceNAO] status:", response.status_code)
                        print("[SauceNAO] body:", response.text[:1000])
            						#第一行 打印HTTP状态码 ， 第二行打印响应体前一千字符
            						
                        if response.status_code != 200:
                            return []
                        #无正确返回，当失败处理
            
                        result = response.json()
                        #把接口响应 转成 py 字典
            
                    results = result.get("results", [])
                    if not results:
                        return []
                     #取核心结果
            
                    return [_build_candidate(item) for item in results[:3]]
            				#返回前三条
            				
                except Exception as e:
                    print("[SauceNAO] error:", e)
                    return []
            ```
            
            ```python
            async def search_image_by_saucenao(image_url: str) -> dict | None:
                """
                保持给“搜图”用：默认取第一条候选。
                """
                candidates = await search_image_candidates_by_saucenao(image_url)
                return candidates[0] if candidates else None
                
            ```
            
        - AppManga_service.py　　　　　   Manga_service 漫画模块 搜索和判断漫画，并给出最优结果
            
            ```python
            import re　　　　　#正则模块
            import httpx　　　 #py 的 http 客户端，让程序能访问网页
            from app.AppSearch_service import (
                search_image_candidates_by_saucenao,
                is_manga_candidate,
            )
            from app.AppConfig import NHENTAI_API_BASE
            ```
            
            ```python
            HEADERS = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            #固定请求头 后续请求 nHentai 详情接口 会带上这个 User-Agent
            ```
            
            ```python
            async def fetch_nhentai_details(manga_id: str | int) -> dict | None:
                """直接调用 nHentai API 获取漫画详情"""
                url = f"{NHENTAI_API_BASE}/{manga_id}"  #拼接 完整请求地址
                try:
                    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
                        #创建异步 HTTP 客户端 请求头为HEADERS 超时时间为 10 秒
                        response = await client.get(url)
                        print("[fetch_nhentai_details] status:", response.status_code)
                        if response.status_code == 200:
                            return response.json() #状态码 正确 就返回 json
                except Exception as e:
                    print(f"[fetch_nhentai_details] error: {e}")
                return None
            ```
            
            ```python
            def _collect_candidate_urls(candidate: dict) -> list[str]:
                """
                把一条候选里所有可能有用的 URL 都收集起来。
                """
                urls = []
            
                source_url = candidate.get("source_url")
                if source_url:
                    urls.append(source_url) #将整理好的来源链接，放进去
            
                raw_result = candidate.get("raw_data", {})
                data_part = raw_result.get("data", {})
            
                ext_urls = data_part.get("ext_urls", [])
                if isinstance(ext_urls, list):
                    for url in ext_urls:
                        if url and url not in urls:
                            urls.append(url)
            
                source = data_part.get("source")
                if source and source not in urls:　#如原始数据有 source 字段也补进去
                    urls.append(source)
            		
                return urls
            ```
            
            ```python
            def _extract_nhentai_id_from_url(url: str) -> str | None:
                match = re.search(r"nhentai\.net/g/(\d+)", url)
                if match:
                    return match.group(1)
                return None
                #提炼出 含有 nhentai 相关的 url
            ```
            
            ```python
            def _extract_nhentai_id(candidate: dict) -> str | None:
                """
                从候选结果中尽可能多地尝试提取 gallery id。
                """
                raw_result = candidate.get("raw_data", {})
                data_part = raw_result.get("data", {})
            
                nh_id = data_part.get("nhentai_id")
                if nh_id:
                    return str(nh_id)
                #原始数据有 nh_id 就直接返回 
            
                for url in _collect_candidate_urls(candidate):
                    parsed_id = _extract_nhentai_id_from_url(url)
                    if parsed_id:
                        return parsed_id
            		#一个个提炼出有可用 url 并收集起来
            		
                return None
            ```
            
            ```python
            def _manga_score(candidate: dict) -> int:
                """
                给候选打分，分越高越像漫画结果。
                """
                score = 0
            
                if is_manga_candidate(candidate): #基础漫画关键词匹配
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
            		#sauceNAO 搜索词本身也匹配 加分
            		
                try:
                    similarity = float(candidate.get("similarity", 0))
                    if similarity >= 80:
                        score += 2
                    elif similarity >= 60:
                        score += 1
                except Exception:
                    pass
            
                return score
            ```
            
            ```python
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
                #做降序排序，匹配度高的在前
            
                print("[search_manga_by_image] scored_candidates:", scored_candidates)
            
                for candidate in scored_candidates:
                    nh_id = _extract_nhentai_id(candidate)
                    print("[search_manga_by_image] trying nh_id:", nh_id, "candidate:", candidate)
            
                    if not nh_id:
                        continue
            				#尝试候选
            				
                    detail = await fetch_nhentai_details(nh_id)
                    print("[search_manga_by_image] detail:", detail)
            				#拿到 ID 后 就去请求详情接口
            				
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
                
            ```
            
        - AppOnebot_api.py　　　　　　　通信模块 主要负责前后端串联起来（bot/fastapi）
            
            ```python
            import os
            import httpx
            from app.AppConfig import NAPCAT_API_URL, NAPCAT_TOKEN, PUBLIC_BASE_URL
            ```
            
            ```python
            def build_headers() -> dict:
                """
                给 NapCat API 请求构造请求头。
                如果配置了 token，就带上 Authorization。
                """
                if NAPCAT_TOKEN:
                    return {"Authorization": f"Bearer {NAPCAT_TOKEN}"}
                return {}
            ```
            
            ```python
            async def send_group_message(group_id: int, message: str) -> None:
                """
                发送群消息。
                group_id: 群号
                message: 要发送的文本内容
                """
                url = f"{NAPCAT_API_URL}/send_group_msg" #NapCat 发群消息接口路径
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
            ```
            
            ```python
            async def get_msg(message_id: str | int) -> dict | None:
                """
                根据 message_id 获取某条历史消息的详细内容。
                message_id: 消息编号，可以是字符串，也可以是整数
                return: 如果成功，返回 NapCat 返回的 data 部分；失败返回 None
                """
                url = f"{NAPCAT_API_URL}/get_msg" #此 get_msg 是 napcat 专用接口
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
            ```
            
            ```python
            async def get_reply_image_url(parsed: dict) -> tuple[str | None, str | None]:
                """
                从被回复消息中提取图片 URL。
                返回 (image_url, error_message)。成功时 error_message 为 None，
                失败时 image_url 为 None。
                """
                from app.AppParser import extract_reply_id, extract_image_urls
            
                reply_id = extract_reply_id(parsed.get("message"))
                if not reply_id:
                    return None, "未找到回复 ID，请在消息中引用（回复）一张图片"
            
                replied_msg = await get_msg(reply_id)
                if not replied_msg:
                    return None, f"无法获取被回复消息 {reply_id} 的内容"
            
                replied_message = replied_msg.get("message")
                image_urls = extract_image_urls(replied_message) #获取图片 url 
            
                if not image_urls:
                    return None, "被回复的消息中没有找到图片"
            
                return image_urls[0], None
            ```
            
            ```python
            def build_public_file_url(file_path: str) -> str:
                """
                把容器内文件路径转换为 FastAPI 可公开访问的 URL。
                例如：
                /workspace/cache/jm_download/903485102/86632/86632.pdf
                ->
                http://192.168.61.128:8000/public/903485102/86632/86632.pdf
                """
                prefix = "/workspace/cache/jm_download/"
                normalized = file_path.replace("\\", "/") #替换成 linux 风格的路径
            
                if not normalized.startswith(prefix):
                    raise ValueError(f"文件路径不在公开目录下: {file_path}")
            
                relative_path = normalized[len(prefix):]
                return f"{PUBLIC_BASE_URL}/public/{relative_path}"
            ```
            
            ```python
            async def upload_group_file(group_id: int, file_path: str) -> dict | None:
                """
                上传文件到群文件列表。
                这里不传 base64，不传 multipart，不传本地路径。
                直接传 FastAPI 暴露出来的 HTTP 下载地址。
                """
                url = f"{NAPCAT_API_URL}/upload_group_file" #napcat 上传群文件的 接口
                file_name = os.path.basename(file_path) #取在 完整路径 的 文件名
            
                if not os.path.exists(file_path):
                    print("[upload_group_file] file not found:", file_path)
                    return None
            
                try:
                    public_url = build_public_file_url(file_path)
                except Exception as e:
                    print("[upload_group_file] build_public_file_url error:", e)
                    return None
                    #构造公开 URL 把 本地路径 转为 可访问外链
            
                payload = {
                    "group_id": group_id,
                    "file": public_url,
                    "name": file_name,
                }
            
                try:
                    async with **httpx.AsyncClient**(timeout=120) as client:
                        response = await client.post(
                            url,
                            json=payload,
                            headers=build_headers(),
                        )
                        #发送上传请求， 源文件传输可能会慢 ，所以 超时时间为 120 秒
                        
                        print("[upload_group_file] status:", response.status_code)
                        print("[upload_group_file] payload:", payload)
                        print("[upload_group_file] body:", response.text[:500])
            						#打印详细日志
            						
                        result = response.json()
                        if result.get("status") == "ok":
                            return result.get("data")
            						
                        return None  
            
                except Exception as e:
                    print("[upload_group_file] error:", e)
                    return None
            ```
            
            ```python
            async def get_group_root_files(group_id: int) -> list[dict]:
                """
                获取群根目录文件列表。
                """
                url = f"{NAPCAT_API_URL}/get_group_root_files" #调用群根目录文件接口
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
            ```
            
            ```python
            async def upload_to_fileio(file_path: str) -> str | None:
                """
                将文件上传到 file.io，返回下载 URL。失败返回 None。
                """
                url = "https://file.io/"
                file_name = os.path.basename(file_path)
            
                if not os.path.exists(file_path): # exists 判断文件夹是否存在并返回 -> bool
                    print("[upload_to_fileio] file not found:", file_path)
                    return None
            
                try:
                    with open(file_path, "rb") as f:
                        files = {"file": (file_name, f)}
                        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                            response = await client.post(url, files=files)
            				#打开文件传入的文件 ， 构造 multipart
            				
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
              
            ```
            
            ```python
            async def upload_group_file_by_url(group_id: int, file_url: str, file_name: str) -> dict | None:
                """
                通过程序配置好的下载 URL 将文件上传到群文件列表。
                主要作用是告诉 napcat ，
                把已经下载处理好的文件并外链的 url 调用 上传到群文件里。
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
            ```
            
            ```python
            async def delete_group_file(group_id: int, file_id: str, busid: int) -> bool:
                """
                告诉 napcat 执行 删除群文件的操作。
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
            ```
            
        - AppJm_downloader.py　　　　　负责下载本子，整理文件与路径，清理过期/旧文件
            
            ```python
            import os
            import shutil
            from pathlib import Path
            import asyncio
            
            from jmcomic import create_option, download_album
            ```
            
            ```python
            CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
            # __file__ 当前文件路径 ，.resolve() 转成绝对路径 ，
            # .parent.parent 回退两层目录 ， / "cache" 再拼上 cache 目录
            
            JM_CONFIG_FILE = CACHE_DIR / "jm_config.yml"
            JM_DOWNLOAD_DIR = CACHE_DIR / "jm_download"
            ```
            
            ```python
            def get_option():
                return create_option(str(JM_CONFIG_FILE))
                #读取 jm_config.yml ，拿取下载参数
            ```
            
            ```python
            async def download_album_by_id(album_id: str, option):
                album, _ = await asyncio.to_thread(download_album, album_id, option=option)
                return album
                #根据 album_id 调用 jmcomic 下载 album，并返回下载结果里的 album 对象
            ```
            
            ```python
            def move_album_dirs_by_photo_titles(album, user_id: str) -> str:
                album_id = album.album_id
                target_dir = JM_DOWNLOAD_DIR / user_id / album_id
                os.makedirs(target_dir, exist_ok=True)
                #拿取本子 ID
                #构建目标目录
                #父级目录不存在就创建
            
                for photo in album:
                    title = photo.title 
                    
                    if not title or not str(title).strip(): #空标题判断
                        print(f"[MOVE] Skip photo with empty title: photo_id={getattr(photo, 'photo_id', '?')}")
                        continue
                        #后续需要拿tiitle来拼路径，如果是空字符会出现异常
                        
                    source = JM_DOWNLOAD_DIR / title  #title 拼接
                    
                    if source == JM_DOWNLOAD_DIR:  #路径保护，防止路径等于下载目录本身
                        print(f"[MOVE] Skip invalid source (equals JM_DOWNLOAD_DIR): title={repr(title)}")
                        continue
                        
                    target = target_dir / title #拼接目录
                    
                    if source.exists(): #源目录存在判断
                        if target.exists(): 
                            shutil.rmtree(target) #如果目标目录已存在则删除旧䣌
                        shutil.move(str(source), str(target)) #把原始章节目录移动到整理后的结构里
            
                return str(target_dir)  #返回整理后的本子根目录字符串路径
            ```
            
            ```python
            def safe_cleanup(user_id: str, album_id: str):
            '''
            安全清理 本子 缓存
            删除当前本子目录，如用户目录空了，再顺手删掉用户目录
            '''
                user_path = JM_DOWNLOAD_DIR / user_id
                album_path = user_path / album_id
            
                if album_path.exists(): #路径存在则 true
                    try:
                        shutil.rmtree(album_path)
                        print(f"[CLEANUP] Deleted album: {album_path}")
                    except Exception as e:
                        print(f"[CLEANUP ERROR] Failed to delete album dir: {e}")
            
                if user_path.exists() and not any(user_path.iterdir()):
                    try:
                        shutil.rmtree(user_path)
                        print(f"[CLEANUP] Deleted empty user dir: {user_path}")
                    except Exception as e:
                        print(f"[CLEANUP ERROR] Failed to delete user dir: {e}")
            ```
            
        - AppJm_tools.py                                   处理下载好的本子，生成pdf/zip
            
            ```python
            import os
            from PIL import Image      #打开图片把多张图片保存成为pdf
            import zipfile             #把多个章节的pdf打包成为zip包
            ```
            
            ```python
            def images_to_pdf(image_dir, output_pdf_path):
            '''
             把下载好的多张图片合成一个pdf
            '''
                images = []
                
                for file in sorted(os.listdir(image_dir)): #列出目录下的所有文件
                    if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")): #筛选图片类型
                        img_path = os.path.join(image_dir, file) #拼接图片路径
                        img = Image.open(img_path).convert("RGB") #打开图片并转 RGB
            	            images.append(img) 
            
                print(f"[DEBUG] Converting {len(images)} images from {image_dir} to PDF")
            		#打印日志
            		
                if images:
                    images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
                    #只有有图片时才保存pdf
            ```
            
            ```python
            def batch_chapter_to_pdfs(album_dir):
            '''
            把本子目录的多个章节目录，批量转成多个pdf
            '''
                pdf_paths = [] #收集成功的pdf路径，给后续zip打包用
                
                for chapter in sorted(os.listdir(album_dir)): #sorted 降序排序
                    chapter_dir = os.path.join(album_dir, chapter) #拼章节目录路径
                    if os.path.isdir(chapter_dir): #只处理目录
                        pdf_path = os.path.join(album_dir, f"{chapter}.pdf") #生成每章pdf路径
                        images_to_pdf(chapter_dir, pdf_path)
                        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0: #判断生成是否成功
                            pdf_paths.append(pdf_path)
            
                return pdf_paths #返回路径
            ```
            
            ```python
            def zip_pdfs(pdf_paths, zip_path):
            '''
            压缩包制作
            '''
                with zipfile.ZipFile(zip_path, "w") as zipf: # 'w' 写模式，存在zip 会覆盖重写
                    for pdf in pdf_paths:
                        zipf.write(pdf, arcname=os.path.basename(pdf))
            ```
            
        - AppJm_handler.py
            
            ```python
            import asyncio
            import os
            from app.AppJm_downloader import (
                get_option,
                download_album_by_id,
                move_album_dirs_by_photo_titles,
                safe_cleanup,
                JM_DOWNLOAD_DIR,
            )
            from app.AppJm_tools import images_to_pdf, batch_chapter_to_pdfs, zip_pdfs
            from app.AppOnebot_api import (
                send_group_message,
                upload_group_file,
                get_group_root_files,
                delete_group_file,
            )
            ```
            
            ```python
            active_tasks: dict[str, bool] = {}
            ```
            
            ```python
            async def send_group_file(group_id: int, file_path: str, file_name: str):
                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                    await send_group_message(group_id, "文件未找到，暂时无法上传...")
                    return
            
                file_size_mb = os.path.getsize(file_path) / 1024 / 1024
                if file_size_mb > 90:
                    await send_group_message(
                        group_id,
                        f"阁下需要的资源体积较大（{file_size_mb:.2f} MB），请耐心等待…"
                    )
            
                await send_group_message(group_id, "正在提交到群文件...")
                uploaded = await upload_group_file(group_id, file_path)
                if not uploaded:
                    await send_group_message(group_id, "文件上传失败，NapCat 可能不支持此操作，请检查 NapCat 配置")
                    return
            
                await send_group_message(
                    group_id,
                    f"[文件]{file_name} 上传成功，野寻将在一分半后销毁它…"
                )
            
                await asyncio.sleep(5)
            
                file_list = await get_group_root_files(group_id)
                target_file = next(
                    (f for f in file_list if f["file_name"] == file_name), None
                )
            
                if not target_file:
                    await send_group_message(
                        group_id,
                        "上传后未找到群文件，可能已经被野寻弄坏了..."
                    )
                    return
            
                await asyncio.sleep(85)
                await delete_group_file(
                    group_id,
                    target_file["file_id"],
                    target_file["busid"]
                )
            ```
            
            ```python
            async def handle_jm(user_id: str, group_id: int, album_id: str):
                if active_tasks.get(user_id, False):
                    await send_group_message(
                        group_id,
                        "阁下的上一个请求还在处理，稍微耐心一些..."
                    )
                    return
            
                active_tasks[user_id] = True
            
                try:
                    await send_group_message(
                        group_id,
                        f"已接收到阁下的请求，开始收集材料 {album_id}，请稍候…"
                    )
            
                    safe_cleanup(user_id, album_id)
            
                    option = get_option()
                    album = await download_album_by_id(album_id, option)
                    album_dir = move_album_dirs_by_photo_titles(album, user_id)
            
                    if not os.path.exists(album_dir):
                        await send_group_message(group_id, "下载任务失败：主目录不存在")
                        return
            
                    subdirs = sorted([
                        d for d in os.listdir(album_dir)
                        if os.path.isdir(os.path.join(album_dir, d))
                    ])
                    image_files = [
                        f for f in os.listdir(album_dir)
                        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                    ]
            
                    if len(subdirs) == 0 and image_files:
                        pdf_path = os.path.join(album_dir, f"{album_id}.pdf")
                        await asyncio.to_thread(images_to_pdf, album_dir, pdf_path)
                        await send_group_file(group_id, pdf_path, f"{album_id}.pdf")
            
                    elif len(subdirs) == 1:
                        chapter_dir = os.path.join(album_dir, subdirs[0])
                        pdf_path = os.path.join(album_dir, f"{album_id}.pdf")
                        await asyncio.to_thread(images_to_pdf, chapter_dir, pdf_path)
                        await send_group_file(group_id, pdf_path, f"{album_id}.pdf")
            
                    else:
                        pdf_paths = await asyncio.to_thread(
                            batch_chapter_to_pdfs, album_dir
                        )
                        if not pdf_paths:
                            await send_group_message(
                                group_id,
                                "没有发现可以打包的章节 PDF 文件"
                            )
                            return
                        zip_path = os.path.join(album_dir, f"{album_id}.zip")
                        await asyncio.to_thread(zip_pdfs, pdf_paths, zip_path)
                        await send_group_file(group_id, zip_path, f"{album_id}.zip")
            
                    await asyncio.sleep(1)
                    safe_cleanup(user_id, album_id)
            
                except Exception as e:
                    await send_group_message(group_id, f"发生错误：{e}")
                finally:
                    active_tasks[user_id] = False
            ```
            
            ```python
            async def handle_jmzip(user_id: str, group_id: int, album_id: str):
                if active_tasks.get(user_id, False):
                    await send_group_message(
                        group_id,
                        "阁下的上一个请求还在处理，稍微耐心一些..."
                    )
                    return
            
                active_tasks[user_id] = True
            
                try:
                    album_dir = os.path.join(JM_DOWNLOAD_DIR, user_id, album_id)
                    zip_path = os.path.join(album_dir, f"{album_id}.zip")
            
                    if not os.path.exists(album_dir):
                        await send_group_message(
                            group_id,
                            "阁下所需要的材料还未缓存，请先使用 .JM 下载"
                        )
                        return
            
                    if not os.path.exists(zip_path):
                        pdf_paths = await asyncio.to_thread(
                            batch_chapter_to_pdfs, album_dir
                        )
                        if not pdf_paths:
                            await send_group_message(
                                group_id,
                                "没有发现可以打包的 PDF 文件"
                            )
                            return
                        await asyncio.to_thread(zip_pdfs, pdf_paths, zip_path)
            
                    await send_group_file(group_id, zip_path, f"{album_id}.zip")
                    await asyncio.sleep(1)
                    safe_cleanup(user_id, album_id)
            
                except Exception as e:
                    await send_group_message(group_id, f"发生错误：{e}")
                finally:
                    active_tasks[user_id] = False
            ```
            
        - AppConfig.py　　　　　                环境变量
            
            ```docker
            import os
            ```
            
            ```python
            #将系统环境配置 传参 以便后续开发调用
            NAPCAT_API_URL = os.getenv("NAPCAT_API_URL", "http://192.168.61.128:3000")
            NAPCAT_TOKEN = os.getenv("NAPCAT_TOKEN", "")
            SAUCENAO_API_KEY = os.getenv("SAUCENAO_API_KEY", "")
            NHENTAI_API_BASE = os.getenv("NHENTAI_API_BASE", "https://nhentai.net/api/gallery/")
            PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://192.168.61.128:8000")
            ```
            
            ```python
            #与上一样，但是是获取群号的，并制作能被使用的参数
            ALLOW_GROUP_IDS = {
                int(x.strip())
                for x in os.getenv("ALLOW_GROUP_IDS", "").split(",")
                if x.strip().isdigit()
            }
            ```
            
        
    - cache 缓存目录
        - jm_config.yml
            
            ```yaml
            client:
              cache: null
              domain:
                html:
                  - 18comic.org
                api:
                  - www.cdnhth.club
                  - www.cdngwc.cc
                  - www.cdngwc.net
                  - www.cdngwc.club
                  - www.cdnhjk.cc
              impl: api
              postman:
                meta_data:
                  headers: null
                  impersonate: chrome110
                  proxies: {}
                type: cffi
              retry_times: 5
            dir_rule:
              base_dir: /workspace/cache/jm_download
              rule: Bd_Pname
            download:
              cache: true
              image:
                decode: true
                suffix: null
              threading:
                image: 6
                photo: 3
            log: true
            plugins:
              valid: log
            version: '2.1'
            
            ```