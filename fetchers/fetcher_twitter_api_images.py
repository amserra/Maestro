import requests
from django.conf import settings
from operator import itemgetter


def build_query(search_string, keywords):
    keywords_hashtags = ' '.join(f'#{keyword}' for keyword in keywords)
    return f'({search_string} has:images) OR ({keywords_hashtags} has:images has:hashtags)'


def main(data: dict):
    dtformat = '%Y-%m-%dT%H:%M:%SZ'
    search_string, keywords, country_code = itemgetter('search_string', 'keywords', 'country_code')(data)

    # Add your Bing Search V7 subscription key and endpoint to your environment variables.
    api_key = settings.TWITTER_API_KEY
    endpoint = 'https://api.twitter.com/2/tweets/search/recent'

    params = {
        'query': build_query(search_string, keywords),
        'expansions': 'geo.place_id,attachments.media_keys',
        'media.fields': 'preview_image_url,url',
        'place.fields': 'country,country_code,geo',
        'tweet.fields': 'created_at,lang,text',
        'max_results': 25
    }

    if 'start_date' in data and data['start_date'] is not None:
        params['start_time'] = data['start_date'].strftime(dtformat)

    if 'end_date' in data and data['end_date'] is not None:
        params['end_time'] = data['end_date'].strftime(dtformat)

    headers = {
        'Authorization': f'Bearer {api_key}',
    }

    # Call the API
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        response_json = response.json()

        links = [value['url'] for value in response_json['includes']['media']]

        return links
    except requests.exceptions.RequestException as ex:
        print(ex.response.json())
        raise ex
