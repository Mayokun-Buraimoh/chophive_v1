
import os
import django
from django.conf import settings
from django.test import RequestFactory
from django.core.management import call_command

# Configure minimal settings for the script
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='secret',
        ROOT_URLCONF=__name__,
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'userauths',
            'core',
            'adminpanel',
            'django.contrib.messages',
            'django.contrib.sessions',
        ],
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        }],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        AUTH_USER_MODEL='userauths.User',
    )

django.setup()
call_command('migrate', verbosity=0)

from adminpanel.views.dashboard import AdminOrderListView
from django.contrib.auth import get_user_model
from core.models import Order

User = get_user_model()

# Setup data
try:
    user = User.objects.create(username='admin_test', email='admin@test.com', password='password')
except Exception:
    user = User.objects.get(username='admin_test')

# Make user admin
from django.contrib.auth.models import Group
admin_group, _ = Group.objects.get_or_create(name='Admin')
user.groups.add(admin_group)

# Create an order
Order.objects.create(oid='123', status='Pending', total=1000)

# Request
factory = RequestFactory()
request = factory.get('/admin/orders/')
request.user = user

# Add session to request
from django.contrib.sessions.middleware import SessionMiddleware
middleware = SessionMiddleware(lambda r: None)
middleware.process_request(request)
request.session.save()

# Test the view
try:
    view = AdminOrderListView.as_view()
    response = view(request)
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
       print("Failed response.")
    else:
       # render
       response.render()
       print("Rendered successfully")
except Exception as e:
    print(f"Caught error: {e}")
    import traceback
    traceback.print_exc()
