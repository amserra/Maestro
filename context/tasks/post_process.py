import importlib.util
from context.models import SearchContext, Configuration, PostProcessor
from maestro.celery import app


@app.task(bind=True)
def run_post_processors(self, context_id):
    context = SearchContext.objects.get(id=context_id)
    datastream = context.datastream
    # post processors only used if context has advanced configuration
    advanced_configuration = context.configuration.advanced_configuration
    if not datastream.exists():
        return False

    context.status = SearchContext.POST_PROCESSING
    context.save()

    post_processors = advanced_configuration.post_processors.filter(is_active=True)

    for post_processor in post_processors:
        if post_processor.type == PostProcessor.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(post_processor.name, post_processor.path)
            post_processor_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(post_processor_script)

            # Post processors shouldn't return exceptions, but for safety it's better to catch if one occurs
            try:
                for data in datastream:
                    result = post_processor_script.main(data.data)
                    if result is not None:
                        if post_processor.kind == PostProcessor.DATA_MANIPULATION:
                            if post_processor.data_type == Configuration.IMAGES:
                                # TODO: Not needed yet! Use functions in utils/image. What is the input? PIL object?
                                pass
                            else:
                                data.data = result
                        elif post_processor.kind == PostProcessor.METADATA_RETRIEVAL:
                            data.metadata = result
                        data.save()

            except Exception as ex:
                print(f"Post-processor {post_processor} failed:\n{ex}")

    context.status = SearchContext.FINISHED_POST_PROCESSING
    context.save()

    return True
