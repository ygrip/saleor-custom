
from django.db import connection,transaction

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

    return descendants

def get_filter_values(categories, filter_field):
    cursor = connection.cursor()
    category = "("
    keys = "("
    for i,cat in enumerate(categories):
        category += str(cat)
        if i < (len(categories)-1):
            category += ","
        else:
            category += ")"
    for i,key in enumerate(filter_field):
        keys += "'"+str(key)+"'"
        if i < (len(filter_field)-1):
            keys += ","
        else:
            keys += ")"
    query = """
            WITH
            values AS(
                SELECT CAST(nullif(skeys(attributes),'') AS integer) AS key,
                CAST(nullif(svals(attributes),'') AS integer) AS id 
                FROM product_product 
                WHERE category_id IN """+category+"""
            )
            SELECT DISTINCT values.id AS id FROM values JOIN (
                SELECT id 
                FROM product_productattribute 
                WHERE name IN """+keys+"""
                ORDER BY id
            ) AS index ON index.id = values.key
            ORDER by values.id
            """
    cursor.execute(query)
    return [item[0] for item in cursor.fetchall()]