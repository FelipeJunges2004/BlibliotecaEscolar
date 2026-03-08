import os
import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cria backup do banco SQLite e remove backups antigos.'

    def add_arguments(self, parser):
        parser.add_argument('--keep-days', type=int, default=7)

    def handle(self, *args, **options):
        db_path = Path(settings.DATABASES['default']['NAME'])
        if not db_path.exists():
            self.stderr.write(self.style.ERROR(f'Banco nao encontrado: {db_path}'))
            return

        backup_dir = Path(getattr(settings, 'BACKUP_DIR', settings.BASE_DIR / 'backups'))
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"backup_{timestamp}.sqlite3"
        shutil.copy2(db_path, backup_file)
        self.stdout.write(self.style.SUCCESS(f'Backup criado: {backup_file}'))

        keep_days = options['keep_days']
        cutoff = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        removidos = 0
        for arquivo in backup_dir.glob('backup_*.sqlite3'):
            if arquivo.stat().st_mtime < cutoff:
                os.remove(arquivo)
                removidos += 1

        if removidos:
            self.stdout.write(self.style.WARNING(f'Backups antigos removidos: {removidos}'))
