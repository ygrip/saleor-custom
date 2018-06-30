import json

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from impersonate.views import impersonate as orig_impersonate
from django.conf import settings
from django.core import serializers
from django_mako_plus import view_function, render_template
from ..account.models import User

from ..dashboard.views import staff_member_required
from ..product.utils import products_for_homepage, top_purchased_product
from ..promo.utils import promo_for_homepage
from ..product.utils.availability import products_with_availability
from ..seo.schema.webpage import get_webpage_schema
from .helper import create_navbar_tree

@view_function
def home(request):
    products = list(top_purchased_product(8))
    promo = promo_for_homepage()
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    webpage_schema = get_webpage_schema(request)
    menu_tree = create_navbar_tree(request)
    print([item['name'] for item in menu_tree.get('categories')])
    return TemplateResponse(
        request, 'home.html', {
            'parent': None,
            'products': products,
            'product_promos' : promo,
            'menu_tree' : menu_tree,
            'product_promos_schema' : json.dumps(promo,indent=4,sort_keys=True,default=str),
            'webpage_schema': json.dumps(webpage_schema)})

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
