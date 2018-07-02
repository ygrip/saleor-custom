import json
import time
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from impersonate.views import impersonate as orig_impersonate
from django.conf import settings
from django.core import serializers
from ..account.models import User
from django.shortcuts import render
from ..dashboard.views import staff_member_required
from ..product.utils import products_for_homepage, top_purchased_product
from ..promo.utils import promo_for_homepage
from ..product.utils.availability import products_with_availability
from ..seo.schema.webpage import get_webpage_schema
from .helper import create_navbar_tree

def home(request):
    start_time = time.time()
    products = list(top_purchased_product(8))
    promo = promo_for_homepage()
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    webpage_schema = get_webpage_schema(request)
    print("\nWaktu eksekusi : --- %s detik ---" % (time.time() - start_time))
    return TemplateResponse(
        request, 'home.html', {
            'parent': None,
            'products': products,
            'product_promos' : promo,
            'product_promos_schema' : json.dumps(promo,indent=4,sort_keys=True,default=str),
            'webpage_schema': json.dumps(webpage_schema)})

def render_menu(request):
    start_time = time.time()
    print('sedang render')
    menu_tree = create_navbar_tree(request)
    print("\nWaktu eksekusi : --- %s detik ---" % (time.time() - start_time))
    return render(request, 'top_menu.html', {
            'site_menu':menu_tree,
            'horizontal': True,
        })

@staff_member_required
def styleguide(request):
    return TemplateResponse(request, 'styleguide.html')


def impersonate(request, uid):
    response = orig_impersonate(request, uid)
    if request.session.modified:
        msg = pgettext_lazy(
            'Impersonation message',
            'You are now logged as {}'.format(User.objects.get(pk=uid)))
        messages.success(request, msg)
    return response


def handle_404(request, exception=None):
    return TemplateResponse(request, '404.html', status=404)


def manifest(request):
    return TemplateResponse(
        request, 'manifest.json', content_type='application/json')
