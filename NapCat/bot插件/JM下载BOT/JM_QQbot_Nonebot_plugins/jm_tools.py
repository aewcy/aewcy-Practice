import os
from PIL import Image
import zipfile



def images_to_pdf(image_dir, output_pdf_path):
    images = []
    for file in sorted(os.listdir(image_dir)):
        if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            img_path = os.path.join(image_dir, file)
            img = Image.open(img_path).convert("RGB")
            images.append(img)

    print(f"[DEBUG] Converting {len(images)} images from {image_dir} to PDF")

    if images:
        images[0].save(output_pdf_path, save_all=True, append_images=images[1:])


def batch_chapter_to_pdfs(album_dir):
    pdf_paths = []
    for chapter in sorted(os.listdir(album_dir)):
        chapter_dir = os.path.join(album_dir, chapter)
        if os.path.isdir(chapter_dir):
            pdf_path = os.path.join(album_dir, f"{chapter}.pdf")
            images_to_pdf(chapter_dir, pdf_path)
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                pdf_paths.append(pdf_path)

    return pdf_paths


def zip_pdfs(pdf_paths, zip_path):
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for pdf in pdf_paths:
            zipf.write(pdf, arcname=os.path.basename(pdf))
