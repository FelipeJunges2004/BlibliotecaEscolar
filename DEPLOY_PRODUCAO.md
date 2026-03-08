# Deploy em producao e backup automatico

## 1. Preparacao

```powershell
cd "C:\Users\Felipe Junges\Documents\Codex"
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

## 2. Variaveis de ambiente (exemplo)

```powershell
$env:DJANGO_DEBUG="False"
$env:DJANGO_ALLOWED_HOSTS="seu-dominio.com"
$env:DEFAULT_FROM_EMAIL="biblioteca@escola.local"
$env:EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
$env:EMAIL_HOST="smtp.seuprovedor.com"
$env:EMAIL_PORT="587"
$env:EMAIL_HOST_USER="usuario"
$env:EMAIL_HOST_PASSWORD="senha"
$env:EMAIL_USE_TLS="True"
$env:TWILIO_ACCOUNT_SID=""
$env:TWILIO_AUTH_TOKEN=""
$env:TWILIO_WHATSAPP_FROM="+14155238886"
$env:BACKUP_DIR="C:\Users\Felipe Junges\Documents\Codex\backups"

# Agendador interno do site (automatico)
$env:AUTO_JOBS_ENABLED="True"
$env:AUTO_NOTIFY_HOUR="7"
$env:AUTO_NOTIFY_MINUTE="0"
$env:AUTO_BACKUP_HOUR="23"
$env:AUTO_BACKUP_MINUTE="30"
$env:AUTO_BACKUP_KEEP_DAYS="14"
```

## 3. Subir aplicacao em producao (Windows)

```powershell
python -m waitress --host=0.0.0.0 --port=8000 biblioteca_escolar.wsgi:application
```

Enquanto a aplicacao estiver no ar, ela executa sozinha:
- notificacao de lembrete (5 dias e 1 dia antes)
- backup diario do banco

## 4. Opcional: rotina externa pelo Task Scheduler

Se preferir redundancia externa, use:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\Felipe Junges\Documents\Codex\scripts\rotina_diaria.ps1"
```
