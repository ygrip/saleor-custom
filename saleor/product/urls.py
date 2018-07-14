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
    url(r'^tags/render/$',
        views.tags_render, name='tags_render'),
    url(r'^sale/$',
        views.get_all_discounted_product, name='sale_product'),
    url(r'^sale/render/$',
        views.render_discounted_product, name='sale_render'),
    url(r'(?P<product_id>[0-9]+)/similar/$',
        views.render_similar_product, name="similar-products"),
    url(r'(?P<product_id>[0-9]+)/similar/all/$',
        views.all_similar_product, name="all-similar-products"),
    url(r'(?P<product_id>[0-9]+)/similar/all/render/$',
        views.render_all_similar_product, name="render-all-similar-products"),
    url(r'^recommendation/all/$',
        views.all_recommendation, name="all-recommended-products"),
    url(r'^recommendation/all/render/$',
        views.get_render_all_recommendation, name="render-all-recommended-products"),
    url(r'(?P<slug>[a-z0-9-_]+?)-(?P<product_id>[0-9]+)/add/$',
        views.product_add_to_cart, name="add-to-cart"),
    url(r'^collection/(?P<slug>[a-z0-9-_/]+?)-(?P<pk>[0-9]+)/$',
        views.collection_index, name='collection')]

api_urlpatterns = [
    url(r'^product/similar/(?P<product_id>[0-9]+)/$',
        views.get_similar_product, name='similarproduct'),
    url(r'^update/rating/$',
        views.update_product_rating, name='update_rating'),
    url(r'^recommender/arc/(?P<mode>[a-z0-9-_/]+?)/(?P<limit>[0-9]+)/$',
        views.get_arc_recommendation, name='arcrecommendaion'),
    url(r'^recommendation/hybrid/$',
        views.get_recommendation, name='hybridrecommendation'),
    url(r'^recommendation/partial/render/$',
        views.render_recommendation, name='renderhomerecommendation'),
    url(r'^recommendation/evaluate/$',
        views.evaluate_recommendation, name="evaluate_recommendation"),
]