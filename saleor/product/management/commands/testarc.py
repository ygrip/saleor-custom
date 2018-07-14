from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
import numpy as np
from ...views import process_cross_section, collaborative_similarity

class Command(BaseCommand):
	help = 'Create Dictionary for text mining'

	# def add_arguments(self,parser):
	# 	parser.add_argument(
	# 		'--createdictionary',
	# 		action='store_true',
	# 		dest='createdictionary',
	# 		default=False,
	# 		help='Create Dictionary for Text Mining')

	def handle(self, *args, **options):
		data_input = [
						[1,1,0],
						[1,2,3],
						[1,3,0],
						[1,4,4],
						[2,1,0],
						[2,2,2],
						[2,3,3],
						[2,4,5],
						[3,1,4],
						[3,2,0],
						[3,3,3],
						[3,4,0],
					]

		cross_section, binary_cross_section, distinct_user, distinct_product = process_cross_section(data_input)
		print('data input : ')
		print(cross_section)
		print('data biner : ')
		print(binary_cross_section)

		user_similarity = collaborative_similarity(cross_section, len(distinct_user))
		print('matrix similarity : ')
		print(user_similarity)

		result_matrix = []
		limit = 7
		order = 1
		while True:
			if result_matrix:
				if order >= int(limit):
					break
			if order == 1:
				final_weight = cross_section
				result_matrix.append(final_weight)
			else:
				check = result_matrix[-1]
				final_weight = np.dot((np.dot(binary_cross_section,binary_cross_section.T))*(user_similarity),check)
				result_matrix.append(final_weight)
			order += 2

		print('last ordinality : %s'%order)

		o = 1
		for i,result in enumerate(result_matrix):
			
			print('ordinality ke %s :'%o)
			print(result)
			o += 2

		