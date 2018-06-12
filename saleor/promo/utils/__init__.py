from urllib.parse import urlencode

from django.conf import settings
from django.db.models import F
from django.db.models import Prefetch
from ..models import Messages,Promo

def fetch_promo():
	return Promo.objects.filter(is_featured=True).values('id','image','url','is_featured','created_at')

def promo_with_details():
	promos = fetch_promo()
	result = []
	if promos:
		for promo in promos:
			parent = {}
			parent['promo'] = promo
			messages = Messages.objects.filter(promo_id=promo['id']).values('title','message','position','show','hide')
			parent['messages'] = []
			if messages:
				for message in messages:
					parent['messages'].append(message)
			result.append(parent)
	# promo = promo.prefetch_related(Prefetch('messages',queryset=Messages.objects.select_related('promo_id')))
	return result

def promo_for_homepage():
	return promo_with_details()