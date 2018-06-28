import os
import json
import random
import itertools
from faker import Factory
from pprint import pprint

from django.conf import settings
from django.conf.urls import url
from django.db import connection,transaction
from ...promo.models import Promo, Messages
import datetime

from ...product.models import Category
from django.shortcuts import get_object_or_404, redirect

def make_database_faster():
	if 'sqlite3' in connection.settings_dict['ENGINE']:
		cursor = connection.cursor()
		cursor.execute('PRAGMA temp_store = MEMORY;')
		cursor.execute('PRAGMA synchronous = OFF;')

def create_promo():
	check_promo = Promo.objects.all().values_list('id', flat=True)
	if not check_promo:
		fake = Factory.create()
		promo_dir = 'images/promo/'
		make_database_faster()
		cursor = connection.cursor()
		yield 'Make Promotion Model'
		url_list = []
		url_image = []
		for i in range(1,6):
			url_list.append(get_object_or_404(Category, id=i).get_absolute_url())
			url_image.append(promo_dir+str(i)+'.jpg')
		position_options = ['topLeft', 'topCenter', 'topRight', 'bottomLeft', 'bottomCenter', 'bottomRight', 'centerLeft', 'centerRight', 'centerCenter' ]
		show_options = ['left','right','down','up']
		hide_options = ['left','right','down','up']
		round_options = [True,False]
		message_options = [True,False]
		featured_options = [True,False]

		PROMO_COUNT = 6
		i = 0
		for count,url,image in zip(range(PROMO_COUNT),url_list,url_image):
			i+=1
			result = {}
			is_featured = random.choice(featured_options)
			position = random.choice(position_options)
			show = random.choice(show_options)
			hide = random.choice(hide_options)
			is_round =  False
			now = datetime.datetime.now()

			promo = Promo(image=image,created_at=now,is_featured=is_featured,url=url)
			promo.save()
			current_promo = Promo.objects.latest('id')
			has_message = random.choice(message_options)
			if has_message:
				title = fake.sentence(nb_words=2)
				messages = fake.sentence(nb_words=6)
				result['title'] = title
				result['messages'] = messages
				message = Messages(promo_id=current_promo,title=title,message=messages,position=position,show=show,hide=hide)
				message.save()
			else:
				result['messages'] = None
			
			result['position'] = position
			result['show'] = show
			result['hide'] = hide
			result['is_round'] = is_round
			result['is_featured'] = is_featured
			result['created_at'] = str(now)
			yield 'Mode : '+str(i)
			yield json.dumps(result,indent=4, sort_keys=True)