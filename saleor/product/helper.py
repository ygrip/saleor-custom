
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

def get_all_rating_data():
    query = """
            SELECT user_id_id, product_id_id
            FROM product_productrating;
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [a[:] for a in cursor.fetchall()]
    cursor.close()
    return results

def get_all_order_data():
    query = """
            SELECT DISTINCT o.user_id, p.id
            FROM order_order o, order_orderline l, product_product p, product_productvariant v
            WHERE l.order_id = o.id AND l.variant_id = v.id AND v.product_id = p.id;
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [a[:] for a in cursor.fetchall()]
    cursor.close()
    return results

def get_cross_section_rating(limit=1.0):
    query = """
            WITH
            rating AS(
                SELECT value, updated_at, user_id_id AS uid, product_id_id AS pid
                FROM product_productrating
                ORDER BY updated_at DESC LIMIT (SELECT (COUNT(*)*(%s)::float)::integer FROM product_productrating)
            ),
            tmp AS(
                SELECT a.id AS userid, b.id AS pid, COALESCE(c.value,0) AS value
                FROM account_user a CROSS JOIN product_product b LEFT JOIN rating c
                ON c.uid = a.id AND c.pid = b.id
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
                SELECT a.id AS userid, b.id AS pid, COALESCE(c.value,0) AS value
                FROM account_user a CROSS JOIN product_product b LEFT JOIN orders c
                ON c.uid = a.id AND c.pid = b.id
            )
            SELECT * FROM tmp;
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

def get_all_user_order_history():
    query = """
            SELECT o.user_id AS uid, p.id AS pid, SUM(d.quantity) AS value
            FROM order_order o, order_orderline d, product_product p, product_productvariant v
            WHERE o.id = d.order_id AND v.id = d.variant_id AND v.product_id = p.id
            GROUP BY uid, pid
            ORDER BY uid
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [{'user_id':a[0],'product_id':a[1],'value':a[2]} for a in cursor.fetchall()]
    cursor.close()
    return results

def get_user_order_history(user):
    query = """
            SELECT o.user_id AS uid, p.id AS pid, SUM(d.quantity) AS value
            FROM order_order o, order_orderline d, product_product p, product_productvariant v
            WHERE o.id = d.order_id AND v.id = d.variant_id AND v.product_id = p.id
            AND o.user_id ="""+str(user)+"""
            GROUP BY uid, pid
            ORDER BY uid
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [{'product_id':a[1],'value':a[2]} for a in cursor.fetchall()]
    cursor.close()
    return results

def get_product_order_history():
    query = """
            SELECT p.id AS id, SUM(o.quantity) AS value
            FROM product_product p, product_productvariant v, order_orderline o
            WHERE v.product_id = p.id AND o.variant_id = v.id
            GROUP BY p.id
            ORDER BY value DESC
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [{'product_id':a[0],'value':a[1]} for a in cursor.fetchall()]
    cursor.close()
    return results

def get_product_rating_history():
    query = """
            SELECT p.id AS id, AVG(r.value) AS value
            FROM product_product p, product_productrating r
            WHERE r.product_id_id = p.id
            GROUP BY p.id
            ORDER BY value DESC
            """
    cursor = connection.cursor()
    cursor.execute(query)
    results = [{'product_id':a[0],'value':a[1]} for a in cursor.fetchall()]
    cursor.close()
    return results

def get_rating_relevant_item(user, limit=5):
    query = """
            WITH
            top_rated AS(
                SELECT p.category_id AS cid, r.user_id_id AS uid, AVG(value) AS value
                FROM product_productrating r, product_product p
                WHERE r.product_id_id = p.id
                GROUP BY r.user_id_id, p.category_id
                ORDER BY value DESC
            )

            SELECT DISTINCT p.id AS id
            FROM product_product p, (SELECT cid 
                                    FROM top_rated 
                                    WHERE uid = (%s)::integer
                                    LIMIT (%s)::integer) c
            WHERE p.category_id = c.cid;
            """ %(user,limit)
    cursor = connection.cursor()
    cursor.execute(query)
    results = [a[0] for a in cursor.fetchall()]
    cursor.close()
    return results

def get_order_relevant_item(user, limit=5):
    query = """
            WITH
            top_ordered AS(
                SELECT p.category_id AS cid, o.user_id AS uid, SUM(l.quantity) AS value
                FROM order_order o, order_orderline l, product_product p, product_productvariant v
                WHERE l.order_id = o.id AND l.variant_id = v.id AND v.product_id = p.id
                GROUP BY o.user_id, p.category_id
                ORDER BY value DESC
            )

            SELECT DISTINCT p.id AS id
            FROM product_product p, (SELECT cid 
                                    FROM top_ordered 
                                    WHERE uid = (%s)::integer
                                    LIMIT (%s)::integer) c
            WHERE p.category_id = c.cid;
            """ %(user,limit)
    cursor = connection.cursor()
    cursor.execute(query)
    results = [a[0] for a in cursor.fetchall()]
    cursor.close()
    return results

def get_visit_relevant_item(user, limit=5):
    query = """
            WITH
            top_visited AS(
            SELECT p.category_id AS cid, v.user_id_id AS uid, SUM(v.count) AS value
            FROM track_visitproduct v, product_product p
            WHERE v.product_id_id = p.id
            GROUP BY v.user_id_id, p.category_id
            ORDER BY value DESC
            )

            SELECT DISTINCT p.id AS id
            FROM product_product p, (SELECT cid 
                            FROM top_visited 
                            WHERE uid = (%s)::integer
                            LIMIT (%s)::integer) c
            WHERE p.category_id = c.cid;
            """ %(user,limit)
    cursor = connection.cursor()
    cursor.execute(query)
    results = [a[0] for a in cursor.fetchall()]
    cursor.close()
    return results