import glob, os
import requests
import json
import random
from pprint import pprint
from urllib.parse import urlparse
import re
import base64

from django.conf import settings
from django.db import connection,transaction
import unicodedata

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.core.files import File
from django.template.defaultfilters import slugify
from faker import Factory
from faker.providers import BaseProvider
from payments import PaymentStatus
from prices import Money, TaxedMoney

from ...account.models import Address, User
from ...account.utils import store_user_address
from ...core.utils.text import strip_html_and_truncate
from ...discount import DiscountValueType, VoucherType
from ...discount.models import Sale, Voucher
from ...menu.models import Menu
from ...order.models import Fulfillment, Order, Payment
from ...order.utils import update_order_status
from ...page.models import Page
from ...feature.models import (Feature,ProductFeature)
from ...product.models import (
    AttributeChoiceValue, Category, Collection, Product, ProductAttribute,
    ProductImage, ProductType, ProductVariant, Brand, MerchantLocation, ProductRating)
from ...product.thumbnails import create_product_thumbnails
from ...product.utils.attributes import get_name_from_attributes
from ...shipping.models import ANY_COUNTRY, ShippingMethod
from ...dictionary.utils.mine_feature import populate_feature

PRODUCTS_LIST_DIR = 'products-list/'
DELIVERY_REGIONS = [ANY_COUNTRY, 'ID', 'AUS', 'SG', 'MLY']
cwd = os.getcwd()  # Get the current working directory (cwd)
fake = Factory.create()

current = 0

def make_database_faster():
	if 'sqlite3' in connection.settings_dict['ENGINE']:
		cursor = connection.cursor()
		cursor.execute('PRAGMA temp_store = MEMORY;')
		cursor.execute('PRAGMA synchronous = OFF;')

def create_custom_product(dir_json,placeholders_dir):
	make_database_faster()
	cursor = connection.cursor()
	yield 'Populating Product Files : '
	os.chdir(dir_json)

	try:
		check_product = Product.objects.all().last()
		if not check_product:
			check_product = None
	except Product.DoesNotExist:
		check_product = None
	total = 0

	for filename in glob.glob("*.json"):
		product_type_name = ' '.join(map(lambda e: e.capitalize(), 
								os.path.splitext(os.path.basename(filename))[0].replace('produk-','').split('-')))
		yield 'Processing product type : %s' % product_type_name
		content = json.load(open(filename))
		os.chdir(cwd)
		for element in content:

			total += 1
			status = True
			if check_product is not None:
				if total <= check_product.id:
					status = False
			else:
				status = True

			if not status:
				continue
			else:
				product_type = create_product_type_with_attributes(product_type_name,
								element.get('produk_specification',{}))
				brand = create_brand(placeholders_dir,brand_data={
									'name':element.get('brand'),
									'image':element.get('brand_image'),
									'url':element.get('brand_link'),
									})
				product_category = create_category(element.get('category',{}),placeholders_dir)
				title = element.get('title')
				description = element.get('produk_description')
				service = json.dumps(element.get('produk_services'))
				features = json.dumps(element.get('produk_features'))
				check_price = element.get('harga')
				sku = element.get('produk_code').get('SKU Number')
				price = int(check_price.get('Harga Awal')) if 'Harga Awal' in check_price else int(check_price.get('Harga'))
				location = create_merchant_location(element.get('merchant_location'))
				product = create_product(name=title,
										product_type=product_type,
										category=product_category,
										information=features,
										price=price,
										brand_id=brand,
										description=description,
										service=service,
										location=location,
										seo_description=strip_html_and_truncate(description, 300),
										)

				sentence = title+' '+element.get('brand')+' '+description+' '+(' '.join(element.get('produk_features')))+' '
				sentence += ' '.join(map(lambda e: element.get('produk_specification').get(e), element.get('produk_specification')))+' '
				sentence += ' '.join(element.get('category'))+' '
				sentence += product_type_name+' '
				if location:
					sentence += element.get('merchant_location')+' '

				yield '%s' % sentence

				product_tags = populate_feature(sentence=sentence,treshold=2)[:6]

				for tag in product_tags:
					feature, created = Feature.objects.get_or_create(word=tag['word'], defaults={'count':1})

					product_tag, created_tag = ProductFeature.objects.get_or_create(feature_id=feature,
									product_id=product,
									defaults={'frequency':tag['count']})

					if not created and created_tag:
						feature.count = feature.count + 1
						feature.save()

				set_product_attributes(product, product_type)
				create_variant(product=product, price=price, sku=sku)
				yield '\n\n\t---(%s)---\nID\t\t: %s \nProduct Name\t: %s\n' % (
					product_type.name, product.id, product)
				yield 'Feature\t: %s' % json.dumps(product_tags)

				create_product_image(product,element.get('url_images'),placeholders_dir)
				
				if 'Diskon' in check_price:
					create_sale(product,float(check_price.get('Diskon')))

				shipping = element.get('shipping_option')
				if shipping:
					if 'name' in shipping:
						create_shipping_method(shipping)

				current = product.id
		
		os.chdir(dir_json)
	yield 'Saved %s item(s) from total of %s' % (current,total)

def create_product(name,**kwargs):
    defaults = {
    	'name' : name,
    }
    defaults.update(kwargs)
    return Product.objects.get_or_create(name=name,defaults=defaults)[0]

def create_merchant_location(location):
	if not location:
		return None
	else:
		defaults = {
			'location' : location
		}
		return MerchantLocation.objects.get_or_create(location=location,defaults=defaults)[0]

def create_shipping_method(shipping, **kwargs):
	options = []
	defaults = {
		'name' : shipping['name'],
	}
	defaults.update(kwargs)
	ship,created = ShippingMethod.objects.get_or_create(name=shipping['name'],defaults=defaults)

	if created:
		defaults = {
			'price' : shipping['price'],
		}
		ship.price_per_country.get_or_create(price=shipping['price'],defaults=defaults)[0]
	options.append(ship)
	return options[-1]

def create_brand(placeholders_dir,brand_data, **kwargs):
	image_url = brand_data['image']
	directory = os.path.join(placeholders_dir,'brands/')
	if not os.path.exists(directory):
		os.makedirs(directory)
	extension = os.path.splitext(urlparse(image_url).path)[-1]
	filename = brand_data['name']+extension
	
	filepath = os.path.join(directory,filename)
	if os.path.exists(filepath):
		brand_image = get_image(directory,filename)
	else:
		try:
			image = requests.get(image_url)
			
			if image.status_code == requests.codes.ok:
				with open(filepath, 'wb') as f:
					f.write(image.content)
				brand_image = get_image(directory,filename)
				
			else:
				brand_image = None
		except requests.exceptions.InvalidSchema as e:
			image = base64.b64decode(image_url.partition('base64,')[2])
			filename = brand_data['name']+'.png'
			
			filepath = os.path.join(directory,filename)
			with open(filepath, 'wb') as f:
				f.write(image)
			brand_image = get_image(directory,filename)

	defaults = {
		'brand_name' : brand_data['name'],
		'brand_link' : brand_data['url']
	}

	defaults.update(kwargs)
	brand,created = Brand.objects.get_or_create(brand_name=brand_data['name'],defaults=defaults)
	if created:
		if brand_image:
			brand.brand_image = brand_image
			brand.save()
	return brand
	
def create_attributes_and_values(attribute_data):
    attributes = []
    for attribute_name, attribute_value in attribute_data.items():
        attribute = create_attribute(
            slug=slugify(attribute_name), name=attribute_name)
        attribute_values = []
        attribute_values.append(attribute_value)
        for value in attribute_values:
            create_attribute_value(attribute, value=value)
        attributes.append(attribute)
    return attributes

def create_attribute(name,**kwargs):
    defaults = {
        'slug': slugify(name),
        'name': name}
    defaults.update(kwargs)
    attribute = ProductAttribute.objects.get_or_create(**defaults)[0]
    return attribute


def create_attribute_value(attribute, value, **kwargs):
    defaults = {
        'attribute': attribute,
        'name': value}
    defaults.update(kwargs)
    defaults['slug'] = slugify(defaults['name'])
    attribute_value = AttributeChoiceValue.objects.get_or_create(**defaults)[0]
    return attribute_value

def get_product_list_images_dir(placeholder_dir):
    product_list_images_dir = os.path.join(placeholder_dir, PRODUCTS_LIST_DIR)
    return product_list_images_dir


def get_image(image_dir, image_name):
    img_path = os.path.join(image_dir, image_name)
    return File(open(img_path, 'rb'))

def create_category(category_data,placeholder_dir):
	result = []
	for i,category in enumerate(category_data):
		defaults = {
			'name' : category,
		}
		saved_category = Category.objects.get_or_create(name=category,defaults=defaults)[0]
		if i == 0:
			product_category = save_category({'name':saved_category.name,
				'image_name':str(saved_category.id)+'.jpg'},
				placeholder_dir)
			result.append(product_category)
		else:
			defaults = {
				'name' : category_data[i-1],
			}
			parent = Category.objects.get_or_create(name=category_data[i-1],defaults=defaults)[0]
			product_category = save_category({'name':saved_category.name,
				'image_name':str(saved_category.id)+'.jpg',
				'parent':parent.id},
				placeholder_dir)
			result.append(product_category)
	return result[-1]

def save_category(category_schema, placeholder_dir):
    if 'parent' in category_schema:
        parent_id = category_schema['parent']
    else:
        parent_id = None
    category_name = category_schema['name']
    image_name = category_schema['image_name']
    image_dir = get_product_list_images_dir(placeholder_dir)

    category_image = get_image(image_dir, image_name)
    defaults = {
        'description': fake.text(),
        'parent_id':parent_id,
        'slug': slugify(category_name),
        }
    category,created = Category.objects.update_or_create(
        name=category_name, defaults=defaults)

    if created:
    	category.background_image = category_image
    	category.save()
    else:
    	if not category.background_image:
    		category.background_image = category_image
    		category.save()

    return category

def get_or_create_product_type(name, **kwargs):
    return ProductType.objects.get_or_create(name=name, defaults=kwargs)[0]

def set_product_attributes(product, product_type):
    attr_dict = {}
    for product_attribute in product_type.product_attributes.all():
        value = random.choice(product_attribute.values.all())
        attr_dict[str(product_attribute.pk)] = str(value.pk)
    product.attributes = attr_dict
    product.save(update_fields=['attributes'])

def create_product_type_with_attributes(name, product_specifications):
	product_type = get_or_create_product_type(name=name,is_shipping_required=True)
	product_attributes = create_attributes_and_values(product_specifications)
	product_type.product_attributes.add(*product_attributes)
	return product_type

def create_product_image(product, image_list, placeholder_dir):
	result = []
	directory = os.path.join(placeholder_dir,'products/',str(product.id)+'/')
	
	if not os.path.exists(directory):
			os.makedirs(directory)
	for i,image_url in enumerate(image_list):
		extension = os.path.splitext(urlparse(image_url).path)[-1]
		filename = str(i)+extension
		filepath = os.path.join(directory,filename)
		if os.path.exists(filepath):
			product_image = get_image(directory,filename)

			saved_image,created = ProductImage.objects.get_or_create(product=product, image=product_image, defaults={'image':product_image})
			if created:
				create_product_thumbnails.delay(image_id=saved_image.pk,verbose=False)
				result.append(saved_image)
		else:
			try:
				image = requests.get(image_url)
				
				
				if image.status_code == requests.codes.ok:
					with open(filepath, 'wb') as f:
						f.write(image.content)
					product_image = get_image(directory,filename)
					saved_image,created = ProductImage.objects.get_or_create(product=product, image=product_image, defaults={'image':product_image})
					if created:
						create_product_thumbnails.delay(image_id=saved_image.pk,verbose=False)
						result.append(saved_image)
				else:
					continue
			except requests.exceptions.InvalidSchema as e:
				image = base64.b64decode(image_url.partition('base64,')[2])
				filename = str(i)+'.png'
				
				filepath = os.path.join(directory,filename)
				with open(filepath, 'wb') as f:
					f.write(image)
				product_image = get_image(directory,filename)

				saved_image,created = ProductImage.objects.get_or_create(product=product, image=product_image, defaults={'image':product_image})
				if created:
					create_product_thumbnails.delay(image_id=saved_image.pk,verbose=False)
					result.append(saved_image)
	return result

def create_sale(product,value,**kwargs):
	defaults = {
		'name' : 'Happy %s day!' % fake.word(),
		'type' : DiscountValueType.PERCENTAGE,
		'value' : value
	}
	defaults.update(kwargs)
	sale = Sale.objects.get_or_create(
			value=value,defaults=defaults)[0]
	sale.products.add(product)
	return sale

def create_variant(product, price, sku, **kwargs):
    defaults = {
        'product': product,
        'quantity': fake.random_int(1, 50),
        'cost_price': price,
        'quantity_allocated': fake.random_int(1, 50)}
    defaults.update(kwargs)
    variant = ProductVariant.objects.get_or_create(sku=sku,defaults=defaults)[0]
    return variant

def generate_rating(rated,rating):
	rating_range = [x for x in range(1,6)]

	list_user = User.objects.all().values_list('id', flat=True)
	list_product = Product.objects.all().values_list('id', flat=True)

	for id_product in list_product:
		chance_to_rate = random.uniform(0.0,1.0)

		if chance_to_rate <= rated:
			user_count = random.randint(1,len(list_user))

			random_user = random.shuffle(list_user)[:user_count]

			for user in random_user:
				give_rating = random.uniform(0.0,1.0)

				if give_rating <= rating:
					value = random.choice(rating_range)
					defaults = {
						'product_id' : id_product,
						'user_id' : user,
						'value' : value
					}
					ProductRating.objects.get_or_create(product_id=id_product,user_id=user,defaults=defaults)

					yield 'User %s give rating %s to product %s' % (str(user),str(value),str(id_product))