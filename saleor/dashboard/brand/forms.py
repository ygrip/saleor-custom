from django import forms
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from text_unidecode import unidecode

from ...product.models import Brand
from ..seo.fields import SeoDescriptionField, SeoTitleField


class BrandForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['seo_description'] = SeoDescriptionField(
            extra_attrs={'data-bind': self['brand_name'].auto_id})
        self.fields['seo_title'] = SeoTitleField(
            extra_attrs={'data-bind': self['brand_name'].auto_id})

    class Meta:
        model = Brand
        exclude = ['slug']
        labels = {
            'brand_name': pgettext_lazy('Item name', 'Name'),
            'brand_link': pgettext_lazy('Link', 'link')}

    def save(self, commit=True):
        self.instance.slug = slugify(unidecode(self.instance.name))
        
        return super().save(commit=commit)
