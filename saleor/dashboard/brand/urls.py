from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.brand_list, name='brand-list'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.brand_details, name='brand-details'),
    url(r'^add/$',
        views.brand_create, name='brand-add'),
    url(r'^(?P<root_pk>[0-9]+)/edit/$',
        views.brand_edit, name='brand-edit'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.brand_delete, name='brand-delete')]
