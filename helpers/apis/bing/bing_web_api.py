import json
import os
from pprint import pprint
import requests
from django.conf import settings


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


def bing_web_api(query: str, country_code: str):

    # Add your Bing Search V7 subscription key and endpoint to your environment variables.
    subscription_key = settings.BING_SUBSCRIPTION_KEY
    endpoint = settings.BING_WEB_SEARCH_ENDPOINT

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
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()

        print("\nHeaders:\n")
        print(response.headers)

        print("\nJSON Response:\n")
        response_json = response.json()
        pprint(response_json)

        return response_json
    except requests.exceptions.HTTPError as ex:
        raise ex
