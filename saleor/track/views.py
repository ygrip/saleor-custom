from django.shortcuts import render
from django.db import connection,transaction
# Create your views here.

def insert_search_history(raw_query, clean_query, user_id=None):
	cursor = connection.cursor()
	if user_id:
		query = """
				INSERT INTO track_searchhistory(id, user_id_id, modulo, clean_query, raw_query, search_at)
				SELECT
			      (COALESCE(MAX(t.id), -1) + 1),
				  ("""+str(user_id)+""")::int,
			      ((COALESCE(MAX(t.id), -1) + 1)%10)+(("""+str(user_id)+""")::int*10),
			      """+clean_query+""",
				  """+raw_query+""",
				  NOW()
				FROM track_searchhistory t
			      ON CONFLICT (modulo) DO UPDATE 
				  SET
			         id    = excluded.id,
			         user_id_id = excluded.user_id_id,         
					 raw_query = excluded.raw_query,
					 clean_query = excluded.clean_query,
					 search_at = NOW();
			 	"""
	cursor.execute(query)
	cursor.close()
	transaction.commit()