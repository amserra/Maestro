import os
import shutil
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


@app.task(bind=True)
def gather_urls(self, data_type: str, search_string: str, user_urls: list[str]):
    if data_type == 'image':  # gather images
        # Use search_string to get through SerpAPI's Google Search Engine API to gather images and also urls (2 calls)
        urls = []
    # append to the urls the user_urls
    urls.extend(user_urls)
    # save this urls to a file (to cache on further gather_urls and reduce number of API calls?)
    # pass the urls to the next function/use the file in the next function
    pass


@app.task(bind=True)
def copy_default_gatherers(self, gatherers_list):
    pass


@app.task(bind=True)
def delete_context_folder(self, owner_code, context_code):
    try:
        shutil.rmtree(f'{settings.BASE_DIR}/contexts_data/{owner_code}/{context_code}')
        return True
    except Exception as e:
        print(e)
        return False
