import math
from itertools import chain

from django import forms
from django.utils.encoding import force_str
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from entries.models import ReadAt

class ReadAtForm(forms.ModelForm):
    class Meta:
        model = ReadAt
        exclude = []


class IPForm(forms.Form):
    client_ip = forms.GenericIPAddressField(protocol="IPv4")
    port = forms.IntegerField(initial=8000)
    model = forms.ChoiceField(widget=forms.Select,
        choices=tuple((x, x) for x in "Tag Done Image Entry Person ReadAt".split()))
    diff_wrap = forms.IntegerField(initial=94)


class MergeForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput())
    merge = forms.ChoiceField(widget=forms.Select,
        choices=tuple((x, x) for x in "Undecided Client Server Neither Both".split()))


# https://djangosnippets.org/snippets/2236/
class ColumnCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Widget that renders multiple-select checkboxes in columns.
    Constructor takes number of columns and css class to apply
    to the <ul> elements that make up the columns.
    """
    def __init__(self, columns=2, css_class=None, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        self.columns = columns
        self.css_class = css_class

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs)#, name=name) #  didn't work with name=name
        choices_enum = list(enumerate(chain(self.choices, choices)))

        # This is the part that splits the choices into columns.
        # Slices vertically.  Could be changed to slice horizontally, etc.
        column_sizes = columnize(len(choices_enum), self.columns)
        columns = []
        for column_size in column_sizes:
            columns.append(choices_enum[:column_size])
            choices_enum = choices_enum[column_size:]
        output = []
        for column in columns:
            if self.css_class:
                output.append(u'<ul class="%s"' % self.css_class)
            else:
                output.append(u'<ul>')
            # Normalize to strings
            str_values = set([force_str(v) for v in value])
            for i, (option_value, option_label) in column:
                # If an ID attribute was given, add a numeric index as a suffix,
                # so that the checkboxes don't all have the same ID attribute.
                if has_id:
                    final_attrs = dict(final_attrs, id='%s_%s' % (
                            attrs['id'], i))
                    label_for = u' for="%s"' % final_attrs['id']
                else:
                    label_for = ''

                cb = forms.CheckboxInput(
                    final_attrs, check_test=lambda value: value in str_values)
                option_value = force_str(option_value)
                rendered_cb = cb.render(name, option_value)
                option_label = conditional_escape(force_str(option_label))
                output.append(u'<li><label%s>%s %s</label></li>' % (
                        label_for, rendered_cb, option_label))
            output.append(u'</ul>')
        return mark_safe(u'\n'.join(output))


def columnize(items, columns):
    """
    Return a list containing numbers of elements per column if `items` items
    are to be divided into `columns` columns.

    >>> columnize(10, 1)
    [10]
    >>> columnize(10, 2)
    [5, 5]
    >>> columnize(10, 3)
    [4, 3, 3]
    >>> columnize(3, 4)
    [1, 1, 1, 0]
    """
    elts_per_column = []
    for col in range(columns):
        col_size = int(math.ceil(float(items) / columns))
        elts_per_column.append(col_size)
        items -= col_size
        columns -= 1
    return elts_per_column
