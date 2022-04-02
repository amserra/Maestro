import importlib.util
from context.models import SearchContext
from maestro.celery import app


@app.task(bind=True)
def run_classifiers(self, filter_result, context_id):
    if not filter_result:
        return False

    context = SearchContext.objects.get(id=context_id)
    datastream = context.datastream.filter(filtered=False)  # only use non filtered data objects
    advanced_configuration = context.configuration.advanced_configuration

    context.status = SearchContext.CLASSIFYING
    context.save()

    classifiers = advanced_configuration.classifiers.filter(is_active=True)

    for classifier in classifiers:

        if classifier.type == classifier.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(classifier.name, classifier.path)
            classifier_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(classifier_script)

            try:
                for data in datastream:
                    result = classifier_script.main(data.data)
                    print(f"Result of data object {data}: {result}")
                    classification_result = data.classification_result
                    if classification_result is None:
                        data.classification_result = {classifier.name: result}
                        data.save()
                    else:
                        classification_result[classifier.name] = result
                        data.classification_result = classification_result
                        data.save()

            except Exception as ex:
                print(f"Classifier {classifier} failed:\n{ex}")

    context.status = SearchContext.FINISHED_CLASSIFYING
    context.save()

    return True
