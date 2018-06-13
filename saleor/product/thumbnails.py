from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

from ..core.utils import create_thumbnails
from .models import ProductImage


@shared_task
def create_product_thumbnails(image_id,verbose=False):
    """Takes ProductImage model, and creates thumbnails for it."""
    create_thumbnails(pk=image_id, model=ProductImage, size_set='products',verbose=verbose)
    logger.info('creating image thumbnails')
