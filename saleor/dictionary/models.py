from django.db import models

# Create your models here.
class WordList(models.Model):
	katadasar=models.TextField()
	tipe_katadasar=models.TextField()

class Stopwords(models.Model):
	kata=models.TextField()
		