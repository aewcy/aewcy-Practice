import os
import shutil
from pathlib import Path
import asyncio
from jmcomic import create_option, download_album

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
JM_CONFIG_FILE = CACHE_DIR / "jm_config.yml"
JM_DOWNLOAD_DIR = CACHE_DIR / "jm_download"


def get_option():
    return create_option(str(JM_CONFIG_FILE))


async def download_album_by_id(album_id: str, option):
    album, _ = await asyncio.to_thread(download_album, album_id, option=option)
    return album


def move_album_dirs_by_photo_titles(album, user_id: str) -> str:
    album_id = album.album_id
    target_dir = JM_DOWNLOAD_DIR / user_id / album_id
    os.makedirs(target_dir, exist_ok=True)

    for photo in album:
        title = photo.title
        source = JM_DOWNLOAD_DIR / title
        target = target_dir / title
        if source.exists():
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(source), str(target))

    return str(target_dir)


def safe_cleanup(user_id: str, album_id: str):
    user_path = JM_DOWNLOAD_DIR / user_id
    album_path = user_path / album_id

    if album_path.exists():
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
