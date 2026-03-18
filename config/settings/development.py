from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1']

# Use console email in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use local file storage in dev
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
