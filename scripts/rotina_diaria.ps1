# Execute este script no agendador (Task Scheduler) diariamente.
Set-Location "C:\Users\Felipe Junges\Documents\Codex"
python manage.py enviar_notificacoes_atraso
python manage.py backup_db --keep-days 14
