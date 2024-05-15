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
path = "/home/criativodevs/cd_simple_store_be"
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

# Activate your virtual environment
activate_this = "/home/criativodevs/.virtualenvs/myenv/bin/activate_this.py"
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import Django and set up the application
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
