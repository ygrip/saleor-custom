from django import forms
from django.utils.translation import npgettext, pgettext_lazy
from django_filters import (
    CharFilter, ChoiceFilter, ModelMultipleChoiceFilter, OrderingFilter, NumberFilter, NumericRangeFilter,DateFromToRangeFilter,
    RangeFilter)
from django_filters import widgets
from django.contrib.admin import DateFieldListFilter
from ...core.filters import SortedFilterSet
from ...product.models import Category, Product, ProductAttribute, ProductType, ProductRating, Brand
from ..widgets import MoneyRangeWidget


PRODUCT_SORT_BY_FIELDS = {
    'name': pgettext_lazy('Product list sorting option', 'name'),
    'price': pgettext_lazy('Product type list sorting option', 'price')}

PRODUCT_RATING_SORT_BY_FIELDS = {
    'product_id_id': pgettext_lazy('Product list sorting option', 'product_id_id'),
    'product_id__name': pgettext_lazy('Product list sorting option', 'product_id__name'),
    'avg_rating': pgettext_lazy('Product list sorting option', 'avg_rating'),
    'total_rating': pgettext_lazy('Product list sorting option', 'total_rating'),
    'user_id': pgettext_lazy('Product list sorting option', 'user_id'),
    'updated_at': pgettext_lazy('Product list sorting option', 'updated_at'),
    'value': pgettext_lazy('Product type list sorting option', 'value')}

PRODUCT_ATTRIBUTE_SORT_BY_FIELDS = {
    'name': pgettext_lazy('Product attribute list sorting option', 'name')}

PRODUCT_TYPE_SORT_BY_FIELDS = {
    'name': pgettext_lazy('Product type list sorting option', 'name')}

PUBLISHED_CHOICES = (
    ('1', pgettext_lazy('Is publish filter choice', 'Published')),
    ('0', pgettext_lazy('Is publish filter choice', 'Not published')))

FEATURED_CHOICES = (
    ('1', pgettext_lazy('Is featured filter choice', 'Featured')),
    ('0', pgettext_lazy('Is featured filter choice', 'Not featured')))


class ProductFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Product list filter label', 'Name'),
        lookup_expr='icontains')
    category = ModelMultipleChoiceFilter(
        label=pgettext_lazy('Product list filter label', 'Category'),
        name='category',
        queryset=Category.objects.all())
    brand_id = ModelMultipleChoiceFilter(
        label=pgettext_lazy('Product list filter label', 'Brand'),
        name='brand_id',
        queryset=Brand.objects.all()),
    product_type = ModelMultipleChoiceFilter(
        label=pgettext_lazy('Product list filter label', 'Product type'),
        name='product_type',
        queryset=ProductType.objects.all())
    price = RangeFilter(
        label=pgettext_lazy('Product list filter label', 'Price'),
        name='price',
        widget=MoneyRangeWidget)
    is_published = ChoiceFilter(
        label=pgettext_lazy('Product list filter label', 'Is published'),
        choices=PUBLISHED_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    is_featured = ChoiceFilter(
        label=pgettext_lazy(
            'Product list is featured filter label', 'Is featured'),
        choices=FEATURED_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list filter label', 'Sort by'),
        fields=PRODUCT_SORT_BY_FIELDS.keys(),
        field_labels=PRODUCT_SORT_BY_FIELDS)

    class Meta:
        model = Product
        fields = ['brand_id','location_id']

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard products list',
            'Found %(counter)d matching product',
            'Found %(counter)d matching products',
            number=counter) % {'counter': counter}


class ProductAttributeFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Product attribute list filter label', 'Name'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product attribute list filter label', 'Sort by'),
        fields=PRODUCT_TYPE_SORT_BY_FIELDS.keys(),
        field_labels=PRODUCT_TYPE_SORT_BY_FIELDS)

    class Meta:
        model = ProductAttribute
        fields = []

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard '
            'product attributes list',
            'Found %(counter)d matching attribute',
            'Found %(counter)d matching attributes',
            number=counter) % {'counter': counter}


class ProductTypeFilter(SortedFilterSet):
    name = CharFilter(
        label=pgettext_lazy('Product type list filter label', 'Name'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product type list filter label', 'Sort by'),
        fields=PRODUCT_TYPE_SORT_BY_FIELDS.keys(),
        field_labels=PRODUCT_TYPE_SORT_BY_FIELDS)

    class Meta:
        model = ProductType
        fields = ['name', 'product_attributes', 'variant_attributes']

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard product types list',
            'Found %(counter)d matching product type',
            'Found %(counter)d matching product types',
            number=counter) % {'counter': counter}

class ProductRatingFilter(SortedFilterSet):
    updated_at = DateFromToRangeFilter(label=pgettext_lazy('Product rating list filter label', 'Updated At'), name='updated_at', widget=widgets.RangeWidget(attrs={'class': 'datepicker'}))
    value = RangeFilter(
        label=pgettext_lazy('Product rating list filter label', 'Average Ratings'),name='value')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product rating list filter label', 'Sort by'),
        fields=PRODUCT_RATING_SORT_BY_FIELDS.keys(),
        field_labels=PRODUCT_RATING_SORT_BY_FIELDS)

    class Meta:
        model = ProductRating
        fields = ['user_id']

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard product rating list',
            'Found %(counter)d matching product rating',
            'Found %(counter)d matching product rating',
            number=counter) % {'counter': counter}

class SimpleProductRatingFilter(SortedFilterSet):
    product_id__name = CharFilter(
        label=pgettext_lazy('Product rating list filter label', 'Product Name'),
        lookup_expr='icontains')
    avg_rating = RangeFilter(
        label=pgettext_lazy('Product rating list filter label', 'Average Ratings'),name='avg_rating')
    total_rating = RangeFilter(
        label=pgettext_lazy('Product rating list filter label', 'Total Given'),name='total_rating')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product rating list filter label', 'Sort by'),
        fields=PRODUCT_RATING_SORT_BY_FIELDS.keys(),
        field_labels=PRODUCT_RATING_SORT_BY_FIELDS)

    class Meta:
        model = ProductRating
        fields = ['product_id__name']

    def get_summary_message(self):
        counter = self.qs.count()
        return npgettext(
            'Number of matching records in the dashboard product rating list',
            'Found %(counter)d matching product rating',
            'Found %(counter)d matching product rating',
            number=counter) % {'counter': counter}