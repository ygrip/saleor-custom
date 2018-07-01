from django.db import models
from ..product.models import Product
from django.core.validators import MinValueValidator, RegexValidator
from django.urls import reverse
from django.utils.encoding import smart_text
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from text_unidecode import unidecode

# Create your models here.
class Feature(models.Model):
	word=models.TextField(unique=True)
	count=models.IntegerField(
        validators=[MinValueValidator(0)], default=1)

	def __str__(self):
		return self.word

	def get_full_path(self):
		return slugify(smart_text(unidecode(self.word)))

	def get_absolute_url(self):
		return reverse('product:tags',
					kwargs={'path': slugify(smart_text(unidecode(self.word))),
					'tag_id': self.id})

class ProductFeature(models.Model):
	product_id=models.ForeignKey(Product, related_name='feature', on_delete=models.CASCADE)
	feature_id=models.ForeignKey(Feature, on_delete=models.CASCADE)
	frequency = models.FloatField(default=0.0)

class CleanProductDetails(models.Model):
	product_id=models.ForeignKey(Product, related_name='cleandetails', on_delete=models.CASCADE)
	details=models.TextField()
