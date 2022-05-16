import os
import shutil

from context.models import SearchContext, THUMB_SIZE, ImageData
from maestro.celery import app
import zipfile
from PIL import Image


def generate_thumbnail(image_path, dest_folder):
    image_name = os.path.basename(image_path)
    dest_image_path = os.path.join(dest_folder, image_name)
    try:
        image = Image.open(image_path)
        image.thumbnail(THUMB_SIZE)
        image.save(dest_image_path)
    except IOError as ex:
        print(ex)


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

    # Generate thumbnails and put in static folder
    thumb_folder = os.path.join(context_folder, 'data', 'thumbs')
    os.makedirs(thumb_folder, exist_ok=True)
    os.makedirs(context_folder_static, exist_ok=True)
    for file_name in zip_files_names:
        file_path = os.path.join(dest_folder, file_name)
        thumb_path = os.path.join(thumb_folder, file_name)
        static_path = os.path.join(context_folder_static, file_name)

        generate_thumbnail(image_path=file_path, dest_folder=thumb_folder)
        # Copy to static folder
        shutil.copy(os.path.join(thumb_folder, file_name), context_folder_static)
        # Create data objects
        if not ImageData.objects.filter(context=context, data=file_path, data_thumb=thumb_path, data_thumb_static=static_path).exists():
            ImageData.objects.create(context=context, data=file_path, data_thumb=thumb_path, data_thumb_static=static_path)

    return True
