from django.conf import settings
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.shortcuts import render
from operator import itemgetter
import psutil
from django.template.response import TemplateResponse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions

from ..product.utils import products_with_details
from ..core.helper import create_navbar_tree
from ..product.models import Product, ProductRating
from ..product.utils.availability import products_with_availability,get_availability
from ..dictionary.utils.helper import FeatureHelper
from ..feature.models import (CleanProductDetails,Feature,ProductFeature)
from .forms import SearchForm
from math import log10
from joblib import (Parallel, delayed)
from django.db.models import Q
from django.contrib.sessions.backends.db import SessionStore
from django.db.models import Avg
from django_mako_plus import view_function, render_template

total = 0
query_appendix = {}
product_appendix = []
def paginate_results(results, page_number, paginate_by=settings.PAGINATE_BY):
    print('now paginate result')
    paginator = Paginator(results, paginate_by)

    try:
        page = paginator.page(page_number)
    except InvalidPage:
        raise Http404('No such page!')
    return page


def evaluate_search_query(form, request):
    results = products_with_details(request.user) & form.search()
    return products_with_availability(results, discounts=request.discounts,
                                      local_currency=request.currency)

def check_similarity(item):
    global total
    global query_appendix

    element = {}
    detail = item.details.split(' ')
    c = len(detail)
    similarity = 0
    for q in query_appendix:
        if query_appendix[q] > 0:
            f = detail.count(q)/c
            similarity += (f*(log10(1+total/query_appendix[q])))
    element['id'] = item.product_id
    element['similarity'] = similarity
    if similarity > 0:
        global product_appendix
        product_appendix.append(element)

def render_item(item,discounts,currency,ratings):
    availability = get_availability(item,discounts=discounts,
                                          local_currency=currency)
    check = list(filter(lambda e: e['product_id'] == int(item.id), ratings))
    rating = check[0] if check else {'product_id':item.id,'value':0.0}
    return item, rating, availability

def custom_query_validation(query,request,request_page):
    global query_appendix
    global total
    global product_appendix
    ratings = list(ProductRating.objects.all().values('product_id').annotate(value=Avg('value')))
    if product_appendix:
        product_appendix = []

    query = list(set(query.split(' ')))
    queryset = Q()
    for q in query:
        query_appendix[q] = 0
        queryset = queryset | Q(details__icontains=q)
    product_details = list(CleanProductDetails.objects.filter(queryset))

    if product_details:
        for q in query_appendix:
            for item in product_details:
                if q in item.details:
                    query_appendix[q] += 1

        total = len(product_details)
        Parallel(n_jobs=psutil.cpu_count()*2,
            verbose=50,
            require='sharedmem')(map(delayed(check_similarity),product_details))
        print('Job Done')
        product_appendix = sorted(product_appendix, key=itemgetter('similarity'), reverse=True)
        product_appendix = [item['id'].pk for item in product_appendix]
        print('Sorted')
        start = (settings.PAGINATE_BY*(request_page-1))
        end = start+(settings.PAGINATE_BY)
        products = list(Product.objects.filter(id__in=product_appendix[start:end]))

        results = []
        results = Parallel(n_jobs=psutil.cpu_count()*2,
            verbose=50,
            require='sharedmem',
            backend="threading")(delayed(render_item)(item,request.discounts,request.currency,ratings) for item in products)
        front = [i for i in range((start))]

        results = front+results

        for item in product_appendix[end:]:
            results.append(item)
        return results
    else:
        return []

@view_function
def search_view(request):
    request_page = int(request.GET.get('page','')) if request.GET.get('page','') else 1
    request.session['page_query'] = request_page
    form = SearchForm(data=request.GET or None)
    if form.is_valid():
        query = form.cleaned_data.get('q', '')
    else:
        query = ''
    clean_query = ''
    if not settings.ENABLE_SEARCH:
        raise Http404('No such page!')
    
    ctx = {
        'query': query,
        'query_string': '?q=%s' % query}
    response = render(request, 'search/index.html', ctx)
    return response

@view_function
def search_ajax(request):
    form = SearchForm(data=request.GET or None)
    request_page = 1
    if 'page' not in request.GET:
        if 'page_query' in request.session and request.session['page_query']:
            request_page = request.session['page_query']
    else:
        request_page = int(request.GET.get('page')) if request.GET.get('page') else 1

    if form.is_valid():
        miner  = FeatureHelper()
        query = form.cleaned_data.get('q', '')

        clean_query = miner.stem_query(query)
        if not clean_query:
            query, results = '', []
        else:
            if 'query' in request.session and 'query_results' in request.session and request.session['query'] and request.session['query_results']:
                prev_query = request.session['query']
                compare = [p==c for p in prev_query.split(' ') for c in clean_query.split(' ')].count(True)
                if  compare == len(prev_query.split(' ')) and len(prev_query.split(' ')) == len(clean_query.split(' ')):
                    results = []
                    start = (settings.PAGINATE_BY*(request_page-1))
                    end = start+(settings.PAGINATE_BY)
                    products = list(Product.objects.filter(id__in=request.session['query_results'][start:end]))

                    if not products:
                        raise Http404('No such page!')
                    results = Parallel(n_jobs=psutil.cpu_count()*2,
                        verbose=50,
                        require='sharedmem',
                        backend="threading")(delayed(render_item)(item,request.discounts,request.currency) for item in products)
                    front = [i for i in range((start))]
                    results = front+results
                    for item in request.session['query_results'][end:]:
                        results.append(item)
                else:
                    results = custom_query_validation(clean_query, request, request_page)
                if not results:
                    query, results = '', []
            else:
                results = custom_query_validation(clean_query, request, request_page)
                if not results:
                    query, results = '', []
    else:
        query, results = '', []
    page = paginate_results(list(results), request_page)
    ctx = {
        'query': query,
        'count_query' : len(results) if results else 0,
        'results': page,
        'query_string': '?q=%s' % query}
    response = TemplateResponse(request, 'search/results.html', ctx)
    request.session['query'] = clean_query
    request.session['query_results'] = [item for item in product_appendix]
    return response