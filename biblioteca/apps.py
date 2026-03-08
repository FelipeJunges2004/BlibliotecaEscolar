import os
import sys

from django.apps import AppConfig
from django.conf import settings


class BibliotecaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'biblioteca'

    def ready(self):
        if not getattr(settings, 'AUTO_JOBS_ENABLED', True):
            return

        # Evita iniciar scheduler em comandos administrativos pontuais.
        skip_commands = {
            'makemigrations',
            'migrate',
            'collectstatic',
            'shell',
            'createsuperuser',
            'test',
            'check',
            'backup_db',
            'enviar_notificacoes_atraso',
        }

        if len(sys.argv) > 1:
            cmd = sys.argv[1]
            if cmd in skip_commands:
                return

            # Em desenvolvimento, runserver chama ready duas vezes.
            if cmd == 'runserver' and settings.DEBUG and os.environ.get('RUN_MAIN') != 'true':
                return

        from .scheduler import start_scheduler

        start_scheduler()
