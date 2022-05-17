import os
import requests
from hashlib import md5


def main(url, dest_path):
    file_name = md5(url.encode('utf-8')).hexdigest()
    response = requests.get(url)

    if response.status_code != 200 or response.content == b'':
        return None

    content_type = response.headers['content-type']
    extension = 'mp3'
    if content_type == 'audio/mpeg':
        extension = 'mp3'
    else:
        pass

    file_path = f'{os.path.join(dest_path, file_name)}.{extension}'
    with open(file_path, 'wb') as f:
        f.write(response.content)

    return file_path
