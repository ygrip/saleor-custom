import os
import json
import random
import itertools
from pprint import pprint

from django.conf import settings
from django.conf.urls import url
from django.db import connection,transaction
from ...promo.models import Promo, Messages

def make_database_faster():
	if 'sqlite3' in connection.settings_dict['ENGINE']:
		cursor = connection.cursor()
		cursor.execute('PRAGMA temp_store = MEMORY;')
		cursor.execute('PRAGMA synchronous = OFF;')

def create_promo():
	make_database_faster()
	cursor = connection.cursor()
	yield 'Make Promotion Model'
	url_list = {
		''
	}
	position_options = ['topLeft', 'topCenter', 'topRight', 'bottomLeft', 'bottomCenter', 'bottomRight', 'centerLeft', 'centerRight', 'centerCenter' ]
	show_options = ['left','right','down','up',None]
	hide_options = ['left','right','down','up',None]
	round_options = [True,False]
	message_options = [True,False]
	featured_options = [True,False]

	PROMO_COUNT = 10
	i = 0
	for count,url in zip(range(PROMO_COUNT),url_list):
		i+=1
		is_featured = random.choice(featured_options)
		position = random
		result = {}
		result['position'] = pos
		result['show'] = sh
		result['hide'] = hd
		result['is_round'] = rnd
		yield 'Mode : '+str(i)
		yield json.dumps(result,indent=4, sort_keys=True)