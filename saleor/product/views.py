import datetime
import json
import numpy as np
import time
from operator import itemgetter
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.conf import settings
from django.http import (
    Http404, HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect, JsonResponse
)
from ..cart.utils import set_cart_cookie
from ..core.utils import serialize_decimal
from ..seo.schema.product import product_json_ld
from ..feature.models import ProductFeature, Feature
from .filters import ProductCategoryFilter, ProductBrandFilter, ProductCollectionFilter
from .models import Category, Collection, ProductRating, Brand, Product, MerchantLocation
from ..order.models import Order, OrderLine
from .utils import (
    get_product_images, get_product_list_context, handle_cart_form,
    products_for_cart, products_with_details)
from .utils.attributes import get_product_attributes_data
from .utils.availability import get_availability
from ..search.views import render_item, paginate_results
from .utils.variants_picker import get_variant_picker_data
from ..core.helper import create_navbar_tree
from .helper import (
    get_filter_values, get_descendant, get_cross_section_order,
    get_cross_section_rating, get_list_product_from_order, get_list_product_from_rating,
     get_list_user_from_order, get_list_user_from_rating, get_all_user_rating)
from django.db.models import Avg
from joblib import (Parallel, delayed)
import psutil
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from math import log10
from django.db import connection,transaction
from .utils.availability import products_with_availability
import urllib
from django.forms.models import model_to_dict

APPROVED_FILTER = ['Brand','Jenis','Color','Gender']

def product_details(request, slug, product_id, form=None):
    """Product details page.

    The following variables are available to the template:

    product:
        The Product instance itself.

    is_visible:
        Whether the product is visible to regular users (for cases when an
        admin is previewing a product before publishing).

    form:
        The add-to-cart form.

    price_range:
        The PriceRange for the product including all discounts.

    undiscounted_price_range:
        The PriceRange excluding all discounts.

    discount:
        Either a Price instance equal to the discount value or None if no
        discount was available.

    local_price_range:
        The same PriceRange from price_range represented in user's local
        currency. The value will be None if exchange rate is not available or
        the local currency is the same as site's default currency.
    """
    try:
        product = Product.objects.get(id=product_id)
        
    except Product.DoesNotExist:
        raise Http404('No %s matches the given query.' % product.model._meta.object_name)

    if product.get_slug() != slug:
        return HttpResponsePermanentRedirect(product.get_absolute_url())

    today = datetime.date.today()
    is_visible = (
        product.available_on is None or product.available_on <= today)
    
    if form is None:
        form = handle_cart_form(request, product, create_cart=False)[0]
    availability = get_availability(product, discounts=request.discounts,
                                    local_currency=request.currency)
    product_images = get_product_images(product)
    variant_picker_data = get_variant_picker_data(
        product, request.discounts, request.currency)
    product_attributes = get_product_attributes_data(product)
    # show_variant_picker determines if variant picker is used or select input
    show_variant_picker = all([v.attributes for v in product.variants.all()])
    json_ld_data = product_json_ld(product, product_attributes)
    rating = ProductRating.objects.filter(product_id=product).aggregate(value=Avg('value'))
    rating['value'] = 0.0 if rating['value'] is None else rating['value']
    brand = Brand.objects.get(id=product.brand_id_id)
    tags = []
    product_features = list(ProductFeature.objects.filter(product_id_id=product_id).values_list('feature_id_id', flat=True))
    product_info = product.information
    product_service = product.service
    product_info = json.loads(product_info)
    product_service = json.loads(product_service)
    location = MerchantLocation.objects.get(id=product.location_id)
    location_query = '+'.join(map(lambda e: e, str(location.location).split(' ')))
    if product_features:
        tags = Feature.objects.filter(id__in=product_features)
    return TemplateResponse(
        request, 'product/details.html', {
            'is_visible': is_visible,
            'form': form,
            'availability': availability,
            'rating' : rating,
            'tags' : tags,
            'service' : product_service,
            'information' : product_info,
            'brand' : brand,
            'location':location,
            'location_query':location_query,
            'product': product,
            'product_attributes': product_attributes,
            'product_images': product_images,
            'show_variant_picker': show_variant_picker,
            'variant_picker_data': json.dumps(
                variant_picker_data, default=serialize_decimal),
            'json_ld_product_data': json.dumps(
                json_ld_data, default=serialize_decimal)})


def product_add_to_cart(request, slug, product_id):
    # types: (int, str, dict) -> None

    if not request.method == 'POST':
        return redirect(reverse(
            'product:details',
            kwargs={'product_id': product_id, 'slug': slug}))

    products = products_for_cart(user=request.user)
    product = get_object_or_404(products, pk=product_id)
    form, cart = handle_cart_form(request, product, create_cart=True)
    if form.is_valid():
        form.save()
        if request.is_ajax():
            response = JsonResponse(
                {'next': reverse('cart:index')}, status=200)
        else:
            response = redirect('cart:index')
    else:
        if request.is_ajax():
            response = JsonResponse({'error': form.errors}, status=400)
        else:
            response = product_details(request, slug, product_id, form)
    if not request.user.is_authenticated:
        set_cart_cookie(cart, response)
    return response


def category_index(request, path, category_id):
    category = get_object_or_404(Category, id=category_id)
    actual_path = category.get_full_path()
    if actual_path != path:
        return redirect('product:category', permanent=True, path=actual_path,
                        category_id=category_id)
    # Check for subcategories
    # categories = category.get_descendants(include_self=True)

    categories = get_descendant(category_id,with_self=True)
    products = products_with_details(user=request.user).filter(
        category__in=categories).order_by('category_id','name')
    approved_values = get_filter_values(categories, APPROVED_FILTER)

    product_filter= ProductCategoryFilter(
        request.GET, queryset=products, category=categories, attributes=APPROVED_FILTER, values=approved_values)


    ctx = get_product_list_context(request, product_filter)
    ctx.update({'object': category})

    return TemplateResponse(request, 'category/index.html', ctx)

def brand_index(request, path, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    actual_path = brand.get_full_path()
    if actual_path != path:
        return redirect('product:brand', permanent=True, path=actual_path,
                        brand_id=brand_id)
    
    categories = Product.objects.values('category_id').distinct().filter(brand_id_id=brand_id)
    products = products_with_details(user=request.user).filter(
        brand_id_id=brand_id).order_by('name')

    product_filter= ProductBrandFilter(
        request.GET, queryset=products, category=categories, attributes=['Jenis','Color','Gender'])


    ctx = get_product_list_context(request, product_filter)
    ctx.update({'object': brand})

    return TemplateResponse(request, 'brand/index.html', ctx)

def tags_index(request, path, tag_id):
    request_page = int(request.GET.get('page','')) if request.GET.get('page','') else 1
    tag = get_object_or_404(Feature, id=tag_id)
    actual_path = tag.get_full_path()
    if actual_path != path:
        return redirect('product:tags', permanent=True, path=actual_path,
                        tag_id=tag_id)
    ctx = {
        'query': tag,
        'query_string': '?page='+ str(request_page)
        }
    request.session['tag_query'] = tag_id
    request.session['tag_page'] = request_page
    response = TemplateResponse(request, 'tag/index.html', ctx)
    return response

def tags_render(request):
    ratings = list(ProductRating.objects.all().values('product_id').annotate(value=Avg('value')))
    request_page = 1
    if 'page' not in request.GET:
        if 'tag_page' in request.session and request.session['tag_page']:
            request_page = request.session['tag_page']
    else:
        request_page = int(request.GET.get('page')) if request.GET.get('page') else 1
    tag = get_object_or_404(Feature, id=request.session['tag_query'])
    results = []
    start = (settings.PAGINATE_BY*(request_page-1))
    end = start+(settings.PAGINATE_BY)
    populate_product = list(ProductFeature.objects.filter(feature_id_id=tag.id).values_list('product_id_id', flat=True))
    products = list(Product.objects.filter(id__in=populate_product[start:end]))          
    results = Parallel(n_jobs=psutil.cpu_count()*2,
                verbose=50,
                require='sharedmem',
                backend="threading")(delayed(render_item)(item,request.discounts,request.currency,ratings) for item in products)
    front = [i for i in range((start))]
    results = front+results
    for item in populate_product[end:]:
        results.append(item)
    page = paginate_results(list(results), request_page)
    ctx = {
        'query': tag,
        'count_query' : len(results) if results else 0,
        'results': page,
        'query_string': '?page='+ str(request_page)}
    response = TemplateResponse(request, 'tag/results.html', ctx)

    return response

def collection_index(request, slug, pk):
    collection = get_object_or_404(Collection, id=pk)
    if collection.slug != slug:
        return HttpResponsePermanentRedirect(collection.get_absolute_url())
    products = products_with_details(user=request.user).filter(
        collections__id=collection.id).order_by('name')
    product_filter = ProductCollectionFilter(
        request.GET, queryset=products, collection=collection)
    ctx = get_product_list_context(request, product_filter)
    ctx.update({'object': collection})
    return TemplateResponse(request, 'collection/index.html', ctx)

def get_similar_product(product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        raise Http404('No %s matches the given query.' % product.model._meta.object_name)
    pivot_feature = ProductFeature.objects.filter(product_id_id=product_id).values_list('feature_id_id', flat=True)
    in_clause = '('
    for i,f in enumerate(pivot_feature):
        in_clause += str(f)
        if i < len(pivot_feature)-1:
            in_clause += ', '
    in_clause += ')'
    query = """
                SELECT fp.product_id_id AS id, f.word, f.count, fp.frequency
                FROM feature_feature f JOIN feature_productfeature fp
                ON fp.feature_id_id = f.id AND fp.feature_id_id IN """+in_clause+"""
                ORDER BY id
            """
    cursor = connection.cursor()
    cursor.execute(query)
    product_features = [{'id':item[0],
                         'word':item[1],
                         'count': item[2],
                         'frequency' : item[3]
                        } for item in cursor.fetchall()]
    cursor.close()
    pivot_feature = Feature.objects.filter(id__in=pivot_feature).values_list('word', flat=True)
    product_list = list(Product.objects.filter(id__in=[d['id'] for d in product_features]).values_list('id', flat=True))
    total_product = list(Product.objects.all().values_list('id', flat=True))
    total = len(total_product)
    list_similar_product = Parallel(n_jobs=psutil.cpu_count()*2,
            verbose=50,
            require='sharedmem',
            backend="threading")(delayed(count_similarity)(product_features,pivot_feature,total,item) for item in product_list)
    return list_similar_product


def render_similar_product(request, product_id):
    start_time = time.time()
    list_similar_product = []
    products = []
    try:
        product = Product.objects.get(id=product_id)
        
    except Product.DoesNotExist:
        return TemplateResponse(request, 'product/_small_items.html', {
            'products': products})
    status = False
    check = []
    if 'similar_product' in request.session and request.session['similar_product']:
        check = list(filter(lambda e : e['id'] == product.id, request.session['similar_product']))
        if check and check[0]['related']:
            status = True

    if status:
        list_similar_product = check[0]['related']
    else:
        temp = {}
        list_similar_product = get_similar_product(product_id)
        if list_similar_product:
            list_similar_product = sorted(list_similar_product, key=itemgetter('similarity'), reverse=True)
            all_temp = []
            temp['id'] = product.id
            temp['related'] = list_similar_product
            if 'similar_product' in request.session and request.session['similar_product']:
                all_temp = request.session['similar_product']
            all_temp.append(temp)
            request.session['similar_product'] = all_temp

    list_similarity = []
    if list_similar_product:
        list_similar_product = sorted(list_similar_product, key=itemgetter('similarity'), reverse=True)
        products = Product.objects.filter(id__in=[d['id'] for d in list_similar_product[:12]])
        products = products_with_availability(
            products, discounts=request.discounts, local_currency=request.currency)
        list_similarity = [round(d['similarity'],4) for d in list_similar_product[:12]]
    
    response = TemplateResponse(
        request, 'product/_small_items.html', {
            'products': products, 'product_id':product_id, 'similarity':list_similarity})
    print("\nWaktu eksekusi : --- %s detik ---" % (time.time() - start_time))
    return response

def count_similarity(product_features, pivot_feature, total, item):
    similar_feature = list(filter(lambda e: int(e.get('id')) == int(item) and e.get('word') in pivot_feature, product_features))
    
    similarity = 0.0
    if similar_feature:
        for val in similar_feature:
            similarity += val['frequency']*(log10(1+total/val['count']))
        similarity *= (len(pivot_feature)/len(similar_feature))
    if similarity > 0:
        element = {}
        element['id'] = item
        element['similarity'] = similarity
        return element

def all_similar_product(request, product_id):
    request_page = int(request.GET.get('page','')) if request.GET.get('page','') else 1
    try:
        product = Product.objects.get(id=product_id)
        
    except Product.DoesNotExist:
        raise Http404('No %s matches the given query.' % product.model._meta.object_name)

    ctx = {
        'query': product,
        'product_id' : product_id,
        'query_string': '?page='+ str(request_page)
        }

    request.session['similar_page'] = request_page
    response = TemplateResponse(request, 'product/all_similar.html', ctx)
    return response


def render_all_similar_product(request, product_id):
    start_time = time.time()
    list_similar_product = []
    products = []
    request_page = int(request.GET.get('page')) if request.GET.get('page') else 1
    try:
        product = Product.objects.get(id=product_id)
        
    except Product.DoesNotExist:
        ctx = {
            'query': product.model._meta.object_name,
            'count_query' : '-',
            'results': [],
            'query_string': '?page='+ str(request_page)}
        return TemplateResponse(request, 'product/similar_results.html', ctx)

    status = False
    check = []
    if 'similar_product' in request.session and request.session['similar_product']:
        check = list(filter(lambda e : e['id'] == product.id, request.session['similar_product']))
        if check and check[0]['related']:
            status = True

    if status:
        list_similar_product = check[0]['related']
    else:
        temp = {}
        list_similar_product = get_similar_product(product_id)
        if list_similar_product:
            list_similar_product = sorted(list_similar_product, key=itemgetter('similarity'), reverse=True)
            all_temp = []
            temp['id'] = product.id
            temp['related'] = list_similar_product
            if 'similar_product' in request.session and request.session['similar_product']:
                all_temp = request.session['similar_product']
            all_temp.append(temp)
            request.session['similar_product'] = all_temp

    if list_similar_product:
        ratings = list(ProductRating.objects.all().values('product_id').annotate(value=Avg('value')))
        request_page = 1
        if 'page' not in request.GET:
            if 'similar_page' in request.session and request.session['similar_page']:
                request_page = request.session['similar_page']
        else:
            results = []
            start = (settings.PAGINATE_BY*(request_page-1))
            end = start+(settings.PAGINATE_BY)
            products = list(Product.objects.filter(id__in=[d['id'] for d in list_similar_product[start:end]]))          
            results = Parallel(n_jobs=psutil.cpu_count()*2,
                        verbose=50,
                        require='sharedmem',
                        backend="threading")(delayed(render_item)(item,request.discounts,request.currency,ratings) for item in products)
            front = [i for i in range((start))]
            results = front+results
            for item in [d['id'] for d in list_similar_product[end:]]:
                results.append(item)
            page = paginate_results(list(results), request_page)
            ctx = {
                'query': product,
                'count_query' : len(results) if results else 0,
                'results': page,
                'query_string': '?page='+ str(request_page)}
            response = TemplateResponse(request, 'product/similar_results.html', ctx)

            return response

def get_all_discounted_product(request):
    request_page = int(request.GET.get('page','')) if request.GET.get('page','') else 1
    
    ctx = {
        'query': '',
        'query_string': '?page='+ str(request_page)
        }
    request.session['sale_page'] = request_page
    response = TemplateResponse(request, 'sale/index.html', ctx)
    return response

def render_discounted_product(request):
    ratings = list(ProductRating.objects.all().values('product_id').annotate(value=Avg('value')))
    request_page = 1
    query = """
            SELECT p.id AS id 
            FROM discount_sale_products d, product_product p, product_productvariant v
            WHERE p.id = d.product_id AND p.is_published = True AND p.id = v.product_id AND v.quantity - v.quantity_allocated > 0
            ORDER BY id;
            """
    cursor = connection.cursor()
    cursor.execute(query)
    product_list = row = [item[0] for item in cursor.fetchall()]
    cursor.close()
    if 'page' not in request.GET:
        if 'sale_page' in request.session and request.session['sale_page']:
            request_page = request.session['sale_page']
    else:
        request_page = int(request.GET.get('page')) if request.GET.get('page') else 1
        
    results = []
    start = (settings.PAGINATE_BY*(request_page-1))
    end = start+(settings.PAGINATE_BY)

    products = list(Product.objects.filter(id__in=product_list[start:end]))          
    results = Parallel(n_jobs=psutil.cpu_count()*2,
                verbose=50,
                require='sharedmem',
                backend="threading")(delayed(render_item)(item,request.discounts,request.currency,ratings) for item in products)
    front = [i for i in range((start))]
    results = front+results
    for item in product_list[end:]:
        results.append(item)
    page = paginate_results(list(results), request_page)
    ctx = {
        'query': '',
        'count_query' : len(results) if results else 0,
        'results': page,
        'query_string': '?page='+ str(request_page)}
    response = TemplateResponse(request, 'sale/results.html', ctx)

    return response

MODE_REECOMMENDER = ['verbose','quiet']
@csrf_exempt
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def get_arc_recommendation(request, mode, limit):
    start_time = time.time()
    if request.method == 'GET':
        if mode not in MODE_REECOMMENDER:
            result = {'success':False,'recommendation':None,'process_time':(time.time() -  start_time)}
            return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = request.GET

            if 'user' not in data:
                result = {'success':False,'recommendation':None,'process_time':(time.time() -  start_time)}
                return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)
            if data['user']:
                status_source = False
                source = ''
                try:
                    source_data = ProductRating.objects.filter(user_id=data['user'])
                    source = 'rating'
                    status_source = True
                except ProductRating.DoesNotExist:
                    pass
                if not status_source:
                    try:
                        source_data = Order.objects.filter(user_id=data['user'])
                        source = 'order'
                        status_source = True
                    except Order.DoesNotExist:
                        result = {'success':False,'recommendation':'user has no data to process','process_time':(time.time() -  start_time)}
                        return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)
                del source_data

                print(source)
                if status_source:
                    if source == 'order':
                        distinct_user = get_list_user_from_order()
                        distinct_product = get_list_product_from_order()
                        data_input = get_cross_section_order()
                    else:
                        distinct_user = get_list_user_from_rating()
                        distinct_product = get_list_product_from_rating()
                        data_input = get_cross_section_rating()

                    print('done db queries in %s'%(time.time() -  start_time))
                    start_convert = time.time()
                    cross_section, binary_cross_section = process_cross_section(data_input,distinct_user,distinct_product)
                    print('done generating 2d matrix in %s'%(time.time() -  start_convert))

                    start_count = time.time()
                    user_similarity = collaborative_similarity(cross_section, len(distinct_user), len(distinct_product))
                    print('done processing collaborative similarity in %s'%(time.time() -  start_count))

                    result_matrix = []
                    user_id = distinct_user.index(int(data['user']))
                    order = 1
                    results = {}
                    start_similarity = time.time()
                    while True:
                        if result_matrix:
                            if 0 not in result_matrix[-1][user_id] or order > int(limit):
                                results['ordinality']  = order
                                results['score_for_user'] = result_matrix[-1][user_id]
                                break
                        if order == 1:
                            final_weight = (binary_cross_section.dot(binary_cross_section.T)*(user_similarity)).dot(cross_section)
                            result_matrix.append(final_weight)
                        else:
                            check = result_matrix[-1]
                            final_weight = (binary_cross_section.dot(binary_cross_section.T)*(user_similarity)).dot(check)
                            result_matrix.append(final_weight)
                        order += 2

                    print('done processing similarity %s'%(time.time() -  start_similarity))
                    total_ratings = list(ProductRating.objects.all().values('product_id').annotate(value=Avg('value')))
                    user_ratings = get_all_user_rating(data['user'])
                    results['score_for_user'] = list(filter(lambda e : e > 0, results['score_for_user']))
                    products = [distinct_product[i] for i in range(0,len(results['score_for_user']))]
                    products = list(Product.objects.filter(id__in=products))
                    
                    recommended_items = {}
                    all_products = []
                    for item, score in zip(products, results['score_for_user']):
                        temp = {}
                        temp['id'] = item.id
                        temp['name'] = item.name
                        temp['confident'] = score
                        check = list(filter(lambda e: e['product_id'] == int(item.id), total_ratings))
                        rating = check[0] if check else {'product_id':item.id,'value':0.0}
                        temp['total_rating'] = rating['value']
                        check = list(filter(lambda e: e['product_id'] == int(item.id), user_ratings))
                        rating = check[0] if check else {'product_id':item.id,'value':0.0}
                        temp['user_rating'] = rating['value']
                        all_products.append(temp)

                    all_products = sorted(all_products, key=itemgetter('confident'), reverse=True)
                    del results['score_for_user']
                    recommended_items['products'] = all_products
                    recommended_items['total'] = len(all_products)
                    results['recommendation'] = recommended_items
                    results['status'] = True
                    results['process_time'] = (time.time() -  start_time)
                    return JsonResponse(results) 

    else:
        result = {'success':False,'recommendation':None,'process_time':(time.time() -  start_time)}
        return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST) 
    print("\nWaktu eksekusi : --- %s detik ---" % (time.time() - start_time))

def collaborative_similarity(array_input, users, items):
    list_similarity = create_fixed_array(users,users, dtype=float)
    max_range = np.max(array_input)
    for i in range(0,users):
        for j in range(0,users):
            if i == j:
                list_similarity[i][j] = 1
            else:
                similarity = []
                for k in range(0,items):
                    if array_input[i][k] > 0  and array_input[j][k] > 0:
                        val =  max_range - abs(array_input[i][k]-array_input[j][k])/max_range
                        similarity.append(val)
                    else:
                        similarity.append(0)
                list_similarity[i][j] = sum(similarity)/len(similarity)

    return np.array(list_similarity)

def process_cross_section(array_input, distinct_a, distinct_b):
    total_a = len(distinct_a)
    total_b = len(distinct_b)
    
    results_normal = create_fixed_array(total_a,total_b)
    for item in array_input:
        results_normal[distinct_a.index(item[0])][distinct_b.index(item[1])] = item[2]

    results_binary = np.copy(results_normal)
    results_binary[results_binary>1] = 1
    print(len(results_normal), len(results_binary))
    return results_normal, results_binary

def create_fixed_array(col, row, dtype=int):
    return np.zeros([col,row], dtype=dtype).tolist()