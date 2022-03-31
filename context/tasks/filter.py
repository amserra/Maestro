import importlib.util
from context.models import SearchContext, AdvancedConfiguration, Filter
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
def run_filters(self, post_processors_result, context_id):
    if not post_processors_result:  # something went wrong on the post-processors stage
        return False

    context = SearchContext.objects.get(id=context_id)
    datastream = context.datastream
    advanced_configuration = context.configuration.advanced_configuration

    if not datastream.exists():
        return False

    context.status = SearchContext.FILTERING
    context.save()

    custom_selected_filters = set(advanced_configuration.filters.filter(is_active=True, is_builtin=False))
    builtin_filters = get_used_builtin_filters(advanced_configuration)
    filters = custom_selected_filters.union(builtin_filters)
    filterable_data = advanced_configuration.get_filterable_data()

    for _filter in filters:
        if _filter.type == Filter.PYTHON_SCRIPT:
            spec = importlib.util.spec_from_file_location(_filter.name, _filter.path)
            filter_script = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(filter_script)

            # Post processors shouldn't return exceptions, but for safety it's better to catch if one occurs
            try:
                for data in datastream:
                    result = filter_script.main(data.data, data.metadata, filterable_data)
                    if (result is None and advanced_configuration.strict_filtering is True) or (result is False):
                        # Mark the data object as filtered
                        data.filtered = True
                        data.save()
                    else:
                        data.filtered = False
                        data.save()

            except Exception as ex:
                print(f"Filter {_filter} failed:\n{ex}")

    context.status = SearchContext.FINISHED_FILTERING
    context.save()

    return True
