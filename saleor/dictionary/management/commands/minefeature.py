from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ...utils.mine_feature import create_dictionary

class Command(BaseCommand):
	help = 'The command for executng text mining module'

	# def add_arguments(self,parser):
	# 	parser.add_argument(
	# 		'--createdictionary',
	# 		action='store_true',
	# 		dest='createdictionary',
	# 		default=False,
	# 		help='Create Dictionary for Text Mining')

	def handle(self, *args, **options):
		for msg in create_dictionary(self.dir_json):
			self.stdout.write(msg)
		