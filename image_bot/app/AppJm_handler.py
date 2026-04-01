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


active_tasks: dict[str, bool] = {}


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

    uploaded = await upload_group_file(group_id, file_path)
    if not uploaded:
        await send_group_message(group_id, "文件上传失败，NapCat 可能不支持此操作，请检查 NapCat 配置")
        return

    await send_group_message(
        group_id,
        f"[文件]{file_name} 上传成功，奇美拉将在一分半后销毁它…"
    )

    await asyncio.sleep(5)

    file_list = await get_group_root_files(group_id)
    target_file = next(
        (f for f in file_list if f["file_name"] == file_name), None
    )

    if not target_file:
        await send_group_message(
            group_id,
            "上传后未找到群文件，可能已经被奇美拉弄坏了..."
        )
        return

    await asyncio.sleep(85)
    await delete_group_file(
        group_id,
        target_file["file_id"],
        target_file["busid"]
    )


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
