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
