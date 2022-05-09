import os
import shutil

from context.models import SearchContext, THUMB_SIZE, ImageData
from maestro.celery import app
import zipfile
from PIL import Image


def generate_thumbnail(image_path, dest_folder):
    image_name = os.path.basename(image_path)
    try:
        image = Image.open(image_path)
        image.thumbnail(THUMB_SIZE)
        image.save(os.path.join(dest_folder, image_name))
    except IOError:
        pass


@app.task(bind=True)
def handle_initial_datastream(self, context_id, initial_datastream):
    context = SearchContext.objects.get(id=context_id)
    context_folder = context.context_folder
    context_folder_static = context.context_folder_static

    # Unzip
    dest_folder = os.path.join(context_folder, 'data', 'full')
    zip_files_names = zipfile.ZipFile(initial_datastream).namelist()
    with zipfile.ZipFile(initial_datastream, 'r') as zip_ref:
        zip_ref.extractall(dest_folder)

    # Generate thumbnails
    thumb_folder = os.path.join(context_folder, 'data', 'thumbs')
    for file_name in zip_files_names:
        file_path = os.path.join(dest_folder, file_name)
        thumb_path = os.path.join(thumb_folder, file_name)
        static_path = os.path.join(context_folder_static, file_name)

        generate_thumbnail(os.path.join(dest_folder, file_name), thumb_folder)
        # Copy to static folder
        shutil.copy(os.path.join(thumb_folder, file_name), context_folder_static)
        # Create data objects
        if not ImageData.objects.filter(context=context, data=file_path, data_thumb=thumb_path, data_thumb_static=static_path).exists():
            ImageData.objects.create(context=context, data=file_path, data_thumb=thumb_path, data_thumb_static=static_path)

    return True
