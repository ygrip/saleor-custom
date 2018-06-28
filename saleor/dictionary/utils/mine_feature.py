from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from .helper import FeatureHelper


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
			miner = FeatureHelper()
			strict = data['strict'] if 'strict' in data else False
			treshold = int(data['count']) if 'count' in data else 2

			all_feature = miner.populate_feature(sentence=data['sentence'],treshold=treshold,strict=strict)

			result = {'success':True,'input':data['sentence'],'output':all_feature,'messages':'Succesfully mine features'}
			return JsonResponse(result)
	else:
		result = {'success':False,'input':None,'output':None,'messages':'Wrong request method'}
		return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)