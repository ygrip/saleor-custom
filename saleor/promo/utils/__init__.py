from urllib.parse import urlencode

from django.conf import settings
from django.db.models import F

def fetch_promo():
	from ..models import Promo
	return Promo.objects.all()

def promo_with_details():
	promo = fetch_promo()
	promo = promo.prefetch_related('messages')
	return promo

def promo_for_homepage():
	promo = promo_with_details()
	return promo.filter(is_featured=True)