from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...product.models import Category, Brand
from ..views import staff_member_required
from .filters import BrandFilter
from .forms import BrandForm


@staff_member_required
@permission_required('product.view_brand')
def brand_list(request):
    brands = Brand.objects.all().order_by('brand_name')
    brand_filter = BrandFilter(request.GET, queryset=brands)
    brands = get_paginator_items(
        brand_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'brands': brands, 'filter_set': brand_filter,
        'is_empty': not brand_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/brand/list.html', ctx)


@staff_member_required
@permission_required('product.edit_brand')
def brand_create(request):
    path = None
    brand = Brand()
    
    form = BrandForm(
        request.POST or None, request.FILES or None)
    if form.is_valid():
        brand = form.save()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message', 'Added brand %s') % brand)
        
        return redirect('dashboard:brand-list')
    ctx = {'brand': brand, 'form': form, 'path': path}
    return TemplateResponse(request, 'dashboard/brand/form.html', ctx)


@staff_member_required
@permission_required('product.edit_brand')
def brand_edit(request, root_pk=None):
    path = None
    brand = []
    if root_pk:
        brand = get_object_or_404(Brand, pk=root_pk)
        path = brand
    form = BrandForm(
        request.POST or None, request.FILES or None, instance=brand)
    status = 200
    if form.is_valid():
        brand = form.save()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message', 'Updated brand %s') % brand)
        if root_pk:
            return redirect('dashboard:brand-details', pk=root_pk)
        return redirect('dashboard:brand-list')
    elif form.errors:
        status = 400
    ctx = {'brand': brand, 'form': form, 'status': status, 'path': brand}
    template = 'dashboard/brand/form.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
@permission_required('product.view_brand')
def brand_details(request, pk):
    root = get_object_or_404(Brand, pk=pk)
    path = root
    brands = Brand.objects.filter(id=pk).order_by('name')
    brand_filter = BrandFilter(request.GET, queryset=brands)
    brands = get_paginator_items(
        brand_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {'brands': brands, 'path': path, 'root': root,
           'filter_set': brand_filter,
           'is_empty': not brand_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/brand/detail.html', ctx)


@staff_member_required
@permission_required('product.edit_brand')
def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        brand.delete()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message', 'Removed brand %s') % brand)
        
        if request.is_ajax():
            response = {'redirectUrl': reverse('dashboard:brand-list')}
            return JsonResponse(response)
        return redirect('dashboard:category-list')
    ctx = {'brand': brand,
           'products_count': len(brand.products.all())}
    return TemplateResponse(
        request, 'dashboard/brand/modal/confirm_delete.html', ctx)
