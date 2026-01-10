
import os
import django
from django.conf import settings

# Configure minimal settings for the script
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='secret',
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'userauths',
            'core',
            'adminpanel',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        }],
    )

django.setup()

from django.template.loader import get_template

try:
    t = get_template('adminpanel/vendors/vendor_dashboard.html')
    print("Template loaded successfully")
except Exception as e:
    print(f"Template loading failed: {e}")
