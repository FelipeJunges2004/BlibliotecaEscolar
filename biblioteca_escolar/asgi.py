"""
ASGI config for biblioteca_escolar project.
"""

import os
import site

from django.core.asgi import get_asgi_application

site.addsitedir(site.getusersitepackages())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_escolar.settings')

application = get_asgi_application()
