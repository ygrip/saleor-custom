from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from operator import itemgetter

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

	# clean input sentences
	stopwords = list(Stopwords.objects.all().values_list('kata',flat=True))
	words = set(sentence.split(' '))
	clean_words = [word for word in words if word not in stopwords]

	# create stemmer
	factory = StemmerFactory()
	basewords = list(WordList.objects.all().values_list('katadasar',flat=True))
	stemmer = factory.create_custom_stemmer(basewords)

	# mining text
	output = stemmer.stem(' '.join([str(word) for word in clean_words])).split(' ')
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