from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. 封装加密函数
def get_password_hash(password: str) -> str:
    """接收明文密码，返回哈希加密后的字符串"""
    return pwd_context.hash(password)

# 3. 封装验证函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """对比明文密码和数据库中存储的哈希值，返回布尔值"""
    return pwd_context.verify(plain_password, hashed_password)

if __name__ == "__main__":
    

    users_input_password = input(str("Enter your password: "))

    get_password_hash = pwd_context.hash(users_input_password)

    stored_hash = get_password_hash

    is_correct = pwd_context.verify(users_input_password, stored_hash)

    if is_correct:
        print("Password is True")
    else:
        print("Password is False")