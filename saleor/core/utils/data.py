import glob, os
import requests
import json
from pprint import pprint

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

fake = Factory.create()

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
	result = []
	total = 0

	list_category = []
	i = 0
	for filename in glob.glob("*.json"):
		file = {}
		product_type_name = ' '.join(map(lambda e: e.capitalize(), 
								os.path.splitext(os.path.basename(filename))[0].replace('produk-','').split('-')))
		file['filename'] = filename
		file['product_type'] = product_type_name
		content = json.load(open(filename))
		for element in content:
			product_type = create_product_type_with_attributes(product_type_name,
								element.get('produk_specification',{}))
			brand = create_brand(placeholders_dir, 
								name=element.get('brand'),
								image=element.get('brand_image'),
								url=element.get('brand_link'),
								)
			product_category = create_category(element.get('category',{}),placeholders_dir)
			title = element.get('title')
			description = element.get('produk_description')
			service = json.dumps(element.get('produk_services'))
			features = json.dumps(element.get('produk_features'))
			check_price = element.get('harga')
			sku = element.get('produk_code').get('SKU Number')
			price = int(check_price.get('Harga Awal',{})) if 'Harga Awal' in check_price else int(check_price.get('Harga',{}))
			location = create_merchant_location(element.get('merchant_location'))
			product = create_product(name=title,
									product_type=product_type,
									category=product_category,
									information=features,
									price=price,
									brand_id=brand,
									description=description,
									service=service,
									location=location
									)
			set_product_attributes(product, product_type)
			create_product_image(product,element.get('url_images'),placeholders_dir)
			create_variant(product, sku=sku)
			if 'Diskon' in check_price:
				create_sale(product,float(check_price.get('Diskon')))
		
			check_shipping = element.get('shipping_option',{})
			if check_shipping:
				shipping = []
				create_shipping_method(shipping.append(element.get('shipping_option',{})))

			sentence = title+' '+
						element.get('brand')+' '+
						description+' '+
						(' '.join(element.get('produk_features')))
			product_tags = populate_feature(sentence,2)[:5]

			for tag in product_tags:
				feature, created = Feature.objects.get_or_create(word=tag['word'], defaults={'count':1})

				if not created:
					feature.count = feature.count + 1
					feature.save()

				product_tag = ProductFeature.objects.get_or_create(feature_id=feature,product_id=product,defaults={'frequency':tag['count']})

		result.append(file)
		if stdout is not None:
            stdout.write('Product: %s (%s), %s variant(s)' % (
                product, product_type.name, len(variant_combinations) or 1))

	for data in result:
		yield json.dumps(data,indent=4,default=str)


def create_product(**kwargs):
    defaults = {
        'seo_description': strip_html_and_truncate(description[0], 300)}
    defaults.update(kwargs)
    return Product.objects.create(**defaults)

def create_merchant_location(location):
	defaults = {
		'location' : location
	}
	return MerchantLocation.get_or_create(location=location,defaults=defaults)

def create_shipping_method(shipping_data, **kwargs):
	options = []
	for shipping in shipping_data:
		defaults = {
			'name' : shipping['name'],
		}
		defaults.update(kwargs)
		ship = ShippingMethod.objects.get_or_create(**defaults)[0]

		if ship:
			ship.price_per_country.create(price=shipping['price'])
			options.append(ship)
	return options

def create_brand(placeholders_dir,brand_data, **kwargs):
	image_url = brand_data['image']
	image = requests.get(image_url)
	filename = brand_data['name']+'.png'
	directory = os.path.join(placeholders_dir,'brands')
	if not os.path.exists(directory):
		os.makedirs(directory)
	filepath = os.path.join(directory,filename)
	with open(filepath, 'wb') as f:
		f.write(image.content)
	brand_image = get_image(filepath)
	defaults = {
		'brand_name' : brand_data['name'],
		'brand_link' : brand_data['url'],
		'brand_image' : brand_image
	}
	defaults.update(kwargs)
	brand = Brand.objects.get_or_create(**defaults)[0]
	return brand

def create_attributes_and_values(attribute_data):
    attributes = []
    for attribute_name, attribute_value in attribute_data.items():
        attribute = create_attribute(
            slug=slugify(attribute_name), name=attribute_name)
        attribute_values = []
        attribute_values.append(attribute_value)
        for value in attribute_values:
            create_attribute_value(attribute, name=value)
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
    product_list_images_dir = os.path.join(
        placeholder_dir, PRODUCTS_LIST_DIR)
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
			result.append(get_or_create_category({'name':saved_category.name,
				'image_name':str(saved_category.id)+'.jpg'},
				placeholders_dir))
		else:
			defaults = {
				'name' : category_data[i-1],
			}
			parent = Category.objects.get_or_create(name=category_data[i-1],defaults=defaults)[0]
			result.append(get_or_create_category({'name':saved_category.name,
				'image_name':str(saved_category.id)+'.jpg',
				'parent':parent.id},
				placeholders_dir))	
	return result[-1]

def get_or_create_category(category_schema, placeholder_dir):
    if 'parent' in category_schema:
        parent_id = category_schema['parent']
    else:
        parent_id = None
    category_name = category_schema['name']
    image_name = category_schema['image_name']
    image_dir = get_product_list_images_dir(placeholder_dir)
    defaults = {
        'description': fake.text(),
        'parent_id':parent_id,
        'slug': slugify(category_name),
        'background_image': get_image(image_dir, image_name)}
    return Category.objects.update_or_create(
        name=category_name, defaults=defaults)[0]


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
	for i,image_url in enumerate(image_list):
		image = requests.get(image_url)
		filename = i+'.png'
		directory = os.path.join(placeholder_dir,product.id)
		if not os.path.exists(directory):
			os.makedirs(directory)
		filepath = os.path.join(directory,filename)
		with open(filepath, 'wb') as f:
			f.write(image.content)
		product_image = get_image(filepath)
		saved_image = ProductImage(product=product, image=image)
		saved_image.save()
		if i == 0:
			create_product_thumbnails.delay(saved_image.pk)
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
        value=value,defaults=defaults)
    sale.products.add(product)
    return sale

def create_variant(product, price, **kwargs):
    defaults = {
        'product': product,
        'quantity': fake.random_int(1, 50),
        'cost_price': price,
        'quantity_allocated': fake.random_int(1, 50)}
    defaults.update(kwargs)
    variant = ProductVariant(**defaults)
    if variant.attributes:
        variant.name = get_name_from_attributes(variant)
    variant.save()
    return variant