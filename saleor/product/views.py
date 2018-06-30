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
from .filters import ProductCategoryFilter, ProductBrandFilter, ProductCollectionFilter
from .models import Category, Collection, ProductRating, Brand, Product
from .utils import (
    get_product_images, get_product_list_context, handle_cart_form,
    products_for_cart, products_with_details)
from .utils.attributes import get_product_attributes_data
from .utils.availability import get_availability
from .utils.variants_picker import get_variant_picker_data
from ..core.helper import create_navbar_tree
from .helper import get_filter_values, get_descendant
from django.db.models import Avg

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
    return TemplateResponse(
        request, 'product/details.html', {
            'is_visible': is_visible,
            'menu_tree' : create_navbar_tree(request),
            'form': form,
            'availability': availability,
            'rating' : rating,
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
