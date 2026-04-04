# Agent API

基于 FastAPI 的认证系统，使用 MySQL 数据库存储用户数据。

## 功能

- 用户注册
- 用户登录 (JWT Token)
- 获取当前用户信息

## 技术栈

- FastAPI
- SQLAlchemy
- MySQL
- JWT Authentication

## 快速开始

### 本地开发

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置环境变量 (.env):
```env
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
DB_PASSWORD=your-db-password
```

3. 启动服务:
```bash
uvicorn app.main:app --reload
```

### Docker 部署

```bash
docker-compose up -d
```

## API 端点

- POST `/api/v1/auth/register` - 用户注册
- POST `/api/v1/auth/login` - 用户登录
- GET `/api/v1/users/me` - 获取当前用户信息
