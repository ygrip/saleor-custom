from django.db import models
from ..product.models import Product
from ..account.models import User
from django.utils.encoding import smart_text
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
# Create your models here.

class VisitProduct(models.Model):
	product_id = models.ForeignKey(
	Product, related_name='tracks', on_delete=models.CASCADE)
	user_id = models.ForeignKey(
	User, related_name='tracks', on_delete=models.CASCADE)
	count = models.PositiveIntegerField(editable=True)
	updated_at = models.DateTimeField(auto_now=True, null=True)

	class Meta:
		app_label = 'track'
		permissions = (
			('view_track',
			pgettext_lazy('Permission description', 'Can view visited products by user')),
			('edit_track',
			pgettext_lazy('Permission description', 'Can edit visited products by user')))

class SearchHistory(models.Model):
	user_id = models.ForeignKey(
	User, related_name='search_history', on_delete=models.CASCADE)
	modulo = models.PositiveIntegerField(null=False, unique=True)
	clean_query = models.TextField(null=False)
	raw_query = models.TextField(null=False)
	search_at = models.DateTimeField(auto_now=True, null=True)

	class Meta:
		app_label = 'track'
		permissions = (
			('view_search_history',
			pgettext_lazy('Permission description', 'Can view user search history')),
			('edit_search_history',
			pgettext_lazy('Permission description', 'Can edit user search history')))