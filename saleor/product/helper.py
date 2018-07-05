
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
    cursor.close()
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
    results = [item[0] for item in cursor.fetchall()]
    cursor.close()
    return results

def get_list_user_from_rating():
    query = """
            WITH
            users AS(
                SELECT DISTINCT u.id AS user_id
                FROM account_user u, product_productrating r
                WHERE r.user_id_id = u.id
                ORDER BY user_id
            )
            SELECT * FROM users;
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [a[0] for a in cursor.fetchall()]
    cursor.close()
    return results

def get_list_product_from_rating():
    query = """
            WITH
            products AS(
                SELECT DISTINCT p.id AS product_id
                FROM product_product p, product_productrating r
                WHERE r.product_id_id = p.id
                ORDER BY product_id
            )
            SELECT * FROM products;
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [a[0] for a in cursor.fetchall()]
    cursor.close()
    return results

def get_list_user_from_order():
    query = """
            WITH
            users AS(
                SELECT DISTINCT u.id AS user_id
                FROM account_user u, order_order o
                WHERE u.id = o.user_id 
                ORDER BY user_id
            )
            SELECT * FROM users;
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [a[0] for a in cursor.fetchall()]
    cursor.close()
    return results

def get_list_product_from_order():
    query = """
            WITH
            products AS(
                SELECT DISTINCT p.id AS pid
                FROM product_product p, order_orderline o, product_productvariant v
                WHERE o.variant_id = v.id AND p.id = v.product_id
            )
            SELECT * FROM products;
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [a[0] for a in cursor.fetchall()]
    cursor.close()
    return results

def get_cross_section_rating(limit=1.0):
    query = """
            WITH
            users AS(
                SELECT DISTINCT u.id AS user_id
                FROM account_user u, product_productrating r
                WHERE r.user_id_id = u.id
                ORDER BY user_id
            ),
            products AS(
                SELECT DISTINCT p.id AS product_id
                FROM product_product p, product_productrating r
                WHERE r.product_id_id = p.id
                ORDER BY product_id
            ),
            rating AS(
                SELECT value, updated_at, user_id_id, product_id_id
                FROM product_productrating
                ORDER BY updated_at DESC LIMIT (SELECT (COUNT(*)*(%s)::float)::integer FROM product_productrating)
            ),
            tmp AS(
                SELECT a.user_id AS userid, b.product_id AS pid, COALESCE(c.value,0) AS value
                FROM users a CROSS JOIN products b LEFT JOIN rating c
                ON c.user_id_id = a.user_id AND c.product_id_id = b.product_id
            )
            SELECT * FROM tmp;
            """ % limit
    cursor = connection.cursor()
    cursor.execute(query)
    cross_section = [a[:] for a in cursor.fetchall()]
    cursor.close()
    return cross_section

def get_cross_section_order(limit=1.0):
    query = """
            WITH
            users AS(
                SELECT DISTINCT u.id AS user_id
                FROM account_user u, order_order o
                WHERE u.id = o.user_id 
                ORDER BY user_id
            ),
            products AS(
                SELECT DISTINCT p.id AS pid
                FROM product_product p, order_orderline o, product_productvariant v
                WHERE o.variant_id = v.id AND p.id = v.product_id
            ),
            temp_order AS(
                SELECT * FROM order_order
                ORDER BY created DESC LIMIT (SELECT (COUNT(*)*(%s)::float)::integer FROM order_order)
            ),
            orders AS(
                SELECT p.id AS pid, tor.user_id AS uid,  SUM(o.quantity) AS value
                FROM product_product p, product_productvariant v, order_orderline o, temp_order tor
                WHERE v.product_id = p.id AND o.variant_id = v.id AND tor.id = o.order_id
                GROUP BY p.id, tor.user_id
                ORDER BY value DESC
            ),
            tmp AS(
                SELECT a.user_id AS userid, b.pid AS pid, COALESCE(c.value,0) AS value
                FROM users a CROSS JOIN products b LEFT JOIN orders c
                ON c.uid = a.user_id AND c.pid = b.pid
            )
            SELECT * FROM tmp ORDER BY userid, value DESC;
            """ %limit

    cursor = connection.cursor()
    cursor.execute(query)
    cross_section = [a[:] for a in cursor.fetchall()]
    cursor.close()
    return cross_section

def get_all_user_rating(user):
    query = """
            SELECT product_id_id AS product_id, value AS value
            FROM product_productrating
            WHERE user_id_id = """+str(user)+"""
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [{'product_id':a[0],'value':a[1]} for a in cursor.fetchall()]
    cursor.close()
    return results