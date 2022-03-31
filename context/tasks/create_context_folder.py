import os
from maestro.celery import app
from django.conf import settings


@app.task(bind=True)
def create_context_folder(self, owner_code, context_code):
    # Creates the folder and the intermediary folders if they not exist
    # If these folders already exist, keep everything and continue
    base_context_dir = f'{settings.BASE_DIR}/contexts_data/{owner_code}/{context_code}'
    os.makedirs(base_context_dir, exist_ok=True)
    os.makedirs(f'{base_context_dir}/gatherers', exist_ok=True)
    os.makedirs(f'{base_context_dir}/data', exist_ok=True)
    return True
