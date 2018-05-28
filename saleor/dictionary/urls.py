from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from ..dictionary.utils import mine_feature

urlpatterns = [
    url(r'^minefeature$', mine_feature.minefeature),
]

urlpatterns = format_suffix_patterns(urlpatterns)