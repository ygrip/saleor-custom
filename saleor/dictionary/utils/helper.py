from operator import itemgetter
import re

from ...dictionary.models import WordList, Stopwords

# import StemmerFactory class
from custom_sastrawi.Stemmer.StemmerFactory import StemmerFactory

class FeatureHelper():
	def __init__(self):
		self.prohibited_suffix = ['mah','mhz','khz','ghz','kb','gb','mb','tb','mbps','kbps','gbps','p','k','m','inch','mp','mm','cm','fps','in','v','w','kw','a','kv','watt','volt','x','ml','l','kg','g','lt','liter','gram','kilo','ms','bit','mbit','mbyte','n']
		self.stopwords = list(Stopwords.objects.all().values_list('kata',flat=True))
		self.basewords = list(WordList.objects.all().values_list('katadasar',flat=True))
		self.factory = StemmerFactory()
		self.stemmer = self.factory.create_custom_stemmer(self.basewords)

	def get_stopword(self):
		return self.stopwords

	def get_baseword(self):
		return self.basewords

	def stem_query(self,sentence):
		return self.stemmer.stem(sentence)

	def populate_feature(self,sentence,treshold,strict=False):
		all_feature = []
		
		output = self.stem_query(sentence).split(' ')

		# clean sentences from stopwords
		output = [word for word in output if word not in self.stopwords]
		output = [word for strippedword in list(map(lambda e : e.split('-'), output)) for word in strippedword]
		if strict:
			output = list(filter(lambda e: not self.invalid(e),output))
		features = list(set(output))

		# mining text
		output_lenght = len(output)
		for element in features:
			if element:
				count = output.count(element)
				if count >= treshold:
					weight = round(count/output_lenght,3)
					all_feature.append({'word':element,'count':weight})

		if all_feature:
			all_feature = sorted(all_feature, key=itemgetter('count'), reverse=True)

		return all_feature

	def invalid(self,s):
		c = str(s)
		if len(c) > 15 or len(c) < 2:
			return True
		for p in self.prohibited_suffix:
			if c[-len(p):] == p:
				return True
			else:
				continue
		try:
			float(s)
			if re.search('[a-zA-Z]', s):
				return False
			else:
				return True
		except ValueError:
			pass

		try:
			import unicodedata
			unicodedata.numeric(s)
			return True
		except (TypeError, ValueError):
			pass

		return False