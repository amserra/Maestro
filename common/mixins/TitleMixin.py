class TitleMixin(object):
    """Pass a defined title to context"""

    def get_title(self):
        if '%s' in self.title:
            return self.title % self.object
        return self.title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.get_title()

        return context
