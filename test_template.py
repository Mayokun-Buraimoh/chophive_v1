
import os
import django
from django.conf import settings
from django.template import Context, Template

# Configure minimal settings for the script
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='secret',
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'userauths',
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
    # Try to load the template
    # We might need to mock some tags if they depend on deep context
    # But let's see if it parses.
    t = get_template('adminpanel/profile/profile.html')
    print("Template loaded successfully")
except Exception as e:
    print(f"Template loading failed: {e}")
