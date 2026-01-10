import os
import django
from django.conf import settings

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
            'customer',
            'adminpanel',
            'django.contrib.messages',
            'django.contrib.sessions',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        MIDDLEWARE=[
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        }],
        AUTH_USER_MODEL='userauths.User',
    )

django.setup()

from django.core.management import call_command
call_command('migrate', verbosity=0)

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from adminpanel.views.profile import ProfileView
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

# Setup data
try:
    user = User.objects.create(username='testrider', email='test@test.com', password='password')
except Exception:
    user = User.objects.get(username='testrider')

# Request
factory = RequestFactory()
request = factory.get('/adminpanel/profile/')
request.user = user

# Add session to request
middleware = SessionMiddleware(lambda r: None)
middleware.process_request(request)
request.session.save()


# Test the view's get_context_data method directly
try:
    view = ProfileView()
    view.setup(request)
    context = view.get_context_data()
    print("Context retrieved successfully")
    print(context)
except Exception as e:
    print(f"Caught expected error: {e}")
    import traceback
    traceback.print_exc()
