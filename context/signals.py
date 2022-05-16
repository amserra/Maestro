from django.db.models.signals import post_save
from django.dispatch import receiver
from context.models import SearchContext
from .tasks import delete_context_folder, create_context_folder, run_fetchers, run_default_gatherer, run_post_processors, run_filters, run_classifiers, run_provider, handle_initial_datastream
from celery import chain


def get_amount_seconds(number, unit):
    multiplicity = 1
    if unit == 'MIN':
        multiplicity = 60
    elif unit == 'HOUR':
        multiplicity = 60 * 60
    elif unit == 'DAY':
        multiplicity = 60 * 60 * 24
    return number * multiplicity


@receiver(post_save, sender=SearchContext, dispatch_uid="schedule_start")
def schedule_start(sender, **kwargs):
    instance = kwargs.get('instance', None)
    if not instance or instance.status != SearchContext.FINISHED_PROVIDING:
        return

    if instance.configuration and instance.configuration.repeat_amount is not None and instance.configuration.repeat_unit is not None:
        instance.number_of_iterations = instance.number_of_iterations + 1
        countdown = get_amount_seconds(instance.configuration.repeat_amount, instance.configuration.repeat_unit)
        instance.status = SearchContext.WAITING_ITERATION
        instance.save()
        chain(run_fetchers.s(instance.id), run_default_gatherer.s(instance.id), run_post_processors.s(instance.id), run_filters.s(instance.id), run_classifiers.s(instance.id), run_provider.s(instance.id)).apply_async(countdown=countdown)
        # chain(run_provider.s(True, instance.id)).apply_async(countdown=countdown)
