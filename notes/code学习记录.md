# code学习记录

当前服务器密码:

LaiHongTao123

---

## 3.10号

重装了我的服务器

安装了tmux，swap，docker

tmux主要是用来保存会话记录的，防止突然的服务器断联然后重回时消息记录没了

swap的作用主要是扩内存，主要原理就是拿硬盘的一部分来充当内存，但其速率远远小于真内存，仅防止突然的内存溢出

docker容器沙盒，主要作用是隔离各个工作空间的

```bash
# 启动一个新会话，名称为 my_session
tmux new -s my_session
# 在当前会话中创建新窗口
Ctrl-b c
# 水平分割当前窗格
Ctrl-b %
# 垂直分割当前窗格
Ctrl-b "
# 在窗格之间切换
Ctrl-b 方向键
# 分离当前会话（保持后台运行）
Ctrl-b d
# 列出所有会话
tmux ls
# 重新附着到会话 my_session
tmux attach -t my_session
# 关闭当前窗格或窗口（直接输入 exit 或按 Ctrl-d）
exit
```

---

## 3.12

在本机上制作了三个文件分别为

[main.py](http://main.py)     requirements.txt     dockerfile

[main.py](http://main.py)主要作用是发送内容给网页

requirements.txt主要作用是用来告诉启动程序，这个程序主要是需要什么内容库（ requirements是py库的写法，其他语言也有类似的txt文件但前缀不一）

![image.png](image.png)

dockerfile这个文件就是告诉docker，我们启动沙盒主要需要什么功能什么导向

scp .\[main.py](http://main.py) .\requirements.txt .\Dockerfile root@108.187.15.71:~/my_first_api/

这个代码主要是用来传输我们那三个文件到我们服务器指定的文件夹的

打开cmd用shell来发送比较方便，原来的cmd有点白痴

scp xx（打出文件名Tap就好了）用户名@服务器ip:~/项目文件地址

![image.png](image%201.png)

---

## 3.13

写了个docker-compose.yml

```
version: '3.8'

services:
  # 服务1：你的 FastAPI 后端
  web:
    build: .          # 告诉 docker-compose，去当前目录找 Dockerfile 现场打包镜像
    container_name: agent_api
    ports:
      - "8000:8000"   # 暴露给外网的端口
    depends_on:
      - db            # 核心逻辑：告诉系统，必须等数据库 db 启动了，才能启动 web

  # 服务2：MySQL 8.0 数据库
  db:
    image: mysql:8.0  # 直接拉取官方做好的纯净版 MySQL 8.0 镜像
    container_name: agent_mysql
    ports:
      - "3306:3306"   # 为了你后续在本地用 Navicat 连服务器查数据，先把 3306 暴露出来
    environment:
      MYSQL_ROOT_PASSWORD: "ddac#af**%3"  # 数据库的 Root 密码，严禁改得太简单
      MYSQL_DATABASE: agent_db     # 启动时自动
      
      创建一个名为 agent_db 的空库
    volumes:
      - mysql_data:/var/lib/mysql    # 核心防御：数据持久化。如果不写这个，容器一重启，你存的数据就全丢了！

# 声明需要用到的硬盘卷
volumes:
  mysql_data:
```

按我的理解来讲一遍代码

version 这个就是指定版本，docker-compose有好多版本

services：就是告诉服务要用到的东西
web：和db 一个指网页一个指数据库的配置

build: . 这段说他要开始构筑，默认情况下Docker会在构建上下文中找“Dockerfile”，而“ . ”点就是说在这个文件夹底下找到“Dockerfile”，然后发送到Docker守护进程

container_name:agent_mysql 意思就是这个定义这个沙箱的名称为 agent_mysql

ports:  这个就是设置端口   “-”号在YAML语法短横线表示列表项（数组元素）的开始，主要告诉解析器后面的这个值属于一个列表，列表的一个条目

要是想映射多个端口就这样写法

```yaml
ports:
	- "8000:8000" # 第一个端口映射
	- "3306:3306" # 第二个端口映射
```

“3306:3306”这个就表示宿主机端口:容器端口的映射,左边对外，右边对内。右边3306是MySQL的默认端口，左边的是外部过来访问3306这个端口。要是左边的3306端口被占用了，用其他端口都可以，这是左边映射右边的结果

environment:
      MYSQL_ROOT_PASSWORD: "ddac#af**%3"  
      MYSQL_DATABASE: agent_db

environment: 向容器内部传递环境变量，就像后面那俩行告诉容器数据库的密码和database的名称，也可在加其他变量

volumes:
      - mysql_data:/var/lib/mysql

volumes:声明命名卷，类似创建变量，下方则是告诉‘docker’数据存放的地址

最下面的这个

```yaml
# 声明需要用到的硬盘卷
volumes:
  mysql_data:
```

外部声明 = 准备一个保险箱（命名卷），告诉 Docker 你要用这个保险箱。

内部声明 = 告诉容器：“把你重要的文件（数据库数据）放进这个保险箱里”。

容器只负责放文件，保险箱由 Docker 保管。
（这个deepseek讲的很清晰了，就不做理解更改贴上来了）