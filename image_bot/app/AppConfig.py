import os

NAPCAT_API_URL = os.getenv("NAPCAT_API_URL", "http://192.168.61.128:3000")
NAPCAT_TOKEN = os.getenv("NAPCAT_TOKEN", "")
SAUCENAO_API_KEY = os.getenv("SAUCENAO_API_KEY", "")
NHENTAI_API_BASE = os.getenv("NHENTAI_API_BASE", "https://nhentai.net/api/gallery/")

ALLOW_GROUP_IDS = {
    int(x.strip())
    for x in os.getenv("ALLOW_GROUP_IDS", "").split(",")
    if x.strip().isdigit()
}