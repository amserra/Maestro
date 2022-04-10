from django.db.models.query import QuerySet
from context.models import SearchContext


def get_user_search_contexts(user) -> QuerySet[SearchContext]:
    """Gets the search contexts the user has access to"""
    contexts_user = SearchContext.objects.filter(user=user)
    contexts_user_organizations = SearchContext.objects.filter(
        organization__membership__user=user,
        organization__membership__is_blocked=False,
        organization__membership__has_accepted=True
    )
    return (contexts_user | contexts_user_organizations).distinct()


def compare_status(status1, status2):
    """Given two status, returns if status1 is further more (or equal) in the pipeline than status2 (relies on the order they are declared in the models)."""
    choices = SearchContext.STATUS_CHOICES
    choices_name = [choice[0] for choice in choices]
    index1 = choices_name.index(status1)
    index2 = choices_name.index(status2)

    if index1 >= index2:
        return True
    else:
        return False


def compare_status_leq(status1, status2):
    """Given two status, returns if status1 is before (or equal) in the pipeline than status2 (relies on the order they are declared in the models)."""
    choices = SearchContext.STATUS_CHOICES
    choices_name = [choice[0] for choice in choices]
    index1 = choices_name.index(status1)
    index2 = choices_name.index(status2)

    if index1 <= index2:
        return True
    else:
        return False
