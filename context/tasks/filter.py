import importlib.util
from context.models import SearchContext, AdvancedConfiguration, Filter
from context.tasks.helpers import change_status, write_log
from maestro.celery import app


def get_used_builtin_filters(config: AdvancedConfiguration):
    """Given an advanced configuration, returns the list of builtin filters used"""
    filter_list = set()
    if config.start_date is not None or config.end_date is not None:
        filter_list.add(Filter.objects.get(name='Date filter'))
    if config.location is not None and config.radius is not None:
        filter_list.add(Filter.objects.get(name='Geolocation filter'))
    # Add other builtin filters here
    return filter_list


@app.task(bind=True)
def run_filters(self, post_process_result, context_id):
    stage = 'filter'
    context = SearchContext.objects.get(id=context_id)

    if post_process_result is not True:  # something went wrong on the post-processors stage
        change_status(SearchContext.FAILED_FILTERING, context, stage, f'[ERROR] Filtering failed because there was a problem with the post-processing stage', True)
        return False

    datastream = context.datastream
    advanced_configuration = context.configuration.advanced_configuration

    if advanced_configuration is not None and advanced_configuration.filters is not None:
        custom_selected_filters = set(advanced_configuration.filters.filter(is_active=True, is_builtin=False))
        builtin_filters = get_used_builtin_filters(advanced_configuration)
        filters = custom_selected_filters.union(builtin_filters)
    elif advanced_configuration is not None and advanced_configuration.filters is None:
        filters = get_used_builtin_filters(advanced_configuration)
    else:
        change_status(SearchContext.FINISHED_FILTERING, context, stage, f'No filters used. Continuing to classification', True)
        return True

    # No filters selected
    if filters is None or len(filters) == 0:
        change_status(SearchContext.FINISHED_FILTERING, context, stage, f'No filters used. Continuing to classification', True)
        return True

    change_status(SearchContext.FILTERING, context, stage, f'Will use the filters: {filters}', True)

    filterable_data = advanced_configuration.get_filterable_data()
    filtered_count = 0
    for _filter in filters:
        write_log(context, stage, f'Using filter \'{_filter}\'')
        if _filter.type == Filter.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(_filter.name, _filter.path)
            filter_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(filter_script)

            failures = 0
            failure_tolerance = 10  # if more than 10 failures occur, probably this filter is not doing something right
            for data in datastream:
                if failures > failure_tolerance:
                    write_log(context, stage, f'[ERROR] Filter {_filter} raised too many exceptions. Aborting its execution')
                    break

                try:
                    write_log(context, stage, f'Filtering {data.identifier}')
                    result = filter_script.main(data.data, data.metadata, filterable_data)
                    write_log(context, stage, f'{data.identifier} {"was" if result else "was not"} filtered')
                    if (result is None and advanced_configuration.strict_filtering is True) or (result is False):
                        # Mark the data object as filtered
                        filtered_count += 1
                        data.filtered = True
                        data.save()
                    else:
                        data.filtered = False
                        data.save()
                    write_log(context, stage, f'Saved filtering of {data.identifier} result')
                except Exception as ex:
                    # Filters shouldn't return exceptions, but it's safer to catch if one occurs
                    failures += 1
                    write_log(context, stage, f'[ERROR] Filter failed on {data.identifier}. Continuing...')
                    print(f"Filter {_filter} failed:\n{ex}")

    change_status(SearchContext.FINISHED_FILTERING, context, stage, 'Finished filtering')
    write_log(context, stage, f'Filtered {filtered_count} out of {len(datastream)} objects')
    write_log(context, stage, f'Following stage is classification')
    return True
