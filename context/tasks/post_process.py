import importlib.util
from context.models import SearchContext, Configuration, PostProcessor
from context.tasks.helpers import change_status, write_log
from maestro.celery import app


@app.task(bind=True)
def run_post_processors(self, gather_result, context_id):
    stage = 'post_process'
    context = SearchContext.objects.get(id=context_id)

    if gather_result is not True:
        change_status(SearchContext.FAILED_POST_PROCESSING, context, stage, f'[ERROR] Post-processing failed because there was a problem with the gathering stage', True)
        return False

    datastream = context.datastream
    if not datastream.exists():
        change_status(SearchContext.FAILED_POST_PROCESSING, context, stage, f'[ERROR] Post-processing failed because there was a problem with the gathering stage (datastream is empty)', True)
        return False

    # post processors only used if context has advanced configuration
    advanced_configuration = context.configuration.advanced_configuration

    if advanced_configuration is None or advanced_configuration.post_processors is None:
        change_status(SearchContext.FINISHED_POST_PROCESSING, context, stage, f'No post-processor selected. Continuing to filtering', True)
        return True

    post_processors = advanced_configuration.post_processors.filter(is_active=True)

    if post_processors.count() == 0:
        change_status(SearchContext.FINISHED_POST_PROCESSING, context, stage, f'No post-processor selected. Continuing to filtering', True)
        return True

    change_status(SearchContext.POST_PROCESSING, context, stage, f'Will use the post-processors: {post_processors}', True)

    post_processed_count = 0
    for post_processor in post_processors:
        write_log(context, stage, f'Using post-processor \'{post_processor}\'')
        if post_processor.type == PostProcessor.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(post_processor.name, post_processor.path)
            post_processor_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(post_processor_script)

            failures = 0
            failure_tolerance = 10  # if more than 10 failures occur, probably this post-processor is not doing something right
            for data in datastream:
                if failures > failure_tolerance:
                    write_log(context, stage, f'[ERROR] Post-processor {post_processor} raised too many exceptions. Aborting its execution')
                    break

                try:
                    write_log(context, stage, f'Post-processing {data.identifier}')
                    result = post_processor_script.main(data.data)
                    write_log(context, stage, f'Post-processing {data.identifier} result: {result}')
                    if result is not None:
                        post_processed_count += 1
                        write_log(context, stage, f'Saving post-processing of {data.identifier} result')
                        if post_processor.kind == PostProcessor.DATA_MANIPULATION:
                            if post_processor.data_type == Configuration.IMAGES:
                                # TODO: Not needed yet! Use functions in utils/image. What is the input? PIL object?
                                pass
                            else:
                                data.data = result
                        elif post_processor.kind == PostProcessor.METADATA_RETRIEVAL:
                            data.metadata = result
                        data.save()
                        write_log(context, stage, f'Saved post-processing of {data.identifier} result')
                except Exception as ex:
                    # Post processors shouldn't return exceptions, but it's safer to catch if one occurs
                    failures += 1
                    write_log(context, stage, f'[ERROR] Post-processor failed on {data.identifier}. Continuing...')
                    print(f"Post-processor {post_processor} failed:\n{ex}")

    change_status(SearchContext.FINISHED_POST_PROCESSING, context, stage, 'Finished post-processing')
    write_log(context, stage, f'Post-processed {post_processed_count} in {len(datastream)} objects')
    write_log(context, stage, f'Following stage is filtering')
    return True
