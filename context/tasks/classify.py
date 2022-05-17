import importlib.util
from context.models import SearchContext
from context.tasks.helpers import change_status, write_log
from maestro.celery import app


@app.task(bind=True)
def run_classifiers(self, filter_result, context_id):
    stage = 'classify'
    context = SearchContext.objects.get(id=context_id)

    if context.is_stopped:
        return False

    if filter_result is not True:
        return False

    datastream = context.datastream.filter(filtered=False)  # only use non filtered data objects
    advanced_configuration = context.configuration.advanced_configuration

    if datastream.count() == 0:
        change_status(SearchContext.FAILED_CLASSIFYING, context, stage, f'[ERROR] Classification failed because no objects reached this stage (probably they were all filtered out)', True)
        return False

    if advanced_configuration is None or advanced_configuration.classifiers is None:
        change_status(SearchContext.FINISHED_CLASSIFYING, context, stage, f'No classifiers used. Continuing to provide stage', True)
        return True

    classifiers = advanced_configuration.classifiers.filter(is_active=True)

    change_status(SearchContext.CLASSIFYING, context, stage, f'Will use the classifiers: {classifiers}', True)

    classified_count = 0
    for classifier in classifiers:
        write_log(context, stage, f'Using classifier \'{classifier}\'')
        if classifier.type == classifier.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(classifier.name, classifier.path)
            classifier_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(classifier_script)

            datastream_size = datastream.count()
            failures = 0
            failure_tolerance = 10  # if more than 10 failures occur, probably this classifier is not doing something right
            for index, data in enumerate(datastream):
                if failures > failure_tolerance:
                    write_log(context, stage, f'[ERROR] Classifier {classifier} raised too many exceptions. Aborting its execution')
                    break

                try:
                    classification_result = data.classification_result
                    write_log(context, stage, f'Classifying {data.identifier} ({index + 1}/{datastream_size})')

                    if classification_result is None or classification_result[classifier.name] is None:
                        result = classifier_script.main(data.data)
                        write_log(context, stage, f'Classification {data.identifier} result: {result}')
                        classified_count += 1

                        data.classification_result = {classifier.name: result}
                        data.save()
                        write_log(context, stage, f'Saved classification of {data.identifier} result')
                    else:
                        write_log(context, stage, f'Object {data.identifier} was already classified')

                except Exception as ex:
                    failures += 1

                    write_log(context, stage, f'[ERROR] Classifier failed on {data.identifier}. Continuing...')
                    print(f"Classifier {classifier} failed:\n{ex}")

    change_status(SearchContext.FINISHED_CLASSIFYING, context, stage, 'Finished classifying')
    write_log(context, stage, f'Classified {classified_count} out of {len(datastream)} objects')
    write_log(context, stage, f'Following stage is providing')
    return True
