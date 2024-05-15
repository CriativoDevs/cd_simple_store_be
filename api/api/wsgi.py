"""
WSGI config for api project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# Path to your project directory
path = "/home/criativodevs/cd_simple_store_be/api/"
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

# Import Django and set up the application
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
