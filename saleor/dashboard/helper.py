from django.db import connection,transaction
from ..product.models import Category

def get_descendant(parent_id,with_self=False):
    cursor = connection.cursor()
    descendants = []
    if with_self:
        descendants.append(int(parent_id))
    query = """
            WITH RECURSIVE
            descendants AS (
                SELECT parent_id,id AS descendant, 1 AS level
                FROM product_category
                UNION ALL
                SELECT d.parent_id, cat.id, d.level + 1
                FROM descendants AS d
                JOIN product_category cat ON cat.parent_id = d.descendant
            )
            SELECT DISTINCT descendant AS id
            FROM descendants
            WHERE parent_id = """+str(parent_id)+"""
            ORDER BY id
            """
    cursor.execute(query)
    row = [item[0] for item in cursor.fetchall()]
    for d in row:
        descendants.append(d)
    cursor.close()
    return Category.objects.filter(id__in=descendants)