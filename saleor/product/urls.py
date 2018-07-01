from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<slug>[a-z0-9-_]+?)-(?P<product_id>[0-9]+)/$',
        views.product_details, name='details'),
    url(r'^category/(?P<path>[a-z0-9-_/]+?)-(?P<category_id>[0-9]+)/$',
        views.category_index, name='category'),
    url(r'^brand/(?P<path>[a-z0-9-_/]+?)-(?P<brand_id>[0-9]+)/$',
        views.brand_index, name='brand'),
    url(r'^tags/(?P<path>[a-z0-9-_/]+?)-(?P<tag_id>[0-9]+)/$',
        views.tags_index, name='tags'),
    url(r'tags/render/$',
        views.tags_render, name='tags_render'),
    url(r'(?P<slug>[a-z0-9-_]+?)-(?P<product_id>[0-9]+)/add/$',
        views.product_add_to_cart, name="add-to-cart"),
    url(r'^collection/(?P<slug>[a-z0-9-_/]+?)-(?P<pk>[0-9]+)/$',
        views.collection_index, name='collection')]
