from django.conf.urls import url, include
from impersonate.views import stop_impersonate

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^render-categories/$', views.render_home_categories, name='categories_list'),
    url(r'^style-guide/', views.styleguide, name='styleguide'),
    url(r'^render-menu/', views.render_menu, name='rendermenu'),
    url(r'^render-top-brand/', views.render_top_brand, name='renderbrands'),
    url(r'^impersonate/(?P<uid>\d+)/', views.impersonate,
        name='impersonate-start'),
    url(r'^impersonate/stop/$', stop_impersonate,
        name='impersonate-stop'),
    url(r'^404', views.handle_404, name='handle-404'),
    url(r'^manifest\.json$', views.manifest, name='manifest'),
]
