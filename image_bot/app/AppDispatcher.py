def dispatch_command(command:str | None) -> str | None:
    if not command:
        return None
    
    command = command.strip()

    if command == ".ping":
        return "pong"
    
    if command == ".list":
        return "当前可用命令：.ping, .list"
    
    return "无效命令"