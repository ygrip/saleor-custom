from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from operator import itemgetter
import re

from ...dictionary.models import WordList, Stopwords

# import StemmerFactory class
from custom_sastrawi.Stemmer.StemmerFactory import StemmerFactory


@csrf_exempt
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def minefeature(request):
	if request.method == 'POST':
		
		data = request.data
		if 'sentence' in data and not data['sentence'] or 'sentence' not in data:
			result = {'success':False,'input':None,'output':None,'messages':'input could not be empty'}
			return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)
		else:
			treshold = int(data['count']) if 'count' in data else 2

			all_feature = populate_feature(data['sentence'],treshold)

			result = {'success':True,'input':data['sentence'],'output':all_feature,'messages':'Succesfully mine features'}
			return JsonResponse(result)
	else:
		result = {'success':False,'input':None,'output':None,'messages':'Wrong request method'}
		return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)

def populate_feature(sentence,treshold):
	all_feature = []
	factory = StemmerFactory()
	words = set(sentence.split(' '))

	# create stemmer
	basewords = list(WordList.objects.all().values_list('katadasar',flat=True))
	stemmer = factory.create_custom_stemmer(basewords)

	# mining text
	output = stemmer.stem(' '.join([str(word) for word in words])).split(' ')

	# clean sentences from stopwords
	stopwords = list(Stopwords.objects.all().values_list('kata',flat=True))
	output = [word for word in output if word not in stopwords]
	output = list(filter(lambda e: not invalid(e),output))
	features = list(set(output))

	for element in features:
		count = 0
		for word in output:
			if element == word:
				count += 1
		if element and count >= treshold:
			weight = round(count/len(output),3)
			all_feature.append({'word':element,'count':weight})

	if all_feature:
		all_feature = sorted(all_feature, key=itemgetter('count'), reverse=True)

	return all_feature

def invalid(s):
	prohibited_suffix = ['mah','kb','gb','mb','tb','mbps','kbps','gbps','inch','mp','mm','cm','fps','in','v','w','kw','a','kv','watt','volt','x','ml','l','kg','g','lt','liter','gram','kilo']
	
	c = str(s)
	for p in prohibited_suffix:
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