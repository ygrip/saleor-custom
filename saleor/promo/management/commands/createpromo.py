from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ...utils.data import create_promo

class Command(BaseCommand):
	help = 'Create Promo for text mining'

	def handle(self, *args, **options):
		for msg in create_promo():
			self.stdout.write(msg)