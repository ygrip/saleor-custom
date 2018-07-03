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
    url(r'sale/$',
        views.get_all_discounted_product, name='sale_product'),
    url(r'sale/render/$',
        views.render_discounted_product, name='sale_render'),
    url(r'(?P<product_id>[0-9]+)/similar/$',
        views.render_similar_product, name="similar-products"),
    url(r'(?P<product_id>[0-9]+)/similar/all/$',
        views.all_similar_product, name="all-similar-products"),
    url(r'(?P<product_id>[0-9]+)/similar/all/render/$',
        views.render_all_similar_product, name="render-all-similar-products"),
    url(r'(?P<slug>[a-z0-9-_]+?)-(?P<product_id>[0-9]+)/add/$',
        views.product_add_to_cart, name="add-to-cart"),
    url(r'^collection/(?P<slug>[a-z0-9-_/]+?)-(?P<pk>[0-9]+)/$',
        views.collection_index, name='collection')]

api_urlpatterns = [
    url(r'^product/similar/(?P<product_id>[0-9]+)/$',
        views.get_similar_product, name='similarproduct'),
]