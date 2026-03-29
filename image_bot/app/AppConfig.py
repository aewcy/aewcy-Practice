import os

NAPCAT_API_URL = os.getenv("NAPCAT_API_URL", "http://192.168.61.128:3000")

ALLOW_GROUP_IDS = {
    int(x.strip())
    for x in os.getenv("ALLOW_GROUP_IDS", "").split(",")
    if x.strip().isdigit()
}