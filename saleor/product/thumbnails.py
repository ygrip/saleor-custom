from celery import shared_task

from ..core.utils import create_thumbnails
from .models import ProductImage


@shared_task
def create_product_thumbnails(image_id,verbose=False):
    """Takes ProductImage model, and creates thumbnails for it."""
    create_thumbnails(pk=image_id, model=ProductImage, size_set='products',verbose=verbose)
