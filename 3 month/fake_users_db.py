# fake_users_db.py
#py字典，临时假DB，对应main.py中fake_users_db的用法：username -> password（或哈希）
#仅用于开发/联调，勿用于生产。
fake_users_db = {
  "admin": "$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
}
