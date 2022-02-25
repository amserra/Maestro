from django.views import View


class PaginatedFilterView(View):
    def get_context_data(self, **kwargs):
        context = super(PaginatedFilterView, self).get_context_data(**kwargs)
        if self.request.GET:
            querystring = self.request.GET.copy()
            if self.request.GET.get('page'):
                del querystring['page']
            context['querystring'] = querystring.urlencode()
        return context
