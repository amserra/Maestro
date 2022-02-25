from django_filters import FilterSet, filters
from context.models import SearchContext


class SearchContextFilter(FilterSet):
    code = filters.CharFilter(field_name='code', lookup_expr='contains', label='Code')
    owner = filters.ChoiceFilter(field_name='owner', label='Owner', method='owner_filter')
    status = filters.ChoiceFilter(field_name='status', lookup_expr='exact', choices=SearchContext.STATUS_CHOICES)

    def __init__(self, *args, **kwargs):
        super(SearchContextFilter, self).__init__(*args, **kwargs)

        options = [(self.request.user.email, 'Me')]
        for context in self.request.user.all_contexts:
            if context.owner_type.name == 'organization':
                options.append((context.owner.code, context.owner.name))

        self.filters['owner'].field.choices = options

    def owner_filter(self, queryset, name, value):
        if '@' in value:
            return queryset.filter(user__email=value)
        else:
            return queryset.filter(organization__code=value)

    class Meta:
        model = SearchContext
        fields = ['code', 'owner', 'status']
