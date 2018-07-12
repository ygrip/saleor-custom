from django.shortcuts import render
from django.db import connection,transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from .models import VisitProduct
from ..account.models import User
from ..product.models import Product
import datetime
import time
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
# Create your views here.

def insert_search_history(raw_query, clean_query, user_id=None):
	cursor = connection.cursor()
	if user_id:
		query = """
				INSERT INTO track_searchhistory(id, user_id_id, modulo, clean_query, raw_query, search_at)
				SELECT
			      (COALESCE(MAX(t.id), -1) + 1),
				  ("""+str(user_id)+""")::int,
			      ((COALESCE(MAX(t.id), -1) + 1)%10)+(("""+str(user_id)+""")::int*10),
			      '"""+clean_query+"""',
				  '"""+raw_query+"""',
				  NOW()
				FROM track_searchhistory t
			      ON CONFLICT (modulo) DO UPDATE 
				  SET
			         id    = excluded.id,
			         user_id_id = excluded.user_id_id,         
					 raw_query = excluded.raw_query,
					 clean_query = excluded.clean_query,
					 search_at = NOW();
			 	"""
		cursor.execute(query)
		cursor.close()
		transaction.commit()

@csrf_exempt
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def insert_visit_history(request):
	start_time = time.time()
	if request.method=='POST':
		data = request.data
		if '_auth_user_id' in request.session and request.session['_auth_user_id']:
			if 'product_id' in data and data['product_id']:
				try:
					product = Product.objects.get(id=int(data.get('product_id')))
				except Product.DoesNotExist:
					result = {'success':False,'message':'Product does not exist!','process_time':(time.time() -  start_time)}
					return JsonResponse(result)
				try:
					user = User.objects.get(id=int(request.session['_auth_user_id']))
				except User.DoesNotExist:
					result = {'success':False,'message':'Fail to authenticate user!','process_time':(time.time() -  start_time)}
					return JsonResponse(result)
				defaults = {
					'product_id' : product,
					'user_id' : user,
					'count' : 1
				}
				visit, created = VisitProduct.objects.get_or_create(product_id=product,user_id=user,defaults=defaults)
				if not created:
					visit.count += 1
					visit.save()
				result = {'success':True,'message':'saved to database','process_time':(time.time() -  start_time)}
				return JsonResponse(result)
			else:
				result = {'success':False,'message':'Wrong parameter!','process_time':(time.time() -  start_time)}
				return JsonResponse(result)
		else:
			product_id = data.get('product_id')
			if 'history' in request.session and 'visit' in request.session['history']:
				if str(product_id) not in request.session['history']['visit']:
					request.session['history']['visit'].update({str(product_id):1})
				else:
					request.session['history']['visit'][str(product_id)] += 1
			else:
				if 'history' not in request.session:
					request.session['history'] = {'search':[],'visit':{}}
					request.session['history']['visit'].update({str(product_id):1})
			result = {'success':True,'message':'saved to session','process_time':(time.time() -  start_time)}
			return JsonResponse(result)
	else:
		result = {'success':False,'message':'Wrong method!','process_time':(time.time() -  start_time)}
		return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)

@receiver(user_logged_in)
def migrate_session_callback(sender, request, user, **kwargs):
	start_time = time.time()
	print('migrating-session')
	if request.method=='POST':
		if '_auth_user_id' in request.session and request.session['_auth_user_id']:
			if 'history' in request.session and request.session['history']:
				if 'visit' in request.session['history'] and request.session['history']['visit']:
					for key, value in request.session['history']['visit'].items():
						try:
							product = Product.objects.get(id=int(key))
						except Product.DoesNotExist:
							result = {'success':False,'message':'Product does not exist!','process_time':(time.time() -  start_time)}
							return JsonResponse(result)
						try:
							user = User.objects.get(id=int(request.session['_auth_user_id']))
						except User.DoesNotExist:
							result = {'success':False,'message':'Fail to authenticate user!','process_time':(time.time() -  start_time)}
							return JsonResponse(result)
						defaults = {
							'product_id' : product,
							'user_id' : user,
							'count' : value
						}
						visit, created = VisitProduct.objects.get_or_create(product_id=product,user_id=user,defaults=defaults)
						if not created:
							visit.count += int(value)
							visit.save()
				if 'search' in request.session['history'] and request.session['history']['search']:
					for query  in request.session['history']['search']:
						insert_search_history(query.get('actual'), query.get('clean'), int(request.session['_auth_user_id']))
				del request.session['history']
				result = {'success':True,'message':'session saved','process_time':(time.time() -  start_time)}
				return JsonResponse(result)
			else:
				result = {'success':True,'message':'nothing to save','process_time':(time.time() -  start_time)}
				return JsonResponse(result)
		else:
			result = {'success':True,'message':'nothing to save','process_time':(time.time() -  start_time)}
			return JsonResponse(result)
	else:
		result = {'success':False,'message':'Wrong method!','process_time':(time.time() -  start_time)}
		return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)
