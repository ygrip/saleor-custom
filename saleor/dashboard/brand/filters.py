from django.utils.translation import npgettext, pgettext_lazy
from django_filters import CharFilter, OrderingFilter

from ...core.filters import SortedFilterSet
from ...product.models import Brand

SORT_BY_FIELDS = {
    'brand_name': pgettext_lazy('Brand list sorting option', 'name'),
    'brand_url': pgettext_lazy(
        'Brand list sorting option', 'description')}


class BrandFilter(SortedFilterSet):
    brand_name = CharFilter(
        label=pgettext_lazy('Brand list filter label', 'Name'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Brand list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Brand
        fields = []

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard categories list',
            'Found %(counter)d matching brand',
            'Found %(counter)d matching brands',
            number=counter) % {'counter': counter}
