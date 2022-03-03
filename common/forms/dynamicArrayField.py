from itertools import chain
from django import forms
from django.contrib.postgres.utils import prefix_validation_error


class DynamicArrayWidget(forms.TextInput):

    template_name = 'common/dynamic_array.html'

    def get_context(self, name, value, attrs):
        value = value or ['']
        context = super().get_context(name, value, attrs)
        final_attrs = context['widget']['attrs']
        id_ = context['widget']['attrs'].get('id')

        subwidgets = []
        for index, item in enumerate(context['widget']['value']):
            widget_attrs = final_attrs.copy()
            if id_:
                widget_attrs['id'] = '%s_%s' % (id_, index)
            widget = forms.TextInput()
            widget.is_required = self.is_required
            subwidgets.append(widget.get_context(name, item, widget_attrs)['widget'])

        context['widget']['subwidgets'] = subwidgets
        return context

    def value_from_datadict(self, data, files, name):
        try:
            getter = data.getlist
        except AttributeError:
            getter = data.get
        return getter(name)

    def format_value(self, value):
        return value or []


class DynamicArrayField(forms.Field):

    default_error_messages = {
        'item_invalid': '',
    }

    def __init__(self, base_field, **kwargs):
        self.base_field = base_field
        self.max_length = kwargs.pop('max_length', None)
        self.default_error_messages['item_invalid'] = kwargs.pop('invalid_message')
        kwargs.setdefault('widget', DynamicArrayWidget)
        super().__init__(**kwargs)

    def clean(self, value):
        cleaned_data = []
        errors = []
        if value:
            value = filter(None, value)
            for index, item in enumerate(value):
                try:
                    cleaned_data.append(self.base_field.clean(self, item))
                except forms.ValidationError as error:
                    errors.append(prefix_validation_error(
                        error, self.error_messages['item_invalid'],
                        code='item_invalid', params={'nth': index},
                    ))
            if errors:
                raise forms.ValidationError(list(chain.from_iterable(errors)))
            if not cleaned_data and self.required:
                raise forms.ValidationError(self.error_messages['required'])
            return cleaned_data
