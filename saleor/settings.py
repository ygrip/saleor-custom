import ast
import os.path

import dj_database_url
import dj_email_url
import django_cache_url
from django.contrib.messages import constants as messages
from django.utils.translation import gettext_lazy as _
from django_prices.templatetags.prices_i18n import get_currency_fraction


def get_list(text):
    return [item.strip() for item in text.split(',')]


DEBUG = ast.literal_eval(os.environ.get('DEBUG', 'True'))

SITE_ID = 1

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

ROOT_URLCONF = 'saleor.urls'

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

WSGI_APPLICATION = 'saleor.wsgi.application'

ADMINS = (
    ('Yunaz Gilang', 'yunaz.gilang@gmail.com'),
)
MANAGERS = ADMINS

INTERNAL_IPS = get_list(os.environ.get('INTERNAL_IPS', '127.0.0.1'))

# Some cloud providers like Heroku export REDIS_URL variable instead of CACHE_URL
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHE_URL = os.environ.setdefault('CACHE_URL', REDIS_URL)
CACHES = {'default': django_cache_url.config()}

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://saleor:saleor@localhost:5432/saleor',
        conn_max_age=600)}


TIME_ZONE = 'Asia/Jakarta'
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('bg', _('Bulgarian')),
    ('de', _('German')),
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fa-ir', _('Persian (Iran)')),
    ('fr', _('French')),
    ('hu', _('Hungarian')),
    ('it', _('Italian')),
    ('ja', _('Japanese')),
    ('ko', _('Korean')),
    ('nb', _('Norwegian')),
    ('nl', _('Dutch')),
    ('pl', _('Polish')),
    ('pt-br', _('Portuguese (Brazil)')),
    ('ro', _('Romanian')),
    ('ru', _('Russian')),
    ('sk', _('Slovak')),
    ('tr', _('Turkish')),
    ('uk', _('Ukrainian')),
    ('vi', _('Vietnamese')),
    ('zh-hans', _('Chinese'))]
LOCALE_PATHS = [os.path.join(PROJECT_ROOT, 'locale')]
USE_I18N = True
USE_L10N = True
USE_TZ = True

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

EMAIL_URL = os.environ.get('EMAIL_URL')
SENDGRID_USERNAME = os.environ.get('SENDGRID_USERNAME')
SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
if not EMAIL_URL and SENDGRID_USERNAME and SENDGRID_PASSWORD:
    EMAIL_URL = 'smtp://%s:%s@smtp.sendgrid.net:587/?tls=True' % (
        SENDGRID_USERNAME, SENDGRID_PASSWORD)
email_config = dj_email_url.parse(EMAIL_URL or 'console://')

EMAIL_FILE_PATH = email_config['EMAIL_FILE_PATH']
EMAIL_HOST_USER = email_config['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = email_config['EMAIL_HOST_PASSWORD']
EMAIL_HOST = email_config['EMAIL_HOST']
EMAIL_PORT = email_config['EMAIL_PORT']
EMAIL_BACKEND = email_config['EMAIL_BACKEND']
EMAIL_USE_TLS = email_config['EMAIL_USE_TLS']
EMAIL_USE_SSL = email_config['EMAIL_USE_SSL']

ENABLE_SSL = ast.literal_eval(
    os.environ.get('ENABLE_SSL', 'False'))

if ENABLE_SSL:
    SECURE_SSL_REDIRECT = not DEBUG

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
ORDER_FROM_EMAIL = os.getenv('ORDER_FROM_EMAIL', DEFAULT_FROM_EMAIL)

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    )
}


STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    ('assets', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'assets')),
    ('favicons', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'favicons')),
    ('images', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'images')),
    ('fonts', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'fonts')),
    ('dashboard', os.path.join(PROJECT_ROOT, 'saleor', 'static', 'dashboard'))
    ]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder']

context_processors = [
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.debug',
    'django.template.context_processors.i18n',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.template.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.template.context_processors.request',
    'saleor.core.context_processors.default_currency',
    'saleor.cart.context_processors.cart_counter',
    'saleor.core.context_processors.navigation',
    'saleor.core.context_processors.search_enabled',
    'saleor.site.context_processors.site',
    'social_django.context_processors.backends',
    'social_django.context_processors.login_redirect']

loaders = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader']

if not DEBUG:
    loaders = [('django.template.loaders.cached.Loader', loaders)]

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(PROJECT_ROOT, 'templates')],
    'OPTIONS': {
        'debug': DEBUG,
        'context_processors': context_processors,
        'loaders': loaders,
        'string_if_invalid': '<< MISSING VARIABLE "%s" >>' if DEBUG else ''}},
        
    ]

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY')

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django_babel.middleware.LocaleMiddleware',
    'graphql_jwt.middleware.JSONWebTokenMiddleware',
    'saleor.core.middleware.discounts',
    'saleor.core.middleware.google_analytics',
    'saleor.core.middleware.country',
    'saleor.core.middleware.currency',
    'saleor.core.middleware.site',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'impersonate.middleware.ImpersonateMiddleware',
    ]


DEBUG_TOOLBAR_CONFIG = {
    # Add in this line to disable the panel
    'SHOW_TOOLBAR_CALLBACK': lambda r: False,
    'JQUERY_URL' : '',
    'DISABLE_PANELS': {
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.templates.TemplatesPanel'
    },
    'SKIP_TEMPLATE_PREFIXES': ('django/forms/widgets/', 'admin/widgets/'),
}

INSTALLED_APPS = [
    # External apps that need to go before django's
    'storages',

    # Django modules
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'django.contrib.postgres',
    'django.forms',
    'rest_framework',

    # Local apps
    'saleor.account',
    'saleor.discount',
    'saleor.product',
    'saleor.cart',
    'saleor.checkout',
    'saleor.core',
    'saleor.graphql',
    'saleor.menu',
    'saleor.order.OrderAppConfig',
    'saleor.dashboard',
    'saleor.seo',
    'saleor.shipping',
    'saleor.search',
    'saleor.site',
    'saleor.data_feeds',
    'saleor.page',
    'saleor.dictionary',
    'saleor.track',
    'saleor.promo',
    'saleor.feature',

    # External apps
    'versatileimagefield',
    'django_babel',
    'bootstrap4',
    'django_prices',
    'django_prices_openexchangerates',
    'graphene_django',
    'mptt',
    'payments',
    'webpack_loader',
    'social_django',
    'django_countries',
    'django_filters',
    'django_celery_results',
    'impersonate',
    'phonenumber_field'
    ]

if DEBUG:
    MIDDLEWARE.append(
        'debug_toolbar.middleware.DebugToolbarMiddleware')
    INSTALLED_APPS.append('debug_toolbar')

ENABLE_SILK = ast.literal_eval(os.environ.get('ENABLE_SILK', 'False'))
if ENABLE_SILK:
    MIDDLEWARE.insert(0, 'silk.middleware.SilkyMiddleware')
    INSTALLED_APPS.append('silk')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'INFO',
        'handlers': ['console']},
    'formatters': {
        'verbose': {
            'format': (
                '%(levelname)s %(name)s %(message)s'
                ' [PID:%(process)d:%(threadName)s]')},
        'simple': {
            'format': '%(levelname)s %(message)s'}},
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'}},
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'},
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'}},
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            'propagate': True},
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True},
        'saleor': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True}}}

AUTH_USER_MODEL = 'account.User'

LOGIN_URL = '/account/login/'

DEFAULT_COUNTRY = 'ID'
DEFAULT_CURRENCY = 'IDR'
DEFAULT_DECIMAL_PLACES = get_currency_fraction(DEFAULT_CURRENCY)
AVAILABLE_CURRENCIES = [DEFAULT_CURRENCY]

OPENEXCHANGERATES_API_KEY = os.environ.get('OPENEXCHANGERATES_API_KEY')

ACCOUNT_ACTIVATION_DAYS = 3

LOGIN_REDIRECT_URL = 'home'

GOOGLE_ANALYTICS_TRACKING_ID = os.environ.get('GOOGLE_ANALYTICS_TRACKING_ID')

# VAT configuration
# Enabling vat requires valid vatlayer access key.
VATLAYER_ACCESS_KEY = os.environ.get('VATLAYER_ACCESS_KEY')

def get_host():
    from django.contrib.sites.models import Site
    return Site.objects.get_current().domain


PAYMENT_HOST = get_host

PAYMENT_MODEL = 'order.Payment'

PAYMENT_VARIANTS = {
    'default': ('payments.dummy.DummyProvider', {})}

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

CHECKOUT_PAYMENT_CHOICES = [
    ('default', 'Dummy provider')]

MESSAGE_TAGS = {
    messages.ERROR: 'danger'}

LOW_STOCK_THRESHOLD = 10
MAX_CART_LINE_QUANTITY = int(os.environ.get('MAX_CART_LINE_QUANTITY', 50))

PAGINATE_BY = 16
DASHBOARD_PAGINATE_BY = 30
DASHBOARD_SEARCH_LIMIT = 5

bootstrap4 = {
    'set_placeholder': False,
    'set_required': False,
    'success_css_class': '',
    'form_renderers': {
        'default': 'saleor.core.utils.form_renderer.FormRenderer'}}

TEST_RUNNER = ''

ALLOWED_HOSTS = get_list(os.environ.get('ALLOWED_HOSTS', 'localhost'))

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Amazon S3 configuration
AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_STATIC_CUSTOM_DOMAIN')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_MEDIA_BUCKET_NAME = os.environ.get('AWS_MEDIA_BUCKET_NAME')
AWS_MEDIA_CUSTOM_DOMAIN = os.environ.get('AWS_MEDIA_CUSTOM_DOMAIN')
AWS_QUERYSTRING_AUTH = ast.literal_eval(
    os.environ.get('AWS_QUERYSTRING_AUTH', 'False'))

if AWS_STORAGE_BUCKET_NAME:
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

if AWS_MEDIA_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'saleor.core.storages.S3MediaStorage'
    THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'products': [
        ('product_gallery', 'crop__540x540'),
        ('product_gallery_2x', 'crop__1080x1080'),
        ('product_small', 'crop__60x60'),
        ('product_small_2x', 'crop__120x120'),
        ('product_list', 'crop__255x255'),
        ('product_list_2x', 'crop__510x510')]}

VERSATILEIMAGEFIELD_SETTINGS = {
    # Images should be pre-generated on Production environment
    'create_images_on_demand': ast.literal_eval(
        os.environ.get('CREATE_IMAGES_ON_DEMAND', repr(DEBUG))),
}

PLACEHOLDER_IMAGES = {
    60: 'images/placeholder60x60.png',
    120: 'images/placeholder120x120.png',
    255: 'images/placeholder255x255.png',
    540: 'images/placeholder540x540.png',
    1080: 'images/placeholder1080x1080.png'}

DEFAULT_PLACEHOLDER = 'images/placeholder255x255.png'

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'assets/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'webpack-bundle.json'),
        'POLL_INTERVAL': 0.1,
        'IGNORE': [
            r'.+\.hot-update\.js',
            r'.+\.map']}}


LOGOUT_ON_PASSWORD_CHANGE = False

# SEARCH CONFIGURATION
DB_SEARCH_ENABLED = True

# support deployment-dependant elastic enviroment variable
ES_URL = (os.environ.get('ELASTICSEARCH_URL') or
          os.environ.get('SEARCHBOX_URL') or os.environ.get('BONSAI_URL'))

ENABLE_SEARCH = bool(ES_URL) or DB_SEARCH_ENABLED  # global search disabling

SEARCH_BACKEND = 'saleor.search.backends.postgresql'

if ES_URL:
    SEARCH_BACKEND = 'saleor.search.backends.elasticsearch'
    INSTALLED_APPS.append('django_elasticsearch_dsl')
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': ES_URL}}


GRAPHENE = {'MIDDLEWARE': ['graphene_django.debug.DjangoDebugMiddleware']}

AUTHENTICATION_BACKENDS = [
    'saleor.account.backends.facebook.CustomFacebookOAuth2',
    'saleor.account.backends.google.CustomGoogleOAuth2',
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend']

SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details']

SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, email'}

# CELERY SETTINGS
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or ''
CELERY_TASK_ALWAYS_EAGER = False if CELERY_BROKER_URL else True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'

# Impersonate module settings
IMPERSONATE = {
    'URI_EXCLUSIONS': [r'^dashboard/'],
    'CUSTOM_USER_QUERYSET': 'saleor.account.impersonate.get_impersonatable_users',  # noqa
    'USE_HTTP_REFERER': True,
    'CUSTOM_ALLOW': 'saleor.account.impersonate.can_impersonate'}


# Rich-text editor
ALLOWED_TAGS = [
    'a',
    'b',
    'blockquote',
    'br',
    'em',
    'h2',
    'h3',
    'i',
    'img',
    'li',
    'ol',
    'p',
    'strong',
    'ul']
ALLOWED_ATTRIBUTES = {
    '*': ['align', 'style'],
    'a': ['href', 'title'],
    'img': ['src']}
ALLOWED_STYLES = ['text-align']


# Slugs for menus precreated in Django migrations
DEFAULT_MENUS = {
    'top_menu_name': 'navbar',
    'bottom_menu_name': 'footer'}