import datetime
import json

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
from .models import Category, Collection, ProductRating, Brand, Product
from .utils import (
    get_product_images, get_product_list_context, handle_cart_form,
    products_for_cart, products_with_details)
from .utils.attributes import get_product_attributes_data
from .utils.availability import get_availability
from ..search.views import render_item, paginate_results
from .utils.variants_picker import get_variant_picker_data
from ..core.helper import create_navbar_tree
from .helper import get_filter_values, get_descendant
from django.db.models import Avg
from joblib import (Parallel, delayed)
import psutil
from django_mako_plus import view_function, render_template

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
    if product_features:
        tags = Feature.objects.filter(id__in=product_features)
    return TemplateResponse(
        request, 'product/details.html', {
            'is_visible': is_visible,
            'menu_tree' : create_navbar_tree(request),
            'form': form,
            'availability': availability,
            'rating' : rating,
            'tags' : tags,
            'brand' : brand,
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

@view_function
def tags_index(request, path, tag_id):
    request_page = int(request.GET.get('page','')) if request.GET.get('page','') else 1
    tag = get_object_or_404(Feature, id=tag_id)
    actual_path = tag.get_full_path()
    if actual_path != path:
        return redirect('product:tags', permanent=True, path=actual_path,
                        tag_id=tag_id)
    ctx = {
        'query': tag,
        'menu_tree' : create_navbar_tree(request),
        'query_string': '?page='+ str(request_page)
        }
    request.session['tag_query'] = tag_id
    request.session['tag_page'] = request_page
    response = TemplateResponse(request, 'tag/index.html', ctx)
    return response

@view_function
def tags_render(request):
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
                backend="threading")(delayed(render_item)(item,request.discounts,request.currency) for item in products)
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
