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
from django.db.models import Case, When
from .utils.availability import get_availability
from ..search.views import render_item, paginate_results, custom_query_validation
from .utils.variants_picker import get_variant_picker_data
from ..core.helper import create_navbar_tree
from .helper import (
    get_filter_values, get_descendant, get_cross_section_order,
    get_cross_section_rating, get_list_product_from_order, get_list_product_from_rating,
    get_list_user_from_order, get_list_user_from_rating, get_all_user_rating, get_all_user_order_history,
    get_product_order_history, get_user_order_history, get_product_rating_history, get_rating_relevant_item,
    get_order_relevant_item, get_visit_relevant_item, get_all_rating_data, get_all_order_data)
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
from django.contrib.auth.models import AnonymousUser
from ..account.models import User
from ..track.models import VisitProduct, SearchHistory

APPROVED_FILTER = ['Brand','Jenis','Color','Gender']

#RECOMMENDATION MODULE PARAMETER:
"""
EVALUATION:
A strict approach means the evaluation only compare the recommended item with user actual item data,
whilst the non-strict approach means the evaluation will compare the recommended item with all item from top 5 (default)
categories which each user favoured. The non-strict approach is inspired by how a user behaviour, a user tend to like or need
only a specific number of categories, so we can recommend all product from a specific categories for them.

COLLABORATIVE:
We are using Associative Retrieval Correlation Algorithm as collaborative filtering, You need to specify the maximum limit
of ordinality used by ARC. By default our system will break the iteration if all product can successfully matched to a user
but to avoid a high number of iteration you can specify ARC_ORDINALITY as the maximum ordinality our system will handle.

CONTENT BASE:
We are using a TF-IDF Smooth approach to count the similarity between each item. This method retrieve information from item's
name, brand, category, description, information, service, location, and specification. By that, this method is highly dependent
on how clear you put information in each item. Luckily we use an actual E-commerce data crawled from www.blibli.com (Thanks for the data)
so we cann get satisfying result with this type of filtering. By default you will get all similar items, but you can specify a number as
a limit on how many similar item you would like to retrieve.
"""

LIMIT_COLLABORATIVE = 15 #A REAL NUMBER RANGE FROM 0 TO ANY POSITIVE NUMBER, IF NOT 0 THEN USE THE LIMIT IF 0 THEN USE ALL
LIMIT_CONTENT_BASE = 30 #A REAL NUMBER RAGE FROM 1 TO ANY POSITIVE NUMBER, GET THE NUMBER OF SIMILAR ITEM(S)
EVALUATION_MODE = 0 #A NUMBER OF 0 OR 1, IF 0 THEN USE A NON-STRICT APPROACH IF 1 THEN USE A STRICT APPROACH
ARC_ORDINALITY = 9 #A POSITIVE ODD REAL NUMBER, IN RANGE OF 1 TO 13, IF 1 THEN RETURNED THE USER ORIGINAL DATA
LIMIT_FEATURED = 12 #A POSITIVE REAL NUMBER STARTING FROM 1, TO LIMIT NUMBER OF FEATURED PRODUCT IN STOREFRONT

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

def get_similar_product(product_id,limit=0):
    start_time = time.time()
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        raise Http404('No %s matches the given query.' % product.model._meta.object_name)
    pivot_feature = list(ProductFeature.objects.filter(product_id_id=product_id).values_list('feature_id_id', flat=True))
    in_clause = '('
    for i,f in enumerate(pivot_feature):
        in_clause += str(f)
        if i < len(pivot_feature)-1:
            in_clause += ', '
    in_clause += ')'
    query = """
                SELECT fp.product_id_id AS id, f.id AS fid, f.count, fp.frequency
                FROM feature_feature f JOIN feature_productfeature fp
                ON fp.feature_id_id = f.id AND fp.feature_id_id IN """+in_clause+"""
                ORDER BY id
            """
    cursor = connection.cursor()
    cursor.execute(query)
    temp_product_features = np.array([item[:] for item in cursor.fetchall()] )

    cursor.close()
    total = len(list(Product.objects.all().values_list('id', flat=True)))
    xs = temp_product_features[:,0]
    ys = temp_product_features[:,1]
    zs = temp_product_features[:,2]
    fs = temp_product_features[:,3]
    xs_val, xs_idx = np.unique(xs, return_inverse=True)
    ys_val, ys_idx = np.unique(ys, return_inverse=True)
    results_count = np.zeros(xs_val.shape+ys_val.shape)
    results_freq = np.zeros(xs_val.shape+ys_val.shape)
    results_count.fill(0)
    results_freq.fill(0)
    results_count[xs_idx,ys_idx] = zs
    results_freq[xs_idx,ys_idx] = fs
    pivot_idx = np.in1d(xs_val, float(product_id)).nonzero()[0]
    pivot_freq = results_freq[pivot_idx]
    results_freq = (1-(abs(results_freq-pivot_freq)/pivot_freq)) #normalize the frequency in order to make the pivot item always ranked first
    temp_pivot = np.array(pivot_feature)
    results_freq[results_freq[:,:]<0] = 0
    check_idx = np.in1d(ys_val, temp_pivot).nonzero()[0]
    # results_count = total/results_count
    # results_count[results_count[:,:]==float('inf')] = 0
    # final_weight = np.log10(1+results_count) 
    final_weight = results_freq
    mask = np.ones(len(ys_val), np.bool)
    mask[check_idx] = 0
    final_weight[:,mask] = 0

    del temp_product_features
    del results_count
    del results_freq
    del check_idx
    del xs
    del ys
    del zs
    del fs
    target_feature = len(pivot_feature)

    arr_sum = np.zeros((len(xs_val),2))
    arr_sum[:,0] = xs_val
    arr_sum[:,1] = (np.sum(final_weight, axis=1))/target_feature
    arr_sum = arr_sum[arr_sum[:,1].argsort()[::-1]]
    if limit > 0:
        arr_sum = arr_sum[:limit]
    del final_weight
    
    arr_sum = arr_sum.tolist()
    list_similar_product = [{'id':item[0],'similarity':item[1]} for item in arr_sum]
    list_similar_product = list(filter(lambda e:e.get('similarity') > 0, list_similar_product))
    list_similar_product = sorted(list_similar_product, key=itemgetter('similarity'), reverse=True)
    print('done populating similar products in %s'%(time.time() -  start_time))
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
            all_temp = []
            temp['id'] = product.id
            temp['related'] = list_similar_product
            if 'similar_product' in request.session and request.session['similar_product']:
                all_temp = request.session['similar_product']
            all_temp.append(temp)
            request.session['similar_product'] = all_temp

    list_similarity = []
    if list_similar_product:
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate([d['id'] for d in list_similar_product[:12]])])
        products = list(Product.objects.filter(id__in=[d['id'] for d in list_similar_product[:12]]).order_by(preserved))
        products = products_with_availability(
            products, discounts=request.discounts, local_currency=request.currency)
        list_similarity = [round(d['similarity'],4) for d in list_similar_product[:12]]
    
    response = TemplateResponse(
        request, 'product/_small_items.html', {
            'products': products, 'product_id':product_id, 'similarity':list_similarity})
    print("\nWaktu eksekusi : --- %s detik ---" % (time.time() - start_time))
    return response

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
            all_temp = []
            temp['id'] = product.id
            temp['related'] = list_similar_product
            if 'similar_product' in request.session and request.session['similar_product']:
                all_temp = request.session['similar_product']
            all_temp.append(temp)
            request.session['similar_product'] = all_temp

    if list_similar_product:
        ratings = list(ProductRating.objects.all().values('product_id').annotate(value=Avg('value')))
        if 'page' not in request.GET:
            if 'similar_page' in request.session and request.session['similar_page']:
                request_page = request.session['similar_page']
        else:
            results = []
            start = (settings.PAGINATE_BY*(request_page-1))
            end = start+(settings.PAGINATE_BY)
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate([d['id'] for d in list_similar_product[start:end]])])
            products = list(Product.objects.filter(id__in=[d['id'] for d in list_similar_product[start:end]]).order_by(preserved))         
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
    else:
        ctx = {
            'query': product.model._meta.object_name,
            'count_query' : '-',
            'results': [],
            'query_string': '?page='+ str(request_page)}
        return TemplateResponse(request, 'product/similar_results.html', ctx)

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

def get_data_order():
    return get_cross_section_order()

def get_data_rating():
    return get_cross_section_rating()

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
                    source_data = Order.objects.filter(user_id=data['user'])
                    source = 'order'
                    status_source = True
                except Order.DoesNotExist:
                    pass
                if not status_source:
                    try:
                        source_data = ProductRating.objects.filter(user_id=data['user'])
                        source = 'rating'
                        status_source = True
                    except ProductRating.DoesNotExist:
                        result = {'success':False,'recommendation':'user has no data to process','process_time':(time.time() -  start_time)}
                        return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)
                del source_data

                if status_source:
                    if source == 'order':
                        data_input = get_data_order()
                    else:
                        data_input = get_data_rating()

                    print('done db queries in %s'%(time.time() -  start_time))
                    cross_section, binary_cross_section, distinct_user, distinct_product = process_cross_section(data_input)

                    start_count = time.time()
                    user_similarity = collaborative_similarity(cross_section, len(distinct_user))
                    print('done processing collaborative similarity in %s'%(time.time() -  start_count))

                    result_matrix = []
                    user_id = distinct_user.index(int(data['user']))
                    order = 1
                    results = {}
                    start_similarity = time.time()
                    while True:
                        if result_matrix:
                            if 0 not in result_matrix[-1][user_id] or order >= int(limit):
                                results['ordinality']  = order
                                results['score_for_user'] = result_matrix[-1][user_id]
                                break
                        if order == 1:
                            final_weight = cross_section
                            result_matrix.append(final_weight)
                        else:
                            check = result_matrix[-1]
                            final_weight = np.matmul((np.matmul(binary_cross_section,binary_cross_section.T))*(user_similarity),check)
                            result_matrix.append(final_weight)
                        order += 2

                    print('done processing similarity %s'%(time.time() -  start_similarity))
                    all_info = []
                    user_info = []
                    if source == 'rating':
                        all_info = list(ProductRating.objects.all().values('product_id').annotate(value=Avg('value')))
                        user_info = get_all_user_rating(data['user'])
                    else:
                        all_info = get_product_order_history()
                        user_info = get_user_order_history(data['user'])

                    results['score_for_user'] = list(filter(lambda e : e > 0, results['score_for_user']))
                    products = [distinct_product[i] for i in range(0,len(results['score_for_user']))]
                    products = list(Product.objects.filter(id__in=products))
                    
                    recommended_items = {}
                    all_products = []
                    process_result = zip(products, results['score_for_user'])
                    for item, score in process_result:
                        temp = {}
                        temp['id'] = item.id
                        temp['name'] = item.name
                        temp['confident'] = score
                        all_products.append(temp)

                    all_products = sorted(all_products, key=itemgetter('confident'), reverse=True)
                    if LIMIT_COLLABORATIVE > 0:
                        all_products = all_products[:LIMIT_COLLABORATIVE]
                    products = {}
                    for item in reversed(all_products):
                        products[item['id']] = {'name':item['name'],
                                                    'value':item['confident']}
                        if LIMIT_CONTENT_BASE > 1:
                            similar_product = get_similar_product(item['id'], LIMIT_CONTENT_BASE)
                            for sub_item in similar_product:
                            	if sub_item['id'] in products:
                            		new_val = item['confident']*sub_item['similarity']
                            		if products[sub_item['id']]['value'] < new_val:
                            			products[sub_item['id']] = {'name':item['name'],
                                                            'value':new_val}
                            	else:
                                	products[sub_item['id']] = {'name':item['name'],
                                                            'value':item['confident']*sub_item['similarity']}

                    final_product = []
                    for key, value in products.items():
                        element = {}
                        element['id'] = int(key)    
                        element['name'] = value['name']
                        element['confident'] = round(value['value'],4)
                        check = list(filter(lambda e: e['product_id'] == int(key), all_info))
                        info = check[0] if check else {'product_id':int(key),'value':0.0}
                        if source == 'rating':
                            element['total_rating'] = info['value']
                        else:
                            element['total_order'] = info['value']
                        check = list(filter(lambda e: e['product_id'] == int(key), user_info))
                        info = check[0] if check else {'product_id':int(key),'value':0.0}
                        if source == 'rating':
                            element['user_rating'] = info['value']
                        else:
                            element['user_order'] = info['value']
                        final_product.append(element)

                    final_product = sorted(final_product, key=itemgetter('confident'), reverse=True)

                    del results['score_for_user']
                    recommended_items['products'] = final_product
                    recommended_items['total'] = len(final_product)
                    results['recommendation'] = recommended_items
                    results['success'] = True
                    results['source'] = source
                    results['process_time'] = (time.time() -  start_time)
                    return JsonResponse(results) 

    else:
        result = {'success':False,'recommendation':None,'process_time':(time.time() -  start_time)}
        return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST) 
    print("\nWaktu eksekusi : --- %s detik ---" % (time.time() - start_time))

def get_recommendation(request):
    start_time = time.time()
    if '_auth_user_id' in request.session and request.session['_auth_user_id']:
        user = request.session['_auth_user_id']
        status_source = False
        source = ''
        source_order = get_user_order_history(user)
        source_rating = get_all_user_rating(user)
        
        if source_order and source_rating:
            status_source = True
            if len(source_rating) >= len(source_order):
                source = 'rating'
            else:
                source = 'order'
        elif source_order and not source_rating:
            status_source = True
            source = 'order'
        elif source_rating and not source_order:
            status_source = True
            source = 'rating'
        else:
            results = {}
            try:
                source_data = list(VisitProduct.objects.filter(user_id=user).values('product_id_id','count'))
                if source_data:
                    if source == 'order':
                        data_input = get_data_order()
                    else:
                        data_input = get_data_rating()

                    print('done db queries in %s'%(time.time() -  start_time))
                    visited = np.array([[item.get('product_id_id'), item.get('count')] for item in source_data] )
                    results = {}
                    recommended_items = {}
                    cross_section, binary_cross_section, distinct_user, distinct_product = process_cross_section(data_input)
                    anon_user = int(np.max(distinct_user)) + 1
                    distinct_user.append(anon_user)
                    anon_record = np.zeros([1,len(distinct_product)])
                    ys = visited[:,0]
                    zs = visited[:,1]
                    ys_val, ys_idx = np.unique(distinct_product, return_inverse=True)
                    check_idx = np.in1d(ys_val, ys).nonzero()[0]
                    anon_record[:,check_idx] = zs
                    anon_record[anon_record>5] = 5
                    anon_binary = np.copy(anon_record)
                    anon_binary[anon_binary>1] = 1
                    cross_section = np.vstack((cross_section,anon_record))
                    binary_cross_section = np.vstack((binary_cross_section,anon_binary))

                    source = 'visit'
                    status_source = True
                    all_products, ordinality = collaborative_filtering(anon_user, cross_section, binary_cross_section, distinct_user, distinct_product)
                    
                    if LIMIT_COLLABORATIVE > 0:
                        all_products = all_products[:LIMIT_COLLABORATIVE] #select number of recommended product from another user

                    products = {}
                    for item in reversed(all_products):
                        products[item['id']] = item['confidence']
                        if LIMIT_CONTENT_BASE>1:
                            similar_product = get_similar_product(item['id'], LIMIT_CONTENT_BASE) #select number of similar products on each recommended product
                            for sub_item in similar_product:
                            	if sub_item['id'] in products:
                            		new_val = item['confidence']*sub_item['similarity']
                            		if new_val > products[sub_item['id']]:
                            			products[sub_item['id']] = new_val
                            	else:
                                	products[sub_item['id']] = item['confidence']*sub_item['similarity']

                    final_product = []
                    for key, value in products.items():
                        element = {}
                        element['id'] = key
                        element['confidence'] = round(value,4)
                        final_product.append(element)

                    final_product = sorted(final_product, key=itemgetter('confidence'), reverse=True)
                    recommended_items['products'] = final_product
                    recommended_items['total'] = len(final_product)
                    results['recommendation'] = recommended_items
                    results['success'] = True
                    results['ordinality'] = ordinality
                    results['evaluate'] = True
                    results['source'] = source
                    results['process_time'] = (time.time() -  start_time)
                    return JsonResponse(results)
                else:
                    status_source = False
            except VisitProduct.DoesNotExist:
                pass
            if not status_source:
                try:
                    source_data = list(SearchHistory.objects.filter(user_id=user).values_list('clean_query', flat=True))
                    if source_data:
                        source = 'search'
                        status_source = True
                        common_query = []
                        for query in source_data:
                            common_query += query.split(' ')
                        common_query = np.array(common_query)
                        unique, pos = np.unique(common_query, return_inverse=True)
                        counts = np.bincount(pos)
                        maxsort = counts.argsort()[::-1]
                        user_query = ' '.join(unique[maxsort][:3].tolist())

                        products = custom_query_validation(user_query)
                        final_product = []
                        for item in products:
                            element = {}
                            element['id'] = item.get('id')
                            element['confidence'] = round(item.get('similarity'),4)
                            final_product.append(element)

                        recommended_items = {}
                        final_product = sorted(final_product, key=itemgetter('confidence'), reverse=True)
                        recommended_items['products'] = final_product
                        recommended_items['total'] = len(final_product)
                        results['recommendation'] = recommended_items
                        results['success'] = True
                        results['evaluate'] = False
                        results['source'] = source
                        results['process_time'] = (time.time() -  start_time)
                        return JsonResponse(results)
                    else:
                        status_source = False
                except SearchHistory.DoesNotExist:
                    pass
            del source_data
            if not status_source:
                results = get_default_recommendation(request)
                return JsonResponse(results)

        if status_source:
            if source == 'order':
                data_input = get_data_order()
            else:
                data_input = get_data_rating()

            print('done db queries in %s'%(time.time() -  start_time))
            
            results = {}
            recommended_items = {}
            cross_section, binary_cross_section, distinct_user, distinct_product = process_cross_section(data_input)

            all_products, ordinality = collaborative_filtering(user, cross_section, binary_cross_section, distinct_user, distinct_product)
            
            if LIMIT_COLLABORATIVE > 0:
                all_products = all_products[:LIMIT_COLLABORATIVE] #select number of recommended product from another user

            products = {}
            for item in reversed(all_products):
                products[item['id']] = item['confidence']
                if LIMIT_CONTENT_BASE > 1:
                    similar_product = get_similar_product(item['id'], LIMIT_CONTENT_BASE) #select number of similar products on each recommended product
                    for sub_item in similar_product:
                    	if sub_item['id'] in products:
                    		new_val = item['confidence']*sub_item['similarity']
                    		if new_val > products[sub_item['id']]:
                    			products[sub_item['id']] = new_val
                    	else:
                    		products[sub_item['id']] = item['confidence']*sub_item['similarity']

            final_product = []
            for key, value in products.items():
                element = {}
                element['id'] = key
                element['confidence'] = round(value,4)
                final_product.append(element)

            final_product = sorted(final_product, key=itemgetter('confidence'), reverse=True)
            recommended_items['products'] = final_product
            recommended_items['total'] = len(final_product)
            results['recommendation'] = recommended_items
            results['ordinality'] = ordinality
            results['success'] = True
            results['evaluate'] = True
            results['source'] = source
            results['process_time'] = (time.time() -  start_time)
            return JsonResponse(results)
        else:
            results = get_default_recommendation(request)
            return JsonResponse(results)
    else:
        results = get_default_recommendation(request)
        return JsonResponse(results)

def collaborative_filtering(user, cross_section, binary_cross_section, distinct_user, distinct_product, limit=ARC_ORDINALITY):
    start_count = time.time()
    user_similarity = collaborative_similarity(cross_section, len(distinct_user))
    print('done processing collaborative similarity in %s'%(time.time() -  start_count))

    result_matrix = []
    user_id = distinct_user.index(int(user))
    order = 1
    results = []
    start_similarity = time.time()
    ordinality = 1
    while True:
        if order == 1:
            final_weight = cross_section
            result_matrix.append(final_weight)
        else:
            check = result_matrix[-1]
            final_weight = np.dot((np.dot(binary_cross_section,binary_cross_section.T))*(user_similarity),check)
            result_matrix.append(final_weight)
        if result_matrix:
            if 0 not in result_matrix[-1][user_id] and order >= 3 or order >= int(limit):
                ordinality = order
                results = result_matrix[-1][user_id]
                break
        order += 2


    del result_matrix

    print('done processing similarity %s'%(time.time() -  start_similarity))

    all_products = []
    process_result = zip(distinct_product, results.tolist())
    for item, score in process_result:
        temp = {}
        temp['id'] = item
        temp['confidence'] = score
        all_products.append(temp)

    all_products = list(filter(lambda e: e.get('confidence') > 0, all_products))
    all_products = sorted(all_products, key=itemgetter('confidence'), reverse=True)
    return all_products, ordinality

def get_default_recommendation(request):
    start_time = time.time()
    source = 'top'
    results = {}
    recommended_items = {}
    products = []
    if 'history' in request.session and request.session['history']:
        if 'visit' in request.session['history'] and request.session['history']['visit']:
            data_input = get_data_order()
            if not data_input:
                data_input = get_data_rating()
            
            if not data_input:
                products = get_product_order_history()
                final_product = []
                if not products:
                    products = get_product_rating_history()
                for item in products:
                    element = {}
                    element['id'] = item['product_id']
                    element['confidence'] = item['value']
                    final_product.append(element)

                recommended_items['products'] = final_product
                recommended_items['total'] = len(final_product)
                results['recommendation'] = recommended_items
                results['success'] = True
                results['process_time'] = (time.time() - start_time)
                results['evaluate'] = False
                results['source'] = source
                return results

            print('done db queries in %s'%(time.time() -  start_time))
            source = "visit"
            visited = np.array([[int(item),value] for item,value in request.session['history']['visit'].items()] )
            results = {}
            recommended_items = {}
            cross_section, binary_cross_section, distinct_user, distinct_product = process_cross_section(data_input)
            anon_user = int(np.max(distinct_user)) + 1
            distinct_user.append(anon_user)
            anon_record = np.zeros([1,len(distinct_product)])
            ys = visited[:,0]
            zs = visited[:,1]
            ys_val, ys_idx = np.unique(distinct_product, return_inverse=True)
            check_idx = np.in1d(ys_val, ys).nonzero()[0]
            anon_record[:,check_idx] = zs
            anon_record[anon_record>5] = 5
            anon_binary = np.copy(anon_record)
            anon_binary[anon_binary>1] = 1
            cross_section = np.vstack((cross_section,anon_record))
            binary_cross_section = np.vstack((binary_cross_section,anon_binary))

            all_products, ordinality = collaborative_filtering(anon_user, cross_section, binary_cross_section, distinct_user, distinct_product)
        
            if LIMIT_COLLABORATIVE > 0:
                all_products = all_products[:LIMIT_COLLABORATIVE] #select number of recommended product from another user

            products = {}
            for item in reversed(all_products):
                products[item['id']] = item['confidence']
                if LIMIT_CONTENT_BASE > 1:
                    similar_product = get_similar_product(item['id'], LIMIT_CONTENT_BASE) #select number of similar products on each recommended product
                    for sub_item in similar_product:
                    	if sub_item['id'] in products:
                    		new_val = item['confidence']*sub_item['similarity']
                    		if new_val > products[sub_item['id']]:
                    			products[sub_item['id']] = new_val
                    	else:
                    		products[sub_item['id']] = item['confidence']*sub_item['similarity']

            final_product = []
            for key, value in products.items():
                element = {}
                element['id'] = key
                element['confidence'] = round(value,4)
                final_product.append(element)

            final_product = sorted(final_product, key=itemgetter('confidence'), reverse=True)
            recommended_items['products'] = final_product
            recommended_items['total'] = len(final_product)
            results['recommendation'] = recommended_items
            results['success'] = True
            results['ordinality'] = ordinality
            results['evaluate'] = False
            results['source'] = source
            results['process_time'] = (time.time() -  start_time)
            return results
        elif 'search' in request.session['history'] and request.session['history']['search']:
            source = "search"
            common_query = []
            for query in request.session['history'] and request.session['history']['search']:
                common_query += query.get('clean').split(' ')
            common_query = np.array(common_query)
            unique, pos = np.unique(common_query, return_inverse=True)
            counts = np.bincount(pos)
            maxsort = counts.argsort()[::-1]
            user_query = ' '.join(unique[maxsort][:3].tolist())

            products = custom_query_validation(user_query)
            final_product = []
            for item in products:
                element = {}
                element['id'] = item.get('id')
                element['confidence'] = round(item.get('similarity'),4)
                final_product.append(element)

            final_product = sorted(final_product, key=itemgetter('confidence'), reverse=True)
            recommended_items['products'] = final_product
            recommended_items['total'] = len(final_product)
            results['recommendation'] = recommended_items
            results['success'] = True
            results['evaluate'] = False
            results['source'] = source
            results['process_time'] = (time.time() -  start_time)
            return results
        else:
            products = get_product_order_history()
    else:
        products = get_product_order_history()
    final_product = []
    if not products:
        products = get_product_rating_history()
    for item in products:
        element = {}
        element['id'] = item['product_id']
        element['confidence'] = item['value']
        final_product.append(element)

    recommended_items['products'] = final_product
    recommended_items['total'] = len(final_product)
    results['recommendation'] = recommended_items
    results['success'] = True
    results['process_time'] = (time.time() - start_time)
    results['evaluate'] = False
    results['source'] = source
    return results

@csrf_exempt
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def render_recommendation(request):
    allowed_source = ['visit','search','rating','order']
    if request.method == 'POST':
        data = request.data
        list_confidence = []
        list_product = json.loads(data.get('products'))        
        list_product = sorted(list_product, key=itemgetter('confidence'), reverse=True)
        request.session['recommendation'] = list_product
        request.session['source_recommendation'] = data.get('source')
        list_product = list_product[:LIMIT_FEATURED]
        
        products = []
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate([d.get('id') for d in list_product])])
        products = list(Product.objects.filter(id__in=[d.get('id') for d in list_product]).order_by(preserved))
        
        products = products_with_availability(
            products, discounts=request.discounts, local_currency=request.currency)
        if data.get('source') in allowed_source:
            list_confidence = [round(d.get('confidence'),4) for d in list_product]
        response = TemplateResponse(
        request, 'product/_items.html', {
            'products': products, 'confidences':list_confidence})
        return response

def all_recommendation(request):
    request_page = int(request.GET.get('page','')) if request.GET.get('page','') else 1
    ctx = {
        'query_string': '?page='+ str(request_page)
        }

    request.session['recommendation_page'] = request_page
    response = TemplateResponse(request, 'recommendation/index.html', ctx)
    return response

def get_render_all_recommendation(request):
    start_time = time.time()
    allowed_source = ['visit','search','rating','order']
    list_recommendation = []
    products = []
    source = ''
    request_page = int(request.GET.get('page')) if request.GET.get('page') else 1
    print(request_page)
    if 'recommendation' in request.session and request.session['recommendation'] and 'source_recommendation' in request.session and request.session['source_recommendation']:
        list_recommendation = request.session['recommendation']
        source = request.session['source_recommendation']
    else:
        temp = json.loads(get_recommendation(request).content)
        list_recommendation = temp['recommendation']['products']
        source = temp['source']

    if list_recommendation:
        confidences = []
        ratings = list(ProductRating.objects.all().values('product_id').annotate(value=Avg('value')))

        if 'page' not in request.GET:
            if 'recommendation_page' in request.session and request.session['recommendation_page']:
                request_page = request.session['recommendation_page']
        else:
            results = []
            start = (settings.PAGINATE_BY*(request_page-1))
            end = start+(settings.PAGINATE_BY)
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate([d['id'] for d in list_recommendation[start:end]])])
            products = list(Product.objects.filter(id__in=[d['id'] for d in list_recommendation[start:end]]).order_by(preserved))         
            results = Parallel(n_jobs=psutil.cpu_count()*2,
                        verbose=50,
                        require='sharedmem',
                        backend="threading")(delayed(render_item)(item,request.discounts,request.currency,ratings) for item in products)
            front = [i for i in range((start))]
            results = front+results
            for item in [d['id'] for d in list_recommendation[end:]]:
                results.append(item)
            if source in allowed_source:
                confidences = [round(d.get('confidence'),4) for d in list_recommendation]
            page = paginate_results(list(results), request_page)
            ctx = {
                'query': '',
                'count_query' : len(results) if results else 0,
                'results': page,
                'confidences': confidences,
                'query_string': '?page='+ str(request_page)}
            response = TemplateResponse(request, 'recommendation/results.html', ctx)

            return response
    else:
        ctx = {
            'query': '',
            'count_query' : '-',
            'results': [],
            'confidences': [],
            'query_string': '?page='+ str(request_page)}
        return TemplateResponse(request, 'recommendation/results.html', ctx)

@csrf_exempt
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def evaluate_recommendation(request):
    allowed_source = ['visit','rating','order']
    start_time = time.time()
    results = {}

    if request.method == 'POST':
        if '_auth_user_id' in request.session and request.session['_auth_user_id']:
            user = request.session['_auth_user_id']
            data = request.data
            if 'source' in data and data.get('source') in allowed_source:
                source = data.get('source')
                actual = []
                if source == 'rating':
                    all_data = get_all_rating_data()
                    all_data = [{'y':item[0], 'x':item[1]} for item in all_data]
                    if EVALUATION_MODE==0:
                        actual = get_rating_relevant_item(user)
                    else:
                        actual = get_all_user_rating(user)
                        actual = [item.get('product_id') for item in actual]
                elif source == 'order':
                    all_data = get_all_order_data()
                    all_data = [{'y':item[0], 'x':item[1]} for item in all_data]
                    if EVALUATION_MODE==0:
                        actual = get_order_relevant_item(user)
                    else:
                        actual = get_user_order_history(user)
                        actual = [item.get('product_id') for item in actual]
                else:
                    all_data = get_all_rating_data()
                    all_data = [{'y':item[0], 'x':item[1]} for item in all_data]
                    if EVALUATION_MODE==0:
                        actual = get_visit_relevant_item(user)
                    else:
                        actual = list(VisitProduct.objects.filter(user_id_id=user).values_list('product_id_id', flat=True))

                if actual:
                    target = [{'y':user,'x':item} for item in actual]
                    total = len(list(Product.objects.all()))
                    if 'recommended' in data and data.get('recommended'):
                        products = json.loads(data.get('recommended')) 
                        recommended = [item['id'] for item in products]
                        recommended_products = [{'y':user,'x':item['id']} for item in products]
                        tp = len(set(actual)&set(recommended))
                        fp = abs(len(recommended) - tp)
                        fn = abs(len(actual) - tp)
                        relevant = tp + fn
                        irrelevant = abs(total - len(actual))
                        tn = abs(irrelevant - fp)
                        current_user = User.objects.get(id=user)
                        score = {}
                        score['Method'] = 'Hybrid' if LIMIT_CONTENT_BASE > 1 else 'Collaborative'
                        score['Rule'] = 'Strict' if EVALUATION_MODE == 1 else 'Non-Strict'
                        score['Precission'] = round(tp/(tp+fp),4)
                        score['Recall'] = round(tp/(tp+fn),4)
                        score['Fallout'] = round(fp/(fp+tn),4)
                        score['Missrate'] = round(fn/(tp+fn),4)
                        score['F-one-score'] = round((2*score['Precission']*score['Recall'])/(score['Precission']+score['Recall']),4)
                        results['evaluation'] = score
                        results['user'] = {'id':user,'email':current_user.email}
                        results['data'] = {'tp':tp,
                                            'fn':fn,
                                            'tn':tn,
                                            'fp':fp,
                                            'total':total,
                                            'relevant':relevant,
                                            'irrelevant':irrelevant}
                        results['success'] = True
                        results['all_products'] = all_data
                        results['target'] = target
                        results['recommended_products'] = recommended_products
                        results['process_time'] = time.time() - start_time
                        return JsonResponse(results)
                    else:
                        result = {'success':False,'evaluation':None,'process_time':(time.time() -  start_time)}
                        return JsonResponse(result)
                else:
                    result = {'success':False,'evaluation':None,'process_time':(time.time() -  start_time)}
                    return JsonResponse(result)
            else:
                result = {'success':False,'evaluation':None,'process_time':(time.time() -  start_time)}
                return JsonResponse(result)
        else:
            result = {'success':False,'evaluation':None,'process_time':(time.time() -  start_time)}
            return JsonResponse(result)
    else:
        result = {'success':False,'evaluation':None,'process_time':(time.time() -  start_time)}
        return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)
        

def fake_user_data(data_input, distinct_user, distinct_product, fake_data):
    new_user =  int(np.max(distinct_user))
    new_distinct_user = distinct_user.append(new_user)
    new_data = np.vstack([data_input, fake_data])

    return new_data, new_distinct_user, distinct_product

def collaborative_similarity(array_input, users):
    list_similarity = []
    max_range = np.max(array_input)
    for i in range(0,users):
        row = []
        for j in range(0,users):
            if i == j:
                row.append(1.0)
            else:
                user_a = np.array(array_input[i])
                user_b = np.array(array_input[j])
                user_a[(user_a==0)|(user_b==0)] = 0
                user_b[(user_a==0)|(user_b==0)] = 0
                val = (max_range-abs(np.subtract(user_a,user_b)))/max_range
                val[(user_a==0)&(user_b==0)] = 0

                similarity = np.sum(val)/val.size
                row.append(similarity)
        list_similarity.append(row)
    return np.array(list_similarity)

def process_cross_section(array_input):
    start_convert = time.time() 
    np_array = np.array(array_input)
    xs = np_array[:,0]
    ys = np_array[:,1]
    zs = np_array[:,2]
    xs_val, xs_idx = np.unique(xs, return_inverse=True)
    ys_val, ys_idx = np.unique(ys, return_inverse=True)
    results_normal = np.zeros(xs_val.shape+ys_val.shape)
    results_normal.fill(0)
    results_normal[xs_idx,ys_idx] = zs
    results_binary = np.copy(results_normal)
    results_binary[results_binary>1] = 1
    print('done generating 2d matrix in %s'%(time.time() -  start_convert))
    return results_normal, results_binary, xs_val.tolist(), ys_val.tolist()

@csrf_exempt
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def update_product_rating(request):
    start_time = time.time()
    if request.method == 'POST':
        data = request.data
        if '_auth_user_id' in request.session and request.session['_auth_user_id'] and 'product_id' in data and data['product_id'] and 'value' in data and data['value']:
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
            value = data.get('value')
            try:
                defaults = {
                    'product_id' : product,
                    'user_id' : user,
                    'value' : value
                }

                rating, created = ProductRating.objects.get_or_create(product_id=product,user_id=user,defaults=defaults)
               
                if not created:
                    rating.value = value
                    rating.save()
                result = {'success':True,'message':'Successfully update rating!','process_time':(time.time() -  start_time)}
                return JsonResponse(result)
            except ProductRating.DoesNotExist:
                result = {'success':False,'message':'Something went wrong!','process_time':(time.time() -  start_time)}
                return JsonResponse(result)
        else:
            previous_page = data.get('previous_page')
            result = {'success':False,'message':'You must login first!','process_time':(time.time() -  start_time),'url':(settings.LOGIN_URL+'?next='+previous_page)}
            return JsonResponse(result)
    else:
        result = {'success':False,'message':'Something went wrong!','process_time':(time.time() -  start_time)}
        return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)