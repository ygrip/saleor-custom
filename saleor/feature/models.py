from django.db import models
from ..product.models import Product
from django.core.validators import MinValueValidator, RegexValidator

# Create your models here.
class Feature(models.Model):
	word=models.TextField(unique=True)
	count=models.IntegerField(
        validators=[MinValueValidator(0)], default=1)

class ProductFeature(models.Model):
	product_id=models.ForeignKey(Product, related_name='feature', on_delete=models.CASCADE)
	feature_id=models.ForeignKey(Feature, on_delete=models.CASCADE)
	frequency = models.FloatField(default=0.0)

class CleanProductDetails(models.Model):
	product_id=models.ForeignKey(Product, related_name='cleandetails', on_delete=models.CASCADE)
	details=models.TextField()
