import os
import json
from pprint import pprint

from django.conf import settings
from django.db import connection,transaction
from ...dictionary.models import Stopwords,WordList

def make_database_faster():
	if 'sqlite3' in connection.settings_dict['ENGINE']:
		cursor = connection.cursor()
		cursor.execute('PRAGMA temp_store = MEMORY;')
		cursor.execute('PRAGMA synchronous = OFF;')

def create_dictionary(dir_json):
	make_database_faster()
	cursor = connection.cursor()
	check_wordlist = WordList.objects.all().values_list('id', flat=True)
	if not check_wordlist:
		yield 'Create WordList'
		wordlist = json.load(open(dir_json+'wordlist.json'))
		query = "INSERT INTO dictionary_wordlist (katadasar, tipe_katadasar) VALUES "
		values = ""
		for i in range(0,len(wordlist)):
			words = wordlist[i]
			val = "("+"'"+words['kata']+"'"+","+"'"+words['tipe']+"'"+")"
			if i < len(wordlist)-1:
				values += val+','
			else:
				values += val+';'
		query += values
		cursor.execute(query)

	check_stopwords = Stopwords.objects.all().values_list('id', flat=True)
	if not check_stopwords:
		yield 'Create Stopwords'
		query = "INSERT INTO dictionary_stopwords (kata) VALUES "
		values = ""
		stopword = json.load(open(dir_json+'stopword.json'))
		for i in range(0,len(stopword)):
			words = stopword[i]
			val = "("+"'"+words['kata']+"'"+")"
			if i < len(stopword)-1:
				values += val+','
			else:
				values += val+';'
		query += values
		cursor.execute(query)

		yield 'Dictionary Created'