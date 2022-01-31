from django.http import Http404
from django.shortcuts import redirect


class SafePaginationMixin(object):
    """
    Mixin used to safely paginate. If a user is for some reason in a page /example/?page=10, where the 10th page doesn't exist,
    the user is redirected to /example/.
    """
    def get(self, *args, **kwargs):
        try:
            return super().get(*args, **kwargs)
        except Http404:
            page = self.request.GET.get('page', None)
            if page:
                return redirect(self.request.path)
            else:
                raise Http404
