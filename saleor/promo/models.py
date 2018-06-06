from django.db import models

# Create your models here.
class Promo(models.Model):
	image=models.TextField()
	url=models.TextField()
	is_featured=models.BooleanField(default=False)
	created_at = models.DateField()

class Messages(models.Model):
	promo_id=models.ForeignKey(Promo, related_name='messages', on_delete=models.CASCADE)
	title = models.TextField()
	message=models.TextField()
	position = models.TextField()
	show = models.TextField()
	horizontal = models.TextField()
	vertical = models.TextField()
	is_round=models.BooleanField(default=False)