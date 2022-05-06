from context.models import SearchContext
from context.tasks.helpers import change_status, write_log
from maestro.celery import app
import requests
from django.core.mail import EmailMessage


def generate_json(classifiers, datastream, keep_null=True):
    json_data = {}
    for classifier in classifiers:
        classifier_name = classifier.name
        json_data[classifier_name] = {}
        data_object_list = []
        for data in datastream:
            classification_result = data.classification_result
            if keep_null or (not keep_null and classification_result[classifier_name] is not None):
                json_data_object = {
                    'name': data.identifier,
                    'preview_url': f'http://{data.thumb_url}',
                    'result': classification_result[classifier_name]
                }
                data_object_list.append(json_data_object)
        json_data[classifier_name] = data_object_list

    return json_data


def send_notification_email(context):
    mail_subject = 'Search context finished'
    message = f'Hello. The search context \'{context.name}\' you created in Maestro has finished. The data has been sent to the remote server specified in the webhook configuration field. If you want to inspect this data manually, head to the Search Context details page and click \'Download results\''
    email = EmailMessage(mail_subject, message, to=[context.creator])
    email.send()


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

    if advanced_configuration.minimum_objects is not None and datastream.count() < advanced_configuration.minimum_objects:
        change_status(SearchContext.FINISHED_PROVIDING, context, stage, f'The number of gathered objects was {datastream.count()}, but according to this search context configuration {advanced_configuration.minimum_objects} are required to send the data to the webhook.', True)
        return True

    webhook = advanced_configuration.webhook
    change_status(SearchContext.PROVIDING, context, stage, f'Will send the data to {webhook}', True)

    classifiers = advanced_configuration.classifiers.filter(is_active=True)

    json_data = generate_json(classifiers, datastream, advanced_configuration.keep_null)

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
    send_notification_email(context)
    return True
