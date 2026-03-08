from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.utils import timezone

from biblioteca.models import Emprestimo, NotificacaoAtrasoLog


def construir_mensagem(emprestimo, dias_restantes):
    nome = emprestimo.aluno.first_name or emprestimo.aluno.username
    livro = emprestimo.nome_livro
    data_limite = emprestimo.data_devolucao.strftime('%d/%m/%Y')

    assunto = 'Biblioteca Escolar - Lembrete de devolucao de livro'

    texto = (
        f'Olá, {nome}.\n\n'
        'Este é um lembrete da Biblioteca Escolar sobre um livro emprestado em seu nome.\n\n'
        f'Livro: {livro}\n'
        f'Data limite de devolução: {data_limite}\n'
        f'Prazo restante: {dias_restantes} dia(s)\n\n'
        'Pedimos que a devolução seja realizada até a data informada para evitar pendências.\n\n'
        'Em caso de dúvida, procure a equipe da biblioteca.\n\n'
        'Biblioteca Escolar'
    )

    html = f'''
    <html>
      <body style="font-family: Arial, sans-serif; color: #1f2937; line-height: 1.5;">
        <h2 style="margin-bottom: 8px; color: #0f4c5c;">Lembrete de devolução</h2>
        <p>Olá, <strong>{nome}</strong>.</p>
        <p>Este é um lembrete da Biblioteca Escolar sobre um livro emprestado em seu nome.</p>
        <table style="border-collapse: collapse; margin: 12px 0;">
          <tr><td style="padding: 6px 10px; border: 1px solid #d8e1e8;"><strong>Livro</strong></td><td style="padding: 6px 10px; border: 1px solid #d8e1e8;">{livro}</td></tr>
          <tr><td style="padding: 6px 10px; border: 1px solid #d8e1e8;"><strong>Data limite</strong></td><td style="padding: 6px 10px; border: 1px solid #d8e1e8;">{data_limite}</td></tr>
          <tr><td style="padding: 6px 10px; border: 1px solid #d8e1e8;"><strong>Prazo restante</strong></td><td style="padding: 6px 10px; border: 1px solid #d8e1e8;">{dias_restantes} dia(s)</td></tr>
        </table>
        <p>Pedimos que a devolução seja realizada até a data informada para evitar pendências.</p>
        <p>Em caso de dúvida, procure a equipe da biblioteca.</p>
        <p style="margin-top: 20px; color: #475569;">Biblioteca Escolar</p>
      </body>
    </html>
    '''

    return assunto, texto, html


class Command(BaseCommand):
    help = 'Envia notificacoes de lembrete por e-mail quando faltarem 5 dias e 1 dia para a devolucao.'

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        datas_alvo = [hoje + timedelta(days=1), hoje + timedelta(days=5)]

        emprestimos_alvo = list(
            Emprestimo.objects.select_related('aluno').filter(devolvido=False, data_devolucao__in=datas_alvo)
        )

        existing_logs = set(
            NotificacaoAtrasoLog.objects.filter(
                data_referencia=hoje,
                emprestimo_id__in=[e.id for e in emprestimos_alvo],
            ).values_list('emprestimo_id', 'canal')
        )

        enviados = 0
        processados = len(emprestimos_alvo)
        novos_logs = []

        for emprestimo in emprestimos_alvo:
            dias_restantes = (emprestimo.data_devolucao - hoje).days
            destino_email = (emprestimo.aluno.email or '').strip()
            if not destino_email:
                continue

            if (emprestimo.id, NotificacaoAtrasoLog.Canal.EMAIL) in existing_logs:
                continue

            assunto, mensagem_texto, mensagem_html = construir_mensagem(emprestimo, dias_restantes)

            try:
                email = EmailMultiAlternatives(
                    subject=assunto,
                    body=mensagem_texto,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'biblioteca@escola.local'),
                    to=[destino_email],
                )
                email.attach_alternative(mensagem_html, 'text/html')
                email.send(fail_silently=False)
                status = NotificacaoAtrasoLog.Status.ENVIADO
                info = f'E-mail enviado (faltam {dias_restantes} dia(s)).'
                enviados += 1
            except Exception as exc:
                status = NotificacaoAtrasoLog.Status.ERRO
                info = str(exc)

            novos_logs.append(
                NotificacaoAtrasoLog(
                    emprestimo=emprestimo,
                    canal=NotificacaoAtrasoLog.Canal.EMAIL,
                    destino=destino_email,
                    data_referencia=hoje,
                    status=status,
                    mensagem=info,
                )
            )

        if novos_logs:
            NotificacaoAtrasoLog.objects.bulk_create(novos_logs)

        self.stdout.write(
            self.style.SUCCESS(
                f'Lembretes processados. Emprestimos alvo: {processados}. E-mails enviados: {enviados}'
            )
        )
