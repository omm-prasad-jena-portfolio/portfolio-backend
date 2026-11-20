"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# Run database migrations and seed default study data on startup if needed
try:
    from django.core.management import call_command
    call_command("migrate", interactive=False)
    from api.models import Subject
    if not Subject.objects.exists():
        call_command("seed_study_data")
except Exception as e:
    print("Auto-migration/seed notice on startup:", e)
