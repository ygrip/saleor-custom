from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from ...utils.data import create_product


class Command(BaseCommand):
	help = 'Create Products from www.blibli.com'
	dir_json = r'saleor/static/json/products/'
	placeholders_dir = r'saleor/static/placeholders/'

	def handle(self, *args, **options):
		for msg in create_custom_product(self.dir_json,self.placeholders_dir):
			self.stdout.write(msg)