import json
import requests
from django.conf import settings
from datetime import datetime


def country_code_to_language(country_code):
    if country_code == 'US':
        return 'en-US, en'
    elif country_code == 'PT':
        return 'pt-PT, pt'


def build_accept_language(country_code: str, get_english_results: bool = True) -> str:
    """Accept language header is built based on the country code.
    mkt header is prefered by Bing, however it doesn't support the Portuguese market, thus we use the cc (country code)+Accept-Language option.
    This function is made simple because only Portuguese (Portugal) and US (USA) country codes are supported at the time.

    Parameters
    ----------
    country_code : str
    get_english_results: bool
        Besides the country_code correspondent headers, add the 'en' to include english results
    """

    language = country_code_to_language(country_code)

    if not country_code == 'US' and get_english_results:
        language += ', en'

    return language


def parse_args(*args):
    query = args[0]
    country_code = args[1]
    return query, country_code


def main(*args):
    query, country_code = parse_args(*args)

    # Add your Bing Search V7 subscription key and endpoint to your environment variables.
    subscription_key = settings.BING_SUBSCRIPTION_KEY
    endpoint = 'https://api.bing.microsoft.com/v7.0/images/search'

    params = {
        'q': query,
        'cc': country_code
    }
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Accept-Language': build_accept_language(country_code)
    }

    # Call the API
    try:
        response = None
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        response_json = response.json()

        links = [value['contentUrl'] for value in response_json['value']]

        with open(f'{settings.LOGS_PATH}/apis/{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_bing_image_api.json', 'w') as f:
            json.dump(response_json, f)

        # print("\nHeaders:\n")
        # print(response.headers)
        #
        # print("\nJSON Response:\n")
        # pprint(response_json)

        return links
    except requests.exceptions.HTTPError as ex:
        raise ex
