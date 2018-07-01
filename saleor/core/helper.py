import collections
import threading
from django.db.models import Count
from threading import Thread
from ..product.models import Product, Category, Brand
from ..product.helper import get_descendant

from django.db import connection,transaction

def create_navbar_tree(request):
    global results_brand
    global results_category
    results_brand = []
    results_category = []
    brand = list(Brand.objects.all().order_by('brand_name'))
    category = list(Category.objects.all().order_by('name'))
    categories = []
    for item in category:
        elements = {}
        elements['id'] = item.id
        elements['url'] = item.get_absolute_url()
        elements['name'] = item.name
        categories.append(elements)
    results = {}
    Thread(target = query_brand(brand)).start()
    Thread(target = query_category(categories)).start()
    results['categories'] = results_category
    results['brands'] = results_brand
    return results

results_brand = []
results_category = []
def query_brand(brands):
    temp = collections.defaultdict(list)
    all_count = list(Product.objects.all().values('brand_id_id').annotate(total=Count('brand_id_id')).order_by('total'))
    for item in brands:
        elements = {}
        elements['children'] = None
        elements['url'] = item.get_absolute_url()
        elements['name'] = item.brand_name
        elements['count'] = list(filter(lambda e: e.get('brand_id_id') == item.id, all_count))[0]['total']

        first_char = str(item.brand_name[:1])
        key = '#'+first_char.upper()

        temp[key].append(elements)

    global results_brand
    for key in temp:
        elements = {}
        elements['name'] = key
        elements['url'] = None
        elements['count'] = None
        elements['children'] = temp[str(key)]
        results_brand.append(elements)

def query_category(categories):
    global results_category
    temp = category_tree()

    all_count = list(Product.objects.all().values('category_id').annotate(total=Count('category_id')).order_by('total'))
    for item in temp:
        elements = {}
        if temp[str(item)]:
            total = 0
            current_node = list(filter(lambda e: e['id'] == int(item), categories))[0]
            elements['name'] = current_node['name']
            elements['url'] = current_node['url']
            children = []

            for child in temp[str(item)]:
                if str(child) not in list(filter(lambda e: temp[e], temp.keys())):
                    child_element = {}
                    child_node = list(filter(lambda e: e['id'] == int(child), categories))[0]
                    child_element['name'] = child_node['name']
                    child_element['url'] = child_node['url']
                    child_element['count'] = list(filter(lambda e: e.get('category_id') == int(child), all_count))[0]['total']
                    child_element['children'] = None
                    total += child_element['count']
                    children.append(child_element)
            elements['count'] = total
            elements['children'] = children
            results_category.append(elements)

def category_tree():
    cursor = connection.cursor()
    results = collections.defaultdict(list)
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
            SELECT DISTINCT parent_id AS id, descendant AS child
            FROM descendants WHERE parent_id IS NOT NULL
            ORDER BY id, child
            """
    cursor.execute(query)
    row = [{'id':item[0], 'child':item[1]} for item in cursor.fetchall()]

    for item in row:
        results[str(item.get('id'))].append(item.get('child'))

    return results
