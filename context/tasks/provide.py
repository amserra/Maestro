from context.models import SearchContext
from context.tasks.helpers import change_status, write_log
from maestro.celery import app
import requests


def generate_json(classifiers, datastream):
    json_data = {}
    for classifier in classifiers:
        classifier_name = classifier.name
        json_data[classifier_name] = {}
        for data in datastream:
            classification_result = data.classification_result
            json_data[classifier_name][data.identifier] = classification_result[classifier_name]

    return json_data


@app.task(bind=True)
def run_provider(self, classification_result, context_id):
    stage = 'provide'
    context = SearchContext.objects.get(id=context_id)

    if classification_result is not True:  # something went wrong on the classification stage
        return False

    datastream = context.datastream
    advanced_configuration = context.configuration.advanced_configuration

    if advanced_configuration is None or (advanced_configuration is not None and advanced_configuration.webhook is None):
        change_status(SearchContext.FINISHED_PROVIDING, context, stage, 'No providers used. You can either provide a webhook and rerun, or download the results directly from the download button.', True)
        return True

    webhook = advanced_configuration.webhook
    change_status(SearchContext.PROVIDING, context, stage, f'Will send the data to {webhook}', True)

    classifiers = advanced_configuration.classifiers.filter(is_active=True)

    json_data = generate_json(classifiers, datastream)

    write_log(context, stage, f'Sending request...')
    try:
        response = requests.post(webhook, json=json_data, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        change_status(SearchContext.FAILED_PROVIDING, context, stage, f'[ERROR] A network problem occurred while requesting')
        return False
    except requests.exceptions.HTTPError:
        change_status(SearchContext.FAILED_PROVIDING, context, stage, f'[ERROR] Received a response with status code different than 200')
        return False
    except requests.exceptions.Timeout:
        change_status(SearchContext.FAILED_PROVIDING, context, stage, f'[ERROR] Request to the remote server timed out')
        return False
    except requests.exceptions.TooManyRedirects:
        change_status(SearchContext.FAILED_PROVIDING, context, stage, f'[ERROR] Request exceeded the maximum number of redirects')
        return False

    change_status(SearchContext.FINISHED_PROVIDING, context, stage, 'The remote server responded with status 200')
    write_log(context, stage, f'Finished all the steps')
    return True
