from django.conf.urls import url

from . import views

api_urlpatterns = [
    url(r'^track/insertvisit/$',
        views.insert_visit_history, name='visit_history'),
]