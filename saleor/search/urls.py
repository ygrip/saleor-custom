from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.search_view, name='search_view'),
    url(r'^$', views.search_ajax, name='search_ajax')]
