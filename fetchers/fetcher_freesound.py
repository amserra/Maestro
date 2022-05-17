import requests
from django.conf import settings
from operator import itemgetter


def main(data: dict):
    search_string, keywords, country_code = itemgetter('search_string', 'keywords', 'country_code')(data)

    api_key = settings.FREESOUND_KEY
    endpoint = 'https://freesound.org/apiv2/search/text/'

    params = {
        'query': search_string,
        'tags': ','.join(keywords),
        'fields': 'name,previews',
        'token': api_key
    }

    # Call the API
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        response_json = response.json()

        links = [value['previews']['preview-hq-mp3'] for value in response_json['results']]

        return links
    except requests.exceptions.RequestException as ex:
        print(ex.response.json())
        raise ex
