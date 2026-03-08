import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.core.management import call_command

logger = logging.getLogger(__name__)
_scheduler = None
_started = False


def _run_notify_job():
    try:
        call_command('enviar_notificacoes_atraso')
        logger.info('Job automatico: notificacoes executado com sucesso.')
    except Exception as exc:
        logger.exception('Falha ao executar job de notificacoes: %s', exc)


def _run_backup_job():
    keep_days = getattr(settings, 'AUTO_BACKUP_KEEP_DAYS', 14)
    try:
        call_command('backup_db', keep_days=keep_days)
        logger.info('Job automatico: backup executado com sucesso.')
    except Exception as exc:
        logger.exception('Falha ao executar job de backup: %s', exc)


def start_scheduler():
    global _scheduler, _started

    if _started or not getattr(settings, 'AUTO_JOBS_ENABLED', True):
        return

    _scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    _scheduler.add_job(
        _run_notify_job,
        trigger=CronTrigger(
            hour=getattr(settings, 'AUTO_NOTIFY_HOUR', 7),
            minute=getattr(settings, 'AUTO_NOTIFY_MINUTE', 0),
        ),
        id='biblioteca_notificacoes_diarias',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        _run_backup_job,
        trigger=CronTrigger(
            hour=getattr(settings, 'AUTO_BACKUP_HOUR', 23),
            minute=getattr(settings, 'AUTO_BACKUP_MINUTE', 30),
        ),
        id='biblioteca_backup_diario',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    _started = True
    logger.info('Agendador automatico iniciado.')

    def _shutdown():
        global _started
        if _scheduler and _scheduler.running:
            _scheduler.shutdown(wait=False)
        _started = False

    atexit.register(_shutdown)
